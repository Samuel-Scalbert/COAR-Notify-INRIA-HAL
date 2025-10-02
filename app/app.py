import json
import os
from flask import Flask
from app.utils.db import init_db
from dotenv import load_dotenv
from pyArango.connection import Connection

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

from app.routes import coar_inbox, jsonSOFTCITE_to_DB, api_status, api_software, api_documents

db = init_db(app)

# Print ArangoDB connection information on startup
try:
    host = app.config.get("ARANGO_HOST")
    port = app.config.get("ARANGO_PORT")
    user = app.config.get("ARANGO_USERNAME")
    db_name = app.config.get("ARANGO_DB")

    print(f"Connecting to ArangoDB at {host}:{port}, database '{db_name}' as user '{user}'")
    conn = Connection(
        arangoURL=f"http://{host}:{port}",
        username=user,
        password=app.config.get("ARANGO_PASSWORD")
    )

    version_info = {}
    try:
        # pyArango Connection.getVersion() returns a dict like {"server": "arango", "version": "3.11.x"}
        version_info = conn.getVersion()
    except Exception:
        pass
    version = None
    if isinstance(version_info, dict):
        version = version_info.get("version") or version_info.get("server")

    # Try to estimate number of collections
    num_collections = "unknown"
    try:
        coll_info = db.fetchCollections()
        if isinstance(coll_info, dict) and "result" in coll_info:
            num_collections = len(coll_info["result"])
    except Exception:
        pass

    print(f"ArangoDB connection: host={host} port={port} db='{db_name}' user='{user}' version={version} collections={num_collections}")
except Exception as e:
    print(f"ArangoDB info: failed to fetch info: {e}")


@app.route("/")
def home():
    return "hello world"
