import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import random
import threading
import json

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import re
from joblib import load
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants & Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Global Variables
# Models
water_model = None
water_feature_encoders = None
water_label_encoder = None

traffic_model = None
traffic_feature_encoders = None
traffic_label_encoder = None

electricity_model = None
electricity_feature_encoders = None
electricity_label_encoder = None

# Data
water_data = None
traffic_data = None
electricity_data = None

# Coordinates
ward_coords_map = {}
ward_name_coords_map = {}

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

# Domain-specific prediction inputs
class WaterPredictRequest(BaseModel):
    domain: str = "water"
    rainfall: float
    drainage: str  # poor, average, good
    elevation: str # low, medium, high
    greenCover: float # 0-100
    imperviousSurface: float # 0-100
    populationDensity: float

class TrafficPredictRequest(BaseModel):
    domain: str = "traffic"
    trafficCongestionIndex: float
    avgSpeedKmph: float
    peakDelayMin: float
    vehicleDensityPerKm: float
    accidentRatePer10k: float
    publicTransportScore: float

class ElectricityPredictRequest(BaseModel):
    domain: str = "electricity"
    loadIndex: float
    peakLoadMW: float
    outageFrequency: float
    powerQualityIndex: float
    transformerUtilizationPct: float
    renewableSharePct: float

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
    has_coords: bool
    details: Dict[str, Any]

class CityOverview(BaseModel):
    healthScore: int # 0-100
    aqi: Optional[int] = None # Water specific
    aqiLabel: Optional[str] = None
    greenCover: Optional[float] = None
    
    # Traffic specific
    avgCongestion: Optional[float] = None
    avgSpeed: Optional[float] = None
    
    # Electricity specific
    avgLoadIndex: Optional[float] = None
    outageFrequency: Optional[float] = None
    
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

def load_domain_model(domain: str, model_file: str, encoder_file: str, label_file: str):
    try:
        m_path = MODELS_DIR / model_file
        e_path = MODELS_DIR / encoder_file
        l_path = MODELS_DIR / label_file
        
        if m_path.exists() and e_path.exists() and l_path.exists():
            m = load(m_path)
            e = load(e_path)
            l = load(l_path)
            logger.info(f"{domain} models loaded successfully.")
            return m, e, l
        else:
            logger.warning(f"{domain} models not found.")
            return None, None, None
    except Exception as e:
        logger.error(f"Failed to load {domain} models: {e}")
        return None, None, None

def load_domain_data(filename: str):
    try:
        path = DATA_DIR / filename
        if path.exists():
            df = pd.read_csv(path)
            df.columns = [c.strip() for c in df.columns]
            return df
        else:
            logger.warning(f"Data file {filename} not found.")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}")
        return pd.DataFrame()

@app.on_event("startup")
def load_resources():
    global water_model, water_feature_encoders, water_label_encoder
    global traffic_model, traffic_feature_encoders, traffic_label_encoder
    global electricity_model, electricity_feature_encoders, electricity_label_encoder
    
    global water_data, traffic_data, electricity_data
    
    # Models
    water_model, water_feature_encoders, water_label_encoder = load_domain_model(
        "Water", "stress_model.joblib", "feature_encoders.joblib", "label_encoder.joblib"
    )
    traffic_model, traffic_feature_encoders, traffic_label_encoder = load_domain_model(
        "Traffic", "traffic_stress_model.joblib", "traffic_feature_encoders.joblib", "traffic_label_encoder.joblib"
    )
    electricity_model, electricity_feature_encoders, electricity_label_encoder = load_domain_model(
        "Electricity", "electricity_stress_model.joblib", "electricity_feature_encoders.joblib", "electricity_label_encoder.joblib"
    )
    
    # Data
    water_data = load_domain_data("urban_water_infrastructure_stress_dataset.csv")
    traffic_data = load_domain_data("urban_traffic_infrastructure_stress_dataset_v2.csv")
    electricity_data = load_domain_data("urban_electricity_infrastructure_stress_dataset_v2.csv")

    # Load Coordinates
    global ward_coords_map, ward_name_coords_map
    try:
        coords_path = DATA_DIR / "ward_coordinates_partial.csv"
        if coords_path.exists():
            cdf = pd.read_csv(coords_path)
            for _, row in cdf.iterrows():
                # Map by ID
                if pd.notna(row.get('ward_id')):
                    try:
                        ward_coords_map[int(row['ward_id'])] = (row['lat'], row['lng'])
                    except ValueError: pass
                
                # Map by Name (Dataset Name)
                if pd.notna(row.get('ward_name_in_dataset')):
                    ward_name_coords_map[row['ward_name_in_dataset']] = (row['lat'], row['lng'])
            logger.info(f"Loaded coordinates for {len(ward_coords_map)} wards.")
        else:
            logger.warning("Coordinates file not found.")
    except Exception as e:
        logger.error(f"Failed to load coordinates: {e}")

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

