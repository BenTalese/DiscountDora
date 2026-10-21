"""FU-034 — e2e for the substitute notes + structured ratio wire-up.

Covers:
  - POST `/substitutes` accepts notes + ratio; both surface on the detail
    DTO.
  - PATCH `/substitutes/<id>` replaces metadata; idempotent.
  - The ratio is **direction-aware**: viewing the same pair from the
    other stock item shows the ratio inverted (so `qty_in/unit_in`
    always describes "this" item).
  - Validation: half-filled ratio, non-positive quantity, unknown unit
    all → 400 business-rule-violation.
"""
from uuid import uuid4

import requests

BASE = 'http://localhost:5170/api'


def _create_stock_item(stock_level_id: str, name: str) -> str:
    r = requests.post(f'{BASE}/stock-items', json={
        'name': name,
        'stock_level_id': stock_level_id,
    })
    assert r.status_code == 201, r.text
    return r.json()['stock_item_id']


def _detail(stock_item_id: str) -> dict:
    r = requests.get(f'{BASE}/stock-items/{stock_item_id}/detail')
    assert r.status_code == 200, r.text
    return r.json()


def _find_substitute(detail: dict, substitute_id: str) -> dict | None:
    return next(
        (s for s in detail['substitutes'] if s['stock_item_id'] == substitute_id),
        None,
    )


def _stock_level_id() -> str:
    return requests.get(f'{BASE}/stock-levels').json()['items'][0]['stock_level_id']


def test__add_substitute__notes_only__round_trips_through_detail(api):
    sl = _stock_level_id()
    a = _create_stock_item(sl, f'olive-{uuid4().hex[:6]}')
    b = _create_stock_item(sl, f'butter-{uuid4().hex[:6]}')
    try:
        r = requests.post(f'{BASE}/stock-items/{a}/substitutes', json={
            'substitute_id': b,
            'notes': '1:1 in savoury cooking, not in baking',
        })
        assert r.status_code == 204, r.text

        sub = _find_substitute(_detail(a), b)
        assert sub is not None
        assert sub['notes'] == '1:1 in savoury cooking, not in baking'
        assert sub['ratio_quantity_in'] is None
        assert sub['ratio_unit_in'] is None
        assert sub['ratio_quantity_out'] is None
        assert sub['ratio_unit_out'] is None
    finally:
        requests.delete(f'{BASE}/stock-items/{a}')
        requests.delete(f'{BASE}/stock-items/{b}')


def test__add_substitute__with_ratio__surfaces_and_inverts_for_the_other_side(api):
    sl = _stock_level_id()
    a = _create_stock_item(sl, f'olive-{uuid4().hex[:6]}')
    b = _create_stock_item(sl, f'butter-{uuid4().hex[:6]}')
    try:
        # Sent from A's perspective: 1 tsp olive → 2 tbsp butter.
        r = requests.post(f'{BASE}/stock-items/{a}/substitutes', json={
            'substitute_id': b,
            'notes': 'use 2 tbsp butter per 1 tsp oil',
            'ratio_quantity_in': 1,
            'ratio_unit_in': 'tsp',
            'ratio_quantity_out': 2,
            'ratio_unit_out': 'tbsp',
        })
        assert r.status_code == 204, r.text

        # From A: in = 1 tsp, out = 2 tbsp.
        sub_from_a = _find_substitute(_detail(a), b)
        assert sub_from_a is not None
        assert sub_from_a['ratio_quantity_in'] == 1
        assert sub_from_a['ratio_unit_in'] == 'tsp'
        assert sub_from_a['ratio_quantity_out'] == 2
        assert sub_from_a['ratio_unit_out'] == 'tbsp'

        # From B (other side): in/out flipped.
        sub_from_b = _find_substitute(_detail(b), a)
        assert sub_from_b is not None
        assert sub_from_b['ratio_quantity_in'] == 2
        assert sub_from_b['ratio_unit_in'] == 'tbsp'
        assert sub_from_b['ratio_quantity_out'] == 1
        assert sub_from_b['ratio_unit_out'] == 'tsp'
        # Note isn't directional — same string on both sides.
        assert sub_from_b['notes'] == 'use 2 tbsp butter per 1 tsp oil'
    finally:
        requests.delete(f'{BASE}/stock-items/{a}')
        requests.delete(f'{BASE}/stock-items/{b}')


