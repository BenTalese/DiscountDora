import asyncio
import json
import os
import sys
from typing import List

sys.path.append(os.getcwd())

from application.dtos.stock_item_dto import StockItemDto
from clapy import DependencyInjectorServiceProvider, IServiceProvider
from dependency_injector import containers, providers
from flask import Flask

from framework.api.middleware import middleware
from framework.api.stock_items.stock_items_controller import stock_items
from framework.persistence.infrastructure.persistence_context import \
    SqlAlchemyPersistenceContext
from framework.service_collection_builder import ServiceCollectionBuilder
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController


#FIXME: Carefully consider the placement of this file and what it does...
# The services here might be API specific, or maybe everything is hosted under the
# umbrella of the web app and it makes sense...not sure...
class Startup:

    async def startup():
        service_provider = ServiceCollectionBuilder(DependencyInjectorServiceProvider()) \
            .configure_persistence_services() \
            .configure_application_services() \
            .configure_clapy_services() \
            .configure_interface_adaptors_services() \
            .service_provider

        app = Flask(__name__)

        app.service_provider = service_provider

        basedir = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(basedir,'appsettings.json'), 'r') as _Configuration:
            app.config.update(json.load(_Configuration))

        await SqlAlchemyPersistenceContext.initialise(app)

        app.register_blueprint(middleware)
        app.register_blueprint(stock_items)

        app.stock_item_controller = service_provider.get_service(StockItemController)
        await SqlAlchemyPersistenceContext.test(app)

        app.run()

        # app.add_url_rule("/", view_func=routes.index, methods=['GET'])
        # app.add_url_rule("/search", view_func=routes.add_stock_item, methods=['POST'])


        # _Controller: StockItemController = _ServiceProvider.get_service(StockItemController)
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

if __name__ == '__main__':
    asyncio.run(Startup.startup())
