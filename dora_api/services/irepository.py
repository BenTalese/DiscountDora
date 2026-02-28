# from abc import ABC, abstractmethod
# from typing import Generic

# from dora_api.services.iquerybuilder import IQueryBuilder
# from dora_api.domain.generics import TEntity


# class IRepository(ABC, Generic[TEntity]):
#     @abstractmethod
#     def add(self, entity: TEntity) -> None:
#         pass

#     @abstractmethod
#     def get(self, entity_type: type[TEntity]) -> IQueryBuilder[TEntity]:
#         pass

#     @abstractmethod
#     def remove(self, entity: TEntity) -> None:
#         pass

#     @abstractmethod
#     def save_changes(self) -> None:
#         pass

#     @abstractmethod
#     def update(self, entity: TEntity) -> None:
#         pass
