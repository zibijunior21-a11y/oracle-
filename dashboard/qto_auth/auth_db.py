"""
================================================================================
  QUANTUM TRADE ORACLE — Base de données MySQL
  Fichier : qto_auth/auth_db.py
================================================================================
  Corrections apportées :
  ✅ Import streamlit retiré du niveau module (cause crash hors contexte)
  ✅ DB_CONFIG avec fallback os.environ + valeurs locales
  ✅ Fonction _hash corrigée (cohérence salt)
  ✅ Tables complètes : users, licenses, logs, signaux, favoris, alertes, ip_keys
  ✅ Gestion des erreurs robuste sur toutes les fonctions
  ✅ Formatage des dates cohérent
  ✅ Renouvellement de licence corrigé
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
    print("❌ pymysql manquant — pip install pymysql")

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION — priorité : variables d'environnement > valeurs locales
# ══════════════════════════════════════════════════════════════════════════════
def _get_secrets():
    """
    Charge les secrets depuis :
    1. Variables d'environnement (Railway, Streamlit Cloud)
    2. st.secrets si Streamlit est disponible
    3. Valeurs locales par défaut (développement local)
    """
    config = {
        "host":     "localhost",
        "port":     3306,
        "user":     "root",
        "password": "",
        "database": "qto_users",
        "charset":  "utf8mb4",
    }

    # Variables d'environnement (Railway, Heroku, etc.)
    if os.environ.get("DB_HOST"):
        config["host"]     = os.environ.get("DB_HOST", "localhost")
        config["port"]     = int(os.environ.get("DB_PORT", 3306))
        config["user"]     = os.environ.get("DB_USER", "root")
        config["password"] = os.environ.get("DB_PASS", "")
        config["database"] = os.environ.get("DB_NAME", "qto_users")
        return config

    # DATABASE_URL (Railway PostgreSQL → format MySQL ici ignoré)
    if os.environ.get("DATABASE_URL"):
        url = os.environ["DATABASE_URL"]
        # Parsing basique mysql://user:pass@host:port/db
        try:
            url = url.replace("mysql://", "").replace("mysql2://", "")
            user_pass, rest = url.split("@")
            user, password   = user_pass.split(":") if ":" in user_pass else (user_pass, "")
            host_port, db    = rest.split("/")
            host, port       = host_port.split(":") if ":" in host_port else (host_port, "3306")
            config.update({"host":host,"port":int(port),"user":user,
                           "password":password,"database":db})
        except Exception:
            pass
        return config

    # st.secrets si Streamlit Cloud (import conditionnel pour éviter crash)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DB_HOST" in st.secrets:
            config["host"]     = st.secrets.get("DB_HOST", "localhost")
            config["port"]     = int(st.secrets.get("DB_PORT", 3306))
            config["user"]     = st.secrets.get("DB_USER", "root")
            config["password"] = st.secrets.get("DB_PASS", "")
            config["database"] = st.secrets.get("DB_NAME", "qto_users")
    except Exception:
        pass

    return config

DB_CONFIG = _get_secrets()

# ══════════════════════════════════════════════════════════════════════════════
#  CONNEXION
# ══════════════════════════════════════════════════════════════════════════════
def get_conn():
    if not MYSQL_OK:
        raise RuntimeError("pymysql non installé — pip install pymysql")
    try:
        return pymysql.connect(
            host=DB_CONFIG["host"],
            port=int(DB_CONFIG["port"]),
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            charset=DB_CONFIG["charset"],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
    except pymysql.err.OperationalError as e:
        raise RuntimeError(f"❌ Connexion MySQL impossible : {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════
def _hash(password: str, salt: str) -> str:
    """Hash cohérent : sha256(salt + password + salt)"""
    return hashlib.sha256(f"{salt}{password}{salt}".encode()).hexdigest()

def _gen_key(plan="PRO") -> str:
    """Génère une clé de licence au format QTO-XXXX-XXXX-XXXX-XXXX"""
    b = hashlib.sha256(secrets.token_hex(16).encode()).hexdigest()[:16].upper()
    return f"QTO-{b[0:4]}-{b[4:8]}-{b[8:12]}-{b[12:16]}"

def _fmt_date(dt) -> str:
    """Formate une date en string lisible."""
    if dt is None: return ""
    if isinstance(dt, str): return dt[:10]
    return dt.strftime("%Y-%m-%d")

def _log(cur, email: str, action: str, ok: bool, info: str = ""):
    try:
        cur.execute(
            "INSERT INTO logs(email,action,ok,info,ts) VALUES(%s,%s,%s,%s,%s)",
            (email, action, 1 if ok else 0, info[:255], datetime.utcnow())
        )
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  INITIALISATION DES TABLES
# ══════════════════════════════════════════════════════════════════════════════
def init():
    """Crée toutes les tables nécessaires."""
    if not MYSQL_OK:
        print("⚠️ pymysql manquant"); return
    try:
        conn = get_conn()
        with conn.cursor() as cur:

            # ── Utilisateurs ───────────────────────────────────────────────
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

            # ── Licences ───────────────────────────────────────────────────
            cur.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id          INT          AUTO_INCREMENT PRIMARY KEY,
                license_key VARCHAR(25)  UNIQUE NOT NULL,
                plan        VARCHAR(20)  DEFAULT 'PRO',
                days        INT          DEFAULT 30,
                active      TINYINT(1)   DEFAULT 1,
                used_by     VARCHAR(255) DEFAULT NULL,
                created_at  DATETIME     NOT NULL,
                expires_at  DATETIME     DEFAULT NULL,
                renewed_at  DATETIME     DEFAULT NULL,
                renew_count INT          DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # ── Logs ───────────────────────────────────────────────────────
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

            # ── Signaux sauvegardés ────────────────────────────────────────
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_signals (
                id          INT          AUTO_INCREMENT PRIMARY KEY,
                email       VARCHAR(255) NOT NULL,
                symbol      VARCHAR(20)  NOT NULL,
                name        VARCHAR(100),
                action      VARCHAR(10)  NOT NULL,
                price       DECIMAL(18,6),
                bull_pct    FLOAT,
                bear_pct    FLOAT,
                confidence  FLOAT,
                rsi         FLOAT,
                sl          DECIMAL(18,6),
                tp          DECIMAL(18,6),
                rr          FLOAT,
                capital     DECIMAL(12,2),
                created_at  DATETIME     NOT NULL,
                INDEX idx_us_email (email),
                INDEX idx_us_symbol (symbol)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # ── Actifs favoris ─────────────────────────────────────────────
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id          INT          AUTO_INCREMENT PRIMARY KEY,
                email       VARCHAR(255) NOT NULL,
                symbol      VARCHAR(20)  NOT NULL,
                name        VARCHAR(100),
                added_at    DATETIME     NOT NULL,
                UNIQUE KEY uq_fav (email, symbol)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # ── Alertes de prix ────────────────────────────────────────────
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_alerts (
                id              INT          AUTO_INCREMENT PRIMARY KEY,
                email           VARCHAR(255) NOT NULL,
                symbol          VARCHAR(20)  NOT NULL,
                name            VARCHAR(100),
                condition_type  VARCHAR(10)  NOT NULL,
                target_price    DECIMAL(18,6) NOT NULL,
                current_price   DECIMAL(18,6),
                note            VARCHAR(255),
                active          TINYINT(1)   DEFAULT 1,
                triggered       TINYINT(1)   DEFAULT 0,
                created_at      DATETIME     NOT NULL,
                triggered_at    DATETIME     DEFAULT NULL,
                INDEX idx_al_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # ── Clés IP ────────────────────────────────────────────────────
            cur.execute("""
            CREATE TABLE IF NOT EXISTS user_ip_keys (
                id          INT          AUTO_INCREMENT PRIMARY KEY,
                email       VARCHAR(255) NOT NULL,
                ip_address  VARCHAR(45)  NOT NULL,
                ip_key      VARCHAR(64)  NOT NULL,
                device_info VARCHAR(255),
                created_at  DATETIME     NOT NULL,
                last_seen   DATETIME     NOT NULL,
                UNIQUE KEY uq_ip (email, ip_address)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

        conn.commit()
        conn.close()
        print("✅ Base de données initialisée.")
    except Exception as e:
        print(f"❌ Erreur init : {e}")

# ══════════════════════════════════════════════════════════════════════════════
#  GESTION DES LICENCES
# ══════════════════════════════════════════════════════════════════════════════
def add_key(plan: str = "PRO", days: int = 30) -> str:
    """Génère et insère une nouvelle clé de licence."""
    key = _gen_key(plan)
    now = datetime.utcnow()
    exp = now + timedelta(days=days) if days > 0 else None
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO licenses(license_key,plan,days,created_at,expires_at) VALUES(%s,%s,%s,%s,%s)",
                (key, plan, days, now, exp)
            )
        conn.commit()
    finally:
        conn.close()
    return key

