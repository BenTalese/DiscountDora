"""FU-195 — unit tests for SeedHandler's per-name filter behaviour.

The handler seeds the bundled default groups + locations into an empty
DB. C-5.5 shipped an all-or-none pair of bools; FU-195 added optional
`group_names` / `location_paths` filters so the onboarding wizard can
tick individual defaults.

These tests pin:
* Missing filter (None) → seed every default (backward-compat with the
  original all-or-none path).
* Explicit filter → seed only the intersection with the bundled defaults.
* Location "Zone/Child" paths auto-create their parent zone even when
  the parent path is not in the filter (the FK requires it).
* Skip semantics: rows that would collide with existing entities count as
  `skipped`; parents auto-created as a silent prerequisite for an accepted
  child do NOT count as skipped when the parent path wasn't requested.
"""
from types import SimpleNamespace
from uuid import UUID, uuid4

from dora_api.domain.entities.stock_group import StockGroup
from dora_api.domain.entities.stock_location import StockLocation
from dora_api.features.onboarding.onboarding import SeedHandler, SeedRequest


class _AllQuery:
    def __init__(self, rows):
        self._rows = rows

    def all(self, *_args, **_kwargs):
        return list(self._rows)


class _FakeRepo:
    """Enough of a SqlAlchemyRepository shim to drive the SeedHandler.

    `get(entity).all()` returns whatever's been added so far (existing +
    fresh) for that entity type, so the dedupe path against pre-existing
    rows and the parent-lookup during child creation both work.
    """

    def __init__(self, groups: list, locations: list):
        self._by_type: dict[type, list] = {
            StockGroup: list(groups),
            StockLocation: list(locations),
        }
        self.added: list = []

    def get(self, entity_type):
        return _AllQuery(self._by_type.get(entity_type, []))

    def add(self, entity):
        # Give the entity an id if it doesn't have one (the seed handler
        # reads parent ids during child creation, so parents need theirs
        # before children reference them).
        if getattr(entity, "id", None) is None:
            entity.id = uuid4()
        self.added.append(entity)
        # Route into the per-type list so subsequent `all()` calls include
        # it (parent zones are looked up this way when placing children).
        bucket = self._by_type.setdefault(type(entity), [])
        bucket.append(entity)

    def save_changes(self):
        # No-op — the tests inspect `self.added` directly.
        pass


def _run(request: SeedRequest, *, groups=None, locations=None) -> tuple[list, list, object]:
    """Drive the handler + return (added StockGroups, added StockLocations, result)."""
    repo = _FakeRepo(groups=groups or [], locations=locations or [])
    handler = SeedHandler.__new__(SeedHandler)
    handler.repository = repo
    result = handler.handle(request)
    added_groups = [e for e in repo.added if isinstance(e, StockGroup)]
    added_locations = [e for e in repo.added if isinstance(e, StockLocation)]
    return added_groups, added_locations, result


# ── groups filter ─────────────────────────────────────────────────────


def test__no_filter__seeds_every_default_group():
    added, _, result = _run(SeedRequest(groups=True))
    names = [g.name for g in added]
    # The bundled default set — pinning the count is enough; the exact
    # names are the JSON's job.
    assert result.groups_created == len(names)
    assert result.groups_skipped == 0
    assert len(names) >= 5  # sanity — the shipped set has 7 today


def test__empty_list_filter__seeds_no_groups():
    added, _, result = _run(SeedRequest(groups=True, group_names=[]))
    assert added == []
    assert result.groups_created == 0
    assert result.groups_skipped == 0


def test__list_filter__seeds_only_the_named_defaults():
    added, _, result = _run(SeedRequest(
        groups=True, group_names=["Pantry", "Fridge"],
    ))
    names = [g.name for g in added]
    assert set(names) == {"Pantry", "Fridge"}
    assert result.groups_created == 2


def test__filter_is_case_insensitive():
    added, _, _ = _run(SeedRequest(
        groups=True, group_names=["pantry", "FRIDGE"],
    ))
    assert {g.name for g in added} == {"Pantry", "Fridge"}


def test__filter_unknown_names_are_dropped_silently():
    added, _, result = _run(SeedRequest(
        groups=True, group_names=["Pantry", "Not-A-Default"],
    ))
    assert {g.name for g in added} == {"Pantry"}
    assert result.groups_created == 1


def test__existing_group_matching_filter_is_skipped_not_recreated():
    existing = SimpleNamespace(id=uuid4(), name="Pantry")
    added, _, result = _run(
        SeedRequest(groups=True, group_names=["Pantry", "Fridge"]),
        groups=[existing],
    )
    # Pantry pre-exists → skipped; Fridge is created.
    assert {g.name for g in added} == {"Fridge"}
    assert result.groups_created == 1
    assert result.groups_skipped == 1


