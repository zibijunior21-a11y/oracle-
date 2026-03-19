import hashlib
import secrets
import logging
from datetime import datetime, timedelta, timezone
import pymysql
import pymysql.cursors
import streamlit as st

# ================= HELPER =================
def now_utc():
    # Remplace l'ancien `utcnow()` déprécié en Python 3.12 
    # Le `.replace(tzinfo=None)` permet d'être compatible avec le "TIMESTAMP" pur de MySQL
    return datetime.now(timezone.utc).replace(tzinfo=None)

# ================= CONFIG =================
DB_CONFIG = {
    "host": st.secrets.get("DB_HOST", "localhost"),
    # IMPORTANT: Streamlit stocke souvent dans le toml tout en String, 
    # la DB a absolument besoin d'un port en Entier.
    "port": int(st.secrets.get("DB_PORT", 3306)),
    "user": st.secrets.get("DB_USER", "root"),
    "password": st.secrets.get("DB_PASS", ""),
    "database": st.secrets.get("DB_NAME", "qto_users"),
    "charset": "utf8mb4",
}

# ================= CONNEXION =================
def get_conn():
    return pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        charset=DB_CONFIG["charset"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False, # <-- Le autocommit est sur False, donc on DOIT utiliser des ROLLBACK
    )

# ================= UTILS =================
def _hash(password, salt_hex):
    # Sécurité standard OWASP : PBKDF2 plutôt qu'un sha256 seul qui est ultra vulnérable au Brute Force.
    salt_bytes = bytes.fromhex(salt_hex)
    pwd_hash = hashlib.pbkdf2_hmac(
        hash_name='sha256',
        password=password.encode('utf-8'),
        salt=salt_bytes,
        iterations=100000 # 100 000 passages, c'est ce qui ralenti volontairement la résolution par un attaquant
    )
    return pwd_hash.hex()

def _gen_key(length=24):
    # Optimisation de secrets
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# ================= INIT DB =================
def init():
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            # USERS
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE,
                username VARCHAR(255),
                pw_hash VARCHAR(255),
                salt VARCHAR(32),
                plan VARCHAR(20),
                expires_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                active BOOLEAN DEFAULT 1
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # LICENSES
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                license_key VARCHAR(255) UNIQUE,
                plan VARCHAR(20),
                days INT,
                active BOOLEAN DEFAULT 1,
                used_by VARCHAR(255) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NULL,
                renewed_at TIMESTAMP NULL,
                renew_count INT DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

        conn.commit()
        print("✅ DB initialisée avec succès.")

    except Exception as e:
        conn.rollback() # Règle d'or de ACID, rollback de tout en cas d'erreur avant de relancer l'erreur
        logging.error(f"❌ Erreur DB: {e}")
        raise e
    finally:
        conn.close()

# ================= CREATE LICENSE =================
def create_license(plan="PRO", days=30):
    key = _gen_key()
    now = now_utc()
    exp = now + timedelta(days=days)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO licenses(license_key, plan, days, created_at, expires_at)
                VALUES(%s, %s, %s, %s, %s)
            """, (key, plan, days, now, exp))
        conn.commit()
        return key
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ================= VERIFY LICENSE =================
def check_license(email):
    # La lecture seule n'a pas strictement besoin de try.. except rollback mais c'est propre.
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM licenses WHERE used_by=%s", (email,))
            lic = cur.fetchone()

            if not lic:
                return {"ok": False, "msg": "Aucune licence trouvée"}

            if not lic["active"]:
                return {"ok": False, "msg": "La licence a été désactivée par un administrateur."}

            if lic["expires_at"] and now_utc() > lic["expires_at"]:
                return {"ok": False, "expired": True, "msg": "Votre licence a expiré."}

            return {"ok": True, "plan": lic["plan"], "expires_at": lic["expires_at"]}
    finally:
        conn.close()

# ================= RENEW LICENSE =================
def renew_license(key, days=30):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM licenses WHERE license_key=%s FOR UPDATE", (key,)) # <-- Verrou (Lock) sécurité!
            lic = cur.fetchone()

            if not lic:
                return {"ok": False, "msg": "Licence introuvable"}

            now = now_utc()
            
            if lic["expires_at"] and now > lic["expires_at"]:
                new_exp = now + timedelta(days=days)
            else:
                base = lic["expires_at"] or now
                new_exp = base + timedelta(days=days)

            # Maj de la licence
            cur.execute("""
                UPDATE licenses
                SET expires_at=%s, renewed_at=%s, renew_count = renew_count + 1
                WHERE license_key=%s
            """, (new_exp, now, key))
            
            # BUG CORRIGÉ : Si quelqu'un l'utilise déjà, prolonger aussi ses datas côté table users !
            if lic["used_by"]:
                cur.execute("""
                    UPDATE users 
                    SET expires_at=%s 
                    WHERE email=%s
                """, (new_exp, lic["used_by"]))

        conn.commit()
        return {"ok": True, "new_exp": new_exp}

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ================= REGISTER =================
def register(email, username, password, key):
    email = email.lower().strip()
    key   = key.strip().upper()

    conn = get_conn()
    try:
        with conn.cursor() as cur:

            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                return {"ok": False, "msg": "L'email est déjà utilisé."}

            # L'ajout du FOR UPDATE évite la "Race Condition" de 2 users validant la clé en même temps.
            cur.execute("SELECT * FROM licenses WHERE license_key=%s AND active=1 FOR UPDATE", (key,))
            lic = cur.fetchone()

            if not lic:
                return {"ok": False, "msg": "La clé renseignée est invalide ou introuvable."}

            if lic["used_by"]:
                return {"ok": False, "msg": "Cette clé d'activation a déjà été utilisée."}

            # Cryptographie avec sel de 32 de longueur généré en bytes de 16, qui finit encodé en hex de 32 str
            salt_hex = secrets.token_hex(16)
            hashed_pw = _hash(password, salt_hex)

            cur.execute("""
                INSERT INTO users(email, username, pw_hash, salt, plan, expires_at)
                VALUES(%s, %s, %s, %s, %s, %s)
            """, (email, username, hashed_pw, salt_hex, lic["plan"], lic["expires_at"]))

            # Associe formellement l'utilisateur a sa clé !
            cur.execute("UPDATE licenses SET used_by=%s WHERE license_key=%s", (email, key))

        conn.commit()
        return {"ok": True}

    except Exception as e:
        conn.rollback() # Le code garantit ici de relâcher l'user qui s'enregistrait.
        raise e
    finally:
        conn.close()

# ================= LOGIN =================
def login(email, password):
    email = email.lower().strip()
    
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()

            if not user:
                return {"ok": False, "msg": "Email ou mot de passe incorrect."}

            # Sécurité contre le dictionnaire brute : re-check contre Pbkdf2 !
            if _hash(password, user["salt"]) != user["pw_hash"]:
                return {"ok": False, "msg": "Email ou mot de passe incorrect."}

            if not user["active"]:
                return {"ok": False, "msg": "Compte inactif ou banni."}

            # On vérifie de nouveau le contexte de licence
            lic = check_license(email)
            if not lic["ok"]:
                return lic
            
            # MISE A JOUR OUBLIÉE dans le vieux script : L'historique des co!
            cur.execute("UPDATE users SET last_login=%s WHERE email=%s", (now_utc(), email))
            conn.commit() 
            # Comme on a écrit un login_historique, le COMMIT devient ici primordial.
            
            return {
                "ok": True,
                "username": user["username"],
                "plan": lic["plan"],
                "expires_at": lic["expires_at"]
            }

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ================= MAIN =================
if __name__ == "__main__":
    init()