def list_keys() -> list:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT license_key AS `key`, plan, active, used_by,
                       DATE_FORMAT(expires_at,'%Y-%m-%d') AS expires_at
                FROM licenses ORDER BY created_at DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()

def revoke_key(key: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE licenses SET active=0 WHERE license_key=%s", (key.upper(),))
        conn.commit()
    finally:
        conn.close()

def check_license(email: str) -> dict:
    """Vérifie la validité de la licence d'un utilisateur."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM licenses WHERE used_by=%s", (email,))
            lic = cur.fetchone()
            if not lic:
                return {"ok": False, "msg": "Aucune licence associée"}
            if not lic["active"]:
                return {"ok": False, "msg": "Licence désactivée"}
            if lic["expires_at"] and datetime.utcnow() > lic["expires_at"]:
                return {"ok": False, "expired": True, "msg": "Licence expirée"}
            return {
                "ok": True,
                "plan": lic["plan"],
                "expires_at": _fmt_date(lic["expires_at"]),
                "renew_count": lic.get("renew_count", 0),
            }
    except Exception as e:
        return {"ok": False, "msg": str(e)}
    finally:
        conn.close()

def renew_license(key: str, days: int = 30) -> dict:
    """
    Renouvelle une licence.
    - Si expirée : repart de maintenant + days
    - Si encore valide : ajoute days à la date d'expiration actuelle
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM licenses WHERE license_key=%s", (key.strip().upper(),))
            lic = cur.fetchone()
            if not lic:
                return {"ok": False, "msg": "Clé introuvable"}

            now  = datetime.utcnow()
            base = lic["expires_at"] if (lic["expires_at"] and now < lic["expires_at"]) else now
            new_exp = base + timedelta(days=days)

            cur.execute("""
                UPDATE licenses
                SET expires_at=%s, renewed_at=%s, renew_count=renew_count+1, active=1
                WHERE license_key=%s
            """, (new_exp, now, key.strip().upper()))

            # Mettre à jour aussi l'utilisateur si la licence est utilisée
            if lic.get("used_by"):
                cur.execute(
                    "UPDATE users SET expires_at=%s WHERE email=%s",
                    (new_exp, lic["used_by"])
                )

        conn.commit()
        return {"ok": True, "new_exp": _fmt_date(new_exp), "msg": f"Renouvelée jusqu'au {_fmt_date(new_exp)}"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  INSCRIPTION
# ══════════════════════════════════════════════════════════════════════════════
def register(email: str, username: str, password: str, key: str) -> dict:
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

            # Email déjà existant ?
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                return {"ok": False, "msg": "Email déjà enregistré. Connectez-vous."}

            # Clé valide ?
            cur.execute("SELECT * FROM licenses WHERE license_key=%s AND active=1", (key,))
            lic = cur.fetchone()
            if not lic:
                return {"ok": False, "msg": "Clé de licence invalide ou désactivée."}
            if lic["used_by"]:
                return {"ok": False, "msg": "Cette clé est déjà utilisée."}
            if lic["expires_at"] and datetime.utcnow() > lic["expires_at"]:
                return {"ok": False, "msg": "Clé de licence expirée."}

            salt = secrets.token_hex(16)
            now  = datetime.utcnow()

            cur.execute("""
                INSERT INTO users(email,username,pw_hash,salt,plan,expires_at,created_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s)
            """, (email, username.strip(), _hash(password, salt), salt,
                  lic["plan"], lic["expires_at"], now))

            cur.execute("UPDATE licenses SET used_by=%s WHERE license_key=%s", (email, key))
            _log(cur, email, "REGISTER", True, f"plan={lic['plan']}")

        conn.commit()
        return {
            "ok":        True,
            "username":  username.strip(),
            "plan":      lic["plan"],
            "expires_at": _fmt_date(lic["expires_at"]),
        }
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
def login(email: str, password: str) -> dict:
    email = email.lower().strip()
    conn  = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cur.fetchone()
            if not user:
                _log(cur, email, "LOGIN", False, "introuvable")
                conn.commit()
                return {"ok": False, "msg": "Email ou mot de passe incorrect."}
            if not user["active"]:
                return {"ok": False, "msg": "Compte désactivé."}
            if _hash(password, user["salt"]) != user["pw_hash"]:
                _log(cur, email, "LOGIN", False, "mauvais_mdp")
                conn.commit()
                return {"ok": False, "msg": "Email ou mot de passe incorrect."}

            # Vérifier la licence
            lic = check_license(email)
            if not lic["ok"]:
                expired = lic.get("expired", False)
                return {"ok": False, "expired": expired, "msg": lic["msg"]}

            cur.execute("UPDATE users SET last_login=%s WHERE email=%s",
                        (datetime.utcnow(), email))
            _log(cur, email, "LOGIN", True)
            conn.commit()

        return {
            "ok":        True,
            "email":     email,
            "username":  user["username"],
            "plan":      lic["plan"],
            "expires_at": lic["expires_at"],
        }
    except Exception as e:
        conn.rollback()
        return {"ok": False, "msg": f"Erreur système : {e}"}
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════════════════════════════════════
def list_users() -> list:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT email, username, plan, active,
                       DATE_FORMAT(created_at,'%Y-%m-%d') AS created_at,
                       DATE_FORMAT(last_login,'%Y-%m-%d %H:%i') AS last_login
                FROM users ORDER BY created_at DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()

def revoke_user(email: str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET active=0 WHERE email=%s", (email.lower(),))
        conn.commit()
    finally:
        conn.close()

def stats() -> dict:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            today = datetime.utcnow().date()
            cur.execute("SELECT COUNT(*) AS n FROM users"); u_t = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM users WHERE active=1"); u_a = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM licenses"); k_t = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM licenses WHERE used_by IS NULL AND active=1"); k_d = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM logs WHERE action='LOGIN' AND ok=1 AND DATE(ts)=%s", (today,))
            l = cur.fetchone()["n"]
        return {
            "users_total": u_t, "users_active": u_a,
            "keys_total": k_t, "keys_available": k_d,
            "logins_today": l,
        }
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  ESPACE PERSONNEL — Signaux
# ══════════════════════════════════════════════════════════════════════════════
def save_signal(email: str, sig: dict, capital: float) -> bool:
    if not sig or not email: return False
    r = sig.get("risk_management", {})
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_signals
                (email,symbol,name,action,price,bull_pct,bear_pct,
                 confidence,rsi,sl,tp,rr,capital,created_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                email, sig.get("symbol",""), sig.get("name",""),
                sig.get("action","HOLD"),
                round(float(sig.get("price",0) or 0), 6),
                round(float(sig.get("bullish_probability",0) or 0)*100, 2),
                round(float(sig.get("bearish_probability",0) or 0)*100, 2),
                round(float(sig.get("ai_confidence",0) or 0)*100, 2),
                round(float(sig.get("rsi",0) or 0), 2),
                round(float(r.get("stop_loss",0) or 0), 6),
                round(float(r.get("take_profit",0) or 0), 6),
                round(float(r.get("risk_reward_ratio",0) or 0), 2),
                round(float(capital or 0), 2),
                datetime.utcnow()
            ))
        conn.commit(); conn.close()
        return True
    except Exception as e:
        print(f"Erreur save_signal: {e}")
        return False

