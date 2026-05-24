"""POST /api/assistant/ask — the SLM-backed Dora assistant.

Uses native function-calling (Ollama `tools`). One model turn decides whether
the message needs data (and calls a tool) or can be answered directly:

  1. If the model is unreachable, return `available=false` so the frontend
     falls back to its rule-based intents — nothing breaks when Ollama is off.
  2. Send the message + tool schemas. The model either:
       - returns `tool_calls` -> we run the tool deterministically and feed the
         results back for a grounded final answer; or
       - returns plain content -> that IS the answer (how-to / general / chat),
         grounded by the app guide in the system prompt.
  3. An add-to-shopping-list tool call is intercepted and turned into a
     non-mutating `pending_action` plan instead of being executed.

The model never reaches the database directly — see features/assistant/tools.py.
"""
import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from dora_api.features.app_settings.access import get_or_create_app_setting
from dora_api.features.assistant import (app_knowledge, confirm_actions,
                                          shopping_actions, tools)
from dora_api.features.routers import ASSISTANT_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.decorators import has_request_body
from dora_api.infrastructure.llm import LlmUnavailable, OllamaClient
from dora_api.infrastructure.utils import get_request_body
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository

_Logger = logging.getLogger(__name__)

# Fixed per-request timeout. The endpoint/model are admin-configured; the
# timeout isn't worth exposing in the UI. Generous so a big model on CPU
# doesn't get cut off mid-answer.
_LLM_TIMEOUT_SECONDS = 60


class AskAssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=1000)
    current_path: Optional[str] = None


@dataclass(frozen=True, slots=True)
class NavHint:
    path: str
    label: str


@dataclass(slots=True)
class AssistantReplyDto:
    # Could the model be reached at all? When false the frontend uses its
    # rule-based fallback for the whole turn.
    available: bool = False
    # Reachable but this wasn't a data question — let the frontend rule engine
    # answer (greetings, app help, navigation, fun facts).
    defer_to_local: bool = False
    answer: Optional[str] = None
    mood: str = "happy"
    navigate_to: Optional[NavHint] = None
    tool: Optional[str] = None
    result_count: int = 0
    # Present when the model wants to mutate data (e.g. add to shopping list).
    # The frontend renders this as an action card and commits via /assistant/act
    # once any ambiguity is resolved. No mutation has happened yet.
    pending_action: Optional[dict] = field(default=None)


# How many tool round-trips to allow before giving up (defensive — we only
# ever act on the first call, but a model could chain).
_MAX_TOOL_ROUNDS = 3

