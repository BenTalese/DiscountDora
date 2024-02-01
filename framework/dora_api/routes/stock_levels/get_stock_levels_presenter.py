from application.dtos.stock_level_dto import StockLevelDto
from application.services.iquerybuilder import IQueryBuilder
from application.use_cases.stock_levels.get_stock_levels.iget_stock_levels_output_port import IGetStockLevelsOutputPort
from framework.api.infrastructure.base_presenter import BasePresenter
from framework.api.view_models.stock_level_view_model import get_stock_level_view_model


class GetStockLevelsPresenter(BasePresenter, IGetStockLevelsOutputPort):
    async def present_stock_levels_async(self, stock_levels: IQueryBuilder[StockLevelDto]):
        await self.ok_async(stock_levels.project(get_stock_level_view_model).execute())
