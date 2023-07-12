import requests
url = "http://localhost:8000/upload"
file_path = "/home/mnk/putty.exe"

with open(file_path, 'rb') as f:
    files = {'file': f}
    response = requests.post(url, files=files)

if response.status_code == 200:
    print(response.json()["result"])
else:
    print(f"Error: {response.status_code} ({response.reason})")

    