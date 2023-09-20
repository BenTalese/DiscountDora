from clapy import Interactor

from .create_stock_item_input_port import CreateStockItemInputPort
from .icreate_stock_item_output_port import ICreateStockItemOutputPort


class CreateStockItemInteractor(Interactor):

    async def execute_async(self, input_port: CreateStockItemInputPort, output_port: ICreateStockItemOutputPort):
        pass
