import json
from app.app import app

# Load config.json
with open("config.json") as f:
    config = json.load(f)

flask_config = config.get("FLASK_CONFIG", {})

if __name__ == "__main__":
    app.run(
        host=flask_config.get("FLASK_HOST", "127.0.0.1"),
        port=flask_config.get("FLASK_PORT", 5000),
        debug=False
    )
