import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_new_user_fields():
    print("\n--- Testing New User Fields ---")
    # 1. Create User with new fields
    username = "test_user_bulk_v2"
    payload = {
        "username": username,
        "password": "password123",
        "role": "auxiliar", # Testing new role
        "full_name": "Test User Bulk",
        "city": "Bogotá",
        "neighborhood": "Chapinero", # New
        "blood_type": "O+", # New
        "account_holder": "Test Holder", # New
        "account_holder_cc": "123456789" # New
    }
    
    # Needs auth? Usually create user is open or requires superuser.
    # We will try to login as superuser first if possible, or assume open registration for dev.
    # Looking at main.py, /users/ is post.
    
    try:
        r = requests.post(f"{BASE_URL}/users/", json=payload)
        if r.status_code == 200:
            data = r.json()
            print(f"[OK] User created: ID {data['id']}")
            
            # Verify fields in response
            if data.get('neighborhood') == 'Chapinero' and data.get('blood_type') == 'O+':
                 print("[OK] New fields present in response")
            else:
                 print(f"[FAIL] New fields missing in response: {data}")
                 
            return data['id'], username, "password123"
        elif r.status_code == 400 and "already registered" in r.text:
             print("[WARN] User already exists, skipping creation.")
             # Try to login to get token
             return None, username, "password123"
        else:
            print(f"[FAIL] Create User failed: {r.status_code} {r.text}")
            return None, None, None
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return None, None, None

def login(username, password):
    print(f"\n--- Logging in as {username} ---")
    try:
        r = requests.post(f"{BASE_URL}/token", data={"username": username, "password": password})
        if r.status_code == 200:
            token = r.json()['access_token']
            print("[OK] Login successful")
            return token
        else:
            print(f"[FAIL] Login failed: {r.status_code}")
            return None
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        return None

def test_bizage_study(token):
    print("\n--- Testing Bizage Study Fields ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "study_type": "Ascensor",
        "study_name": "Test Study Bulk",
        "n_value": 100,
        "census": "Test Census Data" # New
    }
    
    r = requests.post(f"{BASE_URL}/bizage/studies", json=payload, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"[OK] Study created: ID {data['id']}")
        if data.get('census') == 'Test Census Data':
             print("[OK] Census field verified")
        else:
             print(f"[FAIL] Census field missing: {data}")
        return data['id']
    else:
        print(f"[FAIL] Create Study failed: {r.status_code} {r.text}")
        return None

def test_bizage_radication(token, study_id):
    if not study_id: return
    print(f"\n--- Testing Bizage Radication (Prices) for Study {study_id} ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "quantity": 50,
        "price": 2000,
        "copies": 10,
        "copies_price": 500, # New
        "vinipel": 5, # Contact
        "vinipel_price": 300 # New
    }
    
    r = requests.put(f"{BASE_URL}/bizage/studies/{study_id}/radicate", json=payload, headers=headers)
    if r.status_code == 200:
         print("[OK] Radication successful")
         # Fetch to verify?
         r2 = requests.get(f"{BASE_URL}/bizage/studies", headers=headers)
         studies = r2.json()
         study = next((s for s in studies if s['id'] == study_id), None)
         if study:
             if study.get('copies_price') == 500 and study.get('vinipel_price') == 300:
                 print("[OK] Price fields verified in fetch")
             else:
                 print(f"[FAIL] Price fields mismatch: {study}")
         else:
             print("[FAIL] Study not found in list")
    else:
         print(f"[FAIL] Radication failed: {r.status_code} {r.text}")

if __name__ == "__main__":
    uid, user, pwd = test_new_user_fields()
    if user:
        token = login(user, pwd)
        if token:
            sid = test_bizage_study(token)
            test_bizage_radication(token, sid)
