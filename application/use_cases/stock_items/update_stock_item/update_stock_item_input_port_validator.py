from clapy import InputPortValidator, ValidationResult
from varname import nameof

from application.use_cases.stock_items.update_stock_item.iupdate_stock_item_output_port import \
    IUpdateStockItemOutputPort
from application.use_cases.stock_items.update_stock_item.update_stock_item_input_port import \
    UpdateStockItemInputPort


class UpdateStockItemInputPortValidator(InputPortValidator):

    async def execute_async(self, input_port: UpdateStockItemInputPort, output_port: IUpdateStockItemOutputPort):
        if input_port.product_ids_to_add.has_been_set and input_port.product_ids_to_remove.has_been_set:

            # todo: may also want to ensure uniqueness with a single collection
            duplicate_product_ids = set(input_port.product_ids_to_add.value).intersection(set(input_port.product_ids_to_remove.value))

            if duplicate_product_ids:

                _Failure = ValidationResult.from_error( \
                    input_port, \
                    "product_ids", \
                    "The product_ids in " + nameof(input_port.product_ids_to_add) + " and " + \
                        nameof(input_port.product_ids_to_remove) + " must be unique.")

                self.has_failures = True
                await output_port.present_validation_failure_async(_Failure)
