
import requests
import json

BASE_URL = "http://localhost:8001"

def get_token():
    # Login as admin
    resp = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin123"})
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return None
    return resp.json()["access_token"]

def test_deletion():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Create Period
    data = {
        "name": "Test Deletion Period",
        "study_code": "TEST_DEL",
        "study_type": "ascensor",
        "start_date": "2026-01-01",
        "end_date": "2026-01-15",
        "census_rate": 5000,
        "effective_rate": 10000,
        "initial_concepts": json.dumps([{"name": "Concepto 1", "rate": 1000}])
    }
    
    print("Creating period...")
    resp = requests.post(f"{BASE_URL}/payroll/periods", data=data, headers=headers)
    if resp.status_code != 200:
        print("Create period failed:", resp.text)
        return
    
    period_id = resp.json()["id"]
    print(f"Period created: {period_id}")

    # 1.5 Get Period to get concepts (POST response might not include relationship)
    resp = requests.get(f"{BASE_URL}/payroll/periods", headers=headers)
    periods = resp.json()
    period_data = next((p for p in periods if p['id'] == period_id), None)
    
    if not period_data or not period_data.get('concepts'):
        print("No concepts found in period")
        return

    concept_id = period_data['concepts'][0]['id']

    # 2. Create Record (Manual)
    # Need a user ID first. Use current user or admin (id 1 usually)
    user_id = 1
    
    rec_data = {
        "total_effective": 1,
        "total_censuses": 1,
        "items": [
            {"concept_id": concept_id, "quantity": 5}
        ]
    }
    
    print("Creating record with items...")
    resp = requests.post(f"{BASE_URL}/payroll/records/manual?period_id={period_id}&user_id={user_id}", json=rec_data, headers=headers)
    if resp.status_code != 200:
        print("Create record failed:", resp.text)
        # Even if failed, try delete to clean up if partial
    else:
        try:
            rjson = resp.json()
            if 'id' in rjson:
                print("Record created:", rjson['id'])
            else:
                print("Record created but no ID in response:", rjson)
        except Exception as e:
            print("Error parsing record response:", e, resp.text)

        
    # 3. Delete Period
    print("Deleting period...")
    resp = requests.delete(f"{BASE_URL}/payroll/periods/{period_id}", headers=headers)
    
    if resp.status_code == 200:
        print("SUCCESS: Period deleted.")
    else:
        print("FAILURE: Delete failed:", resp.text)

if __name__ == "__main__":
    try:
        test_deletion()
    except Exception as e:
        print("Error running test:", e)
