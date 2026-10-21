"""Unified nutrition lookup — ranking, barcode detection, and source honesty.

The network sources are stubbed; what's pinned here is the logic that decides
*what the user sees and in what order*, plus the promise that a source which
failed is reported rather than silently reducing the result list (a search that
quietly drops OFF looks identical to "no such food", which would send someone
off to type numbers by hand).
"""
import pytest

from dora_api.domain.entities.nutrition_food import (
    NUTRITION_SOURCE_OFF,
    NUTRITION_SOURCE_USDA_API,
    NUTRITION_SOURCE_USDA_SR_LEGACY,
)
from dora_api.features.nutrition import lookup as lookup_module
from dora_api.features.nutrition.lookup import (
    FoodResult, _rank, looks_like_barcode, search_foods,
)


class _Setting:
    def __init__(self, off=True, usda_key=""):
        self.nutrition_off_lookup_enabled = off
        self.nutrition_usda_api_key = usda_key


class _NoLocalRepo:
    """Repository stand-in for the source-fan-out cases — local always empty,
    so the assertions are about which live sources were asked."""
    def get(self, _entity):
        return self

    def where(self, _condition):
        return self

    def all(self):
        return []


#region barcode detection

@pytest.mark.parametrize("value", ["12345678", "012345678905", "9300675024235", "01234567890123"])
def test__looks_like_barcode__RealEanLengths__True(value):
    assert looks_like_barcode(value) is True


@pytest.mark.parametrize(
    "value",
    ["500", "banana", "1234567", "930067502423512", "12 34"],
)
def test__looks_like_barcode__EverythingElse__False(value):
    # "500" is someone searching for a 500g thing, not a barcode; 7 and 15
    # digits are either side of the real EAN/UPC/ITF-14 lengths.
    assert looks_like_barcode(value) is False

#endregion

#region ranking

def _result(**kwargs) -> FoodResult:
    base = dict(source=NUTRITION_SOURCE_USDA_SR_LEGACY, source_ref="1", name="thing",
                kcal_per_100g=10.0)
    base.update(kwargs)
    return FoodResult(**base)


def test__rank__BarcodeMatch__OutranksEveryNameMatch():
    ranked = _rank([
        _result(name="banana bread", id="a"),
        _result(name="banana", id="b"),
        _result(name="Barcoded thing", match="barcode", source=NUTRITION_SOURCE_OFF),
    ], "banana")

    assert ranked[0].match == "barcode"


def test__rank__AlreadyLocal__OutranksLiveSuggestion():
    ranked = _rank([
        _result(name="Banana", source=NUTRITION_SOURCE_USDA_API),          # live, id=None
        _result(name="Banana", id="local-1"),                              # local
    ], "banana")

    assert ranked[0].id == "local-1"


def test__rank__PrefixMatch__OutranksMidStringMatch():
    ranked = _rank([
        _result(name="Bread with banana", id="a"),
        _result(name="Banana, raw", id="b"),
    ], "banana")

    assert ranked[0].name == "Banana, raw"


def test__rank__FoodWithNoEnergy__SinksBelowOneThatHasIt():
    ranked = _rank([
        _result(name="Banana a", id="a", kcal_per_100g=None),
        _result(name="Banana b", id="b", kcal_per_100g=89.0),
    ], "banana")

    assert ranked[0].kcal_per_100g == 89.0


def test__rank__EqualOtherwise__ShorterNameFirst():
    # The shortest name is usually the unqualified generic ("Banana, raw"
    # rather than "Bananas, dehydrated, or banana powder").
    ranked = _rank([
        _result(name="Bananas, dehydrated, or banana powder", id="a"),
        _result(name="Bananas, raw", id="b"),
    ], "banana")

    assert ranked[0].name == "Bananas, raw"

#endregion

#region source fan-out

def test__search__ShortQuery__AsksNothing():
    result = search_foods(_NoLocalRepo(), _Setting(), "b")

    assert result["results"] == []
    assert result["sources_queried"] == []


