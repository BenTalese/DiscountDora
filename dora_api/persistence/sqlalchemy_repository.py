from dataclasses import fields
from typing import Any, Callable, Generic, List
from uuid import UUID, uuid4

from flask import Flask
from sqlalchemy import Select, select
from sqlalchemy.orm import contains_eager, registry

from dora_api.app import db
from dora_api.domain.entities.base_entity import BaseEntity
from dora_api.domain.exceptions import PersistenceError
from dora_api.domain.generics import TEntity
from dora_api.persistence.bool_operation import BoolOperation
from dora_api.persistence.field import EntityField
from dora_api.persistence.table_mappings import _mapper_registry


class SqlAlchemyRepository:
    _flask_app: Flask

    @property
    def session(self):
        """Escape hatch for complex queries that the builder can't express cleanly."""
        return db.session

    def add(self, entity: BaseEntity) -> None:
        # Catch inline-constructed related entities that were never added
        for f in fields(entity):
            value = getattr(entity, f.name)
            if isinstance(value, BaseEntity) and value.id == UUID(int=0):
                raise PersistenceError(
                    f"{type(entity).__name__}.{f.name} has not been persisted. "
                    f"Call repo.add() on it before adding {type(entity).__name__}."
                )

        entity.id = uuid4()
        db.session.add(entity)

    def get(self, entity_type: type[TEntity]) -> 'SqlAlchemyQueryBuilder[TEntity]':
        return SqlAlchemyQueryBuilder(entity_type, _mapper_registry, self._flask_app)

    def reattach_and_save(self, entity: BaseEntity) -> None:
        """Use when an entity was loaded outside the current session.
        Example: Loaded in a previous request, serialised, sent to frontend,
        modified, sent back, deserialised — session has no idea about it"""
        db.session.merge(entity)

    def remove(self, entity: BaseEntity):
        db.session.delete(entity)

    def save_changes(self):
        db.session.commit()


