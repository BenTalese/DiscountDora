"""Transactional email sender used by A1's auth flows.

Wraps stdlib smtplib so dora_api can fire one-off transactional emails
(verification, password reset, change confirmation) self-contained.

SMTP config resolves through `resolved_operational_config()`
(FU-333 Bucket B) — the admin edits it in Settings → Admin → System →
Email; the legacy `DORA_SMTP_*` env vars still work as a fallback
during the deprecation window. The `DORA_SMTP_PASSWORD` secret stays
env-only until Bucket C (encrypted-in-DB storage) lands.

Config fields consumed:
  smtp_host       (default: smtp.gmail.com — kept for parity with the env-only
                   pre-FU-333 default, applied here since the entity default is
                   the empty string)
  smtp_port       (default: 587)
  smtp_username   (required for real sends; empty ⇒ dry-run — the sender
                   just logs the body, handy for dev installs without SMTP)
  smtp_from       (default: same as USERNAME)
  smtp_use_tls    (default: True)

Dry-run mode is essential for the desktop / mobile deployment surfaces
that don't need transactional email at all — the verification link is
logged so a self-hosted user can copy-paste it.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "email_templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


@dataclass(slots=True)
class _SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_tls: bool
    dry_run: bool


def _config() -> _SmtpConfig:
    # FU-333 Bucket B — resolve host/port/username/from/use_tls through the
    # AppSetting-first resolver. Password stays env-only (Bucket C).
    from dora_api.features.app_settings.operational_config import \
        resolved_operational_config
    try:
        op = resolved_operational_config()
        host = op.smtp_host or "smtp.gmail.com"
        port = op.smtp_port
        username = op.smtp_username
        sender = op.smtp_from or username
        use_tls = op.smtp_use_tls
    except Exception:
        # Defensive: DB unavailable at boot / in a dry unit test — fall back
        # to env so the sender still functions as a dry-run logger.
        host = os.environ.get("DORA_SMTP_HOST", "smtp.gmail.com").strip()
        port = int(os.environ.get("DORA_SMTP_PORT", "587"))
        username = os.environ.get("DORA_SMTP_USERNAME", "").strip()
        sender = os.environ.get("DORA_SMTP_FROM", username).strip() or username
        use_tls = os.environ.get("DORA_SMTP_USE_TLS", "true").lower() != "false"
    return _SmtpConfig(
        host=host,
        port=port,
        username=username,
        password=os.environ.get("DORA_SMTP_PASSWORD", "").strip(),
        sender=sender,
        use_tls=use_tls,
        dry_run=not username,
    )


def render_template(name: str, **context: Any) -> str:
    """Render a Jinja template under dora_api/email_templates/."""
    template = _env.get_template(name)
    return template.render(**context)


def send_email(
    *,
    to: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> None:
    """Send a single email synchronously. Raises on SMTP failure;
    callers should wrap in `try_send` (auth_helpers) when delivery
    failure shouldn't propagate to the user.
    """
    log = logging.getLogger(__name__)
    cfg = _config()
    if cfg.dry_run:
        log.info(
            "DRY-RUN email | to=%s | subject=%s\n%s",
            to, subject, text_body or html_body,
        )
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = cfg.sender
    message["To"] = to
    if text_body:
        message.attach(MIMEText(text_body, "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP(cfg.host, cfg.port) as server:
        server.ehlo()
        if cfg.use_tls:
            server.starttls(context=context)
            server.ehlo()
        if cfg.username and cfg.password:
            server.login(cfg.username, cfg.password)
        server.sendmail(cfg.sender, [to], message.as_string())
    log.info("Sent transactional email to %s (%s)", to, subject)
