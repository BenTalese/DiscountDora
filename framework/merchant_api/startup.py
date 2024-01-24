from flask import Flask
from flask_cors import CORS


app = Flask(__name__)

if __name__ == "__main__": # TODO: multiple origins?
    CORS(app, resources={r'/mapi/*': {'origins': 'http://localhost:5174', "allow_headers": ["*", "Content-Type"]}})
    app.run('localhost', 5172)
