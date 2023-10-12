import uuid


class BoolOperation:
    def __init__(self, exp1, exp2):
        self.exp1: BoolOperation = exp1
        self.exp2: BoolOperation = exp2

    def sanitise(self):
        if type(self.exp1) == tuple:
            self.exp1 = f"[[{self.exp1[0].__name__}]].{self.exp1[1]}"
        elif (type(self.exp1) == str
              or type(self.exp2) == uuid.UUID):
            self.exp1 = f"'{self.exp1}'"

        if type(self.exp2) == tuple:
            self.exp2 = f"[[{self.exp2[0].__name__}]].{self.exp2[1]}"
        elif (type(self.exp2) == str
              or type(self.exp2) == uuid.UUID):
            self.exp2 = f"'{self.exp2}'"

    def to_str(self):
        pass

class Equal(BoolOperation):
    def to_str(self):
        self.sanitise()
        return f"{self.exp1} == {self.exp2}"

class NotEqual(BoolOperation):
    def to_str(self):
        self.sanitise()
        return f"{self.exp1} != {self.exp2}"

class Greater(BoolOperation):
    def to_str(self):
        self.sanitise()
        return f"{self.exp1} > {self.exp2}"

class Less(BoolOperation):
    def to_str(self):
        self.sanitise()
        return f"{self.exp1} < {self.exp2}"

class GreaterOrEqual(BoolOperation):
    def to_str(self):
        self.sanitise()
        return f"{self.exp1} >= {self.exp2}"

class LessOrEqual(BoolOperation):
    def to_str(self):
        self.sanitise()
        return f"{self.exp1} <= {self.exp2}"

class Not(BoolOperation):
    def __init__(self, exp: BoolOperation):
        self.exp = exp

    def to_str(self):
        return f"~({self.exp.to_str()})"

class And(BoolOperation):
    def to_str(self):
        return f"({self.exp1.to_str()}) & ({self.exp2.to_str()})"

class Or(BoolOperation):
    def to_str(self):
        return f"({self.exp1.to_str()}) | ({self.exp2.to_str()})"
