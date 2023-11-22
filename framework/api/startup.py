import os
import sys

sys.path.append(os.getcwd())

import asyncio
import json

from clapy import DependencyInjectorServiceProvider
from flask import Flask
from flask_cors import CORS

from framework.api.error_handlers import error_handlers
from framework.api.middleware import middleware
from framework.api.routes.products.product_router import product_router
from framework.api.routes.stock_items.stock_item_router import \
    stock_item_router
from framework.api.routes.web_scraper.web_scraper_router import \
    web_scraper_router
from framework.api.service_collection_builder import ServiceCollectionBuilder
from framework.persistence.infrastructure.persistence_context import \
    SqlAlchemyPersistenceContext


async def startup():
    app = Flask(__name__)

    CORS(app, resources={r'/api/*': {'origins': 'http://localhost:5173', "allow_headers": ["*", "Content-Type"]}})

    app.service_provider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()

    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir,'appsettings.json'), 'r') as _Configuration:
        app.config.update(json.load(_Configuration))

    await SqlAlchemyPersistenceContext.initialise(app)

    app.register_blueprint(middleware)
    app.register_blueprint(error_handlers)

    register_routers(app)

    await SqlAlchemyPersistenceContext.test(app)

    app.run()

def register_routers(app: Flask):
    app.register_blueprint(stock_item_router)
    app.register_blueprint(web_scraper_router)
    app.register_blueprint(product_router)

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