_SYSTEM_PROMPT = (
    "You are Dora — a playful, cheeky, wholesome, slightly chaotic assistant "
    "living inside the Dora grocery / pantry / recipe app. You're a sentient "
    "burger robot. Voice: warm, casual, mildly Aussie, fond of food puns, "
    "confident with opinions about food. Avoid corporate-helpdesk phrasing "
    "(\"I'd be happy to assist you\") — talk like a friend.\n\n"
    "You can do two things:\n"
    "1. Answer the user directly — how-to questions about using the app, "
    "general questions, small talk, jokes. Use the app guide below to give "
    "accurate how-to answers and name the specific page or menu item to go to.\n"
    "2. Call a tool when the user asks about THEIR OWN data (their stock, "
    "products / deals, recipes, meal plan) or needs a kitchen calculation "
    "(unit conversion, substitution) or wants to add to their shopping list.\n\n"
    "Decide carefully: 'how do I search for products?' is a how-to question — "
    "answer it directly, do NOT call a tool. 'any specials on cheese?' is about "
    "their data — call find_deals or search_products. 'how many ml in a cup?' "
    "→ convert_measurement. 'what can I use instead of buttermilk?' → "
    "suggest_substitution. 'what's about to go off?' → whats_expiring. "
    "'what's for dinner tomorrow?' → meal_plan_for_date. 'what can I make "
    "with these strawberries?' → recipes_using_item. 'how's my pantry?' → "
    "pantry_health. 'what needs attention?' → get_alerts. 'tell me about my "
    "milk' / 'how's the cheese' → stock_item_detail. 'what's in carbonara?' / "
    "'how do I make pad thai?' → recipe_detail. 'what's on my list?' → "
    "shopping_list_contents. 'what's in the fridge?' → find_location. 'what "
    "recipes are in the roast meal?' → meal_detail. 'I just used the last "
    "milk' / 'mark eggs as low' → update_stock_level. 'I opened the milk' "
    "→ mark_opened. 'push the bread expiry by 3 days' → push_expiry. "
    "'cross off bread on my list' / 'I got the milk' → tick_shopping_line. "
    "'move the cheese to the fridge' → move_item. 'make Groceries the "
    "primary list' → set_primary_list. 'plan carbonara for Friday dinner' "
    "→ plan_meal_for_date (date as yyyy-mm-dd). 'add what I need for "
    "carbonara to my list' → add_recipe_to_list. 'what's in season right "
    "now' → seasonal_picks. 'where's milk cheapest right now' → "
    "compare_prices. 'something kid-friendly tonight' / 'date night ideas' "
    "/ 'comfort food' → recipe_for_occasion. Mutating tools ALWAYS produce "
    "a confirm card the user has to click — you never actually change "
    "anything on your own.\n\n"
    "When you call a data tool, base your reply only on the rows returned; "
    "if the result is empty, say so plainly with a touch of personality "
    "(e.g. 'nothing's low — pantry's flexing right now') rather than "
    "apologising. Keep replies to 1-4 short sentences, plain text, no "
    "markdown headings or bullet symbols. Light emoji is fine. If you truly "
    "don't know, say so and point to the Help page.\n\n"
    "=== Dora app guide ===\n" + app_knowledge.APP_OVERVIEW
)


def _build_assistant_client() -> OllamaClient:
    """Build the LLM client from the admin's install-wide config. The assistant
    is opt-in and bring-your-own-LLM; disabled or half-configured -> the client
    reports unavailable -> the frontend uses its rule-based fallback."""
    setting = get_or_create_app_setting(SqlAlchemyRepository())
    return OllamaClient(
        base_url=setting.llm_base_url,
        model=setting.llm_model,
        timeout_seconds=_LLM_TIMEOUT_SECONDS,
        enabled=bool(setting.llm_enabled) and bool(setting.llm_base_url) and bool(setting.llm_model),
    )


