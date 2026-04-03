import sqlite3

conn = sqlite3.connect('backend/database.db')
c = conn.cursor()

profile_fields = [
    ('first_name', 'TEXT'),
    ('last_name', 'TEXT'),
    ('phone', 'TEXT'),
    ('birthday', 'TEXT'),
    ('bio', 'TEXT'),
    ('country', 'TEXT'),
    ('city', 'TEXT'),
    ('postal_code', 'TEXT'),
    ('tax_id', 'TEXT'),
    ('language', 'TEXT DEFAULT \'English\''),
    ('date_format', 'TEXT DEFAULT \'D/M/Y\''),
    ('currency', 'TEXT DEFAULT \'USD\''),
    ('timezone', 'TEXT DEFAULT \'UTC+0\'')
]

for field_name, field_type in profile_fields:
    try:
        c.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
        print(f"Added {field_name}")
    except sqlite3.OperationalError as e:
        print(f"{field_name} already exists: {e}")

# Populate defaults for existing users
c.execute("""
UPDATE users 
SET first_name = substr(name, 1, instr(name || ' ', ' ') - 1),
    last_name = trim(substr(name, instr(name || ' ', ' '))
""")

conn.commit()
conn.close()
print("Migration complete!")

