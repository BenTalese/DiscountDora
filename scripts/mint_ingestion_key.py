"""Mint an ingestion bearer key from the command line.

Run inside the running container from the repo root:

    docker compose exec -T dashy_dora python scripts/mint_ingestion_key.py --label companion

Prints **only the raw key** on stdout (everything else goes to stderr) so a
deploy script can capture it with `$(...)` and write it straight into a
producer's environment. The key is shown once here for the same reason the
admin page shows it once — only the SHA-256 hash is stored.

Why this exists: `POST /api/ingest` authenticates on a key an admin mints on
the Settings -> API access page. A deploy that wipes the DB (`WIPE_DB=true`)
destroys that key, so every redeploy silently broke the producer until someone
re-minted by hand. This is the same operation as the admin page's create
endpoint, driven from the shell instead of a browser.

`--label` is treated as an identity: any existing source carrying it is
revoked first, so repeated runs converge on exactly one live key per label
rather than accumulating dead rows. Labels stay producer-agnostic by
convention (the entity docstring's invisibility rule) — the caller picks it.

This is a second *door* onto the admin page's handlers, not a second
implementation of them (R-087 / R-003): it drives the same
`CreateIngestionSourceHandler` / `DeleteIngestionSourceHandler` the HTTP routes
do, so key generation, hashing and revocation can never drift between the two
entry points. The only thing it skips is the session-cookie admin gate, which
it replaces with the shell access needed to be inside the container at all.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dora_api.app import app, db  # noqa: E402
from dora_api.domain.entities.ingestion_source import (ALLOWED_TRUSTS,  # noqa: E402
                                                       TRUST_HIGH)
from dora_api.features.ingestion_sources.ingestion_source_admin import (  # noqa: E402
    CreateIngestionSourceHandler, CreateIngestionSourceRequest,
    DeleteIngestionSourceHandler, ListIngestionSourcesHandler)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository  # noqa: E402
from dora_api.persistence.table_mappings import configure_mappings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--label", default="companion",
        help="Label for the source. An existing source with this label is revoked first.",
    )
    parser.add_argument(
        "--trust", default=TRUST_HIGH, choices=list(ALLOWED_TRUSTS),
        help="Trust level recorded on the source (enforcement is deferred).",
    )
    args = parser.parse_args()

    label = args.label.strip()
    if not label:
        print("--label cannot be empty.", file=sys.stderr)
        return 2

    with app.app_context():
        configure_mappings(db)
        repository = SqlAlchemyRepository()

        existing = [
            source for source in ListIngestionSourcesHandler(repository).handle()
            if source.label == label
        ]
        revoke = DeleteIngestionSourceHandler(repository)
        for source in existing:
            revoke.handle(source.id)
        if existing:
            print(
                f"[mint] revoked {len(existing)} existing source(s) labelled {label!r}",
                file=sys.stderr,
            )

        response = CreateIngestionSourceHandler(repository).handle(
            CreateIngestionSourceRequest(label=label, trust=args.trust)
        )

        print(f"[mint] minted a new key for {label!r}", file=sys.stderr)
        print(response.key)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
