import pymysql, pymysql.cursors

conn = pymysql.connect(
    host='btz4g5qttb1ntmbjlwaj-mysql.services.clever-cloud.com',
    port=3306,
    user='ur8r3awo8bauxwpt',
    password='pjAXfJqDqezYXjM5RZXY',
    database='btz4g5qttb1ntmbjlwaj',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS licenses (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    license_key VARCHAR(25) UNIQUE NOT NULL,
    plan        VARCHAR(20) DEFAULT 'PRO',
    days        INT DEFAULT 30,
    active      TINYINT(1) DEFAULT 1,
    used_by     VARCHAR(255) DEFAULT NULL,
    created_at  DATETIME NOT NULL,
    expires_at  DATETIME DEFAULT NULL,
    renewed_at  DATETIME DEFAULT NULL,
    renew_count INT DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(255) UNIQUE NOT NULL,
    username   VARCHAR(100) NOT NULL,
    pw_hash    VARCHAR(64) NOT NULL,
    salt       VARCHAR(32) NOT NULL,
    plan       VARCHAR(20) DEFAULT 'PRO',
    expires_at DATETIME DEFAULT NULL,
    active     TINYINT(1) DEFAULT 1,
    created_at DATETIME NOT NULL,
    last_login DATETIME DEFAULT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    email  VARCHAR(255),
    action VARCHAR(20),
    ok     TINYINT(1),
    info   VARCHAR(255),
    ts     DATETIME NOT NULL
)
""")

conn.commit()
conn.close()
print("Tables creees sur Clever Cloud !")