class SqlAlchemyQueryBuilder(Generic[TEntity]):
    '''
    Example usage:
    ```python
    results = (
        self.repository
        .get(ShoppingList)
        .include("items")
            .then_include("stock_level")
            .then_include("stock_location")
        .where(
            And(
                Or(
                    Field(StockItem, "stocktake_alerts_are_enabled").eq(True),
                    Field(StockLevel, "sequence").gte(0),
                ),
                Field(StockItem, "name").contains("a"),
                Not(Field(StockLocation, "name").eq("freezer")),
                Field(StockLevel, "sequence").between(1, 3),
            )
        )
        .all()
    )

    results = (
        self.repository
        .get(Product)
        .include("merchant")
        .include("current_offer")
        .where(
            Field(Product, "is_active").eq(True)
            & Field(Product, "is_available").eq(True)
            & (
                Field(Merchant, "name").eq("woolworths") |
                Field(Merchant, "name").eq("coles")
            )
            & (
                Field(ProductOffer, "price_now").between(1.0, 50.0) |
                Field(ProductOffer, "price_now").lt(Field(ProductOffer, "price_was"))
            )
            & (
                Field(Product, "name").contains("cake") |
                Field(Product, "name").contains("mix")
            )
            & Field(Product, "web_url").is_not_null()
            & ~Field(Product, "brand").eq("cadbury")
        )
        .all()
    )
    ```
    '''
    def __init__(self, entity_type: type[TEntity], mapper_registry: registry, flask_app: Flask):
        self._mapper_registry = mapper_registry
        self.entity_type = entity_type
        self.query: Select = select(entity_type)
        self.join_paths: dict[str, list] = {}
        self._included_entity: type | None = None
        self._included_path: str = ""
        self._included_chain: list = []
        self._include_root_entity: type | None = None
        self._include_root_chain: list = []
        self._is_partial = False

    def all(self, condition: BoolOperation | None = None) -> List[TEntity]:
        if condition:
            return self.where(condition).all()
        return self._execute()

    def by_id(self, entity_id: UUID) -> TEntity | None:
        return self.one(EntityField(self.entity_type, "id").eq(entity_id))

    def exists(self, entity_id: UUID) -> bool:
        return self.by_id(entity_id) is not None

    def include(self, attribute_name: str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        attr = self._resolve_attribute(self.entity_type, attribute_name)

        if attribute_name not in self.join_paths:
            self.join_paths[attribute_name] = [attr]

        self._included_path = attribute_name
        self._included_chain = [attr]
        self._included_entity = self._get_related_entity(self.entity_type, attribute_name)
        self._include_root_entity = self._included_entity
        self._include_root_chain = [attr]
        return self

    def one(self, condition: BoolOperation | None = None) -> TEntity | None:
        result = self.where(condition)._execute() if condition else self._execute()
        return result[0] if result else None

    def project(self, projection_method: Callable) -> List[Any]:
        '''
        Full entity, project in Python
        repo.get(Product).project(lambda p: p.name)
        repo.get(Merchant).project(to_dto)

        Column-level, project from dict-like row
        repo.get(Product)\
            .select(Field(Product, "name"), Field(Product, "web_url"))\
            .where(Field(Product, "is_active").eq(True))\
            .project(lambda row: {"name": row["name"], "web_url": row["web_url"]})
        '''
        if self._is_partial:
            results = db.session.execute(self.query).all()
            return [projection_method(row._mapping) for row in results]
        return [projection_method(entity) for entity in self._execute()]

    def select(self, *fields: EntityField) -> 'SqlAlchemyQueryBuilder[TEntity]':
        self.query = self.query.with_only_columns(*[f.to_sqla() for f in fields])
        self._is_partial = True
        return self

    def then_include(self, attribute_name: str) -> 'SqlAlchemyQueryBuilder[TEntity]':
        if not self._included_entity or not self._include_root_entity:
            raise PersistenceError("Call include() before then_include().")

        attr = self._resolve_attribute(self._include_root_entity, attribute_name)
        path_key = f"{self._included_path}.{attribute_name}"

        if path_key not in self.join_paths:
            self.join_paths[path_key] = self._include_root_chain + [attr]

        self._included_path = path_key
        self._included_chain = self.join_paths[path_key]
        self._included_entity = self._get_related_entity(self._include_root_entity, attribute_name)
        return self

    def where(self, condition: BoolOperation) -> 'SqlAlchemyQueryBuilder[TEntity]':
        self.query = self.query.where(condition.to_sqla(self._mapper_registry))
        return self

    def _execute(self) -> List[Any]:
        for chain in self.join_paths.values():
            # Add the joins
            for attr in chain:
                self.query = self.query.outerjoin(attr)

            # Build contains_eager chain
            # contains_eager(A).contains_eager(B).contains_eager(C)
            option = contains_eager(chain[0])
            for attr in chain[1:]:
                option = option.contains_eager(attr)

            self.query = self.query.options(option)

        print('\033[34m' + '\n=== EXECUTING QUERY ===\n' + '\033[93m' + str(self.query) + '\033[0m')
        results = db.session.execute(self.query).unique().all()
        return [row[0] for row in results]

    def _resolve_attribute(self, entity_type: type, attribute_name: str):
        if not hasattr(entity_type, attribute_name):
            raise PersistenceError(f"'{attribute_name}' not found on '{entity_type.__name__}'.")

        attr = getattr(entity_type, attribute_name)

        if not hasattr(attr, "property"):
            raise PersistenceError(f"'{attribute_name}' on '{entity_type.__name__}' is not a mapped relationship.")

        return attr

    def _get_related_entity(self, entity_type: type, attribute_name: str) -> type | None:
        attr = getattr(entity_type, attribute_name)
        if hasattr(attr, "property") and hasattr(attr.property, "mapper"):
            return attr.property.mapper.class_
        return None
