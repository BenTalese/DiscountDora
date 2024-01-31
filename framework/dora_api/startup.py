import os
import sys

sys.path.append(os.getcwd())

import asyncio
import json

from clapy import DependencyInjectorServiceProvider
from flask import Flask
from flask_cors import CORS

from framework.dora_api.infrastructure.error_handlers import ERROR_HANDLERS
from framework.dora_api.infrastructure.middleware import MIDDLEWARE
from framework.dora_api.routes.merchants.merchant_router import MERCHANT_ROUTER
from framework.dora_api.routes.products.product_router import PRODUCT_ROUTER
from framework.dora_api.routes.stock_items.stock_item_router import \
    STOCK_ITEM_ROUTER
from framework.dora_api.routes.users.user_router import USER_ROUTER
from framework.dora_api.service_collection_builder import ServiceCollectionBuilder
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

    app.register_blueprint(MIDDLEWARE)
    app.register_blueprint(ERROR_HANDLERS)

    register_routers(app)
    await SqlAlchemyPersistenceContext.test(app)

    app.run('localhost', 5170, app.config.get('DEBUG'), use_reloader=False) # TODO: appsettings


def register_routers(app: Flask):
    app.register_blueprint(MERCHANT_ROUTER)
    app.register_blueprint(PRODUCT_ROUTER)
    app.register_blueprint(STOCK_ITEM_ROUTER)
    app.register_blueprint(USER_ROUTER)


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
