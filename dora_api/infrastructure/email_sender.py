"""Transactional email sender used by A1's auth flows.

Wraps stdlib smtplib so dora_api can fire one-off transactional emails
(verification, password reset, change confirmation) self-contained.

SMTP config resolves through `resolved_operational_config()` (FU-333
Buckets B + C). The admin edits everything — including the password —
in Settings → Admin → System → Email; the password is Fernet-encrypted
at rest. Empty username still puts the sender in dry-run mode (logs
the body), which is essential for dev / desktop installs that don't
need real email.
"""
from __future__ import annotations

import logging
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


_DRY_RUN_CONFIG = _SmtpConfig(
    host="", port=587, username="", password="", sender="", use_tls=True, dry_run=True,
)


def _config() -> _SmtpConfig:
    """Read the resolved AppSetting-backed SMTP config. If the DB isn't
    available (e.g. a unit test that imports this module without a Flask
    context), return a dry-run config so callers still function as
    dry-run loggers."""
    from dora_api.features.app_settings.operational_config import \
        resolved_operational_config
    try:
        op = resolved_operational_config()
    except Exception:
        return _DRY_RUN_CONFIG
    host = op.smtp_host or "smtp.gmail.com"
    username = op.smtp_username
    sender = op.smtp_from or username
    return _SmtpConfig(
        host=host,
        port=op.smtp_port,
        username=username,
        password=op.smtp_password,
        sender=sender,
        use_tls=op.smtp_use_tls,
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