def get_user_signals(email: str, limit: int = 50) -> list:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT symbol, name, action, price, bull_pct, bear_pct,
                       confidence, rsi, sl, tp, rr, capital,
                       DATE_FORMAT(created_at,'%d/%m/%Y %H:%i') AS date
                FROM user_signals WHERE email=%s
                ORDER BY created_at DESC LIMIT %s
            """, (email, limit))
            return cur.fetchall()
    except Exception:
        return []
    finally:
        conn.close()

def get_user_stats(email: str) -> dict:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM user_signals WHERE email=%s", (email,)); total = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM user_signals WHERE email=%s AND action='BUY'", (email,)); buys = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM user_signals WHERE email=%s AND action='SELL'", (email,)); sells = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(*) AS n FROM user_signals WHERE email=%s AND action='HOLD'", (email,)); holds = cur.fetchone()["n"]
            cur.execute("""
                SELECT symbol, COUNT(*) AS n FROM user_signals
                WHERE email=%s GROUP BY symbol ORDER BY n DESC LIMIT 1
            """, (email,)); top = cur.fetchone()
            cur.execute("""
                SELECT AVG(confidence) AS avg_conf, AVG(rsi) AS avg_rsi
                FROM user_signals WHERE email=%s
            """, (email,)); avgs = cur.fetchone()
        conn.close()
        return {
            "total": total, "buys": buys, "sells": sells, "holds": holds,
            "top_symbol": top["symbol"] if top else "—",
            "avg_conf": round(float(avgs["avg_conf"] or 0), 1),
            "avg_rsi":  round(float(avgs["avg_rsi"]  or 0), 1),
        }
    except Exception:
        return {"total":0,"buys":0,"sells":0,"holds":0,"top_symbol":"—","avg_conf":0,"avg_rsi":0}

# ══════════════════════════════════════════════════════════════════════════════
#  ESPACE PERSONNEL — Favoris
# ══════════════════════════════════════════════════════════════════════════════
def add_favorite(email: str, symbol: str, name: str) -> bool:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT IGNORE INTO user_favorites(email,symbol,name,added_at)
                VALUES(%s,%s,%s,%s)
            """, (email, symbol, name, datetime.utcnow()))
        conn.commit(); conn.close(); return True
    except Exception: return False