def test__update_substitute__replaces_metadata_and_clears_when_empty(api):
    sl = _stock_level_id()
    a = _create_stock_item(sl, f'olive-{uuid4().hex[:6]}')
    b = _create_stock_item(sl, f'butter-{uuid4().hex[:6]}')
    try:
        requests.post(f'{BASE}/stock-items/{a}/substitutes', json={
            'substitute_id': b,
            'notes': 'original note',
            'ratio_quantity_in': 1, 'ratio_unit_in': 'tsp',
            'ratio_quantity_out': 1, 'ratio_unit_out': 'tsp',
        })

        # Replace notes + ratio.
        r = requests.patch(f'{BASE}/stock-items/{a}/substitutes/{b}', json={
            'notes': 'updated note',
            'ratio_quantity_in': 3, 'ratio_unit_in': 'cup',
            'ratio_quantity_out': 4, 'ratio_unit_out': 'cup',
        })
        assert r.status_code == 204, r.text
        sub = _find_substitute(_detail(a), b)
        assert sub['notes'] == 'updated note'
        assert sub['ratio_quantity_in'] == 3
        assert sub['ratio_unit_in'] == 'cup'
        assert sub['ratio_quantity_out'] == 4

        # Clear everything by sending an empty body.
        r = requests.patch(f'{BASE}/stock-items/{a}/substitutes/{b}', json={})
        assert r.status_code == 204, r.text
        sub = _find_substitute(_detail(a), b)
        assert sub['notes'] is None
        assert sub['ratio_quantity_in'] is None
        assert sub['ratio_unit_in'] is None
        assert sub['ratio_quantity_out'] is None
        assert sub['ratio_unit_out'] is None
    finally:
        requests.delete(f'{BASE}/stock-items/{a}')
        requests.delete(f'{BASE}/stock-items/{b}')


def test__add_substitute__half_filled_ratio__rejected(api):
    sl = _stock_level_id()
    a = _create_stock_item(sl, f'olive-{uuid4().hex[:6]}')
    b = _create_stock_item(sl, f'butter-{uuid4().hex[:6]}')
    try:
        r = requests.post(f'{BASE}/stock-items/{a}/substitutes', json={
            'substitute_id': b,
            'ratio_quantity_in': 1,
            'ratio_unit_in': 'tsp',
            # ratio_quantity_out + ratio_unit_out missing
        })
        assert r.status_code == 422, r.text
        assert 'incomplete' in r.text.lower() or 'ratio' in r.text.lower()
    finally:
        requests.delete(f'{BASE}/stock-items/{a}')
        requests.delete(f'{BASE}/stock-items/{b}')


def test__add_substitute__non_positive_quantity__rejected(api):
    sl = _stock_level_id()
    a = _create_stock_item(sl, f'olive-{uuid4().hex[:6]}')
    b = _create_stock_item(sl, f'butter-{uuid4().hex[:6]}')
    try:
        r = requests.post(f'{BASE}/stock-items/{a}/substitutes', json={
            'substitute_id': b,
            'ratio_quantity_in': 0,
            'ratio_unit_in': 'tsp',
            'ratio_quantity_out': 1,
            'ratio_unit_out': 'tsp',
        })
        assert r.status_code == 422, r.text
        assert 'greater than zero' in r.text.lower() or 'positive' in r.text.lower()
    finally:
        requests.delete(f'{BASE}/stock-items/{a}')
        requests.delete(f'{BASE}/stock-items/{b}')


def test__add_substitute__unknown_unit__rejected(api):
    sl = _stock_level_id()
    a = _create_stock_item(sl, f'olive-{uuid4().hex[:6]}')
    b = _create_stock_item(sl, f'butter-{uuid4().hex[:6]}')
    try:
        r = requests.post(f'{BASE}/stock-items/{a}/substitutes', json={
            'substitute_id': b,
            'ratio_quantity_in': 1,
            'ratio_unit_in': 'galactic-cubit',
            'ratio_quantity_out': 1,
            'ratio_unit_out': 'tsp',
        })
        assert r.status_code == 422, r.text
        assert 'unknown unit' in r.text.lower()
    finally:
        requests.delete(f'{BASE}/stock-items/{a}')
        requests.delete(f'{BASE}/stock-items/{b}')
