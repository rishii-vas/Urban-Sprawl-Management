import pandas as pd
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "urban_electricity_infrastructure_stress_dataset_v2.csv"

def load_and_preprocess_electricity():
    df = pd.read_csv(DATA_PATH)

    # Features: load_index, peak_load_mw, outage_frequency, power_quality_index,
    # transformer_utilization_pct, renewable_share_pct
    X = df.drop(columns=["stress_level", "ward_name", "month", "ward_id"])
    y = df["stress_level"]
    
    # All features appear numerical based on requirement:
    # load_index, peak_load_mw, outage_frequency, power_quality_index, transformer_utilization_pct, renewable_share_pct
    
    encoders = {}
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)

    return X, y, encoders, label_encoder
