import abc
from typing import Optional, Dict, List
from typing_extensions import Literal


class Product(abc.ABC):
    # NOTE: Only used by email template to show where offer came from
    merchant: Literal['coles', 'woolies']

    @property
    @abc.abstractmethod
    def display_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def price(self) -> Optional[float]:
        pass

    @property
    @abc.abstractmethod
    def is_on_special(self) -> Optional[bool]:
        pass

    @property
    @abc.abstractmethod
    def link(self) -> str:
        pass

    def __lt__(self, other: 'Product'):
        # n.b. all that's required for sorted()/.sort()
        return (self.price or 1e6) < (other.price or 1e6)  # default to big number when no price available


ProductOffers = Dict[str, List[Product]]  # {'product_name': [Product, ...]}

# NOTE: Only used under "examples", probably not needed
Merchant = Literal['coles', 'woolies']


# class OfferDict(dict):
#     @classmethod
#     def from_list(cls): ...
#
#     def price_by_merchant(self, merchant: Merchant) -> Optional[float]:
#         return self[merchant].price
#
#     def to_list(self, sort: bool = False) -> List[_Product]:
#         if sort:
#             return sorted(self.items(), key=_sort_by_price_key)
#         else:
#             return list(self.items())
#
#     def best_offers(self):
#         return min(self.items(), key=_sort_by_price_key)
#
#     def best_price(self) -> float:
#         return self.best_offers().price
