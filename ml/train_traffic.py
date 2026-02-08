from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from joblib import dump
from pathlib import Path
import sys

# Add ml directory to path to allow imports if run directly
sys.path.append(str(Path(__file__).parent))

from preprocess_traffic import load_and_preprocess_traffic

# Resolve project root
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

def train_traffic_model():
    print("Loading Traffic Data...")
    X, y, encoders, label_encoder = load_and_preprocess_traffic()

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Train
    print("Training Traffic Model...")
    model = LogisticRegression(max_iter=2000)
    model.fit(X_train, y_train)

    # Save artifacts
    print("Saving Traffic Artifacts...")
    dump(model, MODELS_DIR / "traffic_stress_model.joblib")
    dump(encoders, MODELS_DIR / "traffic_feature_encoders.joblib")
    dump(label_encoder, MODELS_DIR / "traffic_label_encoder.joblib")

    print("Traffic Model training complete.")

if __name__ == "__main__":
    train_traffic_model()
