import json
from flask import Flask
from app.utils.db import init_db

with open("config.json") as f:
    config = json.load(f)
    flask_config = config["ARANGO_CONFIG"]

app = Flask(__name__, template_folder="templates", static_folder="static")

app.config.update(flask_config)

from app.routes import coar_inbox, db_updater, status, softwares, documents

db = init_db(app)

@app.route("/")
def home():
    return "hello world"
