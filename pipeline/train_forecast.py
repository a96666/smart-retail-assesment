"""
Pipeline Step 3a – Train Demand Forecasting Model
Uses curated data to train a Random Forest regressor with lag features.
Saves model to ml_models/demand_model.pkl
"""
import os
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

MODEL_OUTPUT = "ml_models/demand_model.pkl"


def train(curated_path: str = "data/curated/sales_curated.parquet"):
    os.makedirs("ml_models", exist_ok=True)

    logger.info("Loading curated data from %s", curated_path)
    df = pd.read_parquet(curated_path)

    # Feature columns
    feature_cols = ["lag_1", "lag_2", "lag_3", "lag_7"]
    # Map from curated column names
    rename_map = {
        "qty_lag_1": "lag_1",
        "qty_lag_2": "lag_2",
        "qty_lag_3": "lag_3",
        "qty_lag_7": "lag_7",
    }
    df = df.rename(columns=rename_map)

    # Drop rows with NaN lag features
    df_model = df[feature_cols + ["quantity"]].dropna()

    X = df_model[feature_cols].values
    y = df_model["quantity"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info("Training RandomForest on %d samples...", len(X_train))
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    logger.info("Demand Model – MAE: %.2f | RMSE: %.2f", mae, rmse)

    # Save
    joblib.dump(model, MODEL_OUTPUT)
    logger.info("Demand model saved to %s", MODEL_OUTPUT)

    return {"mae": round(mae, 2), "rmse": round(rmse, 2)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train()
