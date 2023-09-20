import asyncio
import json
import os
import sys
from typing import List

from flask_sqlalchemy import SQLAlchemy

sys.path.append(os.getcwd())

from clapy import DependencyInjectorServiceProvider, RequiredInputValidator
from dependency_injector import providers
from flask import Flask, current_app, render_template

from application.infrastructure.mapping.mapper import Mapper
from application.services.imapper import IMapper
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_items.get_stock_items.iget_stock_items_output_port import \
    IGetStockItemsOutputPort
from domain.entities.stock_item import StockItem
from framework.dashboard import routes
from framework.persistence.infrastructure.persistence_context import \
    PersistenceContext
from interface_adaptors.controllers.stock_item_controller import \
    StockItemController

# from framework.persistence.models import *


# TODO: Find a place for this to live:
class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def configure_persistence_services(self):
        self.service_provider.register_service(providers.Factory, PersistenceContext, IPersistenceContext)
        return self

    def configure_application_services(self):
        self.service_provider.register_service(providers.Factory, Mapper, IMapper) # TODO: Separate mapping services method??
        return self

    def configure_interface_adaptors_services(self):
        self.service_provider.register_service(providers.Factory, StockItemController)
        return self

    def configure_clapy_services(self):
        self.service_provider.configure_clapy_services(["application/use_cases"], [r"venv", r"src"], [r".*main\.py"])
        return self

class QuickTestPresenter(IGetStockItemsOutputPort):
    async def present_stock_items(self, stock_items: List[StockItem]):
        x = stock_items()()
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

    # import framework.persistence.models

    # db.init_app(app)

    # x = {
    #         mapper.class_.__name__: mapper.class_
    #         for mapper in db.Model.registry.mappers
    #     }

    PersistenceContext.initialise(app)

    _Controller: StockItemController = _ServiceProvider.get_service(StockItemController)
    gg = QuickTestPresenter()
    await _Controller.get_stock_items_async(gg)
    v = 0
    app.run()

# db = SQLAlchemy()
# migrate = Migrate()
# bcrypt = Bcrypt()

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
