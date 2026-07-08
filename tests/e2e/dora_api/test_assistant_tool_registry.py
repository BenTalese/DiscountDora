"""FU-390 — AI-path assistant reliability.

The Dora AI path (SLM tool-calling in ``ask_assistant.py``) has a few
guarantees that must hold regardless of which model is wired up, and that a
model can't be trusted to enforce. We pin the *deterministic* ones here — no
live model, no network:

1. **Registry integrity.** Every tool the model is offered (``TOOL_SCHEMAS``)
   is actually dispatchable, data and action tools are disjoint, and every
   action tool has a schema. A drift here means the model calls a tool that
   either 500s or silently no-ops.
2. **The mutation gate.** Every action (mutating) tool is classified as an
   action — never a data tool — so ``ask_assistant`` short-circuits it into a
   *proposal* the user must confirm, and it can never be executed via
   ``run_tool``. This is the single most important safety property of an
   action-taking assistant (proposal §B.0); a regression that mislabels an
   action tool as data would let the model mutate the DB unprompted.
3. **Every action tool has a proposer.** The ``_propose_action`` dispatch
   covers every action tool (the bespoke add-to-list flow or a confirm card).
4. **Graceful degradation.** With no model configured, ``/assistant/ask``
   returns ``available=false`` (so the SPA falls back to Basic mode) rather
   than erroring.
"""
import pytest
import requests

from dora_api.features.assistant import confirm_actions, tools

BASE = "http://localhost:5170/api"


def _schema_names() -> list[str]:
    return [s["function"]["name"] for s in tools.TOOL_SCHEMAS]


def test__tool_registry__every_schema_is_dispatchable():
    """Each tool offered to the model resolves to exactly one executor path."""
    for name in _schema_names():
        is_data = tools.is_data_tool(name)
        is_action = tools.is_action_tool(name)
        assert is_data ^ is_action, (
            f"tool '{name}' must be exactly one of data/action "
            f"(data={is_data}, action={is_action})"
        )


def test__tool_registry__schema_names_are_unique():
    names = _schema_names()
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, f"duplicate tool schema names: {sorted(dupes)}"


def test__tool_registry__data_and_action_sets_are_disjoint():
    overlap = set(tools._TOOLS) & set(tools._ACTION_TOOLS)
    assert not overlap, f"tools classified as both data and action: {sorted(overlap)}"


def test__tool_registry__every_dispatch_target_has_a_schema():
    """No orphan executors — the model can only call what it's shown, so a
    dispatch entry with no schema is dead weight (and a sign of drift)."""
    schema_names = set(_schema_names())
    for name in set(tools._TOOLS) | set(tools._ACTION_TOOLS):
        assert name in schema_names, f"dispatchable tool '{name}' has no TOOL_SCHEMA"


def test__mutation_gate__action_tools_are_never_data_tools():
    """The gate that keeps the LLM from mutating data on its own."""
    for name in tools._ACTION_TOOLS:
        assert tools.is_action_tool(name) is True
        assert tools.is_data_tool(name) is False, (
            f"action tool '{name}' is mislabelled as a data tool — it could be "
            f"executed without user confirmation"
        )


def test__mutation_gate__run_tool_refuses_action_tools():
    """``run_tool`` is the read-only executor. Handing it an action tool must
    raise (KeyError) rather than mutate — actions only ever flow through the
    propose→confirm path."""
    for name in tools._ACTION_TOOLS:
        with pytest.raises(KeyError):
            tools.run_tool(name, {})


def test__mutation_gate__every_action_tool_has_a_proposer():
    """``_propose_action`` routes add-to-shopping-list to its bespoke flow and
    everything else through a confirm card. An action tool that matches
    neither would fall through to the fail-soft branch and silently do
    nothing — assert full coverage."""
    for name in tools._ACTION_TOOLS:
        covered = (name == tools.ADD_TO_SHOPPING_LIST) or confirm_actions.is_confirm_action(name)
        assert covered, f"action tool '{name}' has no proposer (add-flow or confirm card)"


def test__nav_for__never_offers_navigation_for_an_action_tool():
    """Post-answer navigation is a data-tool affordance; actions resolve via a
    confirm card, not a nav button."""
    for name in tools._ACTION_TOOLS:
        assert tools.nav_for(name) is None, f"action tool '{name}' should not carry a nav hint"


def test__assistant_ask__no_model_configured__degrades_to_unavailable(api):
    """The seed user has no LLM configured (llm_enabled defaults False), so the
    AI path must report unavailable + defer to local Basic mode — never 500."""
    resp = requests.post(f"{BASE}/assistant/ask", json={
        "message": "what's expiring soon?",
        "current_path": "/",
    })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["available"] is False, body
    assert body["defer_to_local"] is True, body
