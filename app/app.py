import json
from flask import Flask
from pyArango.connection import Connection

with open("config.json") as f:
    config = json.load(f)
    flask_config = config["ARANGO_CONFIG"]

app = Flask(__name__, template_folder="templates", static_folder="static")

app.config.update(flask_config)

def init_db():
    global db
    conn = Connection(
        arangoURL="http://{host}:{port}".format(
            host=app.config["ARANGO_HOST"],
            port=app.config["ARANGO_PORT"]
        ),
        username=app.config["ARANGO_USERNAME"],
        password=app.config["ARANGO_PASSWORD"]
    )

    if not conn.hasDatabase(app.config["ARANGO_DB"]):
        conn.createDatabase(name=app.config["ARANGO_DB"])

    global db
    db = Connection(
        arangoURL="http://{host}:{port}".format(
            host=app.config["ARANGO_HOST"],
            port=app.config["ARANGO_PORT"]
        ),
        username=app.config["ARANGO_USERNAME"],
        password=app.config["ARANGO_PASSWORD"]
    )[app.config["ARANGO_DB"]]

from app.routes import coar_inbox, db_updater_json, status

init_db()

@app.route("/")
def home():
    return "hello world"
