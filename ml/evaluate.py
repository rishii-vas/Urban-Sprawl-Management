from sklearn.metrics import classification_report, confusion_matrix
from joblib import load

from preprocess import load_and_preprocess

X, y, _, _ = load_and_preprocess()

model = load("../models/stress_model.joblib")

y_pred = model.predict(X)

print(confusion_matrix(y, y_pred))
print(classification_report(y, y_pred))