def predict_domain(domain, input_data, model, feature_encoders, label_encoder):
    if not model or not label_encoder:
        # Fallback Mock - Deterministic based on input hash
        logger.warning(f"{domain} Model not loaded, using mock prediction")
        # Create a simple hash from input values to be deterministic
        input_str = str(input_data.dict())
        val_hash = sum(ord(c) for c in input_str)
        
        # Deterministic logic based on hash
        risk = (val_hash % 90) + 10 # 10 to 99
        level = "High" if risk > 80 else "Medium" if risk > 40 else "Low"
        confidence = 0.85 # Static confidence for mock
        return level, risk, confidence

    try:
        # Prepare DataFrame
        data_dict = input_data.dict()
        
        # Mapping logic based on domain
        row = {}
        if domain == "water":
            row = {
                "rainfall_mm": data_dict['rainfall'],
                "drainage_quality": data_dict['drainage'],
                "elevation_category": data_dict['elevation'],
                "green_cover_percent": data_dict['greenCover'],
                "impervious_surface_percent": data_dict['imperviousSurface'],
                "population_density": data_dict['populationDensity'],
                 "ward_id": 0, "ward_name": "Mock", "month": "2024-01",
                "water_complaints_count": 0, "flood_incidents_count": 0
            }
        elif domain == "traffic":
             row = {
                "traffic_congestion_index": data_dict['trafficCongestionIndex'],
                "avg_speed_kmph": data_dict['avgSpeedKmph'],
                "peak_delay_min": data_dict['peakDelayMin'],
                "vehicle_density_per_km": data_dict['vehicleDensityPerKm'],
                "accident_rate_per_10k": data_dict['accidentRatePer10k'],
                "public_transport_score": data_dict['publicTransportScore'],
                 "ward_id": 0, "ward_name": "Mock", "month": "2024-01"
            }
        elif domain == "electricity":
             row = {
                "load_index": data_dict['loadIndex'],
                "peak_load_mw": data_dict['peakLoadMW'],
                "outage_frequency": data_dict['outageFrequency'],
                "power_quality_index": data_dict['powerQualityIndex'],
                "transformer_utilization_pct": data_dict['transformerUtilizationPct'],
                "renewable_share_pct": data_dict['renewableSharePct'],
                 "ward_id": 0, "ward_name": "Mock", "month": "2024-01"
            }
        
        input_df = pd.DataFrame([row])

        # Preprocess
        if feature_encoders:
            for col, encoder in feature_encoders.items():
                if col in input_df.columns:
                    try:
                        input_df[col] = encoder.transform(input_df[col])
                    except Exception:
                        # Handle unseen labels in mock usage safely?
                        # For now, simplistic fallback to 0 or similar if separate category
                        # But standard encoder throws error. We assume valid input from dropdowns.
                        pass
        
        # Drop columns based on what the model expects (must match training)
        if domain == "water":
            # preprocess.py only drops stress_level, ward_name, month
            # It KEEPS ward_id, water_complaints_count, flood_incidents_count
            input_df = input_df.drop(columns=["stress_level", "ward_name", "month"], errors='ignore')
            
            # Enforce column order to match training data (CSV structure matches X)
            # CSV: ward_id, ward_name, month, rainfall_mm, ...
            # X dropped ward_name, month. So ward_id is first.
            expected_order = [
                "ward_id", 
                "rainfall_mm", "drainage_quality", "elevation_category", 
                "green_cover_percent", "impervious_surface_percent", "population_density", 
                "water_complaints_count", "flood_incidents_count"
            ]
            # Ensure all columns exist (we put them in row dict)
            input_df = input_df[expected_order]
            
        elif domain == "traffic":
             # Traffic Enforced Order
            expected_order = [
                "traffic_congestion_index", "avg_speed_kmph", "peak_delay_min",
                "vehicle_density_per_km", "accident_rate_per_10k", "public_transport_score"
            ]
            cols_to_drop = ["stress_level", "ward_name", "month", "ward_id"]
            input_df = input_df.drop(columns=[c for c in cols_to_drop if c in input_df.columns], errors='ignore')
            input_df = input_df[expected_order]

        elif domain == "electricity":
             # Electricity Enforced Order
            expected_order = [
                "load_index", "peak_load_mw", "outage_frequency",
                "power_quality_index", "transformer_utilization_pct", "renewable_share_pct"
            ]
            cols_to_drop = ["stress_level", "ward_name", "month", "ward_id"]
            input_df = input_df.drop(columns=[c for c in cols_to_drop if c in input_df.columns], errors='ignore')
            input_df = input_df[expected_order]
        
        # Predict
        pred_idx = model.predict(input_df)[0]
        stress_level = label_encoder.inverse_transform([pred_idx])[0]
        
        # Confidence & Risk Score
        confidence = 0.85 # Default
        if hasattr(model, "predict_proba"):
            probs = model.predict_proba(input_df)[0]
            confidence = float(max(probs))
            
            # Deterministic Risk Score Calculation
            class_map = {label: i for i, label in enumerate(label_encoder.classes_)}
            
            if stress_level == "High":
                p = probs[class_map["High"]] if "High" in class_map else 0.5
                risk_score = 80 + int(p * 19)
            elif stress_level == "Medium":
                p = probs[class_map["Medium"]] if "Medium" in class_map else 0.5
                risk_score = 40 + int(p * 39)
            else:
                p = probs[class_map["Low"]] if "Low" in class_map else 0.5
                risk_score = 10 + int(p * 29)
        else:
            if stress_level == "High": risk_score = 90
            elif stress_level == "Medium": risk_score = 60
            else: risk_score = 25

        return stress_level, risk_score, confidence

    except Exception as e:
        logger.error(f"Prediction logic error for {domain}: {e}")
        # Return fallback but logged error
        return "Medium", 50, 0.5

