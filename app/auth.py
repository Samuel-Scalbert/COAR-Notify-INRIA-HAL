from functools import wraps
from flask import request, jsonify
import json

with open("auth_admin.json") as f:
    config = json.load(f)
    API_KEY = config["TOKEN"]

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized Token"}), 401
        return f(*args, **kwargs)
    return decorated