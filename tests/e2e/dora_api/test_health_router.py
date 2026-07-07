import requests

#region ---------------- setup ----------------

base_route = 'http://localhost:5170/api/health'

#endregion setup

#region ---------------- health_check tests ----------------


def test__health_check__ApiIsHealthy__GetsOkayResponse(api):
    _Response = requests.get(base_route)

    # the health endpoint now returns a status document
    # ({ok, profile, schema_version, features}) rather than a bare `True`.
    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['ok'] is True


#endregion health_check tests
