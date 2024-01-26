import os
import sys

sys.path.append(os.getcwd())

from flask import Flask
from flask_cors import CORS

from framework.merchant_api.infrastructure.middleware import MIDDLEWARE
from framework.merchant_api.routes import PRODUCT_ROUTER

if __name__ == "__main__":
    app = Flask(__name__)
    CORS(app, resources={r'/api/*': {'origins': 'http://localhost:5174', "allow_headers": ["*", "Content-Type"]}})
    app.register_blueprint(MIDDLEWARE)
    app.register_blueprint(PRODUCT_ROUTER)
    app.run('localhost', 5172)
