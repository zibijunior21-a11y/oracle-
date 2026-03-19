import hashlib
import secrets
from datetime import datetime, timedelta
import pymysql
import pymysql.cursors
import streamlit as st

# CONFIG
DB_CONFIG = {
    "host": st.secrets.get("DB_HOST", "localhost"),
    "port": st.secrets.get("DB_PORT", 3306),
    "user": st.secrets.get("DB_USER", "root"),
    "password": st.secrets.get("DB_PASS", ""),
    "database": st.secrets.get("DB_NAME", "qto_users"),
    "charset": "utf8mb4",
}

# CONNEXION
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

# HASH
def _hash(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

# LOG
def _log(cursor, email, action, ok, details=""):
    cursor.execute("""
        INSERT INTO logs(email, action, ok, details, ts)
        VALUES(%s, %s, %s, %s, NOW())
    """, (email, action, int(ok), details))

# INIT DB
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
                `key` VARCHAR(255) UNIQUE,
                plan VARCHAR(20),
                days INT,
                active BOOLEAN DEFAULT 1,
                used_by VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NULL
            )
            """)

            # LOGS
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255),
                action VARCHAR(50),
                ok BOOLEAN,
                details TEXT,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

        conn.commit()
        print("✅ DB initialisée correctement")

    finally:
        conn.close()

# VERIFY LICENSE
def verify_license(key):
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM licenses WHERE `key`=%s", (key,))
            return cursor.fetchone() is not None
    finally:
        conn.close()

# REGISTER
def register(email, username, password, key):
    email = email.lower().strip()
    key   = key.strip().upper()

    conn = get_conn()
    try:
        with conn.cursor() as cur:

            # EMAIL EXISTE ?
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                return {"ok": False, "msg": "Email déjà utilisé"}

            # LICENSE OK ?
            cur.execute("SELECT * FROM licenses WHERE `key`=%s AND active=1", (key,))
            lic = cur.fetchone()
            if not lic:
                return {"ok": False, "msg": "Clé invalide"}

            if lic["used_by"]:
                return {"ok": False, "msg": "Clé déjà utilisée"}

            # CREATE USER
            salt = secrets.token_hex(16)
            cur.execute("""
                INSERT INTO users(email, username, pw_hash, salt, plan)
                VALUES(%s, %s, %s, %s, %s)
            """, (email, username, _hash(password, salt), salt, lic["plan"]))

            cur.execute("UPDATE licenses SET used_by=%s WHERE `key`=%s", (email, key))

        conn.commit()
        return {"ok": True}

    except Exception as e:
        conn.rollback()
        return {"ok": False, "msg": str(e)}

    finally:
        conn.close()

# LOGIN
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

            return {"ok": True, "username": user["username"]}

    finally:
        conn.close()

# MAIN
if __name__ == "__main__":
    init()
