import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'apartment.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS unit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_number TEXT UNIQUE NOT NULL,
        floor INTEGER NOT NULL,
        unit_type TEXT NOT NULL,
        monthly_rent REAL NOT NULL,
        description TEXT,
        amenities TEXT,
        is_occupied INTEGER DEFAULT 0,
        tenant_id INTEGER REFERENCES user(id),
        occupancy_start TEXT,
        monthly_due_day INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS rent_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unit_id INTEGER NOT NULL REFERENCES unit(id),
        tenant_id INTEGER NOT NULL REFERENCES user(id),
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        paid_date TEXT,
        is_paid INTEGER DEFAULT 0,
        month_year TEXT NOT NULL,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS message (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL REFERENCES user(id),
        receiver_id INTEGER NOT NULL REFERENCES user(id),
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        message_type TEXT DEFAULT 'general',
        unit_id INTEGER REFERENCES unit(id),
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS notification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES user(id),
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        notif_type TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()
