from dataclasses import dataclass
from datetime import datetime

from dora_api.domain.entities.base_entity import BaseEntity


'''
FIXME: Commit 49362cbf1256accc67ba1c4bc90075635e9205d3
Split historic offers into their own table to fix a weird race condition that appeared to be fixed in update
product if historic offer was commented out. The current offer was failing to change sometimes. This is likely
something to do with the fact two properties were configured to go to the same database table. It makes no
sense to split out in the domain as a separate entity but keeping it that way would require a huge persistence
rework and I can't be assed...
'''


@dataclass
class ProductHistoricOffer(BaseEntity):
    offered_on: datetime
    price_now: float
    price_was: float
