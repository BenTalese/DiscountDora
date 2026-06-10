"""Category CRUD (C-4 Chunk 2) — the user-configurable recipe category
vocabulary, distinct from cuisine (L235). Mirrors manage_cuisines.py.

Endpoints:

  GET    /api/categories        — list all (with recipe counts), ordered
  POST   /api/categories        — create
  PATCH  /api/categories/<id>   — rename
  DELETE /api/categories/<id>   — delete (recipes' category_id → NULL)
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.category import Category
from dora_api.domain.entities.recipe import Recipe
from dora_api.features.routers import CATEGORY_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created, not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class CategoryDto:
    category_id: UUID
    name: str
    sequence: int
    recipe_count: int


# ───── List ──────────────────────────────────────────────────────────────

class GetCategoriesHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[CategoryDto]:
        categories: List[Category] = self.repository.get(Category).all()
        recipes = self.repository.get(Recipe).all()
        counts: dict[UUID, int] = {}
        for r in recipes:
            if r.category is not None:
                counts[r.category.id] = counts.get(r.category.id, 0) + 1
        out = [
            CategoryDto(
                category_id=c.id,
                name=c.name,
                sequence=c.sequence,
                recipe_count=counts.get(c.id, 0),
            )
            for c in categories
        ]
        out.sort(key=lambda c: (c.sequence, c.name.lower()))
        return out


@CATEGORY_ROUTER.route("", methods=["GET"])
def get_categories():
    _Result = get_container().inject(GetCategoriesHandler).handle()
    return ok(_Result)


# ───── Create ────────────────────────────────────────────────────────────

class CreateCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class CreateCategoryResponse:
    category_id: UUID | None = None
    duplicate: bool = False


class CreateCategoryHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateCategoryRequest) -> CreateCategoryResponse:
        existing = self.repository.get(Category).all()
        normalised = request.name.strip().lower()
        if any(c.name.strip().lower() == normalised for c in existing):
            return CreateCategoryResponse(duplicate=True)
        next_seq = max((c.sequence for c in existing), default=-1) + 1
        category = Category(name=request.name.strip(), sequence=next_seq)
        self.repository.add(category)
        self.repository.save_changes()
        return CreateCategoryResponse(category_id=category.id)


@CATEGORY_ROUTER.route("", methods=["POST"])
@has_request_body(CreateCategoryRequest)
def create_category():
    _Logger = logging.getLogger(__name__)
    _Request: CreateCategoryRequest = get_request_body()
    _Response = get_container().inject(CreateCategoryHandler).handle(_Request)
    if _Response.duplicate:
        return business_rule_violation(f"A category named '{_Request.name}' already exists.")
    _Logger.info(f"Created category {_Response.category_id} '{_Request.name}'")
    return created(
        _Response.category_id,
        f"{CATEGORY_ROUTER.name}.{get_categories.__name__}",
        "category_id",
        body={"category_id": _Response.category_id},
    )


# ───── Rename ────────────────────────────────────────────────────────────

class UpdateCategoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class UpdateCategoryResponse:
    not_found: bool = False
    duplicate: bool = False


class UpdateCategoryHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateCategoryRequest, category_id: UUID) -> UpdateCategoryResponse:
        category: Category | None = self.repository.get(Category).by_id(category_id)
        if category is None:
            return UpdateCategoryResponse(not_found=True)
        target = request.name.strip()
        normalised = target.lower()
        for c in self.repository.get(Category).all():
            if c.id != category_id and c.name.strip().lower() == normalised:
                return UpdateCategoryResponse(duplicate=True)
        category.name = target
        self.repository.save_changes()
        return UpdateCategoryResponse()


@CATEGORY_ROUTER.route("/<category_id>", methods=["PATCH"])
@has_request_body(UpdateCategoryRequest)
def update_category(category_id: UUID):
    _Request: UpdateCategoryRequest = get_request_body()
    _Response = get_container().inject(UpdateCategoryHandler).handle(_Request, category_id)
    if _Response.not_found:
        return not_found("Category", category_id)
    if _Response.duplicate:
        return business_rule_violation(f"A category named '{_Request.name}' already exists.")
    return ok({"category_id": category_id})


# ───── Delete ────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteCategoryResponse:
    not_found: bool = False
    recipes_affected: int = 0


class DeleteCategoryHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, category_id: UUID) -> DeleteCategoryResponse:
        category: Category | None = self.repository.get(Category).by_id(category_id)
        if category is None:
            return DeleteCategoryResponse(not_found=True)
        affected = self.repository.get(Recipe).count(
            EntityField(Recipe, "_category_id").eq(category_id)
        )
        self.repository.remove(category)
        self.repository.save_changes()
        return DeleteCategoryResponse(recipes_affected=affected)


@CATEGORY_ROUTER.route("/<category_id>", methods=["DELETE"])
def delete_category(category_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteCategoryHandler).handle(category_id)
    if _Response.not_found:
        return not_found("Category", category_id)
    _Logger.info(f"Deleted category {category_id}; {_Response.recipes_affected} recipe(s) nulled")
    return ok({"recipes_affected": _Response.recipes_affected})