# --- Endpoints: Auth ---

@app.post("/auth/login", response_model=AuthResponse)
def login(creds: LoginRequest):
    user = users_db.get(creds.email)
    if not user or user["password"] != creds.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
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
def predict_stress(input_data: Union[WaterPredictRequest, TrafficPredictRequest, ElectricityPredictRequest] = None):
    # Determine domain. 
    # If no input, error.
    if input_data is None:
         raise HTTPException(status_code=400, detail="Invalid input")

    # If simple water request comes in without "domain", pydantic might parse it as WaterPredictRequest if fields match.
    # But strict union parsing might fail if discriminator isn't set.
    # However, "domain" has a default in all classes. Pydantic will try to match.
    # If frontend sends water data without "domain", it matches WaterPredictRequest (domain='water').
    
    domain = input_data.domain.lower()
    
    if domain == "water":
        level, risk, conf = predict_domain("water", input_data, water_model, water_feature_encoders, water_label_encoder)
    elif domain == "traffic":
        level, risk, conf = predict_domain("traffic", input_data, traffic_model, traffic_feature_encoders, traffic_label_encoder)
    elif domain == "electricity":
        level, risk, conf = predict_domain("electricity", input_data, electricity_model, electricity_feature_encoders, electricity_label_encoder)
    else:
        raise HTTPException(status_code=400, detail="Unknown domain")

    return {
        "stressLevel": level,
        "confidence": round(conf, 2),
        "riskScore": risk
    }

