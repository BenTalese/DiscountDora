import asyncio
import json
import os
import sys
from typing import List

sys.path.append(os.getcwd())

from clapy import DependencyInjectorServiceProvider
from flask import Flask

from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort
from domain.entities.stock_item import StockItem
from framework.dashboard import routes
from framework.persistence.infrastructure.persistence_context import \
    PersistenceContext
from framework.service_collection_builder import ServiceCollectionBuilder
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController


class QuickTestPresenter(IGetStockItemsOutputPort):
    async def present_stock_items_async(self, stock_items: List[StockItem]):
        x = stock_items()
        print("Made it!")

from framework.persistence.infrastructure.persistence_context import db


async def startup():
    _ServiceProvider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()) \
        .configure_persistence_services() \
        .configure_application_services() \
        .configure_clapy_services() \
        .configure_interface_adaptors_services() \
        .service_provider

    app = Flask(__name__, template_folder='dashboard/templates')

    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir,'appsettings.json'), 'r') as _Configuration:
        app.config.update(json.load(_Configuration))

    app.add_url_rule("/", view_func=routes.index, methods=['GET'])
    app.add_url_rule("/search", view_func=routes.add_stock_item, methods=['POST'])

    await PersistenceContext.initialise(app)

    PersistenceContext.test(app)

    _Controller: StockItemController = _ServiceProvider.get_service(StockItemController)
    gg = QuickTestPresenter()
    await _Controller.get_stock_items_async(gg)
    v = 0
    app.run()

# db = SQLAlchemy()
# migrate = Migrate()
# bcrypt = Bcrypt() # TODO: Look into this

# def create_app():
#     app = Flask(__name__, static_url_path='', static_folder='./../react/public')
#     app.config.from_object(os.getenv("APP_SETTINGS", "config.Development"))
#     db.init_app(app)
#     migrate.init_app(app, db)
#     bcrypt.init_app(app)

#     return app


    # Example of simple default use case invocation:


    # testentity = Test(uuid.uuid4(), "test")
    # testconfig = TestConfiguration(**testentity.__dict__)

    # migrate = Migrate(app, db).??? #TODO: Learn https://flask-migrate.readthedocs.io/en/latest/index.html
    #debug_mode = app.config.get('DEBUG')

if __name__ == '__main__':
    asyncio.run(startup())
