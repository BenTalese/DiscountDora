from abc import ABC

from clapy import IOutputPort

from domain.entities.stock_location import StockLocation

class ICreateStockLocation(IOutputPort, ABC):
    
    async def present_stock_location_created_async(stockLocation: StockLocation):
        pass