# --- Feedback Logic ---

FEEDBACK_FILE = DATA_DIR / "feedback.json"
feedback_lock = threading.Lock()

class FeedbackRequest(BaseModel):
    category: str
    message: str
    ward_name: str
    feedback_type: str
    domain: Optional[str] = None

# Inference Logic
# Initialize VADER
analyzer = SentimentIntensityAnalyzer()

def infer_sentiment(message: str, is_platform_issue: bool = False) -> str:
    text = message.lower()
    
    # 1. Deterministic Overrides (Highest Priority)
    # negation/critical patterns that imply NEGATIVE
    patterns = [
        r"no\s+(water|power|electricity|supply)",    # no water, no power...
        r"(water|power)\s+not\s+coming",             # water not coming...
        r"not\s+working",                            # not working
        r"without\s+(water|power)",                  # without water...
        r"outage",
        r"flooding",
        r"leak"
    ]
    
    for p in patterns:
        if re.search(p, text):
            return "negative"

    # 2. Model-based Sentiment (VADER)
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    if compound <= -0.05:
        return "negative"
    elif compound >= 0.05:
        return "positive"
    else:
        return "negative" if is_platform_issue else "positive"

def infer_auto_tags(category: str, message: str) -> List[str]:
    text = (category + " " + message).lower()
    tags = set()
    
    # STRICT Allowed Tags Mapping
    # Domain
    if re.search(r"water|drain|flood|leak|rain", text): tags.add("water")
    if re.search(r"traffic|road|signal|jam|congestion", text): tags.add("traffic")
    if re.search(r"power|electricity|voltage|outage", text): tags.add("electricity")
    
    # Platform / Technical
    if re.search(r"bug|error|crash|fail|broken", text): tags.add("bug")
    if re.search(r"ui|layout|button|screen|color|blur", text): tags.add("ui")
    if re.search(r"server|api|backend|database|slow|timeout", text): tags.add("backend")
    
    # Issue Type
    if re.search(r"outage|cut|shutdown", text): tags.add("outage")
    if re.search(r"flood|waterlog", text): tags.add("flooding")
    if re.search(r"congestion|jam|heavy traffic", text): tags.add("congestion")
    
    # Severity / Intent
    if re.search(r"critical|urgent|emergency|danger", text): tags.add("critical")
    if re.search(r"complaint|bad|worst|issue|problem", text): tags.add("complaint")
    if re.search(r"suggest|idea|maybe|should", text): tags.add("suggestion")
    if re.search(r"feature|add|new", text): tags.add("feature-request")
    if re.search(r"good|great|thanks|love|amazing|best", text): tags.add("appreciation")
    
    # Logic: "no water" -> water, outage, complaint
    if "no water" in text or "water not coming" in text:
        tags.add("water")
        tags.add("outage")
        tags.add("complaint")
        
    return list(tags)[:5] # Max 5 tags

def infer_feedback_metadata(category: str, message: str, explicit_domain: Optional[str] = None):
    # Backward compatibility wrapper if needed, but we typically use submit_feedback logic now
    # We'll just return what we can
    tags = infer_auto_tags(category, message)
    
    # Domain inference (simple)
    domain = "general"
    if explicit_domain:
        domain = explicit_domain.lower()
    elif "water" in tags: domain = "water"
    elif "traffic" in tags: domain = "traffic"
    elif "electricity" in tags: domain = "electricity"
    
    return domain, tags

