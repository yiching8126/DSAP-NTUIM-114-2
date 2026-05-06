import json
import random
from datetime import datetime, timedelta
import os

def gen_transactions(n=10000):
    accounts = ["Cash", "Food", "Transport", "Income", "Rent", "Utilities"]
    descriptions = ["Coffee", "Lunch", "Bus", "Salary", "Groceries", "Movie"]
    start_date = datetime(2025, 1, 1)
    transactions = []
    for i in range(1, n+1):
        rand_days = random.randint(0, 365)
        date = start_date + timedelta(days=rand_days)
        # 隨機決定借貸帳戶 (簡單模擬)
        dr = random.choice(accounts)
        cr = random.choice([a for a in accounts if a != dr])
        amount = round(random.uniform(5, 500), 2)
        transactions.append({
            "id": i,
            "date": date.strftime("%Y-%m-%d %H:%M:%S"),
            "desc": random.choice(descriptions),
            "amount": amount,
            "dr": dr,
            "cr": cr
        })
    return transactions

if __name__ == "__main__":
    data = gen_transactions(10000)

    script_dir = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(script_dir, 'test_data.json')
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


    print("Generated 10k transactions in test_data.json")
    print(f"File will be saved in: {os.getcwd()}")