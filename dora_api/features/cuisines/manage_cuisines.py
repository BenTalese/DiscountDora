"""Cuisine CRUD (C-4 Chunk 2) — the user-configurable recipe cuisine
vocabulary. Mirrors manage_stock_groups.py.

Endpoints:

  GET    /api/cuisines        — list all (with recipe counts), ordered
  POST   /api/cuisines        — create
  PATCH  /api/cuisines/<id>   — rename
  DELETE /api/cuisines/<id>   — delete (recipes' cuisine_id → NULL via the
                                FK's ON DELETE SET NULL)
"""
import logging
from dataclasses import dataclass
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.cuisine import Cuisine
from dora_api.domain.entities.recipe import Recipe
from dora_api.features.routers import CUISINE_ROUTER
from dora_api.infrastructure.api_response import (business_rule_violation,
                                                  created, not_found, ok)
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.field import EntityField
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


@dataclass(frozen=True, slots=True)
class CuisineDto:
    cuisine_id: UUID
    name: str
    sequence: int
    recipe_count: int


# ───── List ──────────────────────────────────────────────────────────────

class GetCuisinesHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self) -> List[CuisineDto]:
        cuisines: List[Cuisine] = self.repository.get(Cuisine).all()
        recipes = self.repository.get(Recipe).all()
        counts: dict[UUID, int] = {}
        for r in recipes:
            if r.cuisine is not None:
                counts[r.cuisine.id] = counts.get(r.cuisine.id, 0) + 1
        out = [
            CuisineDto(
                cuisine_id=c.id,
                name=c.name,
                sequence=c.sequence,
                recipe_count=counts.get(c.id, 0),
            )
            for c in cuisines
        ]
        out.sort(key=lambda c: (c.sequence, c.name.lower()))
        return out


@CUISINE_ROUTER.route("", methods=["GET"])
def get_cuisines():
    _Result = get_container().inject(GetCuisinesHandler).handle()
    return ok(_Result)


# ───── Create ────────────────────────────────────────────────────────────

class CreateCuisineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class CreateCuisineResponse:
    cuisine_id: UUID | None = None
    duplicate: bool = False


class CreateCuisineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: CreateCuisineRequest) -> CreateCuisineResponse:
        existing = self.repository.get(Cuisine).all()
        normalised = request.name.strip().lower()
        if any(c.name.strip().lower() == normalised for c in existing):
            return CreateCuisineResponse(duplicate=True)
        next_seq = max((c.sequence for c in existing), default=-1) + 1
        cuisine = Cuisine(name=request.name.strip(), sequence=next_seq)
        self.repository.add(cuisine)
        self.repository.save_changes()
        return CreateCuisineResponse(cuisine_id=cuisine.id)


@CUISINE_ROUTER.route("", methods=["POST"])
@has_request_body(CreateCuisineRequest)
def create_cuisine():
    _Logger = logging.getLogger(__name__)
    _Request: CreateCuisineRequest = get_request_body()
    _Response = get_container().inject(CreateCuisineHandler).handle(_Request)
    if _Response.duplicate:
        return business_rule_violation(f"A cuisine named '{_Request.name}' already exists.")
    _Logger.info(f"Created cuisine {_Response.cuisine_id} '{_Request.name}'")
    return created(
        _Response.cuisine_id,
        f"{CUISINE_ROUTER.name}.{get_cuisines.__name__}",
        "cuisine_id",
        body={"cuisine_id": _Response.cuisine_id},
    )


# ───── Rename ────────────────────────────────────────────────────────────

class UpdateCuisineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)


@dataclass(slots=True)
class UpdateCuisineResponse:
    not_found: bool = False
    duplicate: bool = False


class UpdateCuisineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, request: UpdateCuisineRequest, cuisine_id: UUID) -> UpdateCuisineResponse:
        cuisine: Cuisine | None = self.repository.get(Cuisine).by_id(cuisine_id)
        if cuisine is None:
            return UpdateCuisineResponse(not_found=True)
        target = request.name.strip()
        normalised = target.lower()
        for c in self.repository.get(Cuisine).all():
            if c.id != cuisine_id and c.name.strip().lower() == normalised:
                return UpdateCuisineResponse(duplicate=True)
        cuisine.name = target
        self.repository.save_changes()
        return UpdateCuisineResponse()


@CUISINE_ROUTER.route("/<cuisine_id>", methods=["PATCH"])
@has_request_body(UpdateCuisineRequest)
def update_cuisine(cuisine_id: UUID):
    _Request: UpdateCuisineRequest = get_request_body()
    _Response = get_container().inject(UpdateCuisineHandler).handle(_Request, cuisine_id)
    if _Response.not_found:
        return not_found("Cuisine", cuisine_id)
    if _Response.duplicate:
        return business_rule_violation(f"A cuisine named '{_Request.name}' already exists.")
    return ok({"cuisine_id": cuisine_id})


# ───── Delete ────────────────────────────────────────────────────────────

@dataclass(slots=True)
class DeleteCuisineResponse:
    not_found: bool = False
    recipes_affected: int = 0


class DeleteCuisineHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, cuisine_id: UUID) -> DeleteCuisineResponse:
        cuisine: Cuisine | None = self.repository.get(Cuisine).by_id(cuisine_id)
        if cuisine is None:
            return DeleteCuisineResponse(not_found=True)
        # FK ON DELETE SET NULL nulls the recipes' cuisine_id; pre-count for
        # the UI warning.
        affected = self.repository.get(Recipe).count(
            EntityField(Recipe, "_cuisine_id").eq(cuisine_id)
        )
        self.repository.remove(cuisine)
        self.repository.save_changes()
        return DeleteCuisineResponse(recipes_affected=affected)


@CUISINE_ROUTER.route("/<cuisine_id>", methods=["DELETE"])
def delete_cuisine(cuisine_id: UUID):
    _Logger = logging.getLogger(__name__)
    _Response = get_container().inject(DeleteCuisineHandler).handle(cuisine_id)
    if _Response.not_found:
        return not_found("Cuisine", cuisine_id)
    _Logger.info(f"Deleted cuisine {cuisine_id}; {_Response.recipes_affected} recipe(s) nulled")
    return ok({"recipes_affected": _Response.recipes_affected})
