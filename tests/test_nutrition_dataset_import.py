"""Parser coverage for the USDA FoodData Central bulk import.

`parse_fdc_csv_zip` is a pure bytes-in/entities-out function, so it's pinned
here against a synthetic archive rather than a 32MB download. The cases that
matter are the ones that would silently corrupt a rollup: picking kcal (not
kJ) off the duplicated "Energy" nutrient, surviving the BOM and the nested
release-dated directory FDC actually ships, and dropping foods with no energy
value instead of storing rows that look usable and aren't.
"""
import io
import zipfile

import pytest

from dora_api.domain.entities.nutrition_food import NUTRITION_SOURCE_USDA_SR_LEGACY
from dora_api.features.nutrition.dataset_import import parse_fdc_csv_zip


_SOURCE = NUTRITION_SOURCE_USDA_SR_LEGACY
# FDC nests its CSVs one directory deep and the directory carries the release
# date — the parser must match on basename or it finds nothing.
_DIR = "FoodData_Central_sr_legacy_food_csv_2018-04"


def _archive(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            # utf-8-sig writes the BOM FDC ships; the parser has to strip it or
            # the first column name comes back mangled.
            archive.writestr(f"{_DIR}/{name}", content.encode("utf-8-sig"))
    return buffer.getvalue()


_NUTRIENT_CSV = (
    "id,name,unit_name\n"
    "1008,Energy,KCAL\n"
    "1062,Energy,kJ\n"
    "1003,Protein,G\n"
    "1004,\"Total lipid (fat)\",G\n"
    "1005,\"Carbohydrate, by difference\",G\n"
    "2000,\"Total Sugars\",G\n"
    "1258,\"Fatty acids, total saturated\",G\n"
    "1079,\"Fiber, total dietary\",G\n"
    "1093,\"Sodium, Na\",MG\n"
    "1007,Ash,G\n"
)

_FOOD_CSV = (
    "fdc_id,data_type,description\n"
    "111,sr_legacy_food,\"Bananas, raw\"\n"
    "222,sr_legacy_food,\"Flour, wheat, all-purpose\"\n"
    "333,sr_legacy_food,\"Water, bottled\"\n"
)

_FOOD_NUTRIENT_CSV = (
    "id,fdc_id,nutrient_id,amount\n"
    "1,111,1008,89.0\n"      # banana kcal
    "2,111,1062,371.0\n"     # banana kJ — must NOT win over kcal
    "3,111,1003,1.09\n"
    "4,111,1004,0.33\n"
    "5,111,1005,22.84\n"
    "6,111,1079,2.6\n"       # fibre
    "7,222,1008,364.0\n"     # flour kcal
    "8,333,1003,0.0\n"       # water has protein but no energy
    "9,111,2000,12.23\n"     # sugars
    "10,111,1258,0.112\n"    # saturated fat
    "11,111,1093,1.0\n"      # sodium, in mg
    "12,111,1007,0.82\n"     # ash — real USDA nutrient we deliberately skip
)

_MEASURE_UNIT_CSV = (
    "id,name\n"
    "1000,cup\n"
    "1001,tbsp\n"
    "9999,undetermined\n"
)

_FOOD_PORTION_CSV = (
    "id,fdc_id,amount,measure_unit_id,portion_description,modifier,gram_weight\n"
    "1,111,1,9999,,medium,118.0\n"          # unit undetermined → modifier wins
    "2,222,1,1000,,,125.0\n"                # cup
    "3,222,1,1001,,,7.8\n"                  # tbsp
    "4,222,1,1000,,,\n"                     # no gram weight → dropped
    "5,333,1,1000,,,240.0\n"                # belongs to a dropped food
)


def _parse(**overrides):
    files = {
        "food.csv": _FOOD_CSV,
        "nutrient.csv": _NUTRIENT_CSV,
        "food_nutrient.csv": _FOOD_NUTRIENT_CSV,
        "measure_unit.csv": _MEASURE_UNIT_CSV,
        "food_portion.csv": _FOOD_PORTION_CSV,
    }
    files.update(overrides)
    return parse_fdc_csv_zip(_archive(files), _SOURCE)


def test__parse__NestedDatedDirectoryAndBom__FindsTheCsvs():
    foods, _ = _parse()

    assert {f.name for f in foods} == {"Bananas, raw", "Flour, wheat, all-purpose"}
    assert all(f.source == _SOURCE for f in foods)
    assert all(f.source_ref in {"111", "222"} for f in foods)


def test__parse__DuplicatedEnergyNutrient__TakesKcalNotKilojoules():
    foods, _ = _parse()
    banana = next(f for f in foods if f.source_ref == "111")

    # 371 kJ is the same energy expressed differently; storing it as "kcal"
    # would inflate every recipe rollup by ~4.2x.
    assert banana.kcal_per_100g == pytest.approx(89.0)


def test__parse__TrackedMacros__AreMappedAndUntrackedOnesIgnored():
    foods, _ = _parse()
    banana = next(f for f in foods if f.source_ref == "111")

    assert banana.protein_g_per_100g == pytest.approx(1.09)
    assert banana.fat_g_per_100g == pytest.approx(0.33)
    assert banana.carbs_g_per_100g == pytest.approx(22.84)
    # 2026-08-16 — the four added on the owner's "is that the only nutrition
    # data we can pull?" The USDA row names differ between Foundation and SR
    # Legacy for sugars, which is why the mapping carries aliases.
    assert banana.sugars_g_per_100g == pytest.approx(12.23)
    assert banana.saturated_fat_g_per_100g == pytest.approx(0.112)
    assert banana.fibre_g_per_100g == pytest.approx(2.6)
    assert banana.sodium_mg_per_100g == pytest.approx(1.0)
    # Ash is a real USDA nutrient we deliberately don't store — the mapping is
    # an allow-list, not "everything in the file".
    assert not hasattr(banana, "ash_g_per_100g")


def test__parse__MacroWithNoValueInSource__StaysNoneRatherThanZero():
    foods, _ = _parse()
    flour = next(f for f in foods if f.source_ref == "222")

    # The source didn't state flour's protein. None means "unknown"; a 0 would
    # be a fabricated fact that silently drags a recipe's macros down.
    assert flour.protein_g_per_100g is None


def test__parse__FoodWithNoEnergyValue__IsDropped():
    foods, portions = _parse()

    assert all(f.source_ref != "333" for f in foods)
    # ...and its portions go with it rather than dangling.
    assert all(p.gram_weight != 240.0 for p in portions)


def test__parse__Portions__ResolveMeasureNamesAndSkipWeightlessRows():
    foods, portions = _parse()
    flour = next(f for f in foods if f.source_ref == "222")
    flour_portions = [p for p in portions if p.fdc_id == flour.source_ref]

    assert {(p.measure, p.gram_weight) for p in flour_portions} == {
        ("cup", 125.0), ("tbsp", 7.8),
    }


def test__parse__UndeterminedMeasureUnit__FallsBackToTheModifier():
    foods, portions = _parse()
    banana = next(f for f in foods if f.source_ref == "111")

    banana_portions = [p for p in portions if p.fdc_id == banana.source_ref]
    assert [(p.measure, p.gram_weight) for p in banana_portions] == [("medium", 118.0)]


def test__parse__ArchiveMissingRequiredCsvs__RaisesSomethingActionable():
    payload = _archive({"food.csv": _FOOD_CSV})

    with pytest.raises(ValueError, match="FoodData Central CSV bundle"):
        parse_fdc_csv_zip(payload, _SOURCE)


def test__parse__NoPortionFile__StillImportsFoods():
    files = {
        "food.csv": _FOOD_CSV,
        "nutrient.csv": _NUTRIENT_CSV,
        "food_nutrient.csv": _FOOD_NUTRIENT_CSV,
    }
    foods, portions = parse_fdc_csv_zip(_archive(files), _SOURCE)

    assert len(foods) == 2
    assert portions == []


#region error messages (what an admin actually reads under a dead button)


def test__friendly_error__Forbidden__NamesTheHostThatBlocksDownloads():
    # The shipped default URL pointed at www.usda.gov, which is Akamai-fronted
    # and answers 403 to any programmatic client — the download button's
    # original failure. Only 404 had a friendly message, so admins saw a raw
    # urllib string that told them nothing.
    from dora_api.features.nutrition.dataset_import import _friendly_error

    message = _friendly_error("HTTP Error 403: Forbidden")
    assert "fdc.nal.usda.gov" in message


def test__friendly_error__NotFound__PointsAtTheDownloadsPage():
    from dora_api.features.nutrition.dataset_import import _friendly_error

    assert "superseded" in _friendly_error("HTTP Error 404: Not Found")


def test__default_urls__PointAtTheOriginNotTheAkamaiMirror():
    from dora_api.features.nutrition.dataset_import import default_url

    for source in ("usda_foundation", "usda_sr_legacy"):
        assert default_url(source).startswith("https://fdc.nal.usda.gov/"), source


#endregion
