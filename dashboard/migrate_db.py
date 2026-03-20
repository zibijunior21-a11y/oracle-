"""
================================================================================
  QUANTUM TRADE ORACLE — Script de migration MySQL
  Fichier : migrate_db.py
================================================================================
  Ce script :
  1. Exporte votre base locale (WAMP/phpMyAdmin)
  2. Importe vers Clever Cloud (ou tout autre MySQL cloud)

  USAGE :
    python migrate_db.py export   → Exporte qto_users.sql depuis localhost
    python migrate_db.py import   → Importe qto_users.sql vers Clever Cloud
    python migrate_db.py test     → Teste la connexion Clever Cloud
    python migrate_db.py genkey   → Génère une clé de licence sur Clever Cloud
================================================================================
"""

import sys, os, subprocess
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
#  ⚙️  CONFIG — MODIFIEZ CES VALEURS
# ══════════════════════════════════════════════════════════════════════════════

# Base de données LOCALE (WAMP / phpMyAdmin)
LOCAL = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "",          # Votre mot de passe local (souvent vide)
    "database": "qto_users",
}

# Base de données CLEVER CLOUD
# Récupérez ces valeurs depuis :
# clever-cloud.com → Console → votre add-on MySQL → Informations de connexion
CLOUD = {
    "host":     "btz4g5qttb1ntmbjlwaj-mysql.services.clever-cloud.com",
    "port":     3306,
    "user":     "ur8r3awo8bauxwpt",
    "password": "pjAXfJqDqezYXjM5RZXY",
    "database": "btz4g5qttb1ntmbjlwaj",
}

EXPORT_FILE = "qto_users_export.sql"

# ══════════════════════════════════════════════════════════════════════════════

def test_connection(cfg: dict, label: str):
    """Teste la connexion à une base MySQL."""
    try:
        import pymysql
        conn = pymysql.connect(
            host=cfg["host"], port=int(cfg["port"]),
            user=cfg["user"], password=cfg["password"],
            database=cfg["database"], charset="utf8mb4",
            connect_timeout=10
        )
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS v, NOW() AS t")
            r = cur.fetchone()
            print(f"✅ {label} — MySQL {r[0]} · {r[1]}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ {label} — Erreur : {e}")
        return False


def export_local():
    """Exporte la base locale en fichier SQL."""
    print(f"\n📤 Export de '{LOCAL['database']}' depuis localhost...")
    pwd_flag = f"-p{LOCAL['password']}" if LOCAL["password"] else ""
    cmd = [
        "mysqldump",
        f"-h{LOCAL['host']}",
        f"-P{LOCAL['port']}",
        f"-u{LOCAL['user']}",
    ]
    if LOCAL["password"]:
        cmd.append(f"-p{LOCAL['password']}")
    cmd += [
        "--no-tablespaces",
        "--skip-add-locks",
        "--set-gtid-purged=OFF",
        LOCAL["database"]
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            print(f"❌ Erreur mysqldump : {result.stderr}")
            print("💡 Assurez-vous que mysqldump est dans votre PATH")
            print("   Chemin WAMP typique : C:\\wamp64\\bin\\mysql\\mysql8.x.x\\bin")
            return False
        with open(EXPORT_FILE, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        size = os.path.getsize(EXPORT_FILE)
        print(f"✅ Export réussi → {EXPORT_FILE} ({size} octets)")
        return True
    except FileNotFoundError:
        print("❌ mysqldump introuvable — Ajoutez WAMP/bin/mysql à votre PATH")
        print("   Ou utilisez phpMyAdmin → Export → SQL pour générer le fichier")
        return False


def import_cloud():
    """Importe le fichier SQL vers Clever Cloud."""
    if not os.path.exists(EXPORT_FILE):
        print(f"❌ Fichier {EXPORT_FILE} introuvable — lancez d'abord 'export'")
        return False
    print(f"\n📥 Import vers Clever Cloud '{CLOUD['database']}'...")
    try:
        import pymysql
        conn = pymysql.connect(
            host=CLOUD["host"], port=int(CLOUD["port"]),
            user=CLOUD["user"], password=CLOUD["password"],
            database=CLOUD["database"], charset="utf8mb4"
        )
        with open(EXPORT_FILE, "r", encoding="utf-8") as f:
            sql = f.read()

        # Diviser en statements individuels
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
        ok = 0; errors = 0
        with conn.cursor() as cur:
            for stmt in statements:
                if not stmt: continue
                try:
                    cur.execute(stmt)
                    ok += 1
                except Exception as e:
                    # Ignorer les erreurs mineures (CREATE TABLE IF NOT EXISTS etc.)
                    if "already exists" not in str(e).lower():
                        errors += 1
                        if errors <= 3:
                            print(f"  ⚠️ {str(e)[:80]}")
        conn.commit()
        conn.close()
        print(f"✅ Import terminé — {ok} statements OK, {errors} erreurs")
        return True
    except Exception as e:
        print(f"❌ Erreur import : {e}")
        return False


def gen_key(plan="PRO", days=365):
    """Génère une clé de licence directement sur Clever Cloud."""
    try:
        import pymysql, pymysql.cursors, hashlib, secrets
        from datetime import timedelta

        conn = pymysql.connect(
            host=CLOUD["host"], port=int(CLOUD["port"]),
            user=CLOUD["user"], password=CLOUD["password"],
            database=CLOUD["database"], charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        now = datetime.utcnow()
        exp = now + timedelta(days=days)
        h   = hashlib.sha256(secrets.token_hex(16).encode()).hexdigest()[:16].upper()
        key = f"QTO-{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO licenses(license_key,plan,days,created_at,expires_at,active)
                VALUES(%s,%s,%s,%s,%s,1)
            """, (key, plan, days, now, exp))
        conn.commit(); conn.close()

        print(f"\n✅ Clé générée sur Clever Cloud :")
        print(f"   Clé     : {key}")
        print(f"   Plan    : {plan}")
        print(f"   Expire  : {exp.strftime('%Y-%m-%d')}")
        return key
    except Exception as e:
        print(f"❌ Erreur génération clé : {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "help"

    if cmd == "test":
        print("\n🔍 Test des connexions...\n")
        test_connection(LOCAL, "Base locale (WAMP)")
        test_connection(CLOUD, "Clever Cloud")

    elif cmd == "export":
        test_connection(LOCAL, "Base locale")
        export_local()

    elif cmd == "import":
        test_connection(CLOUD, "Clever Cloud")
        import_cloud()

    elif cmd == "migrate":
        print("\n🚀 Migration complète : Local → Clever Cloud\n")
        if test_connection(LOCAL, "Base locale") and export_local():
            if test_connection(CLOUD, "Clever Cloud"):
                import_cloud()

    elif cmd == "genkey":
        plan = sys.argv[2].upper() if len(sys.argv) > 2 else "PRO"
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        gen_key(plan, days)

    else:
        print("""
╔══════════════════════════════════════════════════════╗
║   QTO — Script de Migration MySQL                    ║
╠══════════════════════════════════════════════════════╣
║  python migrate_db.py test          Tester connexions║
║  python migrate_db.py export        Exporter local   ║
║  python migrate_db.py import        Importer cloud   ║
║  python migrate_db.py migrate       Migration totale ║
║  python migrate_db.py genkey PRO 365 Générer une clé ║
╚══════════════════════════════════════════════════════╝

Étapes :
  1. Modifiez LOCAL et CLOUD dans ce fichier
  2. python migrate_db.py test
  3. python migrate_db.py migrate
  4. python migrate_db.py genkey PRO 365
        """)