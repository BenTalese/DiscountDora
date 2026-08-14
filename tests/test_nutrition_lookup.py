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
    # UI can distinguish "no such food" from "one source is down".
    assert result["sources_failed"] == [
        {"source": NUTRITION_SOURCE_OFF, "error": "couldn't reach the service"},
    ]


def test__search__EveryResultCarriesItsSourceLabel(monkeypatch):
    monkeypatch.setattr(lookup_module, "_off_by_text", lambda text: [
        FoodResult(source=NUTRITION_SOURCE_OFF, source_ref="1", name="Banana chips",
                   kcal_per_100g=519.0),
    ])
    result = search_foods(_NoLocalRepo(), _Setting(), "banana")

    assert all(r["source_label"] for r in result["results"])

#endregion
