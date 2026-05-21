"""Single source of truth for the current Discount Dora version.

Kept in code (rather than reading from setup.py / pyproject.toml) so the
runtime doesn't need to import build tooling at request time, and so the
Dora assistant can return the version with zero I/O.

Bump when you cut a release. The frontend changelog page expects each
released version to have a matching `## [VERSION]` heading in CHANGELOG.md
at the repo root.
"""

CURRENT_VERSION = "0.7.0"
