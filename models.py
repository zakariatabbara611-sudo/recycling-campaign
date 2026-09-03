import os
import sqlite3
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "checker.db")

def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS volunteers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        is_manager INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        start_time TEXT,
        end_time TEXT,
        description TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER,
        volunteer_id INTEGER,
        FOREIGN KEY (shift_id) REFERENCES shifts(id) ON DELETE CASCADE,
        FOREIGN KEY (volunteer_id) REFERENCES volunteers(id) ON DELETE CASCADE
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS bag_counts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_id INTEGER,
        volunteer_id INTEGER,
        bags INTEGER,
        recorded_at TEXT,
        FOREIGN KEY (shift_id) REFERENCES shifts(id),
        FOREIGN KEY (volunteer_id) REFERENCES volunteers(id)
    )
    """)

    conn.commit()
    conn.close()

def init_sample_data():
    conn = get_db()
    c = conn.cursor()
    # Add a default manager if none exist
    c.execute("SELECT COUNT(*) as cnt FROM volunteers WHERE is_manager = 1")
    row = c.fetchone()
    if row is None or row['cnt'] == 0:
        c.execute("INSERT OR IGNORE INTO volunteers (name, email, phone, is_manager) VALUES (?, ?, ?, ?)",
                  ("Manager", "manager@example.org", "", 1))
    conn.commit()
    conn.close()
