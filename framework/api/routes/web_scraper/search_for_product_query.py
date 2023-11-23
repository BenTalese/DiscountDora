from dataclasses import dataclass


@dataclass
class SearchForProductQuery:
    search_term: str
    start_page: int
