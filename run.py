import json
from app.app import app
from app.utils.db import init_db

# Load config.json
with open("config.json") as f:
    config = json.load(f)

flask_config = config.get("FLASK_CONFIG", {})

if __name__ == "__main__":
    init_db(app)
    app.run(
        host=flask_config.get("FLASK_HOST", "127.0.0.1"),
        port=flask_config.get("FLASK_PORT", 5000),
        debug=False
    )
