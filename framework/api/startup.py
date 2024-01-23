import os
import sys

sys.path.append(os.getcwd())

import asyncio
import json

from clapy import DependencyInjectorServiceProvider
from flask import Flask
from flask_cors import CORS

from application.infrastructure.utils import get_attributes_ending_with
from framework.api.infrastructure.error_handlers import ERROR_HANDLERS
from framework.api.infrastructure.middleware import MIDDLEWARE
from framework.api.service_collection_builder import ServiceCollectionBuilder
from framework.persistence.infrastructure.persistence_context import \
    SqlAlchemyPersistenceContext


async def startup():
    app = Flask(__name__)

    CORS(app, resources={r'/api/*': {'origins': 'http://localhost:5174', "allow_headers": ["*", "Content-Type"]}})

    app.service_provider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()

    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir,'appsettings.json'), 'r') as _Configuration:
        app.config.update(json.load(_Configuration))

    await SqlAlchemyPersistenceContext.initialise(app)
    await SqlAlchemyPersistenceContext.test(app)

    register_routers(app)
    register_api_infrastructure(app)
    app.run(debug = app.config.get('DEBUG'), use_reloader=False) # TODO: appsettings

def register_routers(app: Flask):
    _Routers = get_attributes_ending_with('ROUTER', os.path.normpath('framework/api/routes'))
    for _Router in _Routers:
        app.register_blueprint(_Router)

def register_api_infrastructure(app: Flask):
    app.register_blueprint(MIDDLEWARE)
    app.register_blueprint(ERROR_HANDLERS)

if __name__ == '__main__':
    asyncio.run(startup())



# bcrypt = Bcrypt().init_app(app) # TODO: Look into this

# def create_app():
#     app = Flask(__name__, static_url_path='', static_folder='./../react/public')
#     app.config.from_object(os.getenv("APP_SETTINGS", "config.Development"))
#     db.init_app(app)
#     migrate.init_app(app, db)
#     bcrypt

    # migrate = Migrate(app, db).??? #TODO: Learn https://flask-migrate.readthedocs.io/en/latest/index.html
    #debug_mode = app.config.get('DEBUG')
