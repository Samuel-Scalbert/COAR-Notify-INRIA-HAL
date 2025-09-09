import os
import requests

# URL of your Flask API
API_URL = "http://127.0.0.1:5500/insert"

# Path to directory with JSON files
JSON_DIR = "./app/static/data/json_files"

# Get all JSON files
json_files = [f for f in os.listdir(JSON_DIR) if f.endswith(".json")]

for json_file in json_files:
    file_path = os.path.join(JSON_DIR, json_file)

    with open(file_path, "rb") as f:
        files = {"file": (json_file, f, "application/json")}
        try:
            response = requests.post(API_URL, files=files)
            print(f"Response: {response.status_code} - {response.json()}")
        except Exception as e:
            print(f"Error sending {json_file}: {e}")
