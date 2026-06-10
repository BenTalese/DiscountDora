"""POST /api/recipes/import-from-url — parse a recipe-bearing web page.

Most recipe sites publish their content as schema.org/Recipe JSON-LD inside
a `<script type="application/ld+json">` block. We fetch the page, parse any
JSON-LD we find, look for the Recipe object (it might be at the top level
or nested in an @graph), and convert it into the same shape our editor uses.

Stock items get fuzzy-matched against the user's tracked items by name so
the editor can pre-fill the picker; unmatched ingredients come back with
the raw recipe-site text so the user can deal with them on save (either
pick an existing item or create a new one inline).

We *don't* persist anything here — this is a pure read-and-translate step
so the import can be reviewed before it lands. Saving still goes through
`POST /api/recipes`.
"""
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional
from uuid import UUID

import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import process as fuzz_process
from pydantic import BaseModel, ConfigDict, Field

from dora_api.domain.entities.category import Category
from dora_api.domain.entities.cuisine import Cuisine
from dora_api.domain.entities.stock_item import StockItem
from dora_api.features.routers import RECIPE_ROUTER
from dora_api.infrastructure.api_response import business_rule_violation, ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.utils import get_container, get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository


_LOGGER = logging.getLogger(__name__)

# Polite-ish defaults. Recipe sites tend to be picky about UAs that look
# like bots; pretending to be a current Chrome on macOS sidesteps the
# easiest fingerprint checks without being deceptive about purpose
# (paired with the Referer below most sites are happy).
_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36 DiscountDora-RecipeImporter/0.1"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.8",
}
_FETCH_TIMEOUT = 10  # seconds — we're a foreground UX, not a crawler.
# Hard cap so a misbehaving site can't OOM us. ~3MB is well past the
# largest legit recipe HTML I've seen.
_MAX_BYTES = 3 * 1024 * 1024
_MIN_MATCH_SCORE = 70  # 0-100; fuzzywuzzy default-ish threshold.


# ─── Request / response ──────────────────────────────────────────────


class ImportFromUrlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length = 1, max_length = 2048)


@dataclass(frozen=True, slots=True)
class ImportedIngredientDto:
    raw_text: str
    # Best-guess stock item match; null when nothing tracked is close enough.
    stock_item_id: UUID | None
    stock_item_name: str | None
    match_score: int  # 0-100; ignored when stock_item_id is null.
    quantity: float | None
    unit: str | None
    notes: str | None


@dataclass(frozen=True, slots=True)
class ImportedStepDto:
    """C-4 Chunk 6 — one parsed schema.org/Recipe step (or sub-step) for the
    import preview. `client_id` is server-assigned (a uuid4) so the SPA can
    feed it straight into the create endpoint's `steps[].client_id` /
    `parent_client_id` plumbing without re-keying."""
    client_id: str
    parent_client_id: str | None
    sequence: int
    text: str
    hint: str | None


@dataclass(frozen=True, slots=True)
class ImportedRecipeDto:
    name: str
    # C-4 Chunk 2: cuisine/category are FK vocabularies. The importer is a
    # no-persist preview, so it returns the scraped *name* (for display) plus
    # a resolved *id* when an existing vocab row matches by name. The id is
    # null when the scraped value has no match — the user picks/creates one
    # in the editor on save. No vocab rows are created here.
    cuisine_id: UUID | None
    cuisine_name: str | None
    category_id: UUID | None
    category_name: str | None
    difficulty: str | None
    servings: int | None
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    instructions: str | None
    nutrition: str | None
    source_url: str
    ingredients: List[ImportedIngredientDto] = field(default_factory=list)
    # C-4 Chunk 6 — structured steps parsed from schema.org/Recipe
    # HowToStep / HowToSection nodes. Empty when the source uses a plain
    # string for `recipeInstructions`; the freeform `instructions` field
    # above stays populated as the fallback.
    steps: List[ImportedStepDto] = field(default_factory=list)
    # C-4 Chunk 7 — true when the source page didn't publish a parseable
    # schema.org/Recipe object and we fell back to scraping `<title>`,
    # `og:image`, and the body text. The SPA shows a "couldn't auto-
    # structure; review and edit" banner when this is set.
    is_degraded: bool = False


# ─── ISO 8601 duration → minutes ─────────────────────────────────────


_ISO_DURATION = re.compile(
    r"^P(?:T)?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$",
    re.IGNORECASE,
)


