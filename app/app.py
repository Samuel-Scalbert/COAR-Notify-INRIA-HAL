import json
import os
import logging
from flask import Flask, render_template, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from app.utils.db import init_db, get_db
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # This outputs to stdout/stderr which Docker captures
    ]
)

with open("config.json") as f:
    config = json.load(f)
    flask_config = config["ARANGO_CONFIG"]

# Override with environment variables if set
flask_config["ARANGO_HOST"] = os.environ.get("ARANGO_HOST", flask_config.get("ARANGO_HOST", "arangodb"))
flask_config["ARANGO_PORT"] = int(os.environ.get("ARANGO_PORT", flask_config.get("ARANGO_PORT", 8529)))
flask_config["ARANGO_USERNAME"] = os.environ.get("ARANGO_USERNAME", flask_config.get("ARANGO_USERNAME", "root"))
flask_config["ARANGO_PASSWORD"] = os.environ.get("ARANGO_ROOT_PASSWORD", flask_config.get("ARANGO_PASSWORD", "examplepassword"))
flask_config["ARANGO_DB"] = os.environ.get("ARANGO_DB", flask_config.get("ARANGO_DB", "test"))

# Software Viz configuration
flask_config["SW_VIZ_URL"] = os.environ.get("SW_VIZ_URL", "")
flask_config["SW_VIZ_TOKEN"] = os.environ.get("SW_VIZ_TOKEN", "")

app = Flask(__name__, template_folder="templates", static_folder="static")

app.config.update(flask_config)

# Configure ProxyFix for reverse proxy
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

# Import routes after app creation to avoid circular imports
from app.routes import api_software, api_documents, coar_inbox, api_status

db_manager = init_db(app)

# Print ArangoDB connection information on startup
try:
    connection_info = db_manager.get_connection_info()
    print(f"ArangoDB connection: host={connection_info['host']} port={connection_info['port']} "
          f"db='{connection_info['db']}' user='{connection_info['user']}' "
          f"version={connection_info['version']} collections={connection_info['collections']}")
except Exception as e:
    print(f"ArangoDB info: failed to fetch info: {e}")


@app.get("/")
def home():
    try:
        db_manager = get_db()
        connection_info = db_manager.get_connection_info()

        return render_template("home.html",
            status=connection_info["status"],
            host=connection_info["host"],
            port=connection_info["port"],
            db_name=connection_info["db"],
            user=connection_info["user"],
            version=connection_info["version"],
            num_collections=connection_info["collections"],
            error=connection_info.get("error"),
        )
    except Exception as e:
        # Fallback if database manager is not available
        error_msg = str(e)
        return render_template("error.html", error=error_msg)


@app.get("/health")
def health():
    try:
        db_manager = get_db()
        connection_info = db_manager.get_connection_info()

        if connection_info["status"] == "up":
            return jsonify({
                "status": "up",
                "arango": {
                    "host": connection_info["host"],
                    "port": connection_info["port"],
                    "db": connection_info["db"],
                    "user": connection_info["user"],
                    "version": connection_info["version"],
                    "collections": connection_info["collections"]
                }
            }), 200
        else:
            return jsonify({
                "status": "down",
                "error": connection_info.get("error", "Unknown error"),
                "arango": {
                    "host": connection_info["host"],
                    "port": connection_info["port"],
                    "db": connection_info["db"],
                    "user": connection_info["user"]
                }
            }), 503

    except Exception as e:
        return jsonify({
            "status": "down",
            "error": str(e),
            "arango": {
                "host": app.config.get("ARANGO_HOST", "unknown"),
                "port": app.config.get("ARANGO_PORT", "unknown"),
                "db": app.config.get("ARANGO_DB", "unknown"),
                "user": app.config.get("ARANGO_USERNAME", "unknown")
            }
        }), 503