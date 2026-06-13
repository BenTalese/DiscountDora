import pytest
import requests


@pytest.mark.xfail(
    reason="FU-167: an unknown GET /api/<x> path returns a 404 with the SPA's "
    "text/html body, not the JSON problem-detail the other verbs return. The "
    "SPA history-mode catch-all (GET-only) still intercepts unmatched /api/ "
    "GETs; POST/PATCH/DELETE correctly return JSON. Tracked as a real defect; "
    "this asserts the intended (JSON) contract so it xpasses once fixed.",
    strict=True,
)
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


def test__DeleteEndpointDoesNotExist__EndpointNotFoundResponse(api):
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
