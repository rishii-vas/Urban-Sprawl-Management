# Urban Sprawl Management 
# How to run 

# Prerequisites
- Python 3.9+
- pip
- Git
- Any web browser

1. Clone the Repository
```bash
git clone https://github.com/rishii-vas/Urban-Sprawl-Management.git
cd Urban-Sprawl-Management

2. BackEnd setup:
  Install dependencies: pip install fastapi uvicorn pandas scikit-learn vaderSentiment
  Start backend: uvicorn api.main:app --reload (backend will run at http://127.0.0.1:8000)

3. FrontEnd setup:
  cd frontend
  python -m http.server 3000
  Or open on a browser directly using html page

To retrain models:

python ml/train_model.py
python ml/train_traffic.py
python ml/train_electricity.py

for verification files:

python verify_backend.py
python verify_feedback_upgrade.py

# Common Issues

1. Port already in use (change port): uvicorn api.main:app --reload --port 8001
2. CORS / Fetch errors: Ensure backend is running before opening frontend.
3. Map not loading: Check internet connection (Leaflet uses online tiles).

  