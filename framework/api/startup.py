import asyncio
import json
import os
import sys
from typing import List

from flask_cors import CORS

sys.path.append(os.getcwd())

from clapy import DependencyInjectorServiceProvider
from flask import Flask

from framework.api.error_handlers import error_handlers
from framework.api.middleware import middleware
from framework.api.routes.stock_items.stock_items_controller import stock_items
from framework.api.routes.web_scraper.web_scraper_controller import web_scraper
from framework.api.service_collection_builder import ServiceCollectionBuilder
from framework.persistence.infrastructure.persistence_context import \
    SqlAlchemyPersistenceContext
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController


#FIXME: Carefully consider the placement of this file and what it does...
# The services here might be API specific, or maybe everything is hosted under the
# umbrella of the web app and it makes sense...not sure...
async def startup():
    service_provider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()).build_service_provider()

    app = Flask(__name__)

    CORS(app, resources={r'/api/*': {'origins': 'http://localhost:5173', "allow_headers": "*"}})

    app.service_provider = service_provider

    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir,'appsettings.json'), 'r') as _Configuration:
        app.config.update(json.load(_Configuration))

    await SqlAlchemyPersistenceContext.initialise(app)

    app.register_blueprint(middleware)
    app.register_blueprint(error_handlers)

    register_controllers(app)

    app.stock_item_controller = service_provider.get_service(StockItemController)
    await SqlAlchemyPersistenceContext.test(app)

    app.run()

    # app.add_url_rule("/", view_func=routes.index, methods=['GET'])
    # app.add_url_rule("/search", view_func=routes.add_stock_item, methods=['POST'])

    # _Controller: StockItemController = service_provider.get_service(StockItemController)
    # gg = QuickTestPresenter()
    # await _Controller.get_stock_items_async(gg)

    # v = 0

# bcrypt = Bcrypt().init_app(app) # TODO: Look into this

# def create_app():
#     app = Flask(__name__, static_url_path='', static_folder='./../react/public')
#     app.config.from_object(os.getenv("APP_SETTINGS", "config.Development"))
#     db.init_app(app)
#     migrate.init_app(app, db)
#     bcrypt

#     return app


    # Example of simple default use case invocation:


    # testentity = Test(uuid.uuid4(), "test")
    # testconfig = TestConfiguration(**testentity.__dict__)

    # migrate = Migrate(app, db).??? #TODO: Learn https://flask-migrate.readthedocs.io/en/latest/index.html
    #debug_mode = app.config.get('DEBUG')

def register_controllers(app: Flask):
    app.register_blueprint(stock_items)
    app.register_blueprint(web_scraper)

if __name__ == '__main__':
    asyncio.run(startup())
