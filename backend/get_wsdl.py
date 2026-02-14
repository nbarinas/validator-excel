import requests

URLS = [
    "http://stg.dooblo.net/ws/SimpleAPI.asmx?wsdl",
    "https://stg.dooblo.net/ws/SimpleAPI.asmx?wsdl",
    "http://stg.dooblo.net/SimpleAPI.asmx?wsdl",
    "https://api.dooblo.net/SimpleAPI.asmx?wsdl",
    "https://api.dooblo.net/ws/SimpleAPI.asmx?wsdl",
    "http://www.dooblo.net/ws/SimpleAPI.asmx?wsdl",
    "https://stg.dooblo.net/ws/SurveyToGo.asmx?wsdl", # Guessing
]

for url in URLS:
    print(f"Checking {url}...")
    try:
        res = requests.get(url, timeout=5)
        print(f"Status: {res.status_code}")
        if res.status_code == 200 and "definitions" in res.text:
            print(f"SUCCESS! Found WSDL at {url}")
            with open("backend/stg.wsdl", "w", encoding="utf-8") as f:
                f.write(res.text)
            break
    except Exception as e:
        print(f"Error: {e}")
