"""D2 — one-time migration of legacy on-disk locations into the
config-driven layout.

Runs on merchant_api startup. Each migration is idempotent: if the
destination already has the file it stays put and the source is left
alone (operators may have intentionally repopulated it). Source files
get moved (not copied) so we don't leak duplicates onto disk.

What it covers:
  - Legacy `./.image_cache/` (repo-root product image cache that lived
    in the source tree) → `<CACHE_DIR>/images/`.
  - Bundled `aldi_products_by_category.json` (shipped under the
    provider module) → `<CACHE_DIR>/aldi_products_by_category.json`
    on first boot, so operators can curate the list without forking
    the codebase. The bundled copy stays in the repo as the seed.
"""
import logging
import shutil
from pathlib import Path

_Logger = logging.getLogger(__name__)


def migrate_legacy_image_cache(cache_root: Path) -> int:
    """Move repo-root `.image_cache/*` into `<cache_root>/images/`.
    Returns the count of files moved (0 if there was nothing to do).
    """
    legacy = Path.cwd() / ".image_cache"
    if not legacy.is_dir():
        return 0

    dest = cache_root / "images"
    dest.mkdir(parents=True, exist_ok=True)

    moved = 0
    for src in legacy.iterdir():
        if not src.is_file():
            continue
        target = dest / src.name
        if target.exists():
            # Destination wins — operator may have intentionally
            # populated it. Leave the legacy copy in place too so
            # nothing's silently destroyed.
            continue
        shutil.move(str(src), str(target))
        moved += 1

    if moved:
        _Logger.info(
            "Migrated %d image(s) from legacy .image_cache → %s", moved, dest,
        )
    # Best-effort directory cleanup. If the user still has files in
    # there (e.g. duplicates that we skipped above) leave the dir.
    try:
        legacy.rmdir()
    except OSError:
        pass
    return moved


def migrate_legacy_appsettings(target_path: Path) -> bool:
    """D3: appsettings.json moved from `./config/mapi.appsettings.json`
    (CWD-relative) to `<DATA_DIR>/config/`. Move it once."""
    legacy = Path.cwd() / "config" / "mapi.appsettings.json"
    if not legacy.is_file():
        return False
    if legacy.resolve() == target_path.resolve():
        return False
    if target_path.exists():
        _Logger.warning(
            "Legacy appsettings %s exists but target %s is already populated. "
            "Leaving legacy in place.", legacy, target_path,
        )
        return False
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(legacy), str(target_path))
    _Logger.info("Migrated legacy appsettings %s → %s", legacy, target_path)
    return True


def seed_cache_file(bundled_source: Path, cache_target: Path) -> bool:
    """Copy `bundled_source` to `cache_target` if the target is missing.
    Returns True when the copy happened. Used for the aldi categories
    seed so operators can curate the list without editing the bundled
    file."""
    if cache_target.exists():
        return False
    cache_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundled_source, cache_target)
    _Logger.info("Seeded cache file %s from bundled %s", cache_target, bundled_source)
    return True
