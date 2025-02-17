from domain.entities.base_entity import EntityID

from domain.generics import TEntity


class BoolOperation:
    def __init__(self, expression_one, expression_two, is_case_insensitive: bool = False):
        self.expression_one: BoolOperation = expression_one
        self.expression_two: BoolOperation = expression_two
        self.is_case_insensitive: bool = is_case_insensitive

    def _sanitise_expressions(self):
        def sanitise_expression(exp):
            if type(exp) is tuple:
                return f"func.lower([[{exp[0].__name__}]].{exp[1]})" if self.is_case_insensitive else f"[[{exp[0].__name__}]].{exp[1]}"

            if type(exp) is TEntity:
                return f"[[{exp[0].__name__}]]"

            if type(exp) is str:
                return f"'{exp.lower()}'" if self.is_case_insensitive else f"'{exp}'"

            if type(exp) is EntityID:
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
