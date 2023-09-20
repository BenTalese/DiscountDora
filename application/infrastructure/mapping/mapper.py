from typing import Any, Callable

from application.services.iquerybuilder import IQueryBuilder


class Mapper:

    def project(self, src: IQueryBuilder, mapping_action: Callable[[Any], Any]):
        return lambda: [mapping_action(obj) for obj in src.execute()]
