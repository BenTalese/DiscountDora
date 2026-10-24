"""Single source of truth for the current Dashy Dora version.

Kept in code (rather than reading from setup.py / pyproject.toml) so the
runtime doesn't need to import build tooling at request time, and so the
Dora assistant can return the version with zero I/O.

Bump when you cut a release. The frontend changelog page expects each
released version to have a matching `## [VERSION]` heading in CHANGELOG.md
at the repo root.
"""

CURRENT_VERSION = "0.7.0"

# The GitHub repository, as `owner/name`. One place (R-003): the Help page's
# update check, the "Report an issue" default and the dataset-import
# User-Agent all build their URLs from it. The repository was renamed from
# `DiscountDora` with the product; three call sites were carrying three
# different spellings, one of which (`DashyDora`) never existed, so the update
# check 404'd on every install (finalisation 19-R3).
GITHUB_REPO = "BenTalese/dashy-dora"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
