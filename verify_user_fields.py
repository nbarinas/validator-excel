import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def verify():
    # 1. Login as admin
    print("Logging in as admin...")
    resp = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin123"})
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create User with new fields
    import random
    new_user = {
        "username": f"testuser_{random.randint(1000,9999)}",
        "password": "password123",
        "role": "agent",
        "full_name": "Test User Completo",
        "bank": "Bancolombia",
        "account_type": "Ahorros",
        "account_number": "987654321",
        "birth_date": "1990-01-01",
        "phone_number": "3001234567"
    }
    
    print(f"Creating user {new_user['username']} with details...")
    resp = requests.post(f"{BASE_URL}/users", json=new_user, headers=headers)
    if resp.status_code != 201:
        print("Create user failed:", resp.text)
        return
    
    created_data = resp.json()
    print("User created successfully.")
    
    # 3. Verify returned data matches
    print("Verifying fields in response...")
    passed = True
    for field in ["full_name", "bank", "account_type", "account_number", "birth_date", "phone_number"]:
        if created_data.get(field) != new_user[field]:
            print(f"MISMATCH: {field} - Expected {new_user[field]}, got {created_data.get(field)}")
            passed = False
    
    if passed:
        print("Verification PASSED: All fields saved and returned correctly.")
    else:
        print("Verification FAILED.")

if __name__ == "__main__":
    verify()
