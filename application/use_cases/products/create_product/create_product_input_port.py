from clapy import InputPort

from domain.entities.base_entity import EntityID


# TODO: clapy should have this ctor on input port class, test if plays well with required input enforcement
# TODO: also, DependencyInjectorServiceProvider.get_service() is shit with error message (none at all) for
# when interface mismatches implementation (method signatures), and also when it just can't construct the
# service (e.g. dependencies registered in the wrong order)
# TODO: Errors in previous pipes not checked?? Check clapy, i thought it would check all prev pipes or something
class CreateProductInputPort(InputPort):
    # TODO: Maybe just delete this? I feel explicit mapping is best
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    brand: str = None
    image: bytes = None
    is_available: bool
    merchant_id: EntityID
    merchant_stockcode: str
    name: str
    price_now: float
    price_was: float
    size_unit: str
    size_value: float = 0 # TODO: Can be nothing?
    web_url: str
