import sqlite3

conn = sqlite3.connect('database.db')
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

# ---------------- USERS TABLE ----------------

c.execute('''
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    monthly_budget REAL DEFAULT 0,
    profile_photo TEXT
)
''')

# ---------------- EXPENSES TABLE ----------------

c.execute('''
CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
)
''')

conn.commit()
conn.close()

print("Database Created Successfully")