def test__search__BarcodeQuery__AsksOffAndFlagsIt(monkeypatch):
    called = {}

    def fake_barcode(ean):
        called["ean"] = ean
        return FoodResult(
            source=NUTRITION_SOURCE_OFF, source_ref=ean, name="Beans",
            barcode=ean, kcal_per_100g=80.0, match="barcode", exact=True,
        )

    monkeypatch.setattr(lookup_module, "_off_by_barcode", fake_barcode)
    result = search_foods(_NoLocalRepo(), _Setting(), "9300675024235")

    assert result["is_barcode"] is True
    assert called["ean"] == "9300675024235"
    assert NUTRITION_SOURCE_OFF in result["sources_queried"]
    assert result["results"][0]["match"] == "barcode"
    assert result["results"][0]["source_label"] == "Open Food Facts"


def test__search__OffDisabled__IsNotAsked(monkeypatch):
    monkeypatch.setattr(
        lookup_module, "_off_by_barcode",
        lambda ean: pytest.fail("OFF must not be called when it's switched off"),
    )
    result = search_foods(_NoLocalRepo(), _Setting(off=False), "9300675024235")

    assert NUTRITION_SOURCE_OFF not in result["sources_queried"]
    assert result["results"] == []


def test__search__NoUsdaKey__ApiSourceIsNotAsked(monkeypatch):
    monkeypatch.setattr(lookup_module, "_off_by_text", lambda text: [])
    monkeypatch.setattr(
        lookup_module, "_usda_api_search",
        lambda text, key: pytest.fail("USDA API must not be called without a key"),
    )
    result = search_foods(_NoLocalRepo(), _Setting(usda_key=""), "banana")

    assert NUTRITION_SOURCE_USDA_API not in result["sources_queried"]


def test__search__UsdaKeySet__ApiIsAsked(monkeypatch):
    monkeypatch.setattr(lookup_module, "_off_by_text", lambda text: [])
    monkeypatch.setattr(lookup_module, "_usda_api_search", lambda text, key: [
        FoodResult(source=NUTRITION_SOURCE_USDA_API, source_ref="9", name="Banana, raw",
                   kcal_per_100g=89.0),
    ])
    result = search_foods(_NoLocalRepo(), _Setting(usda_key="abc123"), "banana")

    assert NUTRITION_SOURCE_USDA_API in result["sources_queried"]
    assert result["results"][0]["source_label"] == "USDA (live)"


def test__search__LiveSourceFails__IsReportedNotSwallowed(monkeypatch):
    def boom(text):
        raise RuntimeError("couldn't reach the service")

    monkeypatch.setattr(lookup_module, "_off_by_text", boom)
    result = search_foods(_NoLocalRepo(), _Setting(), "banana")

    # The whole search still succeeds — but it says OFF didn't answer, so the
    # UI can distinguish "no such food" from "one source is down". The human
    # label travels with it: the picker was rendering the raw id
    # ("Couldn't reach off").
    assert result["sources_failed"] == [
        {
            "source": NUTRITION_SOURCE_OFF,
            "source_label": "Open Food Facts",
            "error": "couldn't reach the service",
        },
    ]


def test__search__EveryResultCarriesItsSourceLabel(monkeypatch):
    monkeypatch.setattr(lookup_module, "_off_by_text", lambda text: [
        FoodResult(source=NUTRITION_SOURCE_OFF, source_ref="1", name="Banana chips",
                   kcal_per_100g=519.0),
    ])
    result = search_foods(_NoLocalRepo(), _Setting(), "banana")

    assert all(r["source_label"] for r in result["results"])

#endregion


#region transient-failure retry


def test__is_transient__ServiceUnavailable__IsWorthRetrying():
    # Open Food Facts' search endpoint flaps between 200 and 503 within
    # seconds; a single retry turns most of that into a normal result instead
    # of an empty picker.
    from dora_api.features.nutrition.lookup import _is_transient

    assert _is_transient("couldn't reach the service (HTTP Error 503: ...)") is True
    assert _is_transient("couldn't reach the service (HTTP Error 429: ...)") is True
    assert _is_transient("timed out") is True


def test__is_transient__NotFoundOrBadPayload__IsNotRetried():
    from dora_api.features.nutrition.lookup import _is_transient

    assert _is_transient("couldn't reach the service (HTTP Error 404: ...)") is False
    assert _is_transient("unexpected response shape") is False


