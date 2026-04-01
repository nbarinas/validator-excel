import requests
import os
import sys

# Ensure requests is installed or we might need to install it.
# assuming it is or we will see error. 
# actually, let's use standard library to be safe if requests isn't there, 
# but requests is much more readable. I'll assume users usually have it or I can install it quickly.
# I'll just use requests, if it fails I'll install it.

def test_validation():
    url = "http://127.0.0.1:8000/validate"
    
    files_valid = [
        ('files', ('test_file_1.xlsx', open('test_file_1.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
        ('files', ('test_file_2_valid.xlsx', open('test_file_2_valid.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    ]
    
    # 1. Test Success
    print("Testing Valid Pair...")
    try:
        r = requests.post(url, files=files_valid)
        if r.status_code == 200:
            print("SUCCESS: Valid pair accepted.")
            print(r.json())
        else:
            print(f"FAILURE: Valid pair rejected. {r.status_code} - {r.text}")
    except Exception as e:
        print(f"ERROR connecting: {e}")

    # Re-open files since they are consumed? No, requests reads them. But safe to re-open or seek.
    # Requests usually handles it if we pass open files. But let's close and reopen to be sure.
    for _, (n, f, _) in files_valid: f.close()

    # 2. Test Invalid (Ciudad Mismatch)
    print("\nTesting Invalid Ciudad Pair...")
    files_invalid_ciudad = [
        ('files', ('test_file_1.xlsx', open('test_file_1.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
        ('files', ('test_file_3_invalid_ciudad.xlsx', open('test_file_3_invalid_ciudad.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    ]
    
    r = requests.post(url, files=files_invalid_ciudad)
    if r.status_code == 400 and "Ciudad mismatch" in r.text:
         print("SUCCESS: Invalid Ciudad pair correctly rejected.")
    else:
         print(f"FAILURE: Invalid Ciudad pair not rejected as expected. {r.status_code} - {r.text}")

    for _, (n, f, _) in files_invalid_ciudad: f.close()

    # 3. Test Invalid (Codigo Same)
    print("\nTesting Invalid Codigo Pair (Same Codigo)...")
    files_invalid_codigo = [
        ('files', ('test_file_1.xlsx', open('test_file_1.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')),
        ('files', ('test_file_4_invalid_codigo.xlsx', open('test_file_4_invalid_codigo.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    ]
    r = requests.post(url, files=files_invalid_codigo)
    if r.status_code == 200 and "failed" in r.json().get('status', ''):
         # Wait, my logic returned 200 OK with status: failed for data logic errors, 
         # but 400 for structure errors? 
         # Checked code: logic errors return a dict with status="failed", but implicit status_code=200 by default in FastAPI return?
         # Ah, I returned just the dict. Yes, 200 OK.
         print("SUCCESS: Same Codigo pair flagged as failed.")
    elif r.status_code == 200 and "status" in r.json() and r.json()['status'] == 'success':
         print("FAILURE: Same Codigo pair INCORRECTLY succeeded.")
    else:
         print(f"Check: Response was {r.status_code} - {r.text}")

    for _, (n, f, _) in files_invalid_codigo: f.close()

if __name__ == "__main__":
    try:
        test_validation()
    except NameError:
        print("Please install requests: pip install requests")
