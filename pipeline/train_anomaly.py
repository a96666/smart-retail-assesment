"""
Pipeline Step 3b – Train Anomaly Detection Model
Trains an Isolation Forest on sales quantities.
Saves model to ml_models/anomaly_model.pkl
"""
import os
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

logger = logging.getLogger(__name__)

MODEL_OUTPUT = "ml_models/anomaly_model.pkl"


def train(curated_path: str = "data/curated/sales_curated.parquet"):
    os.makedirs("ml_models", exist_ok=True)

    logger.info("Loading curated data from %s", curated_path)
    df = pd.read_parquet(curated_path)

    # Use quantity as the primary feature
    X = df[["quantity"]].fillna(0).values

    logger.info("Training Isolation Forest on %d samples...", len(X))
    model = IsolationForest(
        n_estimators=100,
        contamination=0.02,   # ~2% anomaly rate
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X)

    # Quick evaluation using injected anomalies
    scores = model.decision_function(X)
    labels = model.predict(X)
    anomaly_count = np.sum(labels == -1)
    logger.info(
        "Isolation Forest trained – flagged %d/%d records as anomalies (%.1f%%)",
        anomaly_count, len(X), 100 * anomaly_count / len(X),
    )

    # Save
    joblib.dump(model, MODEL_OUTPUT)
    logger.info("Anomaly model saved to %s", MODEL_OUTPUT)

    return {"anomaly_rate": round(100 * anomaly_count / len(X), 2)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train()
