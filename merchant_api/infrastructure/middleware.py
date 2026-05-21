from flask import Blueprint

# The Flask-CORS extension (configured in startup.py) handles preflight
# (OPTIONS) requests automatically — including writing the
# Access-Control-Allow-* headers on the response. A previous incarnation of
# this blueprint short-circuited OPTIONS with a JSON body whose keys looked
# like CORS headers, which silently broke the actual headers. Leaving the
# blueprint as an empty placeholder so existing register_blueprint calls
# in startup.py stay valid.
MIDDLEWARE = Blueprint('MIDDLEWARE', __name__)
