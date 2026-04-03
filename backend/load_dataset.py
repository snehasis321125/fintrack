import os
import pandas as pd
from db import get_connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

df = pd.read_csv(os.path.join(BASE_DIR, "expenses_dataset.csv"))

conn = get_connection()

for _, row in df.iterrows():
    conn.execute("""
        INSERT INTO expenses (user_id, category, amount, date)
        VALUES (?, ?, ?, ?)
    """, (row.user_id, row.category, row.amount, row.date))

conn.commit()
conn.close()

print("Dataset loaded into database")
