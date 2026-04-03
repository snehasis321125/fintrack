import pandas as pd
import random
from datetime import datetime, timedelta

records = []

start_date = datetime(2025, 1, 1)
days = 180   # about 6 months of data

categories = [
    "Food & Dining",
    "Transport",
    "Shopping",
    "Bills & Utilities",
    "Entertainment",
    "Health",
    "Education"
]

for i in range(days):

    date = start_date + timedelta(days=i)

    # weekday number
    weekday = date.weekday()

    # number of transactions per day
    transactions = random.randint(1, 4)

    for _ in range(transactions):

        category = random.choice(categories)

        # weekly spending pattern
        if weekday >= 5:  # weekend
            amount = random.randint(300, 900)
        else:  # weekday
            amount = random.randint(80, 400)

        # bills occur occasionally
        if category == "Bills & Utilities":
            amount = random.randint(700, 1500)

        records.append({
            "user_id": 1,
            "category": category,
            "amount": amount,
            "date": date.strftime("%Y-%m-%d")
        })

df = pd.DataFrame(records)

df.to_csv("expenses_dataset.csv", index=False)

print("Dataset generated:", len(df), "records")