def _minutes_from_iso8601(value: Any) -> int | None:
    """Turn 'PT1H30M' into 90. Returns None if unparseable."""
    if not isinstance(value, str):
        return None
    match = _ISO_DURATION.match(value.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    total = hours * 60 + minutes + (1 if seconds >= 30 else 0)
    return total if total > 0 else None


# ─── JSON-LD scraping ────────────────────────────────────────────────


def _iter_recipe_objects(payload: Any):
    """Walk a JSON-LD payload yielding any node whose @type includes Recipe.

    The shape varies wildly: a single object, an array, or an @graph
    wrapper. Recipe might be the top-level type, or buried alongside
    Article/WebPage entries.
    """
    if isinstance(payload, list):
        for item in payload:
            yield from _iter_recipe_objects(item)
        return
    if not isinstance(payload, dict):
        return
    types = payload.get("@type")
    is_recipe = (
        types == "Recipe"
        or (isinstance(types, list) and "Recipe" in types)
    )
    if is_recipe:
        yield payload
    # Recurse — @graph commonly contains the actual Recipe.
    for value in payload.values():
        if isinstance(value, (dict, list)):
            yield from _iter_recipe_objects(value)


def _degraded_import(html: str, url: str) -> "ImportedRecipeDto":
    """Best-effort scrape when no schema.org/Recipe JSON-LD is found.

    Pull `<title>` (or `og:title`), the `og:image` URL into the freeform
    notes, and the body text into `instructions` so the user has something
    to edit. Caller marks the resulting DTO with `is_degraded=True` so the
    SPA can show a "we couldn't auto-structure this" banner; without that
    flag, this returns the same shape as a successful parse.
    """
    soup = BeautifulSoup(html, "html.parser")
    # Prefer og:title (curator-set), fall back to <title> tag.
    name = None
    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        name = og_title["content"].strip() or None
    if not name:
        title_tag = soup.find("title")
        if title_tag and title_tag.text:
            name = title_tag.text.strip() or None
    name = name or "Imported recipe"

    # Drop scripts/styles before extracting text so we don't dump CSS into
    # the instructions blob.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    body_text = soup.get_text("\n", strip=True)
    # Cap so the editor isn't drowned by a 10k-word blog post.
    if len(body_text) > 6000:
        body_text = body_text[:6000] + "\n\n…(truncated; trim what isn't a recipe)"

    return ImportedRecipeDto(
        name=name,
        cuisine_id=None,
        cuisine_name=None,
        category_id=None,
        category_name=None,
        difficulty=None,
        servings=None,
        prep_time_minutes=None,
        cook_time_minutes=None,
        instructions=body_text or None,
        nutrition=None,
        source_url=url,
        ingredients=[],
        steps=[],
        is_degraded=True,
    )


def _first_recipe_from_html(html: str) -> dict | None:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        text = script.string or script.get_text()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            # Some sites embed multiple JSON objects back-to-back which
            # json.loads rejects. Try the slower line-by-line fallback.
            try:
                payload = json.loads(text.strip().split("\n", 1)[0])
            except json.JSONDecodeError:
                continue
        for recipe in _iter_recipe_objects(payload):
            return recipe
    return None


# ─── Ingredient text → quantity/unit/notes ───────────────────────────


# Greedy "1 1/2 cups" / "1.5 tbsp" / "2-3 cloves of garlic" parser. We
# accept a permissive grammar because recipe sites are wildly inconsistent
# and we'd rather hand the user *something* than refuse to parse.
_QTY_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<qty>
        \d+\s*\/\s*\d+              # 1/2
      | \d+(?:\.\d+)?\s+\d+\s*\/\s*\d+   # 1 1/2
      | \d+(?:\.\d+)?              # 1.5
    )?
    \s*
    (?P<unit>
        cups?|tbsps?|tsps?|tablespoons?|teaspoons?|
        g|kg|ml|l|oz|lb|lbs|cloves?|cans?|pinch|slices?|
        sprigs?|bunch(?:es)?|knob|stick|pieces?
    )?
    \s*
    (?P<rest>.*)
    $
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _parse_qty_unit(raw: str) -> tuple[float | None, str | None, str]:
    """Return (quantity, unit, remainder). Remainder is the readable name."""
    text = raw.strip()
    match = _QTY_PATTERN.match(text)
    if not match:
        return None, None, text
    qty_str = (match.group("qty") or "").strip()
    unit = match.group("unit")
    rest = (match.group("rest") or "").strip(" ,.-")
    quantity: float | None = None
    if qty_str:
        try:
            if " " in qty_str:  # "1 1/2" mixed form
                whole, frac = qty_str.split(" ", 1)
                num, den = frac.split("/", 1)
                quantity = float(whole) + (float(num) / float(den))
            elif "/" in qty_str:
                num, den = qty_str.split("/", 1)
                quantity = float(num) / float(den)
            else:
                quantity = float(qty_str)
        except (ValueError, ZeroDivisionError):
            quantity = None
    return quantity, unit, rest or text


