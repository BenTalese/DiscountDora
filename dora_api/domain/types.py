class Unset:
    @classmethod
    def __get_pydantic_core_schema__(cls, source, handler):
        from pydantic_core import core_schema
        return core_schema.is_instance_schema(cls)

    def __repr__(self):
        return "UNSET"


UNSET = Unset()
