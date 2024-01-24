from clapy import InputPort

from domain.entities.base_entity import EntityID


class DeleteStockItemInputPort(InputPort):
    stock_item_id: EntityID
