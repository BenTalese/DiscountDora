from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from framework.dora_api.infrastructure.configuration_manager import \
    ConfigurationManager

app = Flask(__name__)

config_manager = ConfigurationManager()
app.config['SQLALCHEMY_DATABASE_URI'] = config_manager.get_db_connection_string()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy()
