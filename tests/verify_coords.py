import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000"

# Known coords from CSV
# Mahadevapura,12.9853591,77.7081261,mahadevapura,1,Mahadevapura
KNOWN_WARD = {
    "id": 1,
    "name": "Mahadevapura",
    "lat": 12.9853591,
    "lng": 77.7081261
}

def verify_coords():
    print("Verifying Ward Coordinates...")
    try:
        url = f"{BASE_URL}/wards?domain=water"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"Failed to fetch wards: {response.status}")
                return

            data = json.loads(response.read().decode('utf-8'))
            print(f"Fetched {len(data)} wards.")
            
            # 1. Check schema
            if len(data) > 0:
                first = data[0]
                if "has_coords" not in first:
                    print("FAILURE: 'has_coords' field missing.")
                    return
                print("SUCCESS: 'has_coords' field present.")

            # 2. Check Known Ward
            found = False
            for w in data:
                if w['id'] == KNOWN_WARD['id']:
                    found = True
                    print(f"Checking Ward {w['name']} (ID: {w['id']})...")
                    print(f"  Expected: {KNOWN_WARD['lat']}, {KNOWN_WARD['lng']}")
                    print(f"  Actual:   {w['lat']}, {w['lng']}")
                    print(f"  Has Coords: {w['has_coords']}")
                    
                    # Allow small potential float diff parsing, but should be exact if just read/returned
                    if abs(w['lat'] - KNOWN_WARD['lat']) < 0.0001 and abs(w['lng'] - KNOWN_WARD['lng']) < 0.0001:
                        print("SUCCESS: Coordinates match known values.")
                    else:
                         print("FAILURE: Coordinates do not match.")
                    
                    if w['has_coords'] is not True:
                         print("FAILURE: has_coords should be True for known ward.")
                    break
            
            if not found:
                print("WARNING: Known ward not found in response.")

            # 3. Check for Fallback (if any)
            # We don't verify specific value, just availability
            fallback_count = sum(1 for w in data if not w['has_coords'])
            print(f"Wards with missing coords (fallback used): {fallback_count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    time.sleep(1)
    verify_coords()
