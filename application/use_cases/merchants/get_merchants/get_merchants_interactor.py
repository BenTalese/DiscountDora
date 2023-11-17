from clapy import Interactor
from application.dtos.merchant_dto import get_merchant_dto

from application.services.ipersistence_context import IPersistenceContext
from application.use_cases.merchants.get_merchants.get_merchants_input_port import GetMerchantsInputPort
from application.use_cases.merchants.get_merchants.iget_merchants_output_port import IGetMerchantsOutputPort
from domain.entities.merchant import Merchant


class GetMerchantsInteractor(Interactor):

    def __init__(self, persistence_context: IPersistenceContext):
        self.persistence_context = persistence_context

    async def execute_async(self, input_port: GetMerchantsInputPort, output_port: IGetMerchantsOutputPort):
        await output_port \
            .present_merchants_async(self.persistence_context
                                     .get_entities(Merchant)
                                     .project(get_merchant_dto))
