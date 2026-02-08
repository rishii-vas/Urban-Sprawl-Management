from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from joblib import dump
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from preprocess_electricity import load_and_preprocess_electricity

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

def train_electricity_model():
    print("Loading Electricity Data...")
    X, y, encoders, label_encoder = load_and_preprocess_electricity()

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    # Train
    print("Training Electricity Model...")
    model = LogisticRegression(max_iter=2000)
    model.fit(X_train, y_train)

    # Save artifacts
    print("Saving Electricity Artifacts...")
    dump(model, MODELS_DIR / "electricity_stress_model.joblib")
    dump(encoders, MODELS_DIR / "electricity_feature_encoders.joblib")
    dump(label_encoder, MODELS_DIR / "electricity_label_encoder.joblib")

    print("Electricity Model training complete.")

if __name__ == "__main__":
    train_electricity_model()
