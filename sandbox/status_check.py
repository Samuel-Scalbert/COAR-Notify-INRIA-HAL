import requests

url = "http://127.0.0.1:5500/status"
headers = {"x-api-key": "admin"}

response = requests.get(url, headers=headers)
print(response.json())