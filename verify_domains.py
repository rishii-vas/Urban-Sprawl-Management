import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def make_request(url, method="GET", data=None):
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
            req.data = json_data
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
            else:
                print(f"Failed: {response.status}")
                return None
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_get_wards(domain):
    print(f"Testing GET /wards?domain={domain}...")
    data = make_request(f"{BASE_URL}/wards?domain={domain}")
    if data is not None:
        print(f"Success. Found {len(data)} wards.")
        if len(data) > 0:
            print("First ward details:", data[0].get('details'))

def test_city_overview(domain):
    print(f"Testing GET /city/overview?domain={domain}...")
    data = make_request(f"{BASE_URL}/city/overview?domain={domain}")
    if data is not None:
        print("Success:", data)

def test_predict_determinism(domain, payload):
    print(f"Testing Determinism for POST /predict ({domain})...")
    
    resp1 = make_request(f"{BASE_URL}/predict", method="POST", data=payload)
    resp2 = make_request(f"{BASE_URL}/predict", method="POST", data=payload)
    
    if resp1 and resp2:
        if resp1 == resp2:
            print(f"SUCCESS: Responses are identical.\nResp: {resp1}")
        else:
            print(f"FAILURE: Responses differ!\nResp1: {resp1}\nResp2: {resp2}")
    else:
        print("Failed to get responses.")

if __name__ == "__main__":
    # Test Water (Default)
    test_get_wards("water")
    test_city_overview("water")
    test_predict_determinism("water", {
        "domain": "water",
        "rainfall": 120.5,
        "drainage": "poor",
        "elevation": "low",
        "greenCover": 10.0,
        "imperviousSurface": 80.0,
        "populationDensity": 15000.0
    })
    
    # Test Traffic
    test_get_wards("traffic")
    test_city_overview("traffic")
    test_predict_determinism("traffic", {
        "domain": "traffic",
        "trafficCongestionIndex": 8.5,
        "avgSpeedKmph": 25.0,
        "peakDelayMin": 45.0,
        "vehicleDensityPerKm": 1200.0,
        "accidentRatePer10k": 2.5,
        "publicTransportScore": 4.0
    })

    # Test Electricity
    test_get_wards("electricity")
    test_city_overview("electricity")
    test_predict_determinism("electricity", {
        "domain": "electricity",
        "loadIndex": 120.0,
        "peakLoadMW": 500.0,
        "outageFrequency": 5.0,
        "powerQualityIndex": 90.0,
        "transformerUtilizationPct": 85.0,
        "renewableSharePct": 15.0
    })

def verify_frontend_code():
    print("\nVerifying Frontend Code...")
    try:
        with open("frontend/js/app.js", "r", encoding='utf-8') as f:
            content = f.read()
            if "L.tileLayer('https://{s}.tile.openstreetmap.org" in content:
                print("SUCCESS: app.js uses OpenStreetMap.")
            else:
                print("FAILURE: app.js does NOT use OpenStreetMap.")
            
            if "mapInstance.invalidateSize()" in content:
                print("SUCCESS: app.js calls invalidateSize().")
            else:
                print("FAILURE: app.js does NOT call invalidateSize().")

            if "wardsLayer.clearLayers()" in content:
                 print("SUCCESS: app.js uses clearLayers().")
            else:
                 print("FAILURE: app.js does NOT use clearLayers().")

        with open("frontend/pages/civilian-dashboard.html", "r", encoding='utf-8') as f:
            content = f.read()
            if "initMap('map')" in content:
                 print("SUCCESS: civilian-dashboard.html calls initMap().")
            else:
                 print("FAILURE: civilian-dashboard.html does NOT call initMap().")

    except Exception as e:
        print(f"Error reading files: {e}")

if __name__ == "__main__":
    # Run API tests
    test_get_wards("water")
    test_city_overview("water")
    test_predict_determinism("water", {
        "domain": "water",
        "rainfall": 120.5,
        "drainage": "poor",
        "elevation": "low",
        "greenCover": 10.0,
        "imperviousSurface": 80.0,
        "populationDensity": 15000.0
    })
    
    # Run Frontend static checks
    verify_frontend_code()
