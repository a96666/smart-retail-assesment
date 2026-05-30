"""
Pipeline Step 1 – Raw Data Ingestion
Generates synthetic retail sales data and saves to data/raw/
Simulates Azure Data Factory ingestion.
"""
import os
import logging
import random
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

PRODUCTS = [
    ("P001", "Wireless Headphones", "Electronics", 49.99),
    ("P002", "Running Shoes", "Footwear", 89.99),
    ("P003", "Coffee Maker", "Appliances", 39.99),
    ("P004", "Yoga Mat", "Sports", 24.99),
    ("P005", "Backpack", "Accessories", 34.99),
    ("P006", "Bluetooth Speaker", "Electronics", 59.99),
    ("P007", "Water Bottle", "Sports", 14.99),
    ("P008", "Desk Lamp", "Home", 29.99),
    ("P009", "Notebook Set", "Stationery", 9.99),
    ("P010", "Sunglasses", "Accessories", 44.99),
]

STORES = ["S001", "S002", "S003", "S004", "S005"]


def generate_sales_data(days: int = 180, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic sales data with realistic patterns."""
    random.seed(seed)
    np.random.seed(seed)

    records = []
    base_date = datetime.now() - timedelta(days=days)

    for day_offset in range(days):
        current_date = base_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5
        is_month_end = current_date.day >= 25

        for product_id, product_name, category, unit_price in PRODUCTS:
            for store_id in STORES:
                # Base demand with seasonality
                base_demand = random.randint(10, 80)
                if is_weekend:
                    base_demand = int(base_demand * 1.3)
                if is_month_end:
                    base_demand = int(base_demand * 1.15)

                # Add trend (slight growth over time)
                trend_factor = 1 + (day_offset / days) * 0.2
                quantity = max(1, int(base_demand * trend_factor + np.random.normal(0, 5)))

                # Inject anomalies (~2% of records)
                if random.random() < 0.02:
                    quantity = quantity * random.choice([5, 6, 0])

                records.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "category": category,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total_revenue": round(quantity * unit_price, 2),
                    "sale_date": current_date.strftime("%Y-%m-%d"),
                    "store_id": store_id,
                })

    df = pd.DataFrame(records)
    logger.info("Generated %d raw sales records", len(df))
    return df


def run(output_dir: str = "data/raw"):
    os.makedirs(output_dir, exist_ok=True)
    df = generate_sales_data(days=180)
    output_path = os.path.join(output_dir, "sales_raw.csv")
    df.to_csv(output_path, index=False)
    logger.info("Raw data saved to %s", output_path)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
