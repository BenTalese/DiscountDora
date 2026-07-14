"""Support channel — the one place Dora's "Report an issue" affordance points at.

FU-370 (implements PROPOSAL_SUPPORT_CHANNEL, adjusted). This is deliberately a
**hardcoded, commit-and-done switch**, NOT an admin `AppSetting`: Dashy Dora is a
one-person side project, and where support funnels is an author/build decision,
not per-household runtime config. Dropping the AppSetting + migration + admin
editor the proposal originally sketched keeps this Anti-creep and
single-maintainer-legible (a queue-you-can't-drain is worse than none — see the
proposal §2).

To change where support goes, edit the two constants below and commit:

  - GitHub issues repo / hosted form → set ``_DEFAULT_SUPPORT_URL`` (opens in a
    new tab). This is the proposal's recommended shape (Option A / B).
  - Email only                       → leave ``_DEFAULT_SUPPORT_URL`` blank and
    set ``_DEFAULT_SUPPORT_EMAIL`` (the button becomes a ``mailto:`` link).
  - Both set                         → the URL wins (a public log beats a private
    inbox); the client prefers ``url`` when present.
  - Both blank (default)             → **dormant**: no "Report an issue" button
    renders anywhere (matches the C-cross "gone, not greyed" R-014 posture). The
    plumbing ships inert until the operator fills this in.

R-030 out-of-scope by design (NOT a carve-out awaiting promotion): R-030 governs
install-wide *operational* config — the values a **household admin** would tweak
post-deploy through Settings → Admin → System. The support target is deliberately
NOT that: it is the *author's* channel, controlled only by whoever builds/deploys
the instance, and it **must never become an in-app admin setting** (explicit owner
directive, FU-370 / FU-558). A household admin editing where bug reports funnel is
a non-goal, not a missing feature — so this correctly lives as a build/deploy-time
value, not an ``AppSetting`` row. R-030's "public URL" example is about
admin-tweakable URLs; this one is off-limits to admins by intent, so it sits
outside R-030's scope rather than violating it.

R-005 (distribution posture): the env override
(``DORA_SUPPORT_URL`` / ``DORA_SUPPORT_EMAIL``) is a deploy-time operator affordance
(mirrors the FU-392 demo-mode env flags), NOT admin control — it lets a self-hoster
point at their own channel without editing tracked source. The committed constants
are the default; env wins when set.

Actually standing up the channel (create the public issues repo / form / alias,
draft the issue template, paste the URL here) is tracked separately — see the
FU that spun off this build.
"""
import os

# ── The switch — edit these and commit. Blank = dormant. ────────────────
# Example values (do NOT commit real ones until the channel exists):
#   _DEFAULT_SUPPORT_URL = "https://github.com/<you>/dashy-dora-issues/issues/new?template=bug_report.yml"
#   _DEFAULT_SUPPORT_EMAIL = "dora@example.com"
_DEFAULT_SUPPORT_URL: str = ""
_DEFAULT_SUPPORT_EMAIL: str = ""


def resolve_support_channel() -> dict[str, str]:
    """Return ``{"url": ..., "email": ...}`` for the ``/api/health`` support
    block. Env overrides the committed default (R-005); empty strings when
    unset. Both blank ⇒ the client treats the channel as absent and renders
    no report affordance.
    """
    url = (os.environ.get("DORA_SUPPORT_URL") or _DEFAULT_SUPPORT_URL).strip()
    email = (os.environ.get("DORA_SUPPORT_EMAIL") or _DEFAULT_SUPPORT_EMAIL).strip()
    return {"url": url, "email": email}
