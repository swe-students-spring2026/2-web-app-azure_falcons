from flask import Flask
from pymongo import MongoClient
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    client = MongoClient(app.config["MONGO_URI"])
    app.mongo_db = client[app.config["MONGO_DB_NAME"]]

    from app.routes.page_routes import page_bp
    from app.routes.entry_routes import entry_bp
    app.register_blueprint(page_bp)
    app.register_blueprint(entry_bp)

    return app