def test__fetch_json__RetriesOnceThenSucceeds(monkeypatch):
    from dora_api.features.nutrition import lookup as lookup_module

    calls = {"n": 0}

    def flaky(_url, _purpose):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("couldn't reach the service (HTTP Error 503: nope)")
        return {"ok": True}

    monkeypatch.setattr(lookup_module, "_fetch_json_once", flaky)
    monkeypatch.setattr(lookup_module, "_RETRY_DELAY_SECONDS", 0)

    assert lookup_module._fetch_json("http://x", "test") == {"ok": True}
    assert calls["n"] == 2


def test__fetch_json__GivesUpAfterOneRetry(monkeypatch):
    from dora_api.features.nutrition import lookup as lookup_module

    calls = {"n": 0}

    def always_down(_url, _purpose):
        calls["n"] += 1
        raise RuntimeError("couldn't reach the service (HTTP Error 503: nope)")

    monkeypatch.setattr(lookup_module, "_fetch_json_once", always_down)
    monkeypatch.setattr(lookup_module, "_RETRY_DELAY_SECONDS", 0)

    with pytest.raises(RuntimeError):
        lookup_module._fetch_json("http://x", "test")
    # Two attempts, not an unbounded stall in front of a type-ahead.
    assert calls["n"] == 2


#endregion


#region nutrient extraction

def test__off_result__NutrientKeys__AreReadFromTheSharedMapping():
    result = lookup_module._off_result({
        "code": "9300675024235",
        "product_name": "Greek yoghurt",
        "brands": "Someone",
        "nutriments": {
            "energy-kcal_100g": 97,
            "proteins_100g": 9.0,
            "carbohydrates_100g": 3.6,
            "sugars_100g": 3.6,
            "fat_100g": 5.0,
            "saturated-fat_100g": 3.3,
            "fiber_100g": 0.0,
            "sodium_100g": 0.036,
        },
    })

    assert result is not None
    assert result.kcal_per_100g == pytest.approx(97)
    assert result.sugars_g_per_100g == pytest.approx(3.6)
    assert result.saturated_fat_g_per_100g == pytest.approx(3.3)
    # A stated zero is a fact ("this has no fibre") and survives; only an
    # absent key becomes None.
    assert result.fibre_g_per_100g == pytest.approx(0.0)


def test__off_result__Sodium__IsConvertedFromGramsToMilligrams():
    result = lookup_module._off_result({
        "code": "1",
        "product_name": "Salty thing",
        # OFF states sodium in GRAMS per 100g; we store milligrams, the unit
        # packs use. Getting this wrong is a silent 1000x error on a number
        # people actually watch.
        "nutriments": {"energy-kcal_100g": 10, "sodium_100g": 0.4},
    })

    assert result is not None
    assert result.sodium_mg_per_100g == pytest.approx(400.0)


def test__off_result__MissingNutrients__StayNoneRatherThanZero():
    result = lookup_module._off_result({
        "code": "1",
        "product_name": "Sparse entry",
        "nutriments": {"energy-kcal_100g": 10},
    })

    assert result is not None
    assert result.protein_g_per_100g is None
    assert result.sodium_mg_per_100g is None


def test__usda_api_foods__MatchOnNameAndUnit__NotOnNameAlone():
    results = lookup_module._parse_usda_foods({"foods": [{
        "fdcId": 1,
        "description": "Bananas, raw",
        "foodNutrients": [
            {"nutrientName": "Energy", "unitName": "KCAL", "value": 89},
            # Same nutrient name, different unit — must not overwrite kcal.
            {"nutrientName": "Energy", "unitName": "kJ", "value": 371},
            {"nutrientName": "Sodium, Na", "unitName": "MG", "value": 1},
            {"nutrientName": "Fiber, total dietary", "unitName": "G", "value": 2.6},
            {"nutrientName": "Ash", "unitName": "G", "value": 0.82},
        ],
    }]})

    assert len(results) == 1
    assert results[0].kcal_per_100g == pytest.approx(89)
    assert results[0].sodium_mg_per_100g == pytest.approx(1)
    assert results[0].fibre_g_per_100g == pytest.approx(2.6)


#endregion
