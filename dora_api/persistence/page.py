from dataclasses import dataclass
from typing import Generic, List

from dora_api.domain.generics import TValue


# `slots=True` is intentionally omitted: combined with `Generic[T]` it has
# version-dependent quirks on Python 3.10/3.11. The minor memory win isn't
# worth the portability risk for a value type that only lives for the
# duration of one request.
@dataclass(frozen=True)
class Page(Generic[TValue]):
    items: List[TValue]
    total: int
    page: int
    limit: int
