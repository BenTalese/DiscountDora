import os
import secrets
from pathlib import Path

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from dora_api.infrastructure.configuration_manager import DoraConfig

config_manager = DoraConfig()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config_manager.get_db_connection_string()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # True has been deprecated and does nothing

# Session / cookie config. The SECRET_KEY signs the session cookie. Set
# DORA_SECRET_KEY in the environment for prod; the dev fallback writes a
# stable random key to disk so sessions survive restarts. Never commit the
# generated file — it's already covered by the .data folder gitignore.
_SecretKeyFile = Path('data') / '.secret_key'
_SecretKeyFromEnv = os.environ.get('DORA_SECRET_KEY')
if _SecretKeyFromEnv:
    app.config['SECRET_KEY'] = _SecretKeyFromEnv
else:
    if not _SecretKeyFile.exists():
        Path('data').mkdir(exist_ok=True)
        _SecretKeyFile.write_text(secrets.token_hex(32))
    app.config['SECRET_KEY'] = _SecretKeyFile.read_text().strip()

# Same-site=Lax keeps the session cookie on top-level navigations and same-
# origin requests. For cross-origin SPA access (dev: web 5174 → api 5170),
# the CORS layer must enable credentials, and axios must set withCredentials.
app.config['SESSION_COOKIE_NAME'] = 'dora_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# Secure cookies require HTTPS — toggle on for production via env.
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('DORA_SECURE_COOKIES', '').lower() in ('1', 'true', 'yes')

db = SQLAlchemy()
Path('data').mkdir(exist_ok=True)
db.init_app(app)


# SQLite does not enforce foreign-key constraints (including ON DELETE
# cascades) unless this PRAGMA is set per connection.
@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

from dora_api.persistence.table_mappings import \
    configure_mappings  # noqa: E402

configure_mappings(db)

migrate = Migrate()
migrate.init_app(app, db, str(Path(__file__).parent / 'persistence' / 'migrations'))
