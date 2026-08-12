"""FU-520 item 3 (PROPOSAL_TEST_SUITE_IMPROVEMENTS §5.D) — email template
rendering tests.

`email_sender.render_template` uses a plain module-level Jinja
`Environment` (FileSystemLoader over `dora_api/email_templates/`), so no
Flask app context or DB is needed — these are pure unit tests. Context
shapes are copied from the real call sites:

  - verify_email.html      → register_user.py / email_flows.py
                             (subject, username, verify_url)
  - reset_password.html    → email_flows.py forgot_password
                             (subject, username, reset_url)
  - password_changed.html  → email_flows.py reset_password /
                             change_password.py (subject, username)
  - alerts_digest.html     → send_alerts_digest.py _process_user
                             (subject, username, cadence, actionable,
                              fyi, alerts_url)

The digest's *HTML assembly* (subject line, actionable/fyi split) lives
inside the DB-coupled `_process_user`; the e2e layer owns that. Here we
render the template directly with call-site-shaped context.
"""
from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass

# Hazard guard (see tests/e2e/dora_api/conftest.py): make sure nothing a
# dora_api import chain touches can ever resolve to the developer's real
# dev DB from `.env`. Nothing in this module opens a DB — this is pure
# insurance, set before any dora_api import.
os.environ["DORA_DB_PATH"] = os.path.join(
    tempfile.gettempdir(), "dora.email-tests.throwaway.db",
)

from dora_api.infrastructure.email_sender import render_template  # noqa: E402


# ── helpers ─────────────────────────────────────────────────────────────

@dataclass
class _Alert:
    """Duck-typed stand-in for AlertDto — alerts_digest.html only reads
    `.message` and `.detail` (importing the real DTO would drag in the
    whole app import chain for no assertion value)."""
    message: str
    detail: str | None = None


_JINJA_RESIDUE = re.compile(r"\{\{|\}\}|\{%|%\}")


def _assert_fully_rendered(html: str) -> None:
    """No unrendered Jinja delimiters may survive into the sent email."""
    assert not _JINJA_RESIDUE.search(html), (
        f"unrendered Jinja residue in output: {_JINJA_RESIDUE.search(html).group()!r}"
    )


def _assert_layout_applied(html: str, subject: str) -> None:
    """Every content template extends _layout.html — doctype, <title> from
    the subject, the brand banner header, and the footer must all be there.
    The header is the inline banner image (mascot + Cute Dino wordmark),
    referenced via cid:brand-banner and carrying "Dashy Dora" alt text."""
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert f"<title>{subject}</title>" in html
    assert 'src="cid:brand-banner"' in html
    assert 'alt="Dashy Dora"' in html
    assert "your pantry at your fingertips" in html


# ── verify_email.html ───────────────────────────────────────────────────

def test__render_template__verify_email__interpolates_username_and_link():
    subject = "Verify your Dashy Dora account"
    verify_url = "https://dora.example/verify-email?token=tok-abc123"

    html = render_template(
        "verify_email.html",
        subject=subject, username="ben", verify_url=verify_url,
    )

    assert "Hi ben," in html
    # The link appears twice: styled button + paste-into-browser fallback.
    assert html.count(f'href="{verify_url}"') == 2
    assert "Verify email" in html
    assert "expires in 24 hours" in html
    _assert_layout_applied(html, subject)
    _assert_fully_rendered(html)


# ── reset_password.html ─────────────────────────────────────────────────

def test__render_template__reset_password__interpolates_username_and_link():
    subject = "Reset your Dashy Dora password"
    reset_url = "https://dora.example/reset-password?token=tok-r3set"

    html = render_template(
        "reset_password.html",
        subject=subject, username="ben", reset_url=reset_url,
    )

    assert "Hi ben," in html
    assert html.count(f'href="{reset_url}"') == 2  # button + fallback link
    assert "Reset Password" in html
    assert "There was a request to reset the password" in html
    assert "expires in 1 hour" in html
    # The "if you didn't ask for this" line was removed (owner feedback).
    assert "stays" not in html
    _assert_layout_applied(html, subject)
    _assert_fully_rendered(html)


