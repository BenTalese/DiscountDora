from clapy import InputPortValidator, ValidationResult
from varname import nameof

from application.use_cases.products.update_product.iupdate_product_output_port import \
    IUpdateProductOutputPort
from application.use_cases.products.update_product.update_product_input_port import \
    UpdateProductInputPort


class UpdateProductInputPortValidator(InputPortValidator):

    async def execute_async(self, input_port: UpdateProductInputPort, output_port: IUpdateProductOutputPort):
        if input_port.price_now.has_been_set and not input_port.price_was.has_been_set:
            _Failure = ValidationResult.from_error(input_port, nameof(input_port.price_now), "price_now and price_was must both be set.")
            self.has_failures = True
            await output_port.present_validation_failure_async(_Failure)

        if input_port.price_was.has_been_set and not input_port.price_now.has_been_set:
            _Failure = ValidationResult.from_error(input_port, nameof(input_port.price_was), "price_now and price_was must both be set.")
            self.has_failures = True
            await output_port.present_validation_failure_async(_Failure)
