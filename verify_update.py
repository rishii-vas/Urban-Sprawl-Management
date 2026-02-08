import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def verify_wards(domain, expected_count=24, expected_keys=[]):
    print(f"Verifying {domain}...")
    try:
        url = f"{BASE_URL}/wards?domain={domain}"
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"FAILED: Status {response.status}")
                return False
            
            data = json.loads(response.read().decode())
            count = len(data)
            print(f"  Count: {count} (Expected: {expected_count})")
            
            if count != expected_count:
                print("  FAILED: Count mismatch")
                return False
            
            # Check keys in first item details
            if count > 0:
                details = data[0].get("details", {})
                print(f"  Keys found: {list(details.keys())}")
                missing = [k for k in expected_keys if k not in details]
                if missing:
                    print(f"  FAILED: Missing keys in details: {missing}")
                    return False
                else:
                    print("  Keys verified.")
                    
            return True
    except Exception as e:
        print(f"FAILED: Exception {e}")
        return False

def main():
    success = True
    
    # Water Verification
    if not verify_wards("water", expected_keys=["floodIncidents", "waterComplaints", "rainfall", "drainage"]):
        success = False
        
    # Traffic Verification
    if not verify_wards("traffic", expected_keys=["avgSpeed", "peakDelay", "accidentRate"]):
        success = False

    # Electricity Verification
    if not verify_wards("electricity", expected_keys=["peakLoad", "powerQuality", "renewableShare"]):
        success = False
        
    if success:
        print("\nALL CHECKS PASSED")
    else:
        print("\nSOME CHECKS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