def load_feedback():
    if not FEEDBACK_FILE.exists():
        return []
    try:
        with open(FEEDBACK_FILE, "r") as f:
            data = json.load(f)
            processed = []
            for entry in data:
                # Infer metadata if missing (Backward Compatibility)
                if "feedback_type" not in entry:
                    entry["feedback_type"] = "other"
                
                if "tags" not in entry:
                    entry["tags"] = infer_auto_tags(entry.get("category", ""), entry.get("message", ""))
                
                # Re-infer target if it was ancient plain Builder/Developer split
                # But careful not to overwrite valid routing. 
                # Let's trust existing target unless it's missing.
                if "target" not in entry:
                     # Simple logic for old data
                     t = entry.get("tags", [])
                     if "bug" in t or "ui" in t or "backend" in t or "platform" in t:
                         entry["target"] = "developer"
                     else:
                         entry["target"] = "builder"

                if "ward_name" not in entry: entry["ward_name"] = "Unknown"
                if "domain" not in entry: entry["domain"] = "general"
                
                if "sentiment" not in entry:
                     is_platform = entry.get("feedback_type") == "platform"
                     entry["sentiment"] = infer_sentiment(entry.get("message", ""), is_platform)
                     
                processed.append(entry)
            return processed
    except Exception as e:
        logger.error(f"Error loading feedback: {e}")
        return []

def save_feedback(entries):
    try:
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")

@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    if not feedback.category:
        raise HTTPException(status_code=400, detail="Category is required")
    if not feedback.ward_name:
        raise HTTPException(status_code=400, detail="Ward is required")
    if len(feedback.message) < 5:
        raise HTTPException(status_code=400, detail="Message must be at least 5 characters")

    # 1. Auto-Tags
    tags = infer_auto_tags(feedback.category, feedback.message)
    
    # 2. Domain (Explicit > Inferred from Type > Inferred from Tags)
    domain = feedback.domain
    if not domain or domain == "general":
        if feedback.feedback_type in ["water", "traffic", "electricity"]:
            domain = feedback.feedback_type
        elif "water" in tags: domain = "water"
        elif "traffic" in tags: domain = "traffic"
        elif "electricity" in tags: domain = "electricity"
        else: domain = "general"
        
    # 3. Routing Logic (Deterministic)
    # Priority 1: Feedback Type = Platform -> Developer
    if feedback.feedback_type == "platform":
        target = "developer"
    # Priority 2: Tech Tags (bug, ui, backend) -> Developer
    elif any(t in tags for t in ["bug", "ui", "backend"]):
        target = "developer"
    # Priority 3: Domain Types -> Builder
    elif feedback.feedback_type in ["water", "traffic", "electricity", "infrastructure"]:
        target = "builder"
    # Priority 4: Other/General -> Builder (unless tech tags matched above)
    else:
        target = "builder"

    # 4. Sentiment
    is_platform = target == "developer"
    sentiment = infer_sentiment(feedback.message, is_platform)

    with feedback_lock:
        entries = load_feedback()
        new_entry = {
            "id": len(entries) + 1,
            "category": feedback.category,
            "message": feedback.message,
            "ward_name": feedback.ward_name,
            "feedback_type": feedback.feedback_type,
            "domain": domain,
            "tags": tags,
            "target": target,
            "sentiment": sentiment,
            "created_at": datetime.now().isoformat(),
            "status": "ok"
        }
        entries.append(new_entry)
        save_feedback(entries)
    
    return {
        "id": new_entry["id"], 
        "created_at": new_entry["created_at"], 
        "ward_name": new_entry["ward_name"],
        "feedback_type": new_entry["feedback_type"],
        "domain": domain,
        "tags": tags,
        "target": target,
        "sentiment": sentiment,
        "status": "ok"
    }

