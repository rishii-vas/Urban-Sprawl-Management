import pandas as pd
from sklearn.preprocessing import LabelEncoder
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "urban_traffic_infrastructure_stress_dataset_v2.csv"

def load_and_preprocess_traffic():
    df = pd.read_csv(DATA_PATH)

    # Features: traffic_congestion_index, avg_speed_kmph, peak_delay_min, 
    # vehicle_density_per_km, accident_rate_per_10k, public_transport_score
    # Dropping month, ward_name, ward_id (identifiers)
    X = df.drop(columns=["stress_level", "ward_name", "month", "ward_id"])
    y = df["stress_level"]
    
    # Check for categorical columns - in this dataset they seem numeric, 
    # but let's be safe if future data changes or if I missed something.
    # Looking at the CSV head:
    # traffic_congestion_index (int), avg_speed_kmph (float), peak_delay_min (float),
    # vehicle_density_per_km (float), accident_rate_per_10k (float), public_transport_score (float)
    # So actually no categorical features to encode for X.
    
    encoders = {}
    
    # If we had categorical columns:
    # categorical_cols = []
    # for col in categorical_cols:
    #     le = LabelEncoder()
    #     X[col] = le.fit_transform(X[col])
    #     encoders[col] = le

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)

    return X, y, encoders, label_encoder