# ─── Handler ─────────────────────────────────────────────────────────


class ImportRecipeFromUrlHandler:
    def __init__(self):
        self.repository = SqlAlchemyRepository()

    def handle(self, url: str) -> ImportedRecipeDto | None:
        try:
            response = requests.get(
                url,
                headers=_FETCH_HEADERS,
                timeout=_FETCH_TIMEOUT,
                allow_redirects=True,
                stream=True,
            )
            response.raise_for_status()
            # Read with a hard byte cap so a malicious server can't stream
            # us into OOM.
            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_content(8192):
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_BYTES:
                    _LOGGER.warning("Aborted import for %s: exceeded %d bytes", url, _MAX_BYTES)
                    return None
                chunks.append(chunk)
            html = b"".join(chunks).decode(
                response.encoding or "utf-8", errors="replace"
            )
        except requests.RequestException as exc:
            _LOGGER.info("Could not fetch %s: %s", url, exc)
            return None

        recipe = _first_recipe_from_html(html)
        if recipe is None:
            # C-4 Chunk 7 — graceful degradation. The site didn't ship a
            # JSON-LD Recipe object, but the user explicitly asked us to
            # import this URL — fail soft with best-effort scraping (title,
            # og:image, body text) and flag the DTO so the SPA shows a
            # banner. The user opts in to a noisier import rather than
            # getting blocked entirely.
            return _degraded_import(html, url)

        # Most fields are straightforward optional strings on schema.org/Recipe.
        name = _first_string(recipe.get("name")) or "Imported recipe"
        cuisine_name = _first_string(recipe.get("recipeCuisine"))
        category_name = _first_string(recipe.get("recipeCategory"))
        # Resolve scraped names against existing vocab rows (read-only; no
        # creation). Null id => no match, editor lets the user pick/create.
        cuisine_id = self._match_vocab(Cuisine, cuisine_name)
        category_id = self._match_vocab(Category, category_name)
        difficulty = None  # not in schema.org/Recipe
        servings = _parse_servings(recipe.get("recipeYield"))
        prep = _minutes_from_iso8601(recipe.get("prepTime"))
        cook = _minutes_from_iso8601(recipe.get("cookTime"))
        raw_instructions = recipe.get("recipeInstructions")
        instructions = _coerce_instructions(raw_instructions)
        steps = _coerce_structured_steps(raw_instructions)
        nutrition = _coerce_nutrition(recipe.get("nutrition"))

        # Stock items for fuzzy-match lookup. Load once; the match list is
        # the user's tracked-items namespace, not the full product catalog.
        stock_items: list[StockItem] = self.repository.get(StockItem).all()
        name_to_id: dict[str, UUID] = {s.name: s.id for s in stock_items}
        all_names = list(name_to_id.keys())

        ingredient_dtos: list[ImportedIngredientDto] = []
        for raw in recipe.get("recipeIngredient") or []:
            if not isinstance(raw, str):
                continue
            raw = raw.strip()
            if not raw:
                continue
            qty, unit, remainder = _parse_qty_unit(raw)
            match_id: UUID | None = None
            match_name: str | None = None
            match_score = 0
            if all_names and remainder:
                # `extractOne` returns (best_name, score) or None.
                result = fuzz_process.extractOne(remainder, all_names)
                if result is not None:
                    candidate, score = result[0], int(result[1])
                    if score >= _MIN_MATCH_SCORE:
                        match_id = name_to_id[candidate]
                        match_name = candidate
                        match_score = score
            ingredient_dtos.append(ImportedIngredientDto(
                raw_text = raw,
                stock_item_id = match_id,
                stock_item_name = match_name,
                match_score = match_score,
                quantity = qty,
                unit = unit,
                notes = None,
            ))

        return ImportedRecipeDto(
            name = name,
            cuisine_id = cuisine_id,
            cuisine_name = cuisine_name,
            category_id = category_id,
            category_name = category_name,
            difficulty = difficulty,
            servings = servings,
            prep_time_minutes = prep,
            cook_time_minutes = cook,
            instructions = instructions,
            nutrition = nutrition,
            source_url = url,
            ingredients = ingredient_dtos,
            steps = steps,
        )

    def _match_vocab(self, entity_type, name: str | None) -> UUID | None:
        """Case-insensitive lookup of an existing vocab row by name. Returns
        None on no match — the importer never creates vocab rows."""
        if not name:
            return None
        target = name.strip().lower()
        for row in self.repository.get(entity_type).all():
            if row.name.strip().lower() == target:
                return row.id
        return None


