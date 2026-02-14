import requests
from requests.auth import HTTPBasicAuth
import base64

# User Provided:
# QCBTAAZ31
# 2494
# TEST MARKETING LATINOAMERICANA

# Endpoint found: https://api.dooblo.net/newapi/GetActiveSurveys
URL = "https://api.dooblo.net/newapi/GetActiveSurveys"

def test_auth(user_string, password):
    print(f"Testing User: {user_string} | Pass: {password}")
    try:
        res = requests.get(
            URL,
            auth=HTTPBasicAuth(user_string, password),
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text[:200]}")
        return res.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

# Attempt 1: 
# User: QCBTAAZ31 (Maybe this is the Key?)
# Pass: 2494 (Maybe this is the User ID?)
# Or vice versa.
print("--- Attempt 1 ---")
test_auth("QCBTAAZ31", "2494")

# Attempt 2:
# User: 2494
# Pass: QCBTAAZ31
print("\n--- Attempt 2 ---")
test_auth("2494", "QCBTAAZ31")

# Attempt 3:
# User: QCBTAAZ31/2494
# Pass: [Empty] (Sometimes key is passed as user, pass empty)
print("\n--- Attempt 3 ---")
test_auth("QCBTAAZ31/admin", "2494") # 'admin' is common default user?

# Attempt 4:
# User: QCBTAAZ31
# Pass: TEST MARKETING LATINOAMERICANA
print("\n--- Attempt 4 ---")
test_auth("QCBTAAZ31", "TEST MARKETING LATINOAMERICANA")

# Attempt 5:
# User: TEST MARKETING LATINOAMERICANA
# Pass: QCBTAAZ31
print("\n--- Attempt 5 ---")
test_auth("TEST MARKETING LATINOAMERICANA", "QCBTAAZ31")

# Attempt 6:
# Maybe QCBTAAZ31 is the username and 2494 is the password?
# But usually API Key is needed.
# Let's try constructing the 'User ID' as OrgKey/User
# But we don't know which is which. 
# Let's try "QCBTAAZ31" as Key and "2494" as User.
# UserID = "QCBTAAZ31/2494"
# Password = "TEST MARKETING LATINOAMERICANA"? 
print("\n--- Attempt 6 ---")
test_auth("QCBTAAZ31/2494", "TEST MARKETING LATINOAMERICANA")
