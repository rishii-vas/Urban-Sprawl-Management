import urllib.request
import urllib.parse
import json
import time

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

def verify_feedback():
    print("Verifying Feedback System...")
    
    # 1. POST /feedback (Valid)
    print("\n1. Testing POST /feedback (Valid)...")
    payload = {
        "category": "Infrastructure", 
        "message": "Test feedback message 123",
        "ward_name": "Test Ward",
        "feedback_type": "infrastructure"
    }
    res = make_request(f"{BASE_URL}/feedback", method="POST", data=payload)
    if res and res.get("status") == "ok" and "id" in res:
        print("SUCCESS: Feedback submitted.")
        entry_id = res["id"]
    else:
        print("FAILURE: Feedback submission failed.")
        return

    # 2. POST /feedback (Invalid - short message)
    print("\n2. Testing POST /feedback (Invalid - short message)...")
    payload_invalid = {
        "category": "Infrastructure", 
        "message": "Hi",
        "ward_name": "Test Ward",
        "feedback_type": "infrastructure"
    }
    res_invalid = make_request(f"{BASE_URL}/feedback", method="POST", data=payload_invalid)
    if res_invalid is None: 
         print("SUCCESS: Invalid feedback rejected (as expected).")
    else:
         print(f"FAILURE: Invalid feedback accepted! {res_invalid}")

    # 3. GET /feedback
    print("\n3. Testing GET /feedback...")
    entries = make_request(f"{BASE_URL}/feedback")
    if entries and isinstance(entries, list):
        print(f"SUCCESS: Retrieved {len(entries)} entries.")
        # Check if our new entry is there
        found = False
        for e in entries:
            if e["id"] == entry_id:
                found = True
                print(f"Found entry: {e}")
                break
        if found:
            print("SUCCESS: Submitted entry found in listing.")
        else:
             print("FAILURE: Submitted entry NOT found in listing.")
    else:
        print("FAILURE: Failed to retrieve feedback list.")

if __name__ == "__main__":
    # Wait a bit for reload if needed
    time.sleep(2)
    verify_feedback()
