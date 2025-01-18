from pathlib import Path

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from framework.dora_api.infrastructure.configuration_manager import \
    ConfigurationManager

config_manager = ConfigurationManager()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config_manager.get_db_connection_string()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy()
Path('data').mkdir(exist_ok=True)
db.init_app(app)
import framework.dora_api.persistence.models  # Makes models visible to db instance  # noqa: F401

migrate = Migrate()
migrate.init_app(app, db, Path(__file__).parent / 'persistence' / 'migrations')
