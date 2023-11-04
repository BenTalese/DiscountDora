from dataclasses import dataclass
from http.client import (BAD_REQUEST, INTERNAL_SERVER_ERROR, NOT_FOUND,
                         UNPROCESSABLE_ENTITY)

from flask import Response, jsonify


def get_problem_details(status_code, type, title, detail, instance):
    response_data = {
        'status': status_code,
        'type': type,
        'title': title,
        'detail': detail,
        'instance': instance
    }
    response = jsonify(response_data)
    response.status_code = status_code
    return response

@dataclass
class ProblemDetails:
    type: str
    title: str
    detail: str
    instance: str
    status: int
    errors: dict

def get_problem_details(type, title, detail, instance, status, errors):
    problem_details = ProblemDetails(
        type,
        title,
        detail,
        instance,
        status,
        errors
    )

    response = Response(
        response = jsonify(problem_details),
        status = status,
        headers = { 'Content-Language': 'en', 'Access-Control-Allow-Origin': 'http://localhost:5173' },
        content_type = 'application/problem+json'
    )

    return response

def bad_request(message='Bad Request'):
    response = jsonify({'error': message})
    response.status_code = BAD_REQUEST
    return response

def unprocessable_entity(message='Unprocessable Entity'):
    response = jsonify({'error': message})
    response.status_code = UNPROCESSABLE_ENTITY
    return response

def internal_server_error(message='Internal Server Error'):
    response = jsonify({'error': message})
    response.status_code = INTERNAL_SERVER_ERROR
    return response

def not_found(message='Not Found'):
    response = jsonify({'error': message})
    response.status_code = NOT_FOUND
    return response

#TODO: Other responses
