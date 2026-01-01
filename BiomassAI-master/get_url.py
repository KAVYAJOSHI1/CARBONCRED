import time
import requests
import sys

def get_url():
    for _ in range(10):
        try:
            response = requests.get('http://localhost:4040/api/tunnels')
            data = response.json()
            if data['tunnels']:
                return data['tunnels'][0]['public_url']
        except Exception:
            pass
        time.sleep(2)
    return None

url = get_url()
if url:
    print(url)
else:
    print("No tunnel found")
