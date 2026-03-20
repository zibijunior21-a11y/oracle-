import os
from dotenv import load_dotenv
import mysql.connector

# Charger les variables d'environnement
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "qto_users"),
    "charset": "utf8mb4",
    "ssl_disabled": False
}

try:
    print("Tentative de connexion avec:")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Database: {DB_CONFIG['database']}")
    
    conn = mysql.connector.connect(**DB_CONFIG)
    print(" Connexion réussie!")
    
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    print("\nTables dans la base de données:")
    for table in tables:
        print(f"  - {table[0]}")
        
        # Pour chaque table, voir sa structure
        cursor.execute(f"DESCRIBE {table[0]}")
        columns = cursor.fetchall()
        print(f"    Colonnes:")
        for col in columns:
            print(f"       {col[0]} ({col[1]})")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f" Erreur: {e}")
