from flask import Blueprint, jsonify

ERROR_HANDLERS = Blueprint('ERROR_HANDLERS', __name__)

# FIXME: BAD! Read the flask docs: https://flask.palletsprojects.com/en/2.3.x/errorhandling/
@ERROR_HANDLERS.errorhandler(Exception)
def handle_global_exception(error):
    response = {
        'message': 'An unhandled error occurred',
        'error': str(error),
    }
    return jsonify(response), 500
