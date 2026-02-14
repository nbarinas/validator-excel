import requests
from requests.auth import HTTPBasicAuth

# Checking SOAP API availability
# Common endpoint for SurveyToGo SOAP API
URL_SOAP = "http://stg.dooblo.net/ws/SimpleAPI.asmx?wsdl"

def check_soap():
    print(f"Checking SOAP WSDL at {URL_SOAP}")
    try:
        res = requests.get(URL_SOAP)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("SOAP Service is reachable!")
            print(res.text[:500])
        else:
            print("SOAP Service unreachable.")
    except Exception as e:
        print(f"Error: {e}")

check_soap()

# If reachable, we might need to construct a SOAP envelope to authenticate.
# But for now, just checking existence effectively validates the URL.