@app.get("/feedback")
def get_feedback(limit: int = 50, target: Optional[str] = None, domain: Optional[str] = None, tag: Optional[str] = None, sentiment: Optional[str] = None, ward: Optional[str] = None):
    entries = load_feedback()
    
    # Filter
    filtered = []
    for e in entries:
        # Target Filter
        if target:
            if target == "builder" and e.get("target") != "builder": continue
            if target == "developer" and e.get("target") != "developer": continue
            # "both" or None includes all
            
        # Domain Filter
        if domain and domain != "all":
            if e.get("domain") != domain: continue
            
        # Tag Filter
        if tag and tag != "all":
            if tag not in e.get("tags", []): continue

        # Sentiment Filter
        if sentiment and sentiment != "all":
            if e.get("sentiment") != sentiment: continue

        # Ward Filter
        if ward and ward != "all":
             if e.get("ward_name") != ward: continue
            
        filtered.append(e)
        
    # Sort by created_at desc
    filtered.sort(key=lambda x: x["created_at"], reverse=True)
    
    return filtered[:limit]

# --- Endpoints: City Data ---

@app.get("/city/overview", response_model=CityOverview)
def get_city_overview(domain: str = "water"):
    # Select Data
    df = None
    if domain == "traffic": df = traffic_data
    elif domain == "electricity": df = electricity_data
    else: df = water_data # default
    
    # Defaults
    health_score = 75
    trend = [70, 72, 71, 74, 73, 75]
    
    # Specifics
    aqi, aqi_label, green_cover = None, None, None
    avg_congestion, avg_speed = None, None
    avg_load, outage_freq = None, None

    if df is not None and not df.empty:
        latest_data = df.sort_values("month").groupby("ward_name").tail(1)
        stress_counts = latest_data["stress_level"].value_counts()
        high = stress_counts.get("High", 0)
        medium = stress_counts.get("Medium", 0)
        
        # Simple Health Score
        health_score = 100 - (high * 10) - (medium * 5)
        health_score = max(0, min(100, int(health_score)))
        trend = [health_score - 5, health_score - 2, health_score + 1, health_score] # Mock trend
        
        if domain == "traffic":
            avg_congestion = round(latest_data["traffic_congestion_index"].mean(), 1)
            avg_speed = round(latest_data["avg_speed_kmph"].mean(), 1)
        elif domain == "electricity":
             avg_load = round(latest_data["load_index"].mean(), 1)
             outage_freq = round(latest_data["outage_frequency"].mean(), 2)
        else: # water
             green_cover = round(latest_data["green_cover_percent"].mean(), 1)
             aqi = 150 - int(green_cover) # Mock
             aqi_label = "Good" if aqi < 50 else "Fine" if aqi < 100 else "Bad"

    return {
        "healthScore": health_score,
        "trend": trend,
        # Water
        "aqi": aqi,
        "aqiLabel": aqi_label,
        "greenCover": green_cover,
        # Traffic
        "avgCongestion": avg_congestion,
        "avgSpeed": avg_speed,
        # Electricity
        "avgLoadIndex": avg_load,
        "outageFrequency": outage_freq
    }

