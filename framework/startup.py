import asyncio
import json
import os
import sys

from clapy import DependencyInjectorServiceProvider, RequiredInputValidator
from dependency_injector import providers
from flask import Flask, render_template


sys.path.append(os.getcwd())

from application.services.ipersistence_context import IPersistenceContext
from framework.persistence.infrastructure.persistence_context import \
    PersistenceContext

from framework.dashboard import routes

# TODO: Find a place for this to live:
class ServiceCollectionBuilder:
    def __init__(self, service_provider: DependencyInjectorServiceProvider):
        self.service_provider = service_provider

    def configure_persistence_services(self):
        self.service_provider.register_service(providers.Factory, PersistenceContext, IPersistenceContext)
        return self

    def configure_application_services(self):
        self.service_provider.register_service(providers.Factory, RequiredInputValidator)
        return self

    def configure_clapy_services(self):
        self.service_provider.configure_clapy_services(["application/use_cases"], [r"venv", r"src"], [r".*main\.py"])
        return self



async def startup():
    ServiceCollectionBuilder(DependencyInjectorServiceProvider()) \
        .configure_clapy_services() \
        .configure_persistence_services() \
        .configure_application_services()

    app = Flask(__name__, template_folder='dashboard/templates')
    app.add_url_rule("/", view_func=routes.index, methods=['GET'])

    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir,'appsettings.json'), 'r') as _Configuration:
        app.config.update(json.load(_Configuration))

    PersistenceContext.initialise(app)

    app.run()

    # testentity = Test(uuid.uuid4(), "test")
    # testconfig = TestConfiguration(**testentity.__dict__)

    # migrate = Migrate(app, db).??? #TODO: Learn https://flask-migrate.readthedocs.io/en/latest/index.html
    #debug_mode = app.config.get('DEBUG')

if __name__ == '__main__':
    asyncio.run(startup())
