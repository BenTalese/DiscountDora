# TODO: Is this the right spot for this file?

from abc import ABC


class IQueryBuilder(ABC):
    def any(self, condition = None):
        return self

    def execute(self):
        pass

    def find(self):
        return self

    def first(self, condition = None):
        return self

    def first_by_id(self, id):
        return self

    def first_or_none(self, condition = None):
        return self

    def select(self, selector):
       return self

    def where(self, condition):
        return self
