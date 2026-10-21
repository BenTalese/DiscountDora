"""Which nutrition sources this install can actually answer lookups from.

The old `AppSetting.nutrition_db_source` string *asserted* that a source
existed; nothing verified it and nothing could set it. Availability is
**derived** here instead, from facts the server can check: is a dataset
actually imported, is an API key actually set, is OFF lookup actually allowed.

Every source that answers a lookup stamps its rows with its own id, so the
picker can badge each result with where it came from — the owner's ask, and
the honest thing to do when three catalogues disagree about a banana.
"""
from dataclasses import dataclass
from typing import List

from dora_api.domain.entities.app_setting import (
    NUTRITION_MODE_COMPLEX,
    NUTRITION_MODE_OFF,
)
from dora_api.domain.entities.nutrition_food import (
    NUTRITION_DATASET_SOURCES,
    NUTRITION_SOURCE_LABELS,
    NUTRITION_SOURCE_OFF,
    NUTRITION_SOURCE_USDA_API,
)
from dora_api.domain.entities.nutrition_food import NutritionFood
from dora_api.infrastructure.ports import Repository
from dora_api.persistence.field import EntityField as Field


@dataclass(frozen=True, slots=True)
class NutritionSourceStatus:
    """One row per source for the admin page: what it is, whether it can
    answer right now, and how much it holds."""
    id: str
    label: str
    kind: str          # "dataset" | "api" | "web"
    available: bool
    food_count: int    # 0 for live sources — they hold nothing locally


def dataset_counts(repository: Repository) -> dict[str, int]:
    """How many foods each bulk dataset has imported. Drives both the
    availability check and the admin page's per-dataset row."""
    counts: dict[str, int] = {}
    for source in NUTRITION_DATASET_SOURCES:
        counts[source] = repository.get(NutritionFood).where(
            Field(NutritionFood, NutritionFood.Fields.SOURCE).eq(source)
        ).count()
    return counts


def local_catalogue_size(repository: Repository) -> int:
    """How many foods are held locally, from any source.

    This — not `any_source_available` — is what the name-matcher can actually
    work with. The matcher is local-catalogue-only by design (see
    `suggestions.py`), so an install with Open Food Facts switched on but no
    dataset downloaded reports a source as "available" while the matcher has
    nothing to match against and silently suggests nothing. The matching page
    uses this to say so out loud instead of looking broken.
    """
    return repository.get(NutritionFood).count()


def source_statuses(repository: Repository, setting) -> List[NutritionSourceStatus]:  # noqa: ANN001
    counts = dataset_counts(repository)
    statuses = [
        NutritionSourceStatus(
            id = source,
            label = NUTRITION_SOURCE_LABELS[source],
            kind = "dataset",
            # A dataset is available exactly when it holds rows. No flag to
            # get out of sync with reality.
            available = counts.get(source, 0) > 0,
            food_count = counts.get(source, 0),
        )
        for source in NUTRITION_DATASET_SOURCES
    ]
    statuses.append(NutritionSourceStatus(
        id = NUTRITION_SOURCE_USDA_API,
        label = NUTRITION_SOURCE_LABELS[NUTRITION_SOURCE_USDA_API],
        kind = "api",
        available = bool((getattr(setting, "nutrition_usda_api_key", "") or "").strip()),
        food_count = 0,
    ))
    statuses.append(NutritionSourceStatus(
        id = NUTRITION_SOURCE_OFF,
        label = NUTRITION_SOURCE_LABELS[NUTRITION_SOURCE_OFF],
        kind = "web",
        # OFF needs no key — only the admin's permission to reach the network.
        available = bool(getattr(setting, "nutrition_off_lookup_enabled", True)),
        food_count = 0,
    ))
    return statuses


def any_source_available(repository: Repository, setting) -> bool:  # noqa: ANN001
    return any(status.available for status in source_statuses(repository, setting))


def nutrition_mode(setting) -> str:  # noqa: ANN001
    """The install's mode, defensively defaulted. One read point so callers
    don't each re-derive the fallback."""
    if setting is None:
        return NUTRITION_MODE_OFF
    return getattr(setting, "nutrition_mode", None) or NUTRITION_MODE_OFF


def complex_is_usable(repository: Repository, setting) -> bool:  # noqa: ANN001
    """Complex mode is *selected* and can actually answer. Kept separate from
    the mode itself so the UI can say "you picked complex but nothing's
    installed yet" rather than silently pretending the feature is off."""
    return (
        nutrition_mode(setting) == NUTRITION_MODE_COMPLEX
        and any_source_available(repository, setting)
    )
