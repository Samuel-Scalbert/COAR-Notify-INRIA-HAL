import json
import os
from flask import Flask
from app.utils.db import init_db
from dotenv import load_dotenv

load_dotenv()

with open("config.json") as f:
    config = json.load(f)
    flask_config = config["ARANGO_CONFIG"]

# Override with environment variables if set
flask_config["ARANGO_HOST"] = os.environ.get("ARANGO_HOST", flask_config.get("ARANGO_HOST", "arangodb"))
flask_config["ARANGO_PORT"] = int(os.environ.get("ARANGO_PORT", flask_config.get("ARANGO_PORT", 8529)))
flask_config["ARANGO_USERNAME"] = os.environ.get("ARANGO_USERNAME", flask_config.get("ARANGO_USERNAME", "root"))
flask_config["ARANGO_PASSWORD"] = os.environ.get("ARANGO_ROOT_PASSWORD", flask_config.get("ARANGO_PASSWORD", "examplepassword"))
flask_config["ARANGO_DB"] = os.environ.get("ARANGO_DB", flask_config.get("ARANGO_DB", "test"))

app = Flask(__name__, template_folder="templates", static_folder="static")

app.config.update(flask_config)

from app.routes import coar_inbox, db_updater, status, software, documents

db = init_db(app)

@app.route("/")
def home():
    return "hello world"
