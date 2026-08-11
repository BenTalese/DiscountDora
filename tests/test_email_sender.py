"""FU-520 item 3 (PROPOSAL_TEST_SUITE_IMPROVEMENTS §5.D) — send-path tests
for `dora_api.infrastructure.email_sender` with a fake SMTP transport.

Covers:
  - MIME assembly (multipart/alternative, headers, part order, utf-8),
  - the wire choreography (ehlo → starttls → ehlo → login → sendmail) and
    its config-driven branches (no TLS, no password),
  - dry-run mode (unconfigured SMTP → log, never touch the transport),
  - `_config()` mapping from `resolved_operational_config()` including the
    DB-unavailable → dry-run fallback,
  - error propagation to callers, and the `try_send` swallow-and-log wrapper
    the auth flows use,
  - the pure `_render_text_digest` seam of the alerts digest job (the HTML
    assembly in `_process_user` is DB-coupled — the e2e layer owns that).

No network: `smtplib.SMTP` is always replaced before `send_email` runs.
"""
from __future__ import annotations

import logging
import os
import ssl
import tempfile
from email import message_from_string
from types import SimpleNamespace

# Hazard guard (see tests/e2e/dora_api/conftest.py): parts of this module
# import `dora_api.app` transitively (auth_helpers, operational_config,
# send_alerts_digest), and the app resolves its DB connection string from
# the environment at import time. Point it at a throwaway temp path BEFORE
# any dora_api import so the developer's `.env` dev DB can never be
# touched. No test here ever opens a DB connection and startup()/seeding
# is never called.
os.environ["DORA_DB_PATH"] = os.path.join(
    tempfile.gettempdir(), "dora.email-tests.throwaway.db",
)

import pytest  # noqa: E402
import smtplib  # noqa: E402

from dora_api.features.alerts.send_alerts_digest import \
    _render_text_digest  # noqa: E402
from dora_api.features.app_settings import operational_config  # noqa: E402
from dora_api.infrastructure import email_sender  # noqa: E402
from dora_api.infrastructure.auth_helpers import try_send  # noqa: E402
from dora_api.infrastructure.email_sender import (_DRY_RUN_CONFIG,  # noqa: E402
                                                  _SmtpConfig, send_email)


# ── fakes / fixtures ────────────────────────────────────────────────────

def _configured(**overrides) -> _SmtpConfig:
    """A fully configured (non-dry-run) SMTP config; override per test."""
    values = dict(
        host="smtp.test.local", port=2525,
        username="dora@test.local", password="hunter2",
        sender="Dora <dora@test.local>",
        use_tls=True, dry_run=False,
    )
    values.update(overrides)
    return _SmtpConfig(**values)


def _install_fake_smtp(monkeypatch, *, sendmail_exc=None, init_exc=None):
    """Replace smtplib.SMTP (the symbol email_sender calls) with a recording
    double. Returns the list of instances created."""
    created: list = []

    class _FakeSMTP:
        def __init__(self, host, port):
            if init_exc is not None:
                raise init_exc
            self.host, self.port = host, port
            self.calls: list[tuple] = []
            self.exited = False
            created.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            self.exited = True
            return False

        def ehlo(self):
            self.calls.append(("ehlo",))

        def starttls(self, context=None):
            self.calls.append(("starttls", context))

        def login(self, username, password):
            self.calls.append(("login", username, password))

        def sendmail(self, from_addr, to_addrs, msg):
            if sendmail_exc is not None:
                raise sendmail_exc
            self.calls.append(("sendmail", from_addr, to_addrs, msg))

    monkeypatch.setattr(email_sender.smtplib, "SMTP", _FakeSMTP)
    return created


def _send_default(monkeypatch, cfg, **created_kwargs):
    """Arrange a config + fake transport, act with a representative send,
    and return the single fake SMTP instance."""
    monkeypatch.setattr(email_sender, "_config", lambda: cfg)
    created = _install_fake_smtp(monkeypatch, **created_kwargs)
    send_email(
        to="rcpt@example.com",
        subject="Verify your Dashy Dora account",
        html_body="<p>Hi ben, verify here.</p>",
        text_body="Hi ben, verify here.",
    )
    assert len(created) == 1
    return created[0]


# ── MIME assembly ───────────────────────────────────────────────────────

def test__send_email__configured_transport__sends_multipart_with_expected_headers(monkeypatch):
    server = _send_default(monkeypatch, _configured())

    (name, from_addr, to_addrs, raw) = server.calls[-1]
    assert name == "sendmail"
    assert from_addr == "Dora <dora@test.local>"
    assert to_addrs == ["rcpt@example.com"]

    message = message_from_string(raw)
    assert message["Subject"] == "Verify your Dashy Dora account"
    assert message["From"] == "Dora <dora@test.local>"
    assert message["To"] == "rcpt@example.com"
    # The brand banner rides along, so the top level is multipart/related
    # wrapping the alternative + the inline PNG.
    assert message.get_content_type() == "multipart/related"

    related = message.get_payload()
    assert [p.get_content_type() for p in related] == [
        "multipart/alternative", "image/png",
    ]

    parts = related[0].get_payload()
    # text/plain first, text/html last — MIME clients prefer the LAST
    # alternative they can render, so the HTML body must come second.
    assert [p.get_content_type() for p in parts] == ["text/plain", "text/html"]
    assert parts[0].get_payload(decode=True).decode("utf-8") == "Hi ben, verify here."
    assert parts[1].get_payload(decode=True).decode("utf-8") == "<p>Hi ben, verify here.</p>"
    assert parts[1].get_content_charset() == "utf-8"

    image = related[1]
    assert image["Content-ID"] == "<brand-banner>"
    assert image.get_content_disposition() == "inline"
    # Context-managed transport → connection closed after the send.
    assert server.exited is True


def test__send_email__no_text_body__attaches_html_part_only(monkeypatch):
    monkeypatch.setattr(email_sender, "_config", lambda: _configured())
    created = _install_fake_smtp(monkeypatch)

    send_email(to="rcpt@example.com", subject="s", html_body="<p>html only</p>")

    (_, _, _, raw) = created[0].calls[-1]
    related = message_from_string(raw).get_payload()
    assert [p.get_content_type() for p in related] == [
        "multipart/alternative", "image/png",
    ]
    assert [p.get_content_type() for p in related[0].get_payload()] == ["text/html"]


def test__send_email__banner_excluded__sends_bare_alternative(monkeypatch):
    monkeypatch.setattr(email_sender, "_config", lambda: _configured())
    created = _install_fake_smtp(monkeypatch)

    send_email(
        to="rcpt@example.com", subject="s", html_body="<p>x</p>",
        text_body="x", include_brand_banner=False,
    )

    message = message_from_string(created[0].calls[-1][3])
    assert message.get_content_type() == "multipart/alternative"
    assert [p.get_content_type() for p in message.get_payload()] == [
        "text/plain", "text/html",
    ]


# ── wire choreography / config-driven branches ──────────────────────────

def test__send_email__tls_enabled__starttls_with_ssl_context_before_login(monkeypatch):
    server = _send_default(monkeypatch, _configured(use_tls=True))

    names = [c[0] for c in server.calls]
    assert names == ["ehlo", "starttls", "ehlo", "login", "sendmail"]
    starttls_context = server.calls[1][1]
    assert isinstance(starttls_context, ssl.SSLContext)
    assert server.calls[3] == ("login", "dora@test.local", "hunter2")
    assert (server.host, server.port) == ("smtp.test.local", 2525)


def test__send_email__tls_disabled__never_calls_starttls(monkeypatch):
    server = _send_default(monkeypatch, _configured(use_tls=False))

    names = [c[0] for c in server.calls]
    assert names == ["ehlo", "login", "sendmail"]


def test__send_email__password_blank__skips_login_but_still_sends(monkeypatch):
    # username present → not dry-run; blank password → open relay, no AUTH.
    server = _send_default(monkeypatch, _configured(password=""))

    names = [c[0] for c in server.calls]
    assert "login" not in names
    assert names[-1] == "sendmail"


# ── dry-run mode ────────────────────────────────────────────────────────

def test__send_email__dry_run_config__logs_body_and_never_opens_transport(monkeypatch, caplog):
    monkeypatch.setattr(email_sender, "_config", lambda: _DRY_RUN_CONFIG)
    created = _install_fake_smtp(
        monkeypatch, init_exc=AssertionError("transport must not be constructed"),
    )

    with caplog.at_level(logging.INFO, logger="dora_api.infrastructure.email_sender"):
        send_email(
            to="rcpt@example.com",
            subject="Reset your Dashy Dora password",
            html_body="<p>reset</p>",
            text_body="plain reset body",
        )

    assert created == []  # constructor never ran (it would have raised)
    assert "DRY-RUN email" in caplog.text
    assert "rcpt@example.com" in caplog.text
    assert "Reset your Dashy Dora password" in caplog.text
    assert "plain reset body" in caplog.text  # text body preferred in the log


def test__send_email__dry_run_without_text_body__logs_html_body(monkeypatch, caplog):
    monkeypatch.setattr(email_sender, "_config", lambda: _DRY_RUN_CONFIG)
    _install_fake_smtp(monkeypatch, init_exc=AssertionError("no transport"))

    with caplog.at_level(logging.INFO, logger="dora_api.infrastructure.email_sender"):
        send_email(to="a@b.c", subject="s", html_body="<p>the html</p>")

    assert "<p>the html</p>" in caplog.text


# ── error propagation ───────────────────────────────────────────────────

def test__send_email__sendmail_raises__exception_propagates_to_caller(monkeypatch):
    monkeypatch.setattr(email_sender, "_config", lambda: _configured())
    _install_fake_smtp(
        monkeypatch,
        sendmail_exc=smtplib.SMTPDataError(554, b"rejected"),
    )

    with pytest.raises(smtplib.SMTPDataError):
        send_email(to="rcpt@example.com", subject="s", html_body="<p>x</p>")


def test__send_email__connect_fails__oserror_propagates_to_caller(monkeypatch):
    monkeypatch.setattr(email_sender, "_config", lambda: _configured())
    _install_fake_smtp(monkeypatch, init_exc=OSError("connection refused"))

    with pytest.raises(OSError):
        send_email(to="rcpt@example.com", subject="s", html_body="<p>x</p>")


def test__try_send__transport_failure__swallowed_and_warning_logged(monkeypatch, caplog):
    # The auth flows wrap send_email in try_send so a broken SMTP config
    # never fails (or enumerates) the originating request.
    monkeypatch.setattr(email_sender, "_config", lambda: _configured())
    _install_fake_smtp(monkeypatch, sendmail_exc=smtplib.SMTPException("boom"))

    with caplog.at_level(logging.WARNING, logger="dora_api.infrastructure.auth_helpers"):
        result = try_send(
            send_email, to="rcpt@example.com", subject="s", html_body="<p>x</p>",
        )

    assert result is None  # no exception escaped
    assert "auth email send failed" in caplog.text


# ── _config() mapping from resolved_operational_config() ────────────────

def _op_config(**overrides) -> SimpleNamespace:
    """Only the smtp_* fields `_config()` reads — shaped like
    OperationalConfig."""
    values = dict(
        smtp_host="mail.example.com", smtp_port=465,
        smtp_username="ops@example.com", smtp_password="s3cret",
        smtp_from="Dora <noreply@example.com>", smtp_use_tls=False,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _patch_resolver(monkeypatch, fn) -> None:
    monkeypatch.setattr(operational_config, "resolved_operational_config", fn)


def test__config__resolver_raises__falls_back_to_dry_run(monkeypatch):
    def _boom():
        raise RuntimeError("no DB / no app context")
    _patch_resolver(monkeypatch, _boom)

    cfg = email_sender._config()

    assert cfg is _DRY_RUN_CONFIG
    assert cfg.dry_run is True


def test__config__username_configured__maps_fields_and_disables_dry_run(monkeypatch):
    _patch_resolver(monkeypatch, lambda: _op_config())

    cfg = email_sender._config()

    assert cfg.dry_run is False
    assert cfg.host == "mail.example.com"
    assert cfg.port == 465
    assert cfg.username == "ops@example.com"
    assert cfg.password == "s3cret"
    assert cfg.sender == "Dora <noreply@example.com>"
    assert cfg.use_tls is False


def test__config__blank_host__defaults_to_gmail(monkeypatch):
    _patch_resolver(monkeypatch, lambda: _op_config(smtp_host=""))

    assert email_sender._config().host == "smtp.gmail.com"


def test__config__blank_from__sender_falls_back_to_username(monkeypatch):
    _patch_resolver(monkeypatch, lambda: _op_config(smtp_from=""))

    assert email_sender._config().sender == "ops@example.com"


def test__config__blank_username__forces_dry_run_even_with_host_set(monkeypatch):
    _patch_resolver(monkeypatch, lambda: _op_config(smtp_username=""))

    assert email_sender._config().dry_run is True


# ── alerts digest: the pure plain-text seam ─────────────────────────────

class _Alert:
    """Duck-typed AlertDto — _render_text_digest reads .message/.detail."""
    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail


def test__render_text_digest__actionable_and_fyi__renders_sections_with_counts(monkeypatch):
    # The digest builds its "Open alerts" link via spa_deep_link (hash-history
    # deep link — .../#/alerts), which reads public_base_url from auth_helpers;
    # patch it at that source.
    import dora_api.infrastructure.auth_helpers as auth_helpers
    monkeypatch.setattr(
        auth_helpers, "public_base_url", lambda: "https://dora.example",
    )

    text = _render_text_digest(
        "ben", "daily",
        actionable=[_Alert("Milk is out of stock", "Used by 3 meals")],
        fyi=[_Alert("Price drop on olive oil")],
    )

    lines = text.splitlines()
    assert lines[0] == "Hi ben,"
    assert "Your daily alerts digest:" in lines
    assert "NEEDS ACTION (1):" in lines
    assert "  - Milk is out of stock" in lines
    assert "      Used by 3 meals" in lines
    assert "HEADS-UP (1):" in lines
    assert "  - Price drop on olive oil" in lines
    assert "Open alerts: https://dora.example/#/alerts" in lines
    assert lines[-1] == "Manage your channels in Settings → Preferences."


def test__render_text_digest__no_fyi__omits_heads_up_section(monkeypatch):
    import dora_api.infrastructure.auth_helpers as auth_helpers
    monkeypatch.setattr(
        auth_helpers, "public_base_url", lambda: "https://dora.example",
    )

    text = _render_text_digest(
        "ben", "weekly",
        actionable=[_Alert("Bread expires tomorrow")],
        fyi=[],
    )

    assert "HEADS-UP" not in text
    assert "NEEDS ACTION (1):" in text
    assert "Your weekly alerts digest:" in text