def _first_string(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, list) and value:
        return _first_string(value[0])
    if isinstance(value, dict):
        # Sometimes wrapped: {"@type": "Text", "value": "..."}
        for key in ("name", "value", "@value"):
            sub = _first_string(value.get(key))
            if sub:
                return sub
    return None


def _parse_servings(value: Any) -> int | None:
    text = _first_string(value)
    if text is None:
        return None
    match = re.search(r"\d+", text)
    if not match:
        return None
    try:
        n = int(match.group(0))
        return n if n > 0 else None
    except ValueError:
        return None


def _coerce_instructions(value: Any) -> str | None:
    """Recipe instructions come in three shapes: a single string, a list of
    strings, or a list of HowToStep objects. Flatten to a newline-joined
    string suitable for the existing textarea."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item.strip())
            elif isinstance(item, dict):
                text = _first_string(item.get("text")) or _first_string(item.get("name"))
                if text:
                    parts.append(text)
        joined = "\n".join(p for p in parts if p)
        return joined or None
    return None


def _coerce_structured_steps(value: Any) -> List["ImportedStepDto"]:
    """C-4 Chunk 6 — map schema.org `recipeInstructions` into structured
    `ImportedStepDto` rows. Empty list when the source provides only a
    string (the freeform `instructions` field is the fallback).

    Rules per JSON-LD shape:
    - `HowToStep` items become individual top-level steps.
    - `HowToSection` items become a top-level step (text = section name)
      whose `itemListElement` children become its sub-steps.
    - Plain strings inside a list become top-level steps each.
    - One flat string → no structured steps (no point in a single step).
    """
    import uuid as _uuid

    if value is None or isinstance(value, str):
        return []
    if not isinstance(value, list):
        return []

    steps: list[ImportedStepDto] = []
    top_seq = 0

    def _new_id() -> str:
        return str(_uuid.uuid4())

    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            steps.append(ImportedStepDto(
                client_id=_new_id(),
                parent_client_id=None,
                sequence=top_seq,
                text=text,
                hint=None,
            ))
            top_seq += 1
            continue
        if not isinstance(item, dict):
            continue
        types = item.get("@type")
        is_section = (
            types == "HowToSection"
            or (isinstance(types, list) and "HowToSection" in types)
        )
        if is_section:
            section_name = _first_string(item.get("name")) or "Section"
            parent_id = _new_id()
            steps.append(ImportedStepDto(
                client_id=parent_id,
                parent_client_id=None,
                sequence=top_seq,
                text=section_name,
                hint=None,
            ))
            top_seq += 1
            sub_seq = 0
            for child in item.get("itemListElement") or []:
                if isinstance(child, str):
                    child_text = child.strip()
                elif isinstance(child, dict):
                    child_text = (
                        _first_string(child.get("text"))
                        or _first_string(child.get("name"))
                    )
                else:
                    child_text = None
                if not child_text:
                    continue
                steps.append(ImportedStepDto(
                    client_id=_new_id(),
                    parent_client_id=parent_id,
                    sequence=sub_seq,
                    text=child_text,
                    hint=None,
                ))
                sub_seq += 1
            continue
        # Plain HowToStep or unknown object — treat the text/name as a top step.
        text = _first_string(item.get("text")) or _first_string(item.get("name"))
        if not text:
            continue
        steps.append(ImportedStepDto(
            client_id=_new_id(),
            parent_client_id=None,
            sequence=top_seq,
            text=text,
            hint=None,
        ))
        top_seq += 1

    return steps


def _coerce_nutrition(value: Any) -> str | None:
    """schema.org nutrition is a dict; render it as a compact freeform string."""
    if not isinstance(value, dict):
        return None
    fields = []
    for key in (
        "calories", "fatContent", "saturatedFatContent",
        "carbohydrateContent", "sugarContent", "proteinContent",
        "fiberContent", "sodiumContent",
    ):
        text = _first_string(value.get(key))
        if text:
            label = re.sub(r"Content$", "", key).replace("_", " ").title()
            fields.append(f"{label}: {text}")
    return " · ".join(fields) or None


@RECIPE_ROUTER.route("import-from-url", methods=["POST"])
@has_request_body(ImportFromUrlRequest)
def import_from_url():
    request_body: ImportFromUrlRequest = get_request_body()
    handler = get_container().inject(ImportRecipeFromUrlHandler)
    result = handler.handle(request_body.url)
    if result is None:
        return business_rule_violation(
            "Could not fetch or parse a recipe from that URL. "
            "The site might not publish structured recipe data."
        )
    _LOGGER.info(
        "Imported recipe '%s' from %s with %d ingredients",
        result.name, request_body.url, len(result.ingredients),
    )
    return ok(result)
