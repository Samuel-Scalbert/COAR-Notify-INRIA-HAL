import requests

url = "http://127.0.0.1:5500/status"
#headers = {"x-api-key": "woop"}
headers = {"x-api-key": "supersecret123"}

response = requests.get(url, headers=headers)
print(response.json())
