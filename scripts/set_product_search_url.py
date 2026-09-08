"""Set the install's Product Search URL from the command line.

Run inside the running container from the repo root:

    docker compose exec -T dashy_dora python scripts/set_product_search_url.py http://host:5175

This is the URL the "Product Search" nav entry opens; the entry stays hidden
while it is empty (`useProductSearchUrl.ts` + MainLayout). A deploy that wipes
the database clears it along with everything else, so without this the nav
entry silently disappears on every deploy and the address has to be
remembered and re-typed on the admin page.

Like `mint_ingestion_key.py`, this is a second *door* onto the admin page's
handler rather than a second implementation of it (R-087 / R-003): it drives
`UpdateAppSettingsHandler`, so the scheme validation and the write path stay
identical to the HTTP route's. Pass an empty string to clear the setting.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dora_api.app import app, db  # noqa: E402
from dora_api.features.app_settings.update_app_settings import (  # noqa: E402
    UpdateAppSettingsHandler, UpdateAppSettingsRequest)
from dora_api.persistence.sqlalchemy_repository import SqlAlchemyRepository  # noqa: E402
from dora_api.persistence.table_mappings import configure_mappings  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "url",
        help="Absolute http(s) URL, or an empty string to clear the setting.",
    )
    args = parser.parse_args()

    with app.app_context():
        configure_mappings(db)
        response = UpdateAppSettingsHandler(SqlAlchemyRepository()).handle(
            UpdateAppSettingsRequest(product_search_url=args.url)
        )

        if response.invalid_reason:
            print(f"[product-search-url] rejected: {response.invalid_reason}", file=sys.stderr)
            return 1

        stored = response.dto.product_search_url if response.dto else ""
        print(f"[product-search-url] set to {stored!r}" if stored
              else "[product-search-url] cleared")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
