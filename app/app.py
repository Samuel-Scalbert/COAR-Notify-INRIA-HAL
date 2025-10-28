import json
import os
from flask import Flask, render_template_string, jsonify  # <-- add jsonify import
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


@app.get("/")
def home():
    host = app.config.get("ARANGO_HOST")
    port = app.config.get("ARANGO_PORT")
    user = app.config.get("ARANGO_USERNAME")
    db_name = app.config.get("ARANGO_DB")

    status = "down"
    version = None
    num_collections = "unknown"
    error = None

    try:
        conn = Connection(
            arangoURL=f"http://{host}:{port}",
            username=user,
            password=app.config.get("ARANGO_PASSWORD"),
        )
        status = "up"
        try:
            version_info = conn.getVersion() or {}
            version = version_info.get("version") or version_info.get("server")
        except Exception:
            pass

        try:
            database = conn[db_name]
            coll_info = database.fetchCollections()
            if isinstance(coll_info, dict) and "result" in coll_info:
                num_collections = len(coll_info["result"])
        except Exception:
            pass
    except Exception as e:
        error = str(e)

    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Service status</title>
      <style>
        body { font-family: system-ui, sans-serif; margin: 2rem; }
        .up { color: #2e7d32; }
        .down { color: #c62828; }
        code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; }
        ul { line-height: 1.7; }
      </style>
    </head>
    <body>
      <h1>Service</h1>
      <p>Status: <strong class="{{ 'up' if status == 'up' else 'down' }}">{{ status }}</strong></p>
      {% if error %}
        <p><strong>Error:</strong> <code>{{ error }}</code></p>
      {% endif %}
      <h2>ArangoDB</h2>
      <ul>
        <li>Host: <code>{{ host }}</code></li>
        <li>Port: <code>{{ port }}</code></li>
        <li>DB: <code>{{ db_name }}</code></li>
        <li>User: <code>{{ user }}</code></li>
        <li>Version: <code>{{ version or 'unknown' }}</code></li>
        <li>Collections: <code>{{ num_collections }}</code></li>
      </ul>
      <p>Health endpoint: <a href="/health">/health</a></p>
    </body>
    </html>
    """
    return render_template_string(
        html,
        status=status,
        host=host,
        port=port,
        db_name=db_name,
        user=user,
        version=version,
        num_collections=num_collections,
        error=error,
    )


@app.get("/health")
def health():
    host = app.config.get("ARANGO_HOST")
    port = app.config.get("ARANGO_PORT")
    user = app.config.get("ARANGO_USERNAME")
    db_name = app.config.get("ARANGO_DB")

    try:
        conn = Connection(
            arangoURL=f"http://{host}:{port}",
            username=user,
            password=app.config.get("ARANGO_PASSWORD")
        )

        # Server/version check
        version_info = {}
        try:
            version_info = conn.getVersion() or {}
        except Exception:
            version_info = {}
        version = version_info.get("version") or version_info.get("server")

        # DB/collections check
        num_collections = "unknown"
        try:
            database = conn[db_name]
            coll_info = database.fetchCollections()
            if isinstance(coll_info, dict) and "result" in coll_info:
                num_collections = len(coll_info["result"])
        except Exception:
            pass

        return jsonify({
            "status": "up",
            "arango": {
                "host": host,
                "port": port,
                "db": db_name,
                "user": user,
                "version": version,
                "collections": num_collections
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "down",
            "error": str(e),
            "arango": {
                "host": host,
                "port": port,
                "db": db_name,
                "user": user
            }
        }), 503