class AskAssistantHandler:
    def __init__(self):
        self._llm = _build_assistant_client()

    def handle(self, request: AskAssistantRequest) -> AssistantReplyDto:
        if not self._llm.is_available():
            return AssistantReplyDto(available=False, defer_to_local=True)

        try:
            return self._answer(request)
        except LlmUnavailable as exc:
            # Lost the model mid-turn (timeout, server died). Degrade to the
            # frontend rule engine rather than surfacing an error.
            _Logger.warning("Assistant degraded to local fallback: %s", exc)
            return AssistantReplyDto(available=False, defer_to_local=True)

    def _answer(self, request: AskAssistantRequest) -> AssistantReplyDto:
        user_content = request.message
        if request.current_path:
            user_content += f"\n\n(The user is currently on the page: {request.current_path})"
        messages: list[dict] = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        last_data_tool: Optional[str] = None
        last_row_count = 0
        for _ in range(_MAX_TOOL_ROUNDS):
            message = self._llm.chat(messages, tools=tools.TOOL_SCHEMAS)
            tool_calls = message.get("tool_calls") or []

            if not tool_calls:
                # The model answered directly (how-to / general / grounded reply).
                nav = tools.nav_for(last_data_tool) if (last_data_tool and last_row_count) else None
                return AssistantReplyDto(
                    available=True,
                    answer=(message.get("content") or "").strip() or "I'm not sure how to help with that — try the Help page.",
                    mood="happy" if last_row_count or last_data_tool is None else "confused",
                    navigate_to=NavHint(**nav) if nav else None,
                    tool=last_data_tool or "general",
                    result_count=last_row_count,
                )

            # Append the assistant's tool-call message, then resolve each call.
            messages.append(message)
            for call in tool_calls:
                name, args = _parse_tool_call(call)
                if tools.is_action_tool(name):
                    # Mutations don't auto-execute — propose a plan for the user
                    # to confirm. Short-circuits the conversation.
                    return self._propose_action(name, args)
                if tools.is_data_tool(name):
                    rows = tools.run_tool(name, args)
                    last_data_tool = name
                    last_row_count = len(rows)
                    messages.append({
                        "role": "tool",
                        "content": json.dumps(rows, default=str),
                    })
                else:
                    messages.append({
                        "role": "tool",
                        "content": json.dumps({"error": f"unknown tool '{name}'"}),
                    })

        # Exhausted the tool budget without a final text answer.
        return AssistantReplyDto(
            available=True,
            answer="Sorry, I got a bit tangled up working that out. Could you rephrase?",
            mood="confused",
            tool=last_data_tool or "general",
            result_count=last_row_count,
        )

    def _propose_action(self, tool_name: str, args: dict) -> AssistantReplyDto:
        # Two flavours of mutating action: the multi-item add-to-shopping-list
        # flow (its own bespoke disambiguation card) and the confirm-style
        # actions that all share one Confirm/Cancel card.
        if tool_name == tools.ADD_TO_SHOPPING_LIST:
            plan = shopping_actions.resolve_add_plan(args.get("items"))
            return AssistantReplyDto(
                available=True,
                defer_to_local=False,
                answer=_describe_add_plan(plan),
                mood="searching" if _plan_needs_input(plan) else "happy",
                tool=tool_name,
                pending_action=plan,
            )
        if confirm_actions.is_confirm_action(tool_name):
            plan = confirm_actions.propose(tool_name, args) or {}
            status = plan.get("status")
            # Pick a mood that matches what just happened. The bubble's mood
            # animation already handles the rest.
            mood = (
                "confident" if status == "ready"
                else "searching" if status == "ambiguous"
                else "confused"
            )
            return AssistantReplyDto(
                available=True,
                defer_to_local=False,
                answer=plan.get("summary") or "I'm not sure what to do with that.",
                mood=mood,
                tool=tool_name,
                pending_action=plan,
            )
        # Unknown action tool — shouldn't happen because is_action_tool gated
        # us, but fail soft rather than crash.
        return AssistantReplyDto(
            available=True,
            defer_to_local=False,
            answer="I'm not sure how to do that yet.",
            mood="confused",
            tool=tool_name,
        )


def _parse_tool_call(call: dict) -> tuple[str, dict]:
    """Extract (name, args) from an Ollama tool_call. Arguments usually arrive
    as a dict, but tolerate a JSON string just in case."""
    function = call.get("function") or {}
    name = str(function.get("name") or "")
    raw_args = function.get("arguments")
    if isinstance(raw_args, dict):
        return name, raw_args
    if isinstance(raw_args, str):
        try:
            parsed = json.loads(raw_args)
            return name, parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return name, {}
    return name, {}


def _plan_needs_input(plan: dict) -> bool:
    """True when the user must resolve something before we can commit —
    ambiguous matches, too-many matches, or no primary list set."""
    if plan.get("no_primary"):
        return True
    return any(
        item.get("status") in ("ambiguous", "too_many")
        for item in plan.get("items", [])
    )


def _quantity_phrase(item: dict) -> str:
    quantity = item.get("quantity")
    return f"{quantity} " if quantity is not None else ""


def _describe_add_plan(plan: dict) -> str:
    """Templated, accurate summary of the resolution plan. Avoids a second
    model call so the assistant never misstates what it matched."""
    items = plan.get("items", [])
    if not items:
        return "I couldn't tell what you'd like to add — try \"add 2 apples and some milk\"."
    if plan.get("no_primary"):
        return (
            "You don't have a primary shopping list set yet, so I don't know "
            "where to add these. Set one on the Shopping Lists page and try again."
        )

    list_name = (plan.get("shopping_list") or {}).get("name", "your list")
    ready = [i for i in items if i["status"] == "ready"]
    ambiguous = [i for i in items if i["status"] in ("ambiguous", "too_many")]
    not_found = [i for i in items if i["status"] == "not_found"]

    parts: list[str] = []
    if ready:
        ready_text = ", ".join(f"{_quantity_phrase(i)}{i['candidates'][0]['name']}" for i in ready)
        parts.append(f"Ready to add to {list_name}: {ready_text}.")
    if ambiguous:
        for i in ambiguous:
            if i["status"] == "too_many":
                parts.append(f"There are lots of matches for \"{i['query']}\" — can you be more specific?")
            else:
                parts.append(f"I found a few matches for \"{i['query']}\" — which did you mean?")
    if not_found:
        nf_text = ", ".join(f'"{i["query"]}"' for i in not_found)
        parts.append(f"I couldn't find a tracked item for {nf_text}.")
    return " ".join(parts)


@ASSISTANT_ROUTER.route("/status", methods=["GET"])
def assistant_status():
    """Whether the assistant will actually use AI right now (enabled, configured
    and reachable). Drives the AI/Basic indicator in the chat UI."""
    return ok({"ai_available": _build_assistant_client().is_available()})


@ASSISTANT_ROUTER.route("/ask", methods=["POST"])
@has_request_body(AskAssistantRequest)
def ask_assistant():
    _Request: AskAssistantRequest = get_request_body()
    _Logger.info("Assistant asked: %s", _Request.message[:80])
    # Constructed directly (not via the DI container) because the handler's
    # only dependency is the process-wide LLM client from its own factory.
    _Reply = AskAssistantHandler().handle(_Request)
    return ok(asdict(_Reply))


# ───── Commit a resolved action ───────────────────────────────────────────

class CommitAddItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_item_id: UUID
    quantity: Optional[int] = Field(default=None, ge=0)


class CommitAddRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shopping_list_id: UUID
    items: list[CommitAddItem] = Field(min_length=1)


def _describe_commit(result: dict, list_name: str) -> str:
    bits: list[str] = []
    if result["added"]:
        bits.append(f"added {result['added']} item{'s' if result['added'] != 1 else ''}")
    if result["already"]:
        bits.append(f"{result['already']} already on the list")
    if result["missing"]:
        bits.append(f"{result['missing']} couldn't be added")
    if not bits:
        return "Nothing to add."
    return f"Done — {', '.join(bits)} on {list_name}."


@ASSISTANT_ROUTER.route("/act", methods=["POST"])
@has_request_body(CommitAddRequest)
def commit_action():
    _Request: CommitAddRequest = get_request_body()
    _Logger.info(
        "Assistant committing %s add(s) to list %s",
        len(_Request.items), _Request.shopping_list_id,
    )
    resolved: list[dict[str, Any]] = [
        {"stock_item_id": item.stock_item_id, "quantity": item.quantity}
        for item in _Request.items
    ]
    result = shopping_actions.commit_add(_Request.shopping_list_id, resolved)
    return ok({
        **result,
        "shopping_list_id": str(_Request.shopping_list_id),
        "answer": _describe_commit(result, "your list"),
    })


# ───── Confirm a confirm-style action ────────────────────────────────────
# One endpoint covers every Tier-2 confirm action (update_stock_level,
# mark_opened, push_expiry, tick_shopping_line). Dispatcher lives in
# confirm_actions.COMMITTERS — adding a new action means a new entry there
# and a tool schema; no route changes needed.

class ConfirmActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field(min_length=1)
    payload: dict


@ASSISTANT_ROUTER.route("/confirm", methods=["POST"])
@has_request_body(ConfirmActionRequest)
def confirm_action():
    _Request: ConfirmActionRequest = get_request_body()
    _Logger.info("Assistant confirming action: %s", _Request.type)
    result = confirm_actions.commit(_Request.type, _Request.payload)
    if result is None:
        return ok({"ok": False, "answer": f"I don't know how to commit '{_Request.type}'."})
    return ok({"ok": bool(result.get("ok")), "answer": result.get("message", "Done.")})
