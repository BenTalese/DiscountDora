from flask import Blueprint, jsonify

error_handlers = Blueprint('error_handlers', __name__)

# FIXME: BAD! Read the flask docs: https://flask.palletsprojects.com/en/2.3.x/errorhandling/
@error_handlers.errorhandler(Exception)
def handle_global_exception(error):
    response = {
        'message': 'An unhandled error occurred',
        'error': str(error),
    }
    return jsonify(response), 500