# ── password_changed.html ───────────────────────────────────────────────

def test__render_template__password_changed__interpolates_username():
    subject = "Your Dashy Dora password was changed"

    html = render_template(
        "password_changed.html", subject=subject, username="ben",
    )

    assert "Hi ben," in html
    assert "password was just changed" in html
    assert "contact your install's admin" in html
    _assert_layout_applied(html, subject)
    _assert_fully_rendered(html)


# ── autoescaping (select_autoescape(["html"]) on the environment) ───────

def test__render_template__html_in_context_value__is_escaped_not_injected():
    hostile = "<script>alert(1)</script>"

    html = render_template(
        "password_changed.html",
        subject="Your Dashy Dora password was changed", username=hostile,
    )

    assert "<script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


# ── alerts_digest.html ──────────────────────────────────────────────────

def _digest_context(**overrides):
    """Context shaped exactly like send_alerts_digest._process_user builds."""
    ctx = dict(
        subject="Dashy Dora — 2 alerts need your attention",
        username="ben",
        cadence="daily",
        actionable=[
            _Alert("Milk is out of stock", "Used by 3 planned meals this week"),
            _Alert("Bread expires tomorrow"),
        ],
        fyi=[_Alert("Price drop on olive oil", "Now $7.50 at your store")],
        alerts_url="https://dora.example/alerts",
    )
    ctx.update(overrides)
    return ctx


def test__render_template__alerts_digest__renders_sections_with_counts_and_messages():
    html = render_template("alerts_digest.html", **_digest_context())

    assert "Hi ben," in html
    assert "Needs action (2)" in html
    assert "<strong>Milk is out of stock</strong>" in html
    assert "Used by 3 planned meals this week" in html
    assert "<strong>Bread expires tomorrow</strong>" in html
    assert "Heads-up (1)" in html
    assert "Price drop on olive oil" in html
    assert "Now $7.50 at your store" in html
    assert 'href="https://dora.example/alerts"' in html
    assert "Open Alerts" in html
    _assert_layout_applied(html, "Dashy Dora — 2 alerts need your attention")
    _assert_fully_rendered(html)


def test__render_template__alerts_digest__daily_cadence__labels_daily():
    html = render_template("alerts_digest.html", **_digest_context(cadence="daily"))

    assert "(your daily digest)" in html
    assert "(your weekly digest)" not in html


def test__render_template__alerts_digest__weekly_cadence__labels_weekly():
    html = render_template("alerts_digest.html", **_digest_context(cadence="weekly"))

    assert "(your weekly digest)" in html
    assert "(your daily digest)" not in html


def test__render_template__alerts_digest__empty_actionable__omits_needs_action_section():
    html = render_template("alerts_digest.html", **_digest_context(actionable=[]))

    assert "Needs action" not in html
    assert "Heads-up (1)" in html
    _assert_fully_rendered(html)


def test__render_template__alerts_digest__empty_fyi__omits_heads_up_section():
    html = render_template("alerts_digest.html", **_digest_context(fyi=[]))

    assert "Heads-up" not in html
    assert "Needs action (2)" in html
    _assert_fully_rendered(html)


def test__render_template__alerts_digest__alert_without_detail__renders_message_only():
    html = render_template(
        "alerts_digest.html",
        **_digest_context(
            actionable=[_Alert("Bread expires tomorrow", detail=None)], fyi=[],
        ),
    )

    assert "<strong>Bread expires tomorrow</strong>" in html
    # The detail <span> is guarded by `{% if alert.detail %}` — with no
    # detail there is exactly zero detail markup in the needs-action list.
    assert html.count("font-size:13px") == 1  # only the opt-out footer note
    assert "None" not in html
