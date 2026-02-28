from pathlib import Path

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from dora_api.infrastructure.configuration_manager import ConfigurationManager

config_manager = ConfigurationManager()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config_manager.get_db_connection_string()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # True has been deprecated and does nothing

db = SQLAlchemy()
Path('data').mkdir(exist_ok=True)
db.init_app(app)

from dora_api.persistence.table_mappings import configure_mappings  # noqa: E402
configure_mappings(db)

migrate = Migrate()
migrate.init_app(app, db, str(Path(__file__).parent / 'persistence' / 'migrations'))
