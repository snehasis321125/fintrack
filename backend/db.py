import os
import sqlite3


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

USER_COLUMNS = {
    "name": "TEXT",
    "email": "TEXT UNIQUE",
    "password": "TEXT",
    "role": "TEXT DEFAULT 'user'",
    "monthly_budget": "REAL DEFAULT 0",
    "first_name": "TEXT",
    "last_name": "TEXT",
    "phone": "TEXT",
    "birthday": "TEXT",
    "bio": "TEXT",
    "country": "TEXT",
    "city": "TEXT",
    "postal_code": "TEXT",
    "tax_id": "TEXT",
    "language": "TEXT DEFAULT 'English'",
    "date_format": "TEXT DEFAULT 'D/M/Y'",
    "currency": "TEXT DEFAULT 'USD'",
    "timezone": "TEXT DEFAULT 'UTC+0'",
    "profile_photo": "TEXT",
}


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            amount REAL,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    c.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in c.fetchall()}

    for column_name, column_def in USER_COLUMNS.items():
        if column_name not in existing_columns:
            c.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")

    conn.commit()
    conn.close()
