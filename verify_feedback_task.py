import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def submit_feedback(category, message, ward_name="Unknown", domain=None):
    url = f"{BASE_URL}/feedback"
    data = {"category": category, "message": message, "ward_name": ward_name}
    if domain:
        data["domain"] = domain
        
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Submit Failed: {e}")
        return None

def get_feedback(target=None, domain=None, tag=None, sentiment=None, ward=None):
    url = f"{BASE_URL}/feedback?"
    params = []
    if target: params.append(f"target={target}")
    if domain: params.append(f"domain={domain}")
    if tag: params.append(f"tag={tag}")
    if sentiment: params.append(f"sentiment={sentiment}")
    if ward: params.append(f"ward={ward}")
    
    url += "&".join(params)
    
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Get Failed: {e}")
        return []

def main():
    print("--- 1. Submitting Feedback Examples ---")
    
    cases = [
        ("Water", "Flooding in my ward, drains are broken", "Koramangala", "water", "builder", "negative"),
        ("Infrastructure", "Park is beautiful and clean", "Jayanagar", "general", "builder", "positive"),
        ("Bug", "CORS bug on API", "Any", "general", "developer", "negative")
    ]
    
    for cat, msg, ward, dom, exp_tgt, exp_sent in cases:
        print(f"Submitting: '{msg}' (Ward: {ward})")
        res = submit_feedback(cat, msg, ward, dom)
        if res:
            print(f"  -> Created ID {res['id']}")
            print(f"  -> Inferred Sentiment: {res['sentiment']} (Expected: {exp_sent})")
            print(f"  -> Target: {res['target']} (Expected: {exp_tgt})")
            
            if res['sentiment'] != exp_sent: print(f"FAIL: Sentiment mismatch")
            if res['target'] != exp_tgt: print(f"FAIL: Target mismatch")
        else:
            print("FAIL: Submission error")

    print("\n--- 2. Verifying Builder Dashboard Filter (target=builder) ---")
    builder_feed = get_feedback(target="builder")
    print(f"Fetched {len(builder_feed)} items for builder.")
    
    print("\n--- 3. Verifying Sentiment Filter (negative) ---")
    neg_feed = get_feedback(sentiment="negative")
    print(f"Fetched {len(neg_feed)} negative items.")
    for item in neg_feed:
        if item['sentiment'] != 'negative':
            print(f"FAIL: Found non-negative item: {item}")

if __name__ == "__main__":
    main()
