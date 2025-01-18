from clapy import Interactor

from application.dtos.stock_level_dto import get_stock_level_dto
from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.stock_levels.get_stock_levels.get_stock_levels_input_port import \
    GetStockLevelsInputPort
from application.use_cases.stock_levels.get_stock_levels.iget_stock_levels_output_port import \
    IGetStockLevelsOutputPort
from domain.entities.stock_level import StockLevel


class GetStockLevelsInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: GetStockLevelsInputPort, output_port: IGetStockLevelsOutputPort):
        await output_port \
            .present_stock_levels_async(self.persistence_context
                                       .get_entities(StockLevel)
                                       .project(get_stock_level_dto))
