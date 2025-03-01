import requests


def test__GetEndpointDoesNotExist__EndpointNotFoundResponse(api):
    _Response = requests.get("http://localhost:5170/api/55/ety")

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == {
        'detail': 'Endpoint was not found.',
        'errors': {},
        'status': 404,
        'title': 'Endpoint was not found.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4'
    }


def test__PostEndpointDoesNotExist__EndpointNotFoundResponse(api):
    _Response = requests.post("http://localhost:5170/api/aa/bb")

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == {
        'detail': 'Endpoint was not found.',
        'errors': {},
        'status': 404,
        'title': 'Endpoint was not found.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4'
    }


def test__PatchEndpointDoesNotExist__EndpointNotFoundResponse(api):
    _Response = requests.patch("http://localhost:5170/api/aa/bb/cc")

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == {
        'detail': 'Endpoint was not found.',
        'errors': {},
        'status': 404,
        'title': 'Endpoint was not found.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4'
    }


def test__DeletendpointDoesNotExist__EndpointNotFoundResponse(api):
    _Response = requests.delete("http://localhost:5170/api/1/2")

    assert _Response.status_code == 404
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json() == {
        'detail': 'Endpoint was not found.',
        'errors': {},
        'status': 404,
        'title': 'Endpoint was not found.',
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.4'
    }
