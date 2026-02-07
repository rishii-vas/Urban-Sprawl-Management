import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from joblib import load

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants & Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "urban_water_infrastructure_stress_dataset.csv"
MODELS_DIR = BASE_DIR / "models"

# Global Variables
model = None
feature_encoders = None
label_encoder = None
city_data = None

# Mock Database / In-Memory Storage
feedback_store = []
users_db = {
    # email: {password, role, name, department}
    "civilian": {"password": "password", "role": "civilian", "name": "John Doe"}, # keeping simple
    "civilian@example.com": {"password": "password", "role": "civilian", "name": "John Doe"},
    "builder@gov.in": {"password": "admin", "role": "builder", "name": "City Planner", "department": "Water Supply"},
    "admin@dev.com": {"password": "admin", "role": "developer", "name": "System Admin"},
}

# --- Pydantic Models ---

class LoginRequest(BaseModel):
    email: str
    password: str
    department: Optional[str] = None

class AuthResponse(BaseModel):
    token: str
    role: str
    name: str

class UserProfile(BaseModel):
    email: str
    role: str
    name: str
    department: Optional[str] = None

class WardInput(BaseModel):
    # Matches the frontend prediction form requirements
    rainfall: float
    drainage: str  # poor, average, good
    elevation: str # low, medium, high
    greenCover: float # 0-100
    imperviousSurface: float # 0-100
    populationDensity: float

class PredictionOutput(BaseModel):
    stressLevel: str
    confidence: float
    riskScore: float # 0-100

class FeedbackRequest(BaseModel):
    category: str
    message: str

class WardData(BaseModel):
    id: int
    name: str
    stressLevel: str
    color: str # hex code
    lat: float
    lng: float
    details: Dict[str, Any]

class CityOverview(BaseModel):
    healthScore: int # 0-100
    aqi: int
    aqiLabel: str # Good, Fine, Bad
    greenCover: float
    trend: List[int] # Last 6 months health score

# --- FastAPI App ---

