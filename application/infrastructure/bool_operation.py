from domain.entities.base_entity import EntityID

from domain.generics import TEntity


class BoolOperation:
    def __init__(self, expression_one, expression_two):
        self.expression_one: BoolOperation = expression_one
        self.expression_two: BoolOperation = expression_two

    def _sanitise_expressions(self):
        def sanitise_expression(exp):
            if type(exp) == tuple:
                return f"[[{exp[0].__name__}]].{exp[1]}"

            if type(exp) == TEntity:
                return f"[[{exp[0].__name__}]]"

            if type(exp) == str:
                return f"'{exp}'"

            if type(exp) == EntityID:
                return f"'{exp.value}'"

        self.expression_one = sanitise_expression(self.expression_one)
        self.expression_two = sanitise_expression(self.expression_two)

    def __str__(self):
        pass

class Equal(BoolOperation):
    def __str__(self):
        self._sanitise_expressions()
        return f"{self.expression_one} == {self.expression_two}"

class NotEqual(BoolOperation):
    def __str__(self):
        self._sanitise_expressions()
        return f"{self.expression_one} != {self.expression_two}"

class Greater(BoolOperation):
    def __str__(self):
        self._sanitise_expressions()
        return f"{self.expression_one} > {self.expression_two}"

class Less(BoolOperation):
    def __str__(self):
        self._sanitise_expressions()
        return f"{self.expression_one} < {self.expression_two}"

class GreaterOrEqual(BoolOperation):
    def __str__(self):
        self._sanitise_expressions()
        return f"{self.expression_one} >= {self.expression_two}"

class LessOrEqual(BoolOperation):
    def __str__(self):
        self._sanitise_expressions()
        return f"{self.expression_one} <= {self.expression_two}"

class Not(BoolOperation):
    def __init__(self, expression: BoolOperation):
        self.expression = expression

    def __str__(self):
        return f"~({self.expression.__str__()})"

class And(BoolOperation):
    def __str__(self):
        return f"({self.expression_one.__str__()}) & ({self.expression_two.__str__()})"

class Or(BoolOperation):
    def __str__(self):
        return f"({self.expression_one.__str__()}) | ({self.expression_two.__str__()})"
