"""
================================================================================
  QUANTUM TRADE ORACLE — Base de données MySQL (phpMyAdmin / WAMP)
================================================================================
  PRÉREQUIS :
    pip install pymysql

  CONFIGURATION :
    Modifiez DB_CONFIG ci-dessous avec vos infos
    Accès phpMyAdmin : http://localhost/phpmyadmin
================================================================================
"""

import hashlib, secrets, os
from datetime import datetime, timedelta

try:
    import pymysql
    import pymysql.cursors
    MYSQL_OK = True
except ImportError:
    MYSQL_OK = False
    print("❌ pymysql manquant — installez : pip install pymysql")

# ══════════════════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURATION — MODIFIEZ ICI
# ══════════════════════════════════════════════════════════════════════════════
import sqlite3

DB_PATH = "qto_users.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("✅ SQLite connecté")

# ══════════════════════════════════════════════════════════════════════════════
#  CONNEXION
# ══════════════════════════════════════════════════════════════════════════════
def get_conn():
    if not MYSQL_OK:
        raise RuntimeError("pymysql non installé. Lancez : pip install pymysql")
    try:
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset=DB_CONFIG["charset"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
        return conn
    except pymysql.err.OperationalError as e:
        raise RuntimeError(f"""
❌ ERREUR CONNEXION MYSQL :
   {e}

   Vérifiez :
   1. WAMPServer est lancé (icône verte)
   2. La base 'qto_users' existe dans phpMyAdmin
      → http://localhost/phpmyadmin
   3. Le mot de passe dans DB_CONFIG est correct
        """)

# ══════════════════════════════════════════════════════════════════════════════
#  INITIALISATION — Crée les tables automatiquement
# ══════════════════════════════════════════════════════════════════════════════
def init():
    if not MYSQL_OK:
        print("⚠️  pymysql manquant — pip install pymysql")
        return
    try:
        conn = get_conn()
        with conn.cursor() as cur:

            cur.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                `key`       VARCHAR(25)  PRIMARY KEY,
                plan        VARCHAR(20)  DEFAULT 'PRO',
                days        INT          DEFAULT 365,
                created_at  DATETIME     NOT NULL,
                expires_at  DATETIME     DEFAULT NULL,
                active      TINYINT(1)   DEFAULT 1,
                used_by     VARCHAR(255) DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INT          AUTO_INCREMENT PRIMARY KEY,
                email       VARCHAR(255) UNIQUE NOT NULL,
                username    VARCHAR(100) NOT NULL,
                pw_hash     VARCHAR(64)  NOT NULL,
                salt        VARCHAR(32)  NOT NULL,
                plan        VARCHAR(20)  DEFAULT 'PRO',
                expires_at  DATETIME     DEFAULT NULL,
                active      TINYINT(1)   DEFAULT 1,
                created_at  DATETIME     NOT NULL,
                last_login  DATETIME     DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id      INT         AUTO_INCREMENT PRIMARY KEY,
                email   VARCHAR(255),
                action  VARCHAR(20),
                ok      TINYINT(1),
                info    VARCHAR(255),
                ts      DATETIME    NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

        conn.commit()
        conn.close()
        print("✅ Base MySQL initialisée avec succès.")
    except Exception as e:
        print(f"❌ Erreur init MySQL : {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════
def _hash(password, salt):
    return hashlib.sha256(f"{salt}{password}{salt}".encode()).hexdigest()

def _gen_key():
    b = hashlib.sha256(secrets.token_hex(16).encode()).hexdigest()[:16].upper()
    return f"QTO-{b[0:4]}-{b[4:8]}-{b[8:12]}-{b[12:16]}"

def _log(cur, email, action, ok, info=""):
    cur.execute(
        "INSERT INTO logs(email,action,ok,info,ts) VALUES(%s,%s,%s,%s,%s)",
        (email, action, 1 if ok else 0, info, datetime.utcnow()))

# ══════════════════════════════════════════════════════════════════════════════
#  GESTION DES CLÉS (ADMIN)
# ══════════════════════════════════════════════════════════════════════════════
def add_key(plan="PRO", days=365):
    key = _gen_key()
    now = datetime.utcnow()
    exp = (now + timedelta(days=days)) if days > 0 else None
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO licenses(`key`,plan,days,created_at,expires_at) VALUES(%s,%s,%s,%s,%s)",
                (key, plan, days, now, exp))
        conn.commit()
    finally:
        conn.close()
    return key

def add_key_manual(key, plan="PRO", days=365):
    key = key.strip().upper()
    now = datetime.utcnow()
    exp = (now + timedelta(days=days)) if days > 0 else None
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO licenses(`key`,plan,days,created_at,expires_at) VALUES(%s,%s,%s,%s,%s)",
                (key, plan, days, now, exp))
        conn.commit()
        return True
    except pymysql.err.IntegrityError:
        return False
    finally:
        conn.close()

