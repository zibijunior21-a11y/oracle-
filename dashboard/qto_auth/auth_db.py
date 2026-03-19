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


print("✅ auth_db chargé")
import os

# 1. imports
import os
import streamlit as st
import pymysql
import hashlib, secrets
from datetime import datetime

import pymysql

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "qto_users",
    "charset": "utf8mb4"
}

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

def init():
    conn = get_conn()
    cursor = conn.cursor()

    # Table users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table licenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licenses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        license_key VARCHAR(255) NOT NULL UNIQUE,
        email VARCHAR(255) NOT NULL,
        status ENUM('active','inactive','expired') DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Table logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL,
        action VARCHAR(255) NOT NULL,
        ok TINYINT(1) NOT NULL,
        info TEXT,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    print("✅ Tables 'users', 'licenses' et 'logs' créées avec succès !")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    init()
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
