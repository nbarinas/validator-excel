import requests

BASE_URL = "http://localhost:8000"

def login(username, password):
    response = requests.post(f"{BASE_URL}/token", data={"username": username, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    print(f"Login failed for {username}: {response.text}")
    return None

def verify():
    print("1. Logging in as Admin...")
    admin_token = login("admin", "admin123")
    if not admin_token: 
        # Emergency reset if admin fails
        print("Admin login failed. Trying to reset...")
        requests.get(f"{BASE_URL}/debug/reset-admin")
        admin_token = login("admin", "admin123")
        if not admin_token: return

    print("2. Sending Heartbeat as Admin...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = requests.post(f"{BASE_URL}/users/heartbeat", headers=headers)
    print(f"Heartbeat Response: {resp.status_code} - {resp.json()}")

    print("3. Checking User Status...")
    resp = requests.get(f"{BASE_URL}/users/status", headers=headers)
    
    if resp.status_code == 200:
        users = resp.json()
        print(f"Status Response: found {len(users)} users.")
        for u in users:
            print(f" - {u['username']} ({u['role']}): Last Seen: {u['last_seen']}")
            if u['username'] == 'admin' and u['last_seen']:
                print("SUCCESS: Admin found with last_seen timestamp.")
    else:
        print(f"Failed to get status: {resp.status_code} - {resp.text}")

if __name__ == "__main__":
    verify()
