import hashlib
import secrets
from datetime import datetime, timedelta
import pymysql
import pymysql.cursors
import streamlit as st

# ================= CONFIG =================
DB_CONFIG = {
    "host": st.secrets.get("DB_HOST", "localhost"),
    "port": st.secrets.get("DB_PORT", 3306),
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
        autocommit=False,
    )

# ================= UTILS =================
def _hash(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def _gen_key(length=24):
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
            )
            """)

            # LICENSES
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                license_key VARCHAR(255) UNIQUE,
                plan VARCHAR(20),
                days INT,
                active BOOLEAN DEFAULT 1,
                used_by VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NULL,
                renewed_at TIMESTAMP NULL,
                renew_count INT DEFAULT 0
            )
            """)

        conn.commit()
        print("✅ DB initialisée")

    finally:
        conn.close()

# ================= CREATE LICENSE =================
def create_license(plan="PRO", days=30):
    key = _gen_key()
    now = datetime.utcnow()
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
    finally:
        conn.close()

# ================= VERIFY LICENSE =================
def check_license(email):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM licenses WHERE used_by=%s", (email,))
            lic = cur.fetchone()

            if not lic:
                return {"ok": False, "msg": "Aucune licence"}

            if not lic["active"]:
                return {"ok": False, "msg": "Licence désactivée"}

            if lic["expires_at"] and datetime.utcnow() > lic["expires_at"]:
                return {"ok": False, "expired": True, "msg": "Licence expirée"}

            return {"ok": True, "plan": lic["plan"], "expires_at": lic["expires_at"]}

    finally:
        conn.close()

# ================= RENEW LICENSE =================
def renew_license(key, days=30):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM licenses WHERE license_key=%s", (key,))
            lic = cur.fetchone()

            if not lic:
                return {"ok": False, "msg": "Licence introuvable"}

            now = datetime.utcnow()

            if lic["expires_at"] and now > lic["expires_at"]:
                new_exp = now + timedelta(days=days)
            else:
                base = lic["expires_at"] or now
                new_exp = base + timedelta(days=days)

            cur.execute("""
                UPDATE licenses
                SET expires_at=%s,
                    renewed_at=%s,
                    renew_count = renew_count + 1
                WHERE license_key=%s
            """, (new_exp, now, key))

        conn.commit()
        return {"ok": True, "new_exp": new_exp}

    finally:
        conn.close()

# ================= REGISTER =================
def register(email, username, password, key):
    email = email.lower().strip()
    key   = key.strip().upper()

    conn = get_conn()
    try:
        with conn.cursor() as cur:

            # email existe ?
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                return {"ok": False, "msg": "Email déjà utilisé"}

            # licence valide ?
            cur.execute("SELECT * FROM licenses WHERE license_key=%s AND active=1", (key,))
            lic = cur.fetchone()

            if not lic:
                return {"ok": False, "msg": "Clé invalide"}

            if lic["used_by"]:
                return {"ok": False, "msg": "Clé déjà utilisée"}

            salt = secrets.token_hex(16)

            cur.execute("""
                INSERT INTO users(email, username, pw_hash, salt, plan, expires_at)
                VALUES(%s, %s, %s, %s, %s, %s)
            """, (email, username, _hash(password, salt), salt, lic["plan"], lic["expires_at"]))

            cur.execute("UPDATE licenses SET used_by=%s WHERE license_key=%s", (email, key))

        conn.commit()
        return {"ok": True}

    finally:
        conn.close()

# ================= LOGIN =================
def login(email, password):
    conn = get_conn()
    try:
        with conn.cursor() as cur:

            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()

            if not user:
                return {"ok": False}

            if _hash(password, user["salt"]) != user["pw_hash"]:
                return {"ok": False}

            # vérifier licence
            lic = check_license(email)
            if not lic["ok"]:
                return lic

            return {
                "ok": True,
                "username": user["username"],
                "plan": lic["plan"],
                "expires_at": lic["expires_at"]
            }

    finally:
        conn.close()

# ================= MAIN =================
if __name__ == "__main__":
    init()
