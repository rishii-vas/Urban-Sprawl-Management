from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from joblib import dump
from pathlib import Path

from preprocess import load_and_preprocess

# Resolve project root safely
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Load data
X, y, encoders, label_encoder = load_and_preprocess()

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Train
model = LogisticRegression(max_iter=2000)
model.fit(X_train, y_train)

# Save artifacts
dump(model, MODELS_DIR / "stress_model.joblib")
dump(encoders, MODELS_DIR / "feature_encoders.joblib")
dump(label_encoder, MODELS_DIR / "label_encoder.joblib")

print("Model training complete.")
