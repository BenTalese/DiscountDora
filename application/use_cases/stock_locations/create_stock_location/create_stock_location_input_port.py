from clapy import InputPort

class CreateStockLocationInputPort(InputPort):
    description: str #How restrictive do we want to be? Can they provide nothing? Validation?