@app.get("/city/health-trend")
def get_health_trend():
     # Mock trend
    return {"labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], "data": [70, 72, 71, 74, 73, 75]}

@app.get("/wards", response_model=List[WardData])
def get_wards(domain: str = "water"):
    df = None
    if domain == "traffic": df = traffic_data
    elif domain == "electricity": df = electricity_data
    else: df = water_data
    
    if df is None or df.empty:
        return []
    
    latest_data = df.sort_values("month").groupby("ward_name").tail(1)
    wards_list = []
    
    for i, row in latest_data.iterrows():
        w_id = int(row['ward_id']) if pd.notna(row['ward_id']) else 0
        w_name = row['ward_name']
        
        lat, lng = None, None
        has_coords = False
        
        # 1. Try ID Match
        if w_id in ward_coords_map:
            lat, lng = ward_coords_map[w_id]
            has_coords = True
        # 2. Try Name Match
        elif w_name in ward_name_coords_map:
            lat, lng = ward_name_coords_map[w_name]
            has_coords = True
        else:
            # 3. Deterministic Fallback (Hash-based)
            # Center of Blore approx 12.97, 77.59
            # Spread: +/- 0.15 degrees
            
            # Simple hash
            h = hash(f"{w_id}-{w_name}")
            
            # Consistent random-like offset
            lat_offset = ((h % 1000) / 1000.0 - 0.5) * 0.2
            lng_offset = (((h // 1000) % 1000) / 1000.0 - 0.5) * 0.2
            
            lat = 12.97 + lat_offset
            lng = 77.59 + lng_offset
            has_coords = False

        stress_level = row['stress_level']
        
        # Details based on domain
        details = {}
        if domain == "traffic":
            details = {
                "congestionIndex": row.get('traffic_congestion_index'),
                "avgSpeed": row.get('avg_speed_kmph'),
                "peakDelay": row.get('peak_delay_min'),
                "vehicleDensityPerKm": row.get('vehicle_density_per_km'),
                "accidentRate": row.get('accident_rate_per_10k'),
                "transportScore": row.get('public_transport_score'),
                "description": f"Traffic Stress: {stress_level}"
            }
        elif domain == "electricity":
            details = {
                "loadIndex": row.get('load_index'),
                "peakLoad": row.get('peak_load_mw'),
                "outageFrequency": row.get('outage_frequency'),
                "powerQuality": row.get('power_quality_index'),
                "transformerUtilizationPct": row.get('transformer_utilization_pct'),
                "renewableShare": row.get('renewable_share_pct'),
                "description": f"Grid Stress: {stress_level}"
            }
        else: # water
            details = {
                "rainfall": row.get('rainfall_mm'),
                "drainage": row.get('drainage_quality'),
                "popDensity": row.get('population_density'),
                "greenCover": row.get('green_cover_percent'),
                "imperviousSurface": row.get('impervious_surface_percent'),
                "floodIncidents": row.get('flood_incidents_count'),
                "waterComplaints": row.get('water_complaints_count'),
                "description": f"Water Stress: {stress_level}"
            }

        wards_list.append({
            "id": w_id,
            "name": w_name,
            "stressLevel": stress_level,
            "color": get_risk_color(stress_level),
            "lat": lat,
            "lng": lng,
            "has_coords": has_coords,
            "details": details
        })
        
    return wards_list

# --- Endpoints: Dashboards ---

@app.get("/admin/system-overview")
def get_admin_system_overview(user: UserProfile = Depends(get_current_user)):
    if user.role != "developer": raise HTTPException(status_code=403, detail="Forbidden")
    return {
        "totalCivilianUsers": 12450,
        "activeBuilderUsers": 45,
        "totalFeedback": len(feedback_store) + 120,
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
    if len(feedback_store) == 0:
        positive, negative, neutral = 60, 10, 30
    return {
        "sentiment": {"Positive": positive, "Neutral": neutral, "Negative": negative},
        "recentFeedback": feedback_store[-5:]
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
    alerts = []
    # Use water data as default example
    if water_data is not None and not water_data.empty:
        latest = water_data.sort_values("month").groupby("ward_name").tail(1)
        high_stress = latest[latest["stress_level"] == "High"]
        
        for _, row in high_stress.iterrows():
            alerts.append({
                "id": f"ALT-{row['ward_id']}",
                "ward": row['ward_name'],
                "severity": "High",
                "message": f"Critical water infrastructure stress detected.",
                "date": datetime.now().strftime("%Y-%m-%d")
            })
    
    if not alerts:
        alerts.append({"id": "ALT-001", "ward": "General", "severity": "Info", "message": "No critical alerts at this time.", "date": datetime.now().strftime("%Y-%m-%d")})
            
    return alerts

@app.get("/builder/map")
def get_builder_map_data(user: UserProfile = Depends(get_current_user)):
    if user.role != "builder": raise HTTPException(status_code=403, detail="Forbidden")
    return get_wards(domain="water")