def list_keys():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT `key`,plan,active,used_by,
                           DATE_FORMAT(expires_at,'%Y-%m-%d') AS expires_at
                           FROM licenses ORDER BY created_at DESC""")
            return cur.fetchall()
    finally:
        conn.close()

def revoke_key(key):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE licenses SET active=0 WHERE `key`=%s", (key.upper(),))
        conn.commit()
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  INSCRIPTION
# ══════════════════════════════════════════════════════════════════════════════
def register(email, username, password, key):
    email = email.lower().strip()
    key   = key.strip().upper()

    if "@" not in email or "." not in email:
        return {"ok": False, "msg": "Adresse email invalide."}
    if len(username.strip()) < 2:
        return {"ok": False, "msg": "Nom trop court (min. 2 caractères)."}
    if len(password) < 6:
        return {"ok": False, "msg": "Mot de passe trop court (min. 6 caractères)."}

    conn = get_conn()
    try:
        with conn.cursor() as cur:

            # Email déjà utilisé ?
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                return {"ok": False, "msg": "Email déjà enregistré. Connectez-vous."}

            # Clé valide ?
            cur.execute("SELECT * FROM licenses WHERE `key`=%s AND active=1", (key,))
            lic = cur.fetchone()
            if not lic:
                return {"ok": False, "msg": "Clé de licence invalide ou désactivée."}
            if lic["used_by"]:
                return {"ok": False, "msg": "Cette clé est déjà utilisée par un autre compte."}
            if lic["expires_at"]:
                exp = lic["expires_at"]
                if isinstance(exp, str): exp = datetime.fromisoformat(exp)
                if datetime.utcnow() > exp:
                    return {"ok": False, "msg": "Clé de licence expirée."}

            # Créer le compte
            salt = secrets.token_hex(16)
            now  = datetime.utcnow()
            cur.execute("""INSERT INTO users(email,username,pw_hash,salt,plan,expires_at,created_at)
                           VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                        (email, username.strip(), _hash(password, salt),
                         salt, lic["plan"], lic["expires_at"], now))
            cur.execute("UPDATE licenses SET used_by=%s WHERE `key`=%s", (email, key))
            _log(cur, email, "REGISTER", True, f"plan={lic['plan']}")

        conn.commit()
        exp_str = str(lic["expires_at"])[:10] if lic["expires_at"] else ""
        return {"ok": True, "username": username.strip(),
                "plan": lic["plan"], "expires_at": exp_str}

    except pymysql.err.IntegrityError:
        conn.rollback()
        return {"ok": False, "msg": "Email déjà enregistré."}
    except Exception as e:
        conn.rollback()
        return {"ok": False, "msg": f"Erreur système : {e}"}
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  CONNEXION
# ══════════════════════════════════════════════════════════════════════════════
def login(email, password):
    email = email.lower().strip()
    conn  = get_conn()
    try:
        with conn.cursor() as cur:
            now = datetime.utcnow()

            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            u = cur.fetchone()
            if not u:
                _log(cur, email, "LOGIN", False, "introuvable")
                conn.commit()
                return {"ok": False, "msg": "Email ou mot de passe incorrect."}
            if not u["active"]:
                return {"ok": False, "msg": "Compte désactivé. Contactez le support."}
            if _hash(password, u["salt"]) != u["pw_hash"]:
                _log(cur, email, "LOGIN", False, "mauvais_mdp")
                conn.commit()
                return {"ok": False, "msg": "Email ou mot de passe incorrect."}

            # Vérifier la licence
            cur.execute("SELECT * FROM licenses WHERE used_by=%s", (email,))
            lic = cur.fetchone()
            expires = ""
            if lic:
                if not lic["active"]:
                    return {"ok": False, "msg": "Licence révoquée. Contactez le support."}
                if lic["expires_at"]:
                    exp = lic["expires_at"]
                    if isinstance(exp, str): exp = datetime.fromisoformat(exp)
                    if datetime.utcnow() > exp:
                        j = (datetime.utcnow() - exp).days
                        return {"ok": False,
                                "msg": f"Licence expirée il y a {j} jour(s). Renouvelez votre accès."}
                    expires = str(lic["expires_at"])[:10]

            cur.execute("UPDATE users SET last_login=%s WHERE email=%s", (now, email))
            _log(cur, email, "LOGIN", True, "OK")
            conn.commit()

        return {"ok": True, "email": email, "username": u["username"],
                "plan": u["plan"], "expires_at": expires}

    except Exception as e:
        conn.rollback()
        return {"ok": False, "msg": f"Erreur système : {e}"}
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════════════════════════════════════
def list_users():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT email,username,plan,active,
                           DATE_FORMAT(created_at,'%Y-%m-%d') AS created_at,
                           DATE_FORMAT(last_login,'%Y-%m-%d %H:%i') AS last_login
                           FROM users ORDER BY created_at DESC""")
            return cur.fetchall()
    finally:
        conn.close()

def revoke_user(email):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET active=0 WHERE email=%s", (email.lower(),))
        conn.commit()
    finally:
        conn.close()

def stats():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            today = datetime.utcnow().date()
            cur.execute("SELECT COUNT(*) AS n FROM users"); u_t = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM users WHERE active=1"); u_a = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM licenses"); k_t = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM licenses WHERE used_by IS NULL AND active=1"); k_d = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM logs WHERE action='LOGIN' AND ok=1 AND DATE(ts)=%s",(today,)); l = cur.fetchone()["n"]
        return {"users_total":u_t,"users_active":u_a,"keys_total":k_t,"keys_available":k_d,"logins_today":l}
    finally:
        conn.close()

# Init automatique
init()
