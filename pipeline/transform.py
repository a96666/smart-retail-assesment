"""
Pipeline Step 2 – Data Transformation & Feature Engineering
Raw CSV → Staged (cleaned) → Curated (feature-engineered) Parquet
Simulates Azure Databricks / PySpark transformation.
"""
import os
import logging

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def stage_data(df: pd.DataFrame, output_dir: str = "data/staged") -> pd.DataFrame:
    """Clean and validate raw data → staged layer."""
    os.makedirs(output_dir, exist_ok=True)

    original_len = len(df)

    # Parse dates
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Remove nulls
    df = df.dropna(subset=["product_id", "quantity", "unit_price", "sale_date"])

    # Remove negative quantities
    df = df[df["quantity"] >= 0]

    # Cap extreme outliers (> 99th percentile per product)
    def cap_outliers(group):
        q99 = group["quantity"].quantile(0.99)
        group["quantity"] = group["quantity"].clip(upper=q99 * 3)
        return group

    df = df.groupby("product_id", group_keys=False).apply(cap_outliers)
    df["total_revenue"] = (df["quantity"] * df["unit_price"]).round(2)

    logger.info("Staged: %d → %d records (removed %d)", original_len, len(df), original_len - len(df))

    output_path = os.path.join(output_dir, "sales_staged.parquet")
    df.to_parquet(output_path, index=False)
    logger.info("Staged data saved to %s", output_path)
    return df


def curate_data(df: pd.DataFrame, output_dir: str = "data/curated") -> pd.DataFrame:
    """Feature engineering → curated layer (Delta-table equivalent)."""
    os.makedirs(output_dir, exist_ok=True)

    df = df.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])

    # Time features
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month
    df["week_of_year"] = df["sale_date"].dt.isocalendar().week.astype(int)
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_month_end"] = (df["sale_date"].dt.day >= 25).astype(int)

    # Lag features per product (sorted by date)
    df = df.sort_values(["product_id", "store_id", "sale_date"])
    for lag in [1, 2, 3, 7]:
        df[f"qty_lag_{lag}"] = (
            df.groupby(["product_id", "store_id"])["quantity"]
            .shift(lag)
        )

    # Rolling averages
    df["qty_rolling_7d"] = (
        df.groupby(["product_id", "store_id"])["quantity"]
        .transform(lambda x: x.rolling(7, min_periods=1).mean())
    )
    df["qty_rolling_30d"] = (
        df.groupby(["product_id", "store_id"])["quantity"]
        .transform(lambda x: x.rolling(30, min_periods=1).mean())
    )

    # Revenue per unit (sanity check)
    df["revenue_per_unit"] = (df["total_revenue"] / df["quantity"].replace(0, np.nan)).round(2)

    logger.info("Curated dataset: %d records, %d features", len(df), len(df.columns))

    output_path = os.path.join(output_dir, "sales_curated.parquet")
    df.to_parquet(output_path, index=False)
    logger.info("Curated data saved to %s", output_path)
    return df


def run(raw_path: str = "data/raw/sales_raw.csv") -> pd.DataFrame:
    df_raw = pd.read_csv(raw_path)
    df_staged = stage_data(df_raw)
    df_curated = curate_data(df_staged)
    return df_curated


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run()
