import os
import requests

API_URL = "http://127.0.0.1:5500/insert"
JSON_DIR = "./app/static/data/json_files"

API_KEY = "admin"

# Get all JSON files
json_files = [f for f in os.listdir(JSON_DIR) if f.endswith(".json")]

for json_file in json_files:
    file_path = os.path.join(JSON_DIR, json_file)

    with open(file_path, "rb") as f:
        files = {"file": (json_file, f, "application/json")}
        headers = {"x-api-key": API_KEY}  # Send the API key here
        try:
            response = requests.post(API_URL, files=files, headers=headers)
            print(f"Response: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"Error sending {json_file}: {e}")
