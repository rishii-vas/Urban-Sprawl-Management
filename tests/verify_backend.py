import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_endpoint(name, url, method="GET", data=None):
    print(f"\n--- Testing {name} ---")
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            req.add_header('Content-Type', 'application/json')
            jsondata = json.dumps(data).encode('utf-8')
            req.data = jsondata
            
        with urllib.request.urlopen(req) as response:
            print(f"Status: {response.status}")
            body = response.read().decode('utf-8')
            if response.status == 200:
                print("Response:", body[:500] + "...")
            else:
                print("Error:", body)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    # 1. City Overview
    test_endpoint("City Overview", f"{BASE_URL}/city/overview")

    # 2. Wards
    test_endpoint("Wards List", f"{BASE_URL}/wards?domain=water")

    # 3. Predict
    predict_data = {
        "rainfall": 300.0,
        "drainage": "poor",
        "elevation": "low",
        "greenCover": 20.0,
        "imperviousSurface": 80.0,
        "populationDensity": 5000.0
    }
    test_endpoint("Prediction", f"{BASE_URL}/predict", method="POST", data=predict_data)
