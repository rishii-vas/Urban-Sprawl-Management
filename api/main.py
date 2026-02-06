from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from joblib import load
from pathlib import Path

# Resolve project root safely
BASE_DIR = Path(__file__).resolve().parent.parent

model = load(BASE_DIR / "models" / "stress_model.joblib")
feature_encoders = load(BASE_DIR / "models" / "feature_encoders.joblib")
label_encoder = load(BASE_DIR / "models" / "label_encoder.joblib")

app = FastAPI(title="Urban Infrastructure Stress API")


# -------- Input schema --------
class WardInput(BaseModel):
    ward_id: int
    rainfall_mm: float
    drainage_quality: str
    elevation_category: str
    green_cover_percent: float
    impervious_surface_percent: float
    population_density: int
    water_complaints_count: int
    flood_incidents_count: int


# -------- Helper --------
def preprocess_input(data: WardInput):
    df = pd.DataFrame([data.dict()])

    for col, encoder in feature_encoders.items():
        df[col] = encoder.transform(df[col])

    return df


# -------- Routes --------

@app.get("/")
def root():
    return {"status": "Urban Infrastructure API running"}


@app.post("/predict")
def predict_stress(data: WardInput):
    X = preprocess_input(data)
    pred = model.predict(X)[0]
    stress = label_encoder.inverse_transform([pred])[0]

    return {
        "ward_id": data.ward_id,
        "predicted_stress_level": stress
    }



@app.get("/dashboard/government")
def government_dashboard():
    df = pd.read_csv(BASE_DIR / "data" / "urban_water_infrastructure_stress_dataset.csv")

    summary = (
        df.groupby("ward_name")["stress_level"]
        .value_counts()
        .unstack(fill_value=0)
        .reset_index()
    )

    return summary.to_dict(orient="records")


@app.get("/dashboard/civilian")
def civilian_dashboard():
    df = pd.read_csv(BASE_DIR / "data" / "urban_water_infrastructure_stress_dataset.csv")

    latest = df.sort_values("month").groupby("ward_name").tail(1)

    return latest[["ward_name", "stress_level"]].to_dict(orient="records")