app = FastAPI(title="Urban Sprawl Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup ---

@app.on_event("startup")
def load_resources():
    global model, feature_encoders, label_encoder, city_data
    
    try:
        logger.info("Loading ML Models...")
        model_path = MODELS_DIR / "stress_model.joblib"
        if model_path.exists():
            model = load(model_path)
            feature_encoders = load(MODELS_DIR / "feature_encoders.joblib")
            label_encoder = load(MODELS_DIR / "label_encoder.joblib")
            logger.info("ML Models loaded successfully.")
        else:
            logger.warning("ML Models not found at %s", MODELS_DIR)
    except Exception as e:
        logger.error(f"Failed to load ML models: {e}")
        # We allow startup even if ML fails, to debug other parts, but predict will fail
    
    try:
        logger.info("Loading City Data...")
        if DATA_PATH.exists():
            city_data = pd.read_csv(DATA_PATH)
            # Normalize column names just in case
            city_data.columns = [c.strip() for c in city_data.columns]
        else:
            logger.warning("Data file not found at %s", DATA_PATH)
            city_data = pd.DataFrame() # Empty fallback
    except Exception as e:
        logger.error(f"Failed to load CSV data: {e}")
        city_data = pd.DataFrame()

# --- Helper Functions ---

def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    
    # Simple Mock: Token is just "Bearer <email>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
        
        email = token 
        if email in users_db:
            u = users_db[email]
            return UserProfile(email=email, role=u["role"], name=u["name"], department=u.get("department"))
    except Exception:
        pass
    
    # Allow test token for convenience
    if authorization == "Bearer test-token":
        return UserProfile(email="test@test.com", role="developer", name="Test User")

    raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_risk_color(stress_level: str) -> str:
    if stress_level == "Low": return "#2ecc71" # Green
    if stress_level == "Medium": return "#f1c40f" # Yellow
    if stress_level == "High": return "#e74c3c" # Red
    return "#95a5a6" # Grey

# --- Endpoints: Auth ---

@app.post("/auth/login", response_model=AuthResponse)
def login(creds: LoginRequest):
    user = users_db.get(creds.email)
    if not user or user["password"] != creds.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Return email as the "token" for simplicity in this prototype
    return {
        "token": creds.email, 
        "role": user["role"],
        "name": user["name"]
    }

@app.get("/auth/me", response_model=UserProfile)
def get_me(user: UserProfile = Depends(get_current_user)):
    return user

@app.post("/auth/logout")
def logout():
    return {"message": "Logged out successfully"}

# --- Endpoints: Civilian ---

@app.post("/predict", response_model=PredictionOutput)
def predict_stress(input_data: WardInput):
    if not model or not feature_encoders or not label_encoder:
        # Fallback Mock Prediction if model not loaded (for dev without models)
        logger.warning("ML Model not loaded, using mock prediction")
        risk = random.randint(10, 90)
        level = "High" if risk > 70 else "Medium" if risk > 40 else "Low"
        return {
            "stressLevel": level,
            "confidence": 0.85,
            "riskScore": risk
        }

    # Map input key names to what the model expects (based on training data columns)
    # Model expects: rainfall_mm, drainage_quality, elevation_category, green_cover_percent, impervious_surface_percent, population_density
    
    input_df = pd.DataFrame([{
        "ward_id": 0, # Mock ID
        "rainfall_mm": input_data.rainfall,
        "drainage_quality": input_data.drainage,
        "elevation_category": input_data.elevation,
        "green_cover_percent": input_data.greenCover,
        "impervious_surface_percent": input_data.imperviousSurface,
        "population_density": input_data.populationDensity,
        "water_complaints_count": 0, # Default
        "flood_incidents_count": 0 # Default
    }])
    
    try:
        # Preprocess
        for col, encoder in feature_encoders.items():
            if col in input_df.columns:
                 # Helper to handle unknown categories if needed, strictly we assume valid inputs
                 input_df[col] = encoder.transform(input_df[col])
        
        pred = model.predict(input_df)[0]
        stress_level = label_encoder.inverse_transform([pred])[0]
        
        # Calculate Mock Risk Score & Confidence based on Level
        if stress_level == "High":
            risk_score = random.randint(80, 99)
            confidence = random.uniform(0.85, 0.98)
        elif stress_level == "Medium":
            risk_score = random.randint(40, 79)
            confidence = random.uniform(0.70, 0.90)
        else:
            risk_score = random.randint(5, 39)
            confidence = random.uniform(0.75, 0.95)

        return {
            "stressLevel": stress_level,
            "confidence": round(confidence, 2),
            "riskScore": risk_score
        }

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    # Store feedback
    entry = {
        "id": len(feedback_store) + 1,
        "category": feedback.category,
        "message": feedback.message,
        "date": datetime.now().isoformat(),
        "sentiment": random.choice(["Positive", "Updates", "Critical"]) # Mock sentiment
    }
    feedback_store.append(entry)
    return {"message": "Feedback submitted successfully", "id": entry["id"]}

# --- Endpoints: City Data ---

@app.get("/city/overview", response_model=CityOverview)
def get_city_overview():
    # Calculate aggregate stats from city_data if available
    health_score = 75
    green_cover = 35.0
    aqi = 100
    
    if city_data is not None and not city_data.empty:
        # Simple Logic: More High Stress = Lower Health Score
        latest_data = city_data.sort_values("month").groupby("ward_name").tail(1)
        stress_counts = latest_data["stress_level"].value_counts()
        total_wards = len(latest_data)
        
        high_stress_count = stress_counts.get("High", 0)
        medium_stress_count = stress_counts.get("Medium", 0)
        
        # Formula: Start at 100, subtract points for stress
        health_score = 100 - (high_stress_count * 10) - (medium_stress_count * 5)
        health_score = max(0, min(100, int(health_score)))
        
        green_cover = round(latest_data["green_cover_percent"].mean(), 1)
        
        # Mock AQI based on green cover
        aqi = 150 - int(green_cover) # Rough inverse relation

    aqi_label = "Good" if aqi < 50 else "Fine" if aqi < 100 else "Bad"
    
    return {
        "healthScore": health_score,
        "aqi": aqi,
        "aqiLabel": aqi_label,
        "greenCover": green_cover,
        "trend": [70, 72, 71, 74, 73, health_score] # Mock trend
    }

@app.get("/city/health-trend")
def get_health_trend():
     # Mock trend
    return {"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "data": [70, 72, 71, 74, 73, 75]}

@app.get("/wards", response_model=List[WardData])
def get_wards(domain: str = None):
    if city_data is None or city_data.empty:
        return []
    
    latest_data = city_data.sort_values("month").groupby("ward_name").tail(1)
    
    wards_list = []
    
    # Mock Coordinates for Bangalore Wards (approximate/randomized around center)
    base_lat, base_lng = 12.9716, 77.5946
    
    for i, row in latest_data.iterrows():
        # Deterministic mock coordinates based on ward_id
        w_id = row['ward_id']
        # Simple deterministic offset
        lat_offset = ((w_id * 5) % 100) / 1000.0
        lng_offset = ((w_id * 7) % 100) / 1000.0
        
        if w_id % 2 == 0: lat_offset *= -1
        if w_id % 3 == 0: lng_offset *= -1

        stress_level = row['stress_level']
        
        wards_list.append({
            "id": w_id,
            "name": row['ward_name'],
            "stressLevel": stress_level,
            "color": get_risk_color(stress_level),
            "lat": base_lat + lat_offset,
            "lng": base_lng + lng_offset,
            "details": {
                "rainfall": row['rainfall_mm'],
                "drainage": row['drainage_quality'],
                "popDensity": row['population_density'],
                "description": f"Ward {row['ward_name']} has {stress_level} stress."
            }
        })
        
    return wards_list

# --- Endpoints: Dashboards ---

@app.get("/admin/system-overview")
def get_admin_system_overview(user: UserProfile = Depends(get_current_user)):
    if user.role != "developer": raise HTTPException(status_code=403, detail="Forbidden")
    
    return {
        "totalCivilianUsers": 12450,
        "activeBuilderUsers": 45,
        "totalFeedback": len(feedback_store) + 120, # Mock pre-existing
        "roleDistribution": {"Civilian": 90, "Builder": 8, "Developer": 2}
    }

@app.get("/admin/user-stats")
def get_admin_user_stats(user: UserProfile = Depends(get_current_user)):
    if user.role != "developer": raise HTTPException(status_code=403, detail="Forbidden")
    
    return {
        "totalUsers": 12500,
        "avgSessionDuration": "4m 32s",
        "pagesPerSession": 5.4,
        "registrationTrend": [10, 25, 40, 35, 60, 80],
        "recentActivity": [
            {"user": "civilian@example.com", "role": "Civilian", "action": "Submitted Feedback", "time": "2 mins ago"},
            {"user": "builder@gov.in", "role": "Builder", "action": "Updated Ward Data", "time": "15 mins ago"}
        ]
    }

@app.get("/admin/feedback-analytics")
def get_feedback_analytics(user: UserProfile = Depends(get_current_user)):
    if user.role != "developer": raise HTTPException(status_code=403, detail="Forbidden")
    
    positive = len([f for f in feedback_store if f["sentiment"] == "Positive"])
    negative = len([f for f in feedback_store if f["sentiment"] == "Critical"])
    neutral = len([f for f in feedback_store if f["sentiment"] == "Updates"])
    
    # Defaults if empty
    if len(feedback_store) == 0:
        positive, negative, neutral = 60, 10, 30

    return {
        "sentiment": {"Positive": positive, "Neutral": neutral, "Negative": negative},
        "recentFeedback": feedback_store[-5:] # Last 5
    }

@app.get("/builder/sdg-progress")
def get_sdg_progress(user: UserProfile = Depends(get_current_user)):
    if user.role != "builder": raise HTTPException(status_code=403, detail="Forbidden")
    
    return [
        {"sdg": "SDG 3", "name": "Good Health", "progress": 72, "color": "#4C9F38"},
        {"sdg": "SDG 6", "name": "Clean Water", "progress": 65, "color": "#26BDE2"},
        {"sdg": "SDG 9", "name": "Innovation", "progress": 80, "color": "#FD6925"},
        {"sdg": "SDG 11", "name": "Sustainable Cities", "progress": 58, "color": "#FD9D24"},
        {"sdg": "SDG 13", "name": "Climate Action", "progress": 45, "color": "#3F7E44"},
    ]

@app.get("/builder/alerts")
def get_builder_alerts(user: UserProfile = Depends(get_current_user)):
    if user.role != "builder": raise HTTPException(status_code=403, detail="Forbidden")
    
    # Generate alerts based on high stress wards
    alerts = []
    if city_data is not None and not city_data.empty:
        latest = city_data.sort_values("month").groupby("ward_name").tail(1)
        high_stress = latest[latest["stress_level"] == "High"]
        
        for _, row in high_stress.iterrows():
            alerts.append({
                "id": f"ALT-{row['ward_id']}",
                "ward": row['ward_name'],
                "severity": "High",
                "message": f"Critical water infrastructure stress detected. Drainage quality: {row['drainage_quality']}",
                "date": datetime.now().strftime("%Y-%m-%d")
            })
    
    if not alerts:
        alerts.append({"id": "ALT-001", "ward": "General", "severity": "Info", "message": "No critical alerts at this time.", "date": datetime.now().strftime("%Y-%m-%d")})
            
    return alerts

@app.get("/builder/map")
def get_builder_map_data(user: UserProfile = Depends(get_current_user)):
    if user.role != "builder": raise HTTPException(status_code=403, detail="Forbidden")
    # Reuse wards logic but maybe add more details if needed
    return get_wards()
