from sklearn.metrics import classification_report, confusion_matrix
from joblib import load
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from preprocess_electricity import load_and_preprocess_electricity

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

def evaluate_electricity_model():
    print("Evaluating Electricity Model...")
    X, y, _, _ = load_and_preprocess_electricity()
    
    model_path = MODELS_DIR / "electricity_stress_model.joblib"
    if not model_path.exists():
        print("Model not found. Train it first.")
        return

    model = load(model_path)
    
    y_pred = model.predict(X)
    
    print("Confusion Matrix:")
    print(confusion_matrix(y, y_pred))
    print("\nClassification Report:")
    print(classification_report(y, y_pred))

if __name__ == "__main__":
    evaluate_electricity_model()