def test__groups_bool_false_ignores_filter():
    added, _, result = _run(SeedRequest(
        groups=False, group_names=["Pantry"],
    ))
    assert added == []
    assert result.groups_created == 0


# ── location paths filter ─────────────────────────────────────────────


def _location_names(added):
    return [(l.name, l.parent_id) for l in added]


def test__no_filter__seeds_every_zone_and_child():
    _, added, result = _run(SeedRequest(locations=True))
    zones = [l for l in added if l.parent_id is None]
    children = [l for l in added if l.parent_id is not None]
    # Bundled default has zones (Kitchen/Bathroom/Laundry) + their
    # children.
    assert len(zones) >= 3
    assert len(children) >= 3
    assert result.locations_created == len(added)


def test__zone_only_path__creates_zone_without_children():
    _, added, result = _run(SeedRequest(
        locations=True, location_paths=["Bathroom"],
    ))
    names = [l.name for l in added]
    assert names == ["Bathroom"]
    assert result.locations_created == 1


def test__child_path__auto_creates_parent_zone():
    _, added, _ = _run(SeedRequest(
        locations=True, location_paths=["Kitchen/Fridge"],
    ))
    names = [l.name for l in added]
    # Kitchen must exist as a parent FK — server creates it silently.
    assert set(names) == {"Kitchen", "Fridge"}
    kitchen = next(l for l in added if l.name == "Kitchen")
    fridge = next(l for l in added if l.name == "Fridge")
    assert fridge.parent_id == kitchen.id


def test__parent_created_silently_is_not_counted_as_skipped():
    _, _, result = _run(SeedRequest(
        locations=True, location_paths=["Kitchen/Fridge"],
    ))
    # Two rows created (Kitchen + Fridge). Kitchen was NOT explicitly
    # asked for so it should not add to the skipped tally either — a
    # silent prerequisite for the requested child.
    assert result.locations_created == 2
    assert result.locations_skipped == 0


def test__zone_plus_selective_children__seeds_only_the_named_children():
    _, added, _ = _run(SeedRequest(
        locations=True,
        location_paths=["Kitchen", "Kitchen/Pantry", "Kitchen/Fridge"],
    ))
    names = [l.name for l in added]
    assert set(names) == {"Kitchen", "Pantry", "Fridge"}
    # Freezer was NOT in the filter even though it's under Kitchen.
    assert "Freezer" not in names


def test__existing_zone_lets_child_hang_off_it():
    existing_kitchen = SimpleNamespace(
        id=uuid4(), name="Kitchen", kind="zone", parent_id=None, sequence=0,
    )
    _, added, result = _run(
        SeedRequest(locations=True, location_paths=["Kitchen/Freezer"]),
        locations=[existing_kitchen],
    )
    names = [l.name for l in added]
    # Kitchen already existed → not re-added; the filter didn't ask for
    # Kitchen directly so it doesn't count as `skipped` either. Freezer
    # attaches to the existing Kitchen id.
    assert names == ["Freezer"]
    assert added[0].parent_id == existing_kitchen.id
    assert result.locations_created == 1
    assert result.locations_skipped == 0


def test__locations_bool_false_ignores_filter():
    _, added, result = _run(SeedRequest(
        locations=False, location_paths=["Kitchen/Fridge"],
    ))
    assert added == []
    assert result.locations_created == 0


def test__filter_is_case_insensitive_for_locations():
    _, added, _ = _run(SeedRequest(
        locations=True,
        location_paths=["kitchen/FRIDGE", "BATHROOM"],
    ))
    names = {l.name for l in added}
    assert names == {"Kitchen", "Fridge", "Bathroom"}


def test__unknown_paths_are_dropped_silently():
    _, added, _ = _run(SeedRequest(
        locations=True,
        location_paths=["Kitchen/Fridge", "Garage/Workbench"],
    ))
    assert {l.name for l in added} == {"Kitchen", "Fridge"}


# ── round-trip: both filters active on the same request ──────────────


def test__both_filters_active_on_one_request():
    added_groups, added_locations, result = _run(SeedRequest(
        groups=True,
        locations=True,
        group_names=["Pantry"],
        location_paths=["Kitchen/Freezer"],
    ))
    assert [g.name for g in added_groups] == ["Pantry"]
    assert {l.name for l in added_locations} == {"Kitchen", "Freezer"}
    assert result.groups_created == 1
    assert result.locations_created == 2
