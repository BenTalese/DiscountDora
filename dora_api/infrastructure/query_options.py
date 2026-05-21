"""Query parameter parsing for list endpoints.

Standard shape:
    GET /api/recipes?filter=name:ct:pasta&filter=is_favourite:eq:true
                    &sort=name:asc&page=1&limit=50

- Multiple `filter` params are AND-ed.
- `sort` accepts a single `field:asc|desc` value.
- `page` is 1-based; `limit` is clamped to MAX_LIMIT.

Filter operators mirror the legacy in-memory DSL but are now applied at the
database layer by the query builder.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from werkzeug.datastructures import MultiDict


VALID_OPERATORS = frozenset({"eq", "ne", "lt", "gt", "le", "ge", "ct"})
VALID_DIRECTIONS = frozenset({"asc", "desc"})
DEFAULT_LIMIT = 50
MAX_LIMIT = 500


class InvalidQueryParameter(ValueError):
    """Raised when a query parameter cannot be parsed."""


@dataclass(frozen=True, slots=True)
class FilterClause:
    field: str
    operator: str
    value: str


@dataclass(frozen=True, slots=True)
class SortClause:
    field: str
    direction: str


@dataclass(frozen=True, slots=True)
class QueryOptions:
    filters: tuple[FilterClause, ...] = ()
    sort: SortClause | None = None
    page: int = 1
    limit: int = DEFAULT_LIMIT

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def _parse_filter(raw: str) -> FilterClause:
    parts = raw.split(":", 2)
    if len(parts) != 3:
        raise InvalidQueryParameter(
            f"Malformed filter '{raw}'. Expected format: field:operator:value."
        )
    _Field, _Operator, _Value = parts
    if _Operator not in VALID_OPERATORS:
        raise InvalidQueryParameter(
            f"Unsupported filter operator '{_Operator}'. "
            f"Supported: {', '.join(sorted(VALID_OPERATORS))}."
        )
    if not _Field:
        raise InvalidQueryParameter("Filter field cannot be empty.")
    return FilterClause(field=_Field, operator=_Operator, value=_Value)


def _parse_sort(raw: str) -> SortClause:
    parts = raw.split(":")
    if len(parts) != 2:
        raise InvalidQueryParameter(
            f"Malformed sort '{raw}'. Expected format: field:asc|desc."
        )
    _Field, _Direction = parts
    if _Direction not in VALID_DIRECTIONS:
        raise InvalidQueryParameter(
            f"Sort direction '{_Direction}' is not supported. Use 'asc' or 'desc'."
        )
    if not _Field:
        raise InvalidQueryParameter("Sort field cannot be empty.")
    return SortClause(field=_Field, direction=_Direction)


def _parse_int(raw: str, name: str, minimum: int) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise InvalidQueryParameter(f"'{name}' must be an integer.")
    if value < minimum:
        raise InvalidQueryParameter(f"'{name}' must be {minimum} or greater.")
    return value


def parse_query_options(args: MultiDict[str, str]) -> QueryOptions:
    """Parse standard query parameters from a Flask request.args MultiDict."""
    filters: list[FilterClause] = [_parse_filter(raw) for raw in args.getlist("filter")]

    sort: SortClause | None = None
    if "sort" in args:
        sort = _parse_sort(args["sort"])

    page = _parse_int(args.get("page", "1"), "page", minimum=1)
    raw_limit = args.get("limit", str(DEFAULT_LIMIT))
    limit = _parse_int(raw_limit, "limit", minimum=1)
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT

    return QueryOptions(
        filters=tuple(filters),
        sort=sort,
        page=page,
        limit=limit,
    )


def validate_known_fields(options: QueryOptions, known_fields: Iterable[str]) -> None:
    """Raise InvalidQueryParameter if filter or sort references an unknown field."""
    known = frozenset(known_fields)
    for f in options.filters:
        if f.field not in known:
            raise InvalidQueryParameter(
                f"Filter field '{f.field}' is not a valid response field."
            )
    if options.sort and options.sort.field not in known:
        raise InvalidQueryParameter(
            f"Sort field '{options.sort.field}' is not a valid response field."
        )


