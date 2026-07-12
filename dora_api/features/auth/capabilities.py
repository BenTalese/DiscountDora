"""GET /api/auth/capabilities — pre-auth capability probe.

Small unauthenticated surface the SPA reads to decide whether to render
optional entry points on the auth screens. Right now it exposes just one
flag: whether outbound email is actually going somewhere. Add more as
public-facing capabilities appear.

Why this exists: the reset-password flow always runs (204 on request,
dry-run logs the link when SMTP is unset) so anti-enumeration holds even
on installs with no email configured. But a regular user can't read the
server log, so the "Forgot password?" link is a dead end for them on a
fresh install. Gating it on this flag closes that gap.
"""
from dora_api.features.routers import AUTH_ROUTER
from dora_api.infrastructure.api_response import ok
from dora_api.infrastructure.email_sender import email_sender_configured


@AUTH_ROUTER.route("/capabilities", methods=["GET"])
def get_auth_capabilities():
    return ok({
        "email_sender_configured": email_sender_configured(),
    })
