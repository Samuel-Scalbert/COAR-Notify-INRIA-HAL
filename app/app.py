import json
from flask import Flask
from pyArango.connection import Connection

# Load config.json
with open("config.json") as f:
    config = json.load(f)
    flask_config = config["ARANGO_CONFIG"]

app = Flask(__name__, template_folder="templates", static_folder="static")

# Apply config to Flask app
app.config.update(flask_config)

def init_db():
    global db
    # First connection
    conn = Connection(
        arangoURL="http://{host}:{port}".format(
            host=app.config["ARANGO_HOST"],
            port=app.config["ARANGO_PORT"]
        ),
        username=app.config["ARANGO_USERNAME"],
        password=app.config["ARANGO_PASSWORD"]
    )

    # Create DB if it doesn't exist
    if not conn.hasDatabase(app.config["ARANGO_DB"]):
        conn.createDatabase(name=app.config["ARANGO_DB"])

    # Final connection to the DB
    global db
    db = Connection(
        arangoURL="http://{host}:{port}".format(
            host=app.config["ARANGO_HOST"],
            port=app.config["ARANGO_PORT"]
        ),
        username=app.config["ARANGO_USERNAME"],
        password=app.config["ARANGO_PASSWORD"]
    )[app.config["ARANGO_DB"]]

# Import routes *after* app is defined
from app.routes import coar_inbox  

# Initialize DB
init_db()

@app.route("/")
def home():
    return "hello world"
