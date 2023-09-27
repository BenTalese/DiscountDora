# TODO: Is this the right spot for this file?

from abc import ABC


class IQueryBuilder(ABC):
    def any(self, condition = None):
        return self

    def execute(self):
        pass

    def first(self, condition = None):
        return self

    def first_by_id(self, *ids):
        return self

    def first_or_none(self, condition = None):
        return self

    def include(self, attribute_name):
       return self

    def project(self, *attributes):
        return self

    def then_include(self, attribute_name):
        return self

    def where(self, condition):
        return self
