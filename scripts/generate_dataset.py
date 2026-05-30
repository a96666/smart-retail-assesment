"""
generate_dataset.py
-------------------
Generates a realistic synthetic retail sales dataset and saves it to:
  data/raw/sales_raw.csv          – raw transactions (180 days)
  data/raw/products.csv           – product master data
  data/raw/stores.csv             – store master data
  data/raw/customers.csv          – customer profiles
  data/raw/promotions.csv         – promotion calendar

Run:  python scripts/generate_dataset.py
"""

import os
import random
import csv
from datetime import datetime, timedelta

random.seed(42)

# ── Master data ──────────────────────────────────────────────────

PRODUCTS = [
    ("P001", "Wireless Headphones",    "Electronics",  49.99, 120),
    ("P002", "Running Shoes",          "Footwear",     89.99,  80),
    ("P003", "Coffee Maker",           "Appliances",   39.99,  60),
    ("P004", "Yoga Mat",               "Sports",       24.99, 200),
    ("P005", "Backpack",               "Accessories",  34.99, 150),
    ("P006", "Bluetooth Speaker",      "Electronics",  59.99,  90),
    ("P007", "Stainless Water Bottle", "Sports",       14.99, 300),
    ("P008", "LED Desk Lamp",          "Home",         29.99, 100),
    ("P009", "Notebook Set (5-pack)",  "Stationery",    9.99, 400),
    ("P010", "Polarised Sunglasses",   "Accessories",  44.99,  70),
    ("P011", "Resistance Bands Set",   "Sports",       19.99, 180),
    ("P012", "Smart Watch",            "Electronics", 129.99,  40),
    ("P013", "Ceramic Mug Set",        "Home",         22.99, 160),
    ("P014", "Hiking Boots",           "Footwear",    109.99,  50),
    ("P015", "Portable Charger",       "Electronics",  34.99, 110),
]

STORES = [
    ("S001", "Downtown",    "New York",    "NY"),
    ("S002", "Westfield",   "Los Angeles", "CA"),
    ("S003", "Northgate",   "Chicago",     "IL"),
    ("S004", "Eastside",    "Houston",     "TX"),
    ("S005", "Southpark",   "Phoenix",     "AZ"),
]

PROMOTIONS = [
    ("PROMO001", "Summer Sale",       "2024-06-01", "2024-06-15", 0.20),
    ("PROMO002", "Back to School",    "2024-07-20", "2024-08-05", 0.15),
    ("PROMO003", "Flash Weekend",     "2024-08-10", "2024-08-11", 0.30),
    ("PROMO004", "Loyalty Bonus",     "2024-09-01", "2024-09-30", 0.10),
    ("PROMO005", "End of Season",     "2024-10-15", "2024-10-31", 0.25),
]

CUSTOMER_TIERS = ["Bronze", "Silver", "Gold", "Platinum"]

os.makedirs("data/raw", exist_ok=True)

# ── 1. products.csv ──────────────────────────────────────────────
with open("data/raw/products.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["product_id", "product_name", "category", "unit_price", "stock_quantity",
                "supplier", "reorder_point", "lead_time_days"])
    suppliers = ["TechSupply Co", "SportGear Ltd", "HomeGoods Inc", "FashionHub", "OfficeWorld"]
    for pid, name, cat, price, stock in PRODUCTS:
        w.writerow([
            pid, name, cat, price, stock,
            random.choice(suppliers),
            max(10, int(stock * 0.15)),
            random.randint(3, 14),
        ])
print("✓ products.csv written")

# ── 2. stores.csv ────────────────────────────────────────────────
with open("data/raw/stores.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["store_id", "store_name", "city", "state", "manager", "opened_date", "size_sqft"])
    managers = ["Alice Johnson", "Bob Martinez", "Carol White", "David Lee", "Emma Brown"]
    for i, (sid, name, city, state) in enumerate(STORES):
        w.writerow([
            sid, name, city, state,
            managers[i],
            f"201{i+5}-0{i+1}-15",
            random.randint(3000, 8000),
        ])
print("✓ stores.csv written")

# ── 3. customers.csv ─────────────────────────────────────────────
with open("data/raw/customers.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["customer_id", "age_group", "gender", "loyalty_tier",
                "total_purchases", "avg_order_value", "preferred_category"])
    categories = [p[2] for p in PRODUCTS]
    for i in range(1, 501):
        w.writerow([
            f"C{i:04d}",
            random.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
            random.choice(["M", "F", "Other"]),
            random.choice(CUSTOMER_TIERS),
            random.randint(1, 50),
            round(random.uniform(20, 150), 2),
            random.choice(categories),
        ])
print("✓ customers.csv written")

# ── 4. promotions.csv ────────────────────────────────────────────
with open("data/raw/promotions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["promo_id", "promo_name", "start_date", "end_date",
                "discount_pct", "applicable_categories"])
    cat_groups = ["Electronics,Accessories", "Sports,Footwear",
                  "All", "Electronics", "Footwear,Accessories,Home"]
    for i, (pid, name, start, end, disc) in enumerate(PROMOTIONS):
        w.writerow([pid, name, start, end, disc, cat_groups[i]])
print("✓ promotions.csv written")

# ── 5. sales_raw.csv ─────────────────────────────────────────────
def is_promo_active(date_str, category):
    for _, _, start, end, disc in PROMOTIONS:
        if start <= date_str <= end:
            return disc
    return 0.0

rows = []
base_date = datetime(2024, 4, 1)

for day_offset in range(180):
    current = base_date + timedelta(days=day_offset)
    date_str = current.strftime("%Y-%m-%d")
    is_weekend = current.weekday() >= 5
    is_month_end = current.day >= 25

    for pid, pname, cat, price, _ in PRODUCTS:
        for sid, *_ in STORES:
            # Base demand
            base = random.randint(8, 60)
            if is_weekend:
                base = int(base * random.uniform(1.2, 1.5))
            if is_month_end:
                base = int(base * random.uniform(1.1, 1.2))

            # Trend growth
            trend = 1 + (day_offset / 180) * 0.25
            qty = max(1, int(base * trend + random.gauss(0, 4)))

            # Promotion boost
            disc = is_promo_active(date_str, cat)
            if disc > 0:
                qty = int(qty * (1 + disc * 1.5))

            # Inject anomalies (~1.5%)
            if random.random() < 0.015:
                qty = qty * random.choice([6, 7, 8])   # spike
            elif random.random() < 0.008:
                qty = 0                                  # stockout

            effective_price = round(price * (1 - disc), 2)
            revenue = round(qty * effective_price, 2)
            cust_id = f"C{random.randint(1, 500):04d}"

            rows.append([
                f"TXN{len(rows)+1:07d}", pid, pname, cat,
                qty, price, effective_price, revenue,
                date_str, sid, cust_id,
                "Y" if disc > 0 else "N", round(disc * 100, 0),
            ])

with open("data/raw/sales_raw.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([
        "transaction_id", "product_id", "product_name", "category",
        "quantity", "list_price", "selling_price", "total_revenue",
        "sale_date", "store_id", "customer_id",
        "is_promotion", "discount_pct",
    ])
    w.writerows(rows)

print(f"✓ sales_raw.csv written  ({len(rows):,} rows)")
print("\nDataset generation complete.")
print("Files saved to data/raw/")
