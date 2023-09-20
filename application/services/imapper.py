from typing import Any, Callable

from .iquerybuilder import IQueryBuilder


class IMapper:

    def project(self, src: IQueryBuilder, mapping_action: Callable[[Any], Any]): # TODO: Figure out which return type
        pass