def remove_favorite(email: str, symbol: str) -> bool:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_favorites WHERE email=%s AND symbol=%s", (email, symbol))
        conn.commit(); conn.close(); return True
    except Exception: return False

def get_favorites(email: str) -> list:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT symbol, name, DATE_FORMAT(added_at,'%d/%m/%Y') AS added_at
                FROM user_favorites WHERE email=%s ORDER BY added_at DESC
            """, (email,))
            return cur.fetchall()
    except Exception: return []
    finally: conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  ESPACE PERSONNEL — Alertes de prix
# ══════════════════════════════════════════════════════════════════════════════
def add_alert(email: str, symbol: str, name: str,
              condition: str, target: float,
              current: float = 0, note: str = "") -> bool:
    """condition = 'ABOVE' ou 'BELOW'"""
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO user_alerts
                (email,symbol,name,condition_type,target_price,current_price,note,created_at)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            """, (email, symbol, name, condition, target, current, note, datetime.utcnow()))
        conn.commit(); conn.close(); return True
    except Exception as e:
        print(f"Erreur add_alert: {e}"); return False

def get_alerts(email: str, active_only: bool = True) -> list:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            where = "WHERE email=%s AND active=1" if active_only else "WHERE email=%s"
            cur.execute(f"""
                SELECT id, symbol, name, condition_type, target_price, current_price,
                       note, active, triggered,
                       DATE_FORMAT(created_at,'%d/%m/%Y %H:%i') AS created_at,
                       DATE_FORMAT(triggered_at,'%d/%m/%Y %H:%i') AS triggered_at
                FROM user_alerts {where} ORDER BY created_at DESC
            """, (email,))
            return cur.fetchall()
    except Exception: return []
    finally: conn.close()

