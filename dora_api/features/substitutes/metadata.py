"""FU-034 — shared metadata + direction handling for StockItemSubstitute.

`StockItemSubstitute` carries optional metadata (`notes` + a structured
ratio). The pair is stored canonically (`a_id < b_id`), so callers always
think in terms of "from THIS item to its substitute" but the row stores
the ratio in the A→B direction. This module owns:

  - **Validation** (`validate_metadata`) — the API-layer rules: notes ≤ 255
    chars, ratio all-or-none, positive quantities, units present in the
    canonical `dora_api.domain.units` catalogue, units stored in canonical
    form.

  - **Direction flip** (`build_metadata`) — when the caller passed the
    ratio "as seen from `from_id`" and we're about to persist it in the
    canonical A→B direction, swap the in/out pair iff `from_id != a_id`.

Add + update handlers both call these, so the validation rules live in
exactly one place (R-003 single source of truth).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from dora_api.domain import units


@dataclass(frozen=True, slots=True)
class SubstituteMetadata:
    """One bundle of substitute metadata. Empty (all None) is valid — that's
    a bare substitute pair with no notes or ratio."""
    notes: str | None = None
    ratio_quantity_in: float | None = None
    ratio_unit_in: str | None = None
    ratio_quantity_out: float | None = None
    ratio_unit_out: str | None = None


_RATIO_FIELDS = (
    "ratio_quantity_in",
    "ratio_unit_in",
    "ratio_quantity_out",
    "ratio_unit_out",
)


def validate_metadata(meta: SubstituteMetadata) -> str | None:
    """Return a human-readable error message when the metadata is invalid,
    or None when it's clean. Callers map the message to a
    business-rule-violation response.

    Rules:
      - All four ratio fields are None, or all four are present.
      - Quantities are strictly > 0.
      - Units must exist in `units.UNIT_TABLE` (normalised); we normalise
        the input in-place so the persisted value is the canonical form.
    """
    if meta.notes is not None and len(meta.notes) > 255:
        return "Notes must be 255 characters or fewer."

    values = [getattr(meta, f) for f in _RATIO_FIELDS]
    set_count = sum(1 for v in values if v is not None)
    if set_count == 0:
        return None
    if set_count != 4:
        return (
            "Ratio is incomplete — provide quantity + unit for both sides, "
            "or leave the whole ratio blank."
        )

    if (meta.ratio_quantity_in or 0) <= 0 or (meta.ratio_quantity_out or 0) <= 0:
        return "Ratio quantities must be greater than zero."

    if units.find_unit(meta.ratio_unit_in or "") is None:
        return f"Unknown unit on the ratio's left side: {meta.ratio_unit_in!r}."
    if units.find_unit(meta.ratio_unit_out or "") is None:
        return f"Unknown unit on the ratio's right side: {meta.ratio_unit_out!r}."

    return None


def _canonicalise_units(meta: SubstituteMetadata) -> SubstituteMetadata:
    """Replace user-typed unit aliases ("tablespoons" → "tbsp") with the
    canonical display form from the UNIT_TABLE. Called after
    validate_metadata so we know the units resolve."""
    if meta.ratio_unit_in is None and meta.ratio_unit_out is None:
        return meta
    in_def = units.find_unit(meta.ratio_unit_in or "")
    out_def = units.find_unit(meta.ratio_unit_out or "")
    return replace(
        meta,
        ratio_unit_in=in_def.canonical if in_def else meta.ratio_unit_in,
        ratio_unit_out=out_def.canonical if out_def else meta.ratio_unit_out,
    )


def _flip_ratio(meta: SubstituteMetadata) -> SubstituteMetadata:
    """Swap the in/out pair so the same logical ratio is expressed from
    the opposite side. ``notes`` stays put — it isn't directional."""
    return replace(
        meta,
        ratio_quantity_in=meta.ratio_quantity_out,
        ratio_unit_in=meta.ratio_unit_out,
        ratio_quantity_out=meta.ratio_quantity_in,
        ratio_unit_out=meta.ratio_unit_in,
    )


def build_metadata(
    meta: SubstituteMetadata,
    from_id: UUID,
    canonical_a_id: UUID,
) -> SubstituteMetadata:
    """Reorient a caller-supplied metadata bundle into the canonical A→B
    direction for persistence.

    ``meta`` arrived expressed "from ``from_id``'s perspective". If
    ``from_id == canonical_a_id`` the ratio direction already matches the
    canonical storage direction; otherwise we swap in↔out so the persisted
    row's `ratio_*_in` describes A and `ratio_*_out` describes B.

    Always canonicalises the unit strings to the UNIT_TABLE display form.
    """
    if meta.ratio_quantity_in is None:
        # No ratio to reorient — only notes (or nothing) to persist.
        return _canonicalise_units(meta)

    canonical_meta = _canonicalise_units(meta)
    if str(from_id) == str(canonical_a_id):
        return canonical_meta
    return _flip_ratio(canonical_meta)
