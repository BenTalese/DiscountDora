from typing import Any, Callable

from application.services.imapper import IMapper
from application.services.iquerybuilder import IQueryBuilder


class Mapper(IMapper):

    #TODO: define a select, and use in mapper so it actually trims down the result set
    # Yeah this doesn't work, it needs to return an IQueryBuilder to continue without execution, and
    # I need to make it translate the mapping action to a select statement, fun...
    # Alternatively just map and forget about this crap
    def project(self, src: IQueryBuilder, mapping_action: Callable[[Any], Any]):
        return lambda: [mapping_action(obj) for obj in src.execute()]
