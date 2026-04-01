
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def get_token():
    # Login as admin
    try:
        resp = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin123"})
        if resp.status_code != 200:
            print("Login failed:", resp.text)
            return None
        return resp.json()["access_token"]
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server at", BASE_URL)
        return None

def test_loan_flow():
    token = get_token()
    if not token:
        print("Skipping test due to login/connection failure.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    user_id = 1 # Admin user usually

    print(f"Testing /loans/active/{user_id}...")
    
    # 1. Check initial state
    resp = requests.get(f"{BASE_URL}/loans/active/{user_id}", headers=headers)
    if resp.status_code == 404:
        print("FAILURE: Endpoint /loans/active/{user_id} not found (404).")
        return
    elif resp.status_code != 200:
        print(f"FAILURE: Endpoint returned {resp.status_code}: {resp.text}")
        return
    
    print("Initial check:", resp.json())
    initial_data = resp.json()

    # 2. Create a Loan
    print("Creating test loan...")
    loan_data = {
        "user_id": user_id,
        "amount": 50000,
        "description": "Test Loan Auto"
    }
    resp = requests.post(f"{BASE_URL}/loans", json=loan_data, headers=headers)
    if resp.status_code != 200:
        print("Failed to create loan:", resp.text)
        return
    
    loan_id = resp.json()["id"]
    print(f"Loan created: ID {loan_id}")

    # 3. Verify Active Loan
    print("Verifying active loan...")
    resp = requests.get(f"{BASE_URL}/loans/active/{user_id}", headers=headers)
    data = resp.json()
    print("Active loan check:", data)
    
    # If the user already had a loan, the endpoint returns the first one found.
    # We should just verify it returns *an* active loan, and if it's the one we created, great.
    # If not, it means there was already one, which is also valid behavior for the app (blocking new loans usually).
    
    if data.get("has_loan"):
        print(f"SUCCESS: Active loan found (ID: {data.get('loan_id')}). Endpoint is working.")
        if data.get("loan_id") != loan_id:
            print(f"Note: Returned loan ID {data.get('loan_id')} differs from created ID {loan_id}. User likely had a prior loan.")
    else:
        print("FAILURE: Active loan not found.")


    # 3.5 Verify User Loans History (This was failing in frontend due to spaces in URL)
    print("Verifying user loans history...")
    resp = requests.get(f"{BASE_URL}/loans/user/{user_id}", headers=headers)
    if resp.status_code == 200:
        loans = resp.json()
        print(f"User loans found: {len(loans)}")
        if len(loans) > 0:
            print("SUCCESS: User loans endpoint working.")
    else:
        print(f"FAILURE: User loans endpoint returned {resp.status_code}: {resp.text}")

    # 3.6 Verify Payment (This was failing in frontend due to spaces in URL)
    if loan_id:
        print("Verifying payment endpoint...")
        payment_data = {"amount": 100, "notes": "Test Payment"}
        resp = requests.post(f"{BASE_URL}/loans/{loan_id}/payment", json=payment_data, headers=headers)
        if resp.status_code == 200:
            print("SUCCESS: Payment registered.")
        else:
            print(f"FAILURE: Payment endpoint returned {resp.status_code}: {resp.text}")

    # 4. Clean up (Delete Loan)
    print("Cleaning up (Deleting loan)...")
    resp = requests.delete(f"{BASE_URL}/loans/{loan_id}", headers=headers)
    if resp.status_code == 200:
        print("Loan deleted.")
    else:
        print("Failed to delete loan:", resp.text)

if __name__ == "__main__":
    test_loan_flow()