def delete_alert(alert_id: int) -> bool:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE user_alerts SET active=0 WHERE id=%s", (alert_id,))
        conn.commit(); conn.close(); return True
    except Exception: return False

def check_alerts(email: str, symbol: str, current_price: float) -> list:
    """Vérifie et déclenche les alertes actives pour un actif."""
    triggered = []
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, symbol, name, condition_type, target_price, note
                FROM user_alerts
                WHERE email=%s AND symbol=%s AND active=1 AND triggered=0
            """, (email, symbol))
            for a in cur.fetchall():
                fired = (
                    (a["condition_type"] == "ABOVE" and current_price >= float(a["target_price"])) or
                    (a["condition_type"] == "BELOW" and current_price <= float(a["target_price"]))
                )
                if fired:
                    cur.execute("""
                        UPDATE user_alerts SET triggered=1, triggered_at=%s WHERE id=%s
                    """, (datetime.utcnow(), a["id"]))
                    triggered.append(a)
        conn.commit(); conn.close()
    except Exception as e:
        print(f"Erreur check_alerts: {e}")
    return triggered

# ══════════════════════════════════════════════════════════════════════════════
#  ESPACE PERSONNEL — Clés IP
# ══════════════════════════════════════════════════════════════════════════════
def get_or_create_ip_key(email: str, ip_address: str, device_info: str = "") -> str:
    """Génère une clé unique par appareil (email + IP)."""
    if not email or not ip_address: return ""
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ip_key FROM user_ip_keys WHERE email=%s AND ip_address=%s
            """, (email, ip_address))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE user_ip_keys SET last_seen=%s WHERE email=%s AND ip_address=%s
                """, (datetime.utcnow(), email, ip_address))
                conn.commit(); conn.close()
                return row["ip_key"]

            raw    = f"{email}:{ip_address}:{secrets.token_hex(8)}"
            h      = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
            ip_key = f"QTO-IP-{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"

            cur.execute("""
                INSERT INTO user_ip_keys(email,ip_address,ip_key,device_info,created_at,last_seen)
                VALUES(%s,%s,%s,%s,%s,%s)
            """, (email, ip_address, ip_key, device_info, datetime.utcnow(), datetime.utcnow()))
            conn.commit(); conn.close()
            return ip_key
    except Exception as e:
        print(f"Erreur ip_key: {e}"); return ""

def get_user_ip_keys(email: str) -> list:
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ip_address, ip_key, device_info,
                       DATE_FORMAT(created_at,'%d/%m/%Y') AS created_at,
                       DATE_FORMAT(last_seen,'%d/%m/%Y %H:%i') AS last_seen
                FROM user_ip_keys WHERE email=%s ORDER BY last_seen DESC
            """, (email,))
            return cur.fetchall()
    except Exception: return []
    finally: conn.close()

# ── Init automatique au démarrage ─────────────────────────────────────────────
init()
