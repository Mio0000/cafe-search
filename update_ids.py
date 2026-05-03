import json
import os
import time
import requests

SERVICES_JSON = "lib/services.json"
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

def get_place_id(name, suburb):
    if not API_KEY:
        return None
    
    url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
    query = f"{name} {suburb} Victoria Australia"
    
    params = {
        "input": query,
        "inputtype": "textquery",
        "fields": "place_id",
        "key": API_KEY
    }
    
    try:
        resp = requests.get(url, params=params)
        data = resp.json()
        if data.get("status") == "OK":
            return data["candidates"][0]["place_id"]
    except Exception as e:
        print(f"Error searching for {name}: {e}")
    return None

def main():
    if not API_KEY:
        print("Error: GOOGLE_MAPS_API_KEY is not set.")
        return

    with open(SERVICES_JSON, "r", encoding="utf-8") as f:
        services = json.load(f)

    updated_count = 0
    for svc in services:
        # すでに ChIJ から始まる ID がある場合はスキップ
        if svc["id"].startswith("ChIJ"):
            continue
            
        print(f"Searching ID for: {svc['name']} in {svc['suburb']}...")
        new_id = get_place_id(svc["name"], svc["suburb"])
        
        if new_id:
            svc["id"] = new_id
            updated_count += 1
            print(f"  ✅ Found: {new_id}")
        else:
            print(f"  ❌ Not found.")
        
        # API 制限に優しく (少し待つ)
        time.sleep(0.2)

    if updated_count > 0:
        with open(SERVICES_JSON, "w", encoding="utf-8") as f:
            json.dump(services, f, indent=2, ensure_ascii=False)
        print(f"\nDone! Updated {updated_count} IDs in {SERVICES_JSON}")
    else:
        print("\nNo IDs needed updating.")

if __name__ == "__main__":
    main()