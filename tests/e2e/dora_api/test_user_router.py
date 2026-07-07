import uuid

import requests

from tests.support import is_valid_uuid

#region ---------------- setup ----------------

# list endpoints take query options on the query string and return a
# `{items, total, page, limit}` envelope; query-option errors come back via
# `bad_request(str(exc))` (message in `title`). The seed user is now
# `dora` / `ben.talese@gmail.com` (admin), not "The Coolest Guy".

base_route = 'http://localhost:5170/api/users'

#endregion setup

#region ---------------- get_users tests ----------------


def test__get_users__GettingUsers__GetsAllExpectedAttributes(api):
    # Filter to the seeded user — other suites (auth flows) register users into
    # the shared DB, so the unfiltered first row isn't necessarily 'dora'.
    _User = requests.get(f'{base_route}?filter=username:eq:dora').json()['items'][0]

    assert _User['email'] == 'ben.talese@gmail.com'
    assert _User['send_deals_on_day'] == 6
    assert _User['username'] == 'dora'
    assert _User['is_admin'] is True
    assert is_valid_uuid(_User['user_id'])
    assert _User.keys() == {
        'email',
        'send_deals_on_day',
        'username',
        'user_id',
        'is_admin',
        'deals_email_enabled',
        # Settings rebuild Phase 4 — bulk-stamped via _stamp_has_image.
        'has_image',
    }


def test__get_users__GettingAllUsers__GetsAllUsers(api):
    _Response = requests.get(f'{base_route}?limit=500')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    _Body = _Response.json()
    # Other suites (auth flows) register users into the shared DB, so assert
    # the envelope is well-formed and the seeded user is present, not an exact
    # count.
    assert _Body['total'] == len(_Body['items'])
    assert any(u['username'] == 'dora' for u in _Body['items'])


def test__get_users__FilteringByName__GetsSingleMatchingUser(api):
    _Response = requests.get(f'{base_route}?filter=username:ct:dor')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['username'] == 'dora'
    assert len(_Response.json()['items']) == 1


def test__get_users__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=poopus_goopus:ct:guy')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Field 'poopus_goopus' is not filterable on 'User'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_users__FilteringForUserThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}?filter=user_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'] == []
    assert _Response.json()['total'] == 0


def test__get_users__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=user_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Unsupported filter operator 'xx'. Supported: ct, eq, ge, gt, le, lt, ne.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_users__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?sort=dingo:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Field 'dingo' is not filterable on 'User'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_users__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "'page' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_users__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "'limit' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_users__PageWithoutLimit__DefaultsLimit(api):
    # page/limit are now independently optional (limit defaults to 50).
    _Response = requests.get(f'{base_route}?page=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 50
    assert len(_Response.json()['items']) >= 1


def test__get_users__LimitWithoutPage__DefaultsPage(api):
    _Response = requests.get(f'{base_route}?limit=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 1
    assert len(_Response.json()['items']) == 1


def test__get_users__FilteringSortingAndPagingUsers__GetsMatchingUsers(api):
    _Response = requests.get(f'{base_route}?filter=username:ct:dor&sort=username:asc&page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['username'] == 'dora'
    assert len(_Response.json()['items']) == 1


#endregion get_users tests
