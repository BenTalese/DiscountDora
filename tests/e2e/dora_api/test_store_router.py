import uuid

import requests

from tests.support import is_valid_uuid

#region ---------------- setup ----------------

# FU-166: list endpoints take query options on the query string and return a
# `{items, total, page, limit}` envelope; query-option errors come back via
# `bad_request(str(exc))` (message in `title`). Seed provisions 4 stores
# (Woolworths, Coles, Aldi, IGA). FU-189: the entity was renamed
# `Merchant → Store`; the SPA-facing route is now `/api/stores`. The scraping
# surface was removed (companion app); stores remain first-class entities, so
# these list tests stay — they were just on the stale `/merchants` contract.

base_route = 'http://localhost:5170/api/stores'

#endregion setup

#region ---------------- get_stores tests ----------------


def test__get_stores__GettingStore__GetsAllExpectedAttributes(api):
    _Store = requests.get(f'{base_route}?filter=name:eq:Woolworths').json()['items'][0]

    assert is_valid_uuid(_Store['store_id'])
    assert _Store['name'] == 'Woolworths'
    assert _Store.keys() == {
        'store_id',
        'name',
        'has_image',
    }


def test__get_stores__GettingAllStores__GetsAllStores(api):
    # NB: the session DB may carry extra stores from earlier tests in the
    # same run that exercise the create-product reuse path (product_router
    # auto-creates a store from `store_name` when it's not already present).
    # Assert the 4 seeded stores are all present rather than equality on the
    # row count — that's the intent of the test, and it's resilient to other
    # tests in the suite adding rows.
    _Response = requests.get(base_route)

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    _Names = {s['name'] for s in _Response.json()['items']}
    assert {'Aldi', 'Coles', 'IGA', 'Woolworths'}.issubset(_Names)
    assert _Response.json()['total'] >= 4


def test__get_stores__FilteringByName__GetsSingleMatchingStore(api):
    _Response = requests.get(f'{base_route}?filter=name:eq:woolworths')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Woolworths'
    assert len(_Response.json()['items']) == 1


def test__get_stores__FilteringOnNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=thing:eq:woolworths')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Field 'thing' is not filterable on 'Store'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stores__FilteringForStoreThatDoesNotExist__EmptyResult(api):
    _Response = requests.get(f'{base_route}?filter=store_id:eq:{uuid.uuid4()}')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'] == []
    assert _Response.json()['total'] == 0


def test__get_stores__FilteringWithUnsupportedOperator__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?filter=store_id:xx:{uuid.uuid4()}')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'errors': {},
        'status': 400,
        'title': "Unsupported filter operator 'xx'. Supported: ct, eq, ge, gt, le, lt, ne.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stores__SortingByNonExistentAttribute__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?sort=thing:desc')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'status': 400,
        'errors': {},
        'title': "Field 'thing' is not filterable on 'Store'.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stores__SortingByNameAscending__StoresSortedByNameAscending(api):
    _Items = requests.get(f'{base_route}?sort=name:asc').json()['items']

    assert _Items[0]['name'] == 'Aldi'
    assert _Items[1]['name'] == 'Coles'


def test__get_stores__SortingByNameDescending__StoresSortedByNameDescending(api):
    # Filter to the seeded names — other tests in the session may have
    # added stores whose names sort above 'Woolworths' (e.g. a uuid-suffixed
    # store created by the product-router reuse path).
    _Items = [
        s for s in requests.get(f'{base_route}?sort=name:desc').json()['items']
        if s['name'] in {'Aldi', 'Coles', 'IGA', 'Woolworths'}
    ]

    assert _Items[0]['name'] == 'Woolworths'
    assert _Items[1]['name'] == 'IGA'


def test__get_stores__GettingOneStorePerPage__GetsPageOfOneStore(api):
    _Response = requests.get(f'{base_route}?sort=name:asc&page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Aldi'
    assert len(_Response.json()['items']) == 1


def test__get_stores__GettingSecondPage__GetsSecondPageOfStores(api):
    _Response = requests.get(f'{base_route}?sort=name:asc&page=2&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Coles'
    assert len(_Response.json()['items']) == 1


def test__get_stores__PageValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=true&limit=2')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'status': 400,
        'errors': {},
        'title': "'page' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stores__LimitValueIsNotInteger__IsBadRequest(api):
    _Response = requests.get(f'{base_route}?page=1&limit=true')

    assert _Response.status_code == 400
    assert _Response.headers['Content-Type'] == 'application/problem+json'
    assert _Response.json() == {
        'detail': 'See errors property for more details.',
        'status': 400,
        'errors': {},
        'title': "'limit' must be an integer.",
        'type': 'https://datatracker.ietf.org/doc/html/rfc7231#section-6.5.1',
    }


def test__get_stores__PageWithoutLimit__DefaultsLimit(api):
    # FU-166: page/limit are now independently optional (limit defaults to 50).
    _Response = requests.get(f'{base_route}?page=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 50
    # See `test__get_stores__GettingAllStores__GetsAllStores` for why we
    # assert on the seeded subset rather than the row count.
    _Names = {s['name'] for s in _Response.json()['items']}
    assert {'Aldi', 'Coles', 'IGA', 'Woolworths'}.issubset(_Names)


def test__get_stores__LimitWithoutPage__DefaultsPage(api):
    _Response = requests.get(f'{base_route}?limit=1')

    assert _Response.status_code == 200
    assert _Response.json()['page'] == 1
    assert _Response.json()['limit'] == 1
    assert len(_Response.json()['items']) == 1


def test__get_stores__FilteringSortingAndPagingStores__GetsMatchingStores(api):
    _Response = requests.get(f'{base_route}?filter=name:ct:wool&sort=name:asc&page=1&limit=1')

    assert _Response.status_code == 200
    assert _Response.headers['Content-Type'] == 'application/json'
    assert _Response.json()['items'][0]['name'] == 'Woolworths'
    assert len(_Response.json()['items']) == 1


#endregion get_stores tests
