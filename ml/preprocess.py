import pandas as pd
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "urban_water_infrastructure_stress_dataset.csv"

def load_and_preprocess():
    df = pd.read_csv(DATA_PATH)

    X = df.drop(columns=["stress_level", "ward_name", "month"])
    y = df["stress_level"]

    categorical_cols = [
        "drainage_quality",
        "elevation_category"
    ]

    encoders = {}

    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])
        encoders[col] = le

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)

    return X, y, encoders, label_encoder
