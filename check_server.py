import requests
import time

for i in range(10):
    try:
        r = requests.get('http://127.0.0.1:8000/api/v1/health', timeout=2)
        print(f"Attempt {i+1}: status={r.status_code}, body={r.text}")
        if r.status_code == 200:
            break
    except Exception as e:
        print(f"Attempt {i+1}: {e}")
    time.sleep(1)