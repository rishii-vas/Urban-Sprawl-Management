import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def post(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def get(endpoint):
    with urllib.request.urlopen(f"{BASE_URL}{endpoint}") as response:
        return json.loads(response.read().decode('utf-8'))

def log(msg, passed=True):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {msg}")
    if not passed:
        sys.exit(1)

def verify_upgrade():
    print("--- Verifying Hybrid Sentiment System ---")

    test_cases = [
        # Deterministic Overrides
        ("There is no water here in the layout", "negative", "Override: 'no water'"),
        ("Power not coming since morning", "negative", "Override: 'power not coming'"),
        ("The street light is not working", "negative", "Override: 'not working'"),
        ("We are without power for 2 days", "negative", "Override: 'without power'"),
        ("Severe flooding in the main road", "negative", "Override: 'flooding'"),
        
        # Model (VADER) Handling
        ("Great service, thank you!", "positive", "VADER: distinct positive"),
        ("The app is amazing and very useful", "positive", "VADER: distinct positive"),
        ("This is terrible and useless", "negative", "VADER: distinct negative"),
        
        # Subtlety / edge cases
        # VADER handles "not bad" as positive usually, let's see. 
        # (compound score of "not bad" is > 0)
        ("The service is not bad", "positive", "VADER: 'not bad' should be positive"),
    ]
    
    failures = 0
    for txt, expected, desc in test_cases:
        try:
            # We don't care about domain/tags for this test, just sentiment
            res = post("/feedback", {
                "category": "Test",
                "message": txt,
                "ward_name": "TestWard",
                "feedback_type": "other"
            })
            idx = res.get("id")
            sentiment = res.get("sentiment")
            
            if sentiment == expected:
                print(f"[PASS] {desc} -> {sentiment}")
            else:
                print(f"[FAIL] {desc} -> Expected {expected}, Got {sentiment}")
                failures += 1
                
        except Exception as e:
            print(f"[ERROR] {desc} -> Exception: {e}")
            failures += 1
            
    if failures == 0:
        log("All sentiment tests passed!")
    else:
        log(f"{failures} tests failed!", False)

if __name__ == "__main__":
    verify_upgrade()
