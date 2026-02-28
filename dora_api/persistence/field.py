from sqlalchemy import func
from dora_api.domain.entities.base_entity import EntityID


class Field:
    """
    Wraps an (EntityClass, attribute_name) reference so you can build
    conditions fluently rather than passing raw tuples everywhere.

    Can use "And", "Or", "Not", or their operator alternatives "&", "|", and "~"

    Simple:
    ```python
        Field(Product, "name").eq("Milk")
        Field(Product, "is_active").eq(True)
        Field(Product, "score").gt(4.0)
    ```
    Medium:
    ```python
        Field(Product, "name").eq("Milk", case_sensitive=True)
        & Field(Product, "is_active").eq(True)
    ```
    Complex:
    ```python
        Or(
            And(
                Field(Product, "name").contains("milk", case_sensitive=False),
                Field(Product, "score").between(1.0, 5.0),
            ),
            And(
                Field(Product, "merchant_id").in_([id1, id2]),
                Field(Product, "is_active").eq(True),
                ~Field(Product, "web_url").is_null(),
            ),
        )
    ```
    """
    def __init__(self, entity_class: type, attribute_name: str):
        self.entity_class = entity_class
        self.attribute_name = attribute_name

    def _col(self, case_sensitive: bool = False):
        from sqlalchemy import String
        col = getattr(self.entity_class, self.attribute_name)
        if not case_sensitive and isinstance(col.property.columns[0].type, String):
            return func.lower(col)
        return col

    def _coerce(self, value, case_sensitive: bool = False):
        if isinstance(value, EntityID):
            return str(value.value)
        if isinstance(value, str):
            return value.lower() if case_sensitive else value
        if isinstance(value, Field):
            return value._col(case_sensitive)
        return value

    # Comparisons
    def eq(self, value, case_sensitive: bool = False):
        from dora_api.persistence.bool_operation import Equal
        return Equal(self, value, case_sensitive=case_sensitive)

    def ne(self, value, case_sensitive: bool = False):
        from dora_api.persistence.bool_operation import NotEqual
        return NotEqual(self, value, case_sensitive=case_sensitive)

    def gt(self, value):
        from dora_api.persistence.bool_operation import Greater
        return Greater(self, value)

    def lt(self, value):
        from dora_api.persistence.bool_operation import Less
        return Less(self, value)

    def gte(self, value):
        from dora_api.persistence.bool_operation import GreaterOrEqual
        return GreaterOrEqual(self, value)

    def lte(self, value):
        from dora_api.persistence.bool_operation import LessOrEqual
        return LessOrEqual(self, value)

    def is_null(self):
        from dora_api.persistence.bool_operation import IsNull
        return IsNull(self)

    def is_not_null(self):
        from dora_api.persistence.bool_operation import IsNotNull
        return IsNotNull(self)

    def in_(self, values: list):
        from dora_api.persistence.bool_operation import In
        return In(self, values)

    def not_in(self, values: list):
        from dora_api.persistence.bool_operation import NotIn
        return NotIn(self, values)

    def between(self, lower, upper):
        from dora_api.persistence.bool_operation import Between
        return Between(self, lower, upper)

    def contains(self, value: str, case_sensitive: bool = False):
        from dora_api.persistence.bool_operation import Contains
        return Contains(self, value, case_sensitive=case_sensitive)

    def starts_with(self, value: str, case_sensitive: bool = False):
        from dora_api.persistence.bool_operation import StartsWith
        return StartsWith(self, value, case_sensitive=case_sensitive)

    def to_sqla(self, case_sensitive: bool = False):
        return self._col(case_sensitive)
