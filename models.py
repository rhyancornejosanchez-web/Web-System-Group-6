import os
import pymysql
import pymysql.cursors
from dotenv import load_dotenv

load_dotenv()  # reads variables from a .env file in the project root, if present

MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'rhyan12')  # ← change this (or set it in .env)
MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
MYSQL_DB = os.environ.get('MYSQL_DB', 'apartment_db')


def _connect(with_db=True):
    kwargs = dict(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    if with_db:
        kwargs['database'] = MYSQL_DB
    return pymysql.connect(**kwargs)


class _ConnWrapper:
    """Lets existing code keep calling conn.execute(sql, params) directly on the
    connection (like sqlite3.Connection does), backed by a real pymysql cursor."""
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or ())
        return cur

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_db():
    """Returns a connection to the apartment_db database (rows come back as dicts)."""
    return _ConnWrapper(_connect(with_db=True))


def init_db():
    """Creates the database (if missing) and all tables (if missing)."""
    admin_conn = _connect(with_db=False)
    try:
        with admin_conn.cursor() as c:
            c.execute(
                f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        admin_conn.commit()
    finally:
        admin_conn.close()

    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            full_name VARCHAR(150) NOT NULL,
            email VARCHAR(150),
            phone VARCHAR(30),
            status VARCHAR(20) NOT NULL DEFAULT 'approved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS unit (
            id INT AUTO_INCREMENT PRIMARY KEY,
            unit_number VARCHAR(20) UNIQUE NOT NULL,
            floor INT NOT NULL,
            unit_type VARCHAR(50) NOT NULL,
            monthly_rent DECIMAL(10,2) NOT NULL,
            description TEXT,
            amenities TEXT,
            is_occupied TINYINT(1) DEFAULT 0,
            tenant_id INT,
            occupancy_start DATE,
            monthly_due_day INT DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tenant_id) REFERENCES user(id)
        ) ENGINE=InnoDB
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS rent_record (
            id INT AUTO_INCREMENT PRIMARY KEY,
            unit_id INT NOT NULL,
            tenant_id INT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            due_date DATE NOT NULL,
            paid_date DATE,
            is_paid TINYINT(1) DEFAULT 0,
            month_year VARCHAR(20) NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (unit_id) REFERENCES unit(id),
            FOREIGN KEY (tenant_id) REFERENCES user(id)
        ) ENGINE=InnoDB
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS message (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL,
            receiver_id INT NOT NULL,
            subject VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            message_type VARCHAR(30) DEFAULT 'general',
            unit_id INT,
            is_read TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES user(id),
            FOREIGN KEY (receiver_id) REFERENCES user(id),
            FOREIGN KEY (unit_id) REFERENCES unit(id)
        ) ENGINE=InnoDB
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS notification (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            notif_type VARCHAR(30) DEFAULT 'info',
            is_read TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user(id)
        ) ENGINE=InnoDB
        """)

        # Migration: add 'status' column to an existing user table that predates it
        c.execute("""
            SELECT COUNT(*) AS cnt FROM information_schema.columns
            WHERE table_schema=%s AND table_name='user' AND column_name='status'
        """, (MYSQL_DB,))
        if c.fetchone()['cnt'] == 0:
            c.execute("ALTER TABLE user ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'approved'")

        conn.commit()
    finally:
        conn.close()