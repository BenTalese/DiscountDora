#!/usr/bin/env python3
"""Fetch the standalone Piper binary into `packaging/piper/` for bundling.

The desktop bundle ships the Piper neural-TTS engine so Dora's voice works
out of the box (R-018 / ADR-013) — but `piper-tts` can't be pip-installed on
Windows, so we bundle the prebuilt binary instead. `dora.spec` includes
`packaging/piper/` as bundle data when present, and `desktop_app.py` points
`DORA_PIPER_BIN` at it at runtime.

Run before `pyinstaller dora.spec` (build-linux.sh does this automatically):

    python packaging/fetch_piper.py            # auto-detect this OS/arch
    python packaging/fetch_piper.py --platform windows_amd64

Idempotent: skips the download if `packaging/piper/<piper exe>` already exists.
The Piper release tarball/zip extracts a `piper/` folder containing the
executable + its shared libs + `espeak-ng-data/`; we drop that whole folder at
`packaging/piper/` so the libs sit beside the executable (Piper needs them
there).
"""
from __future__ import annotations

import argparse
import io
import platform
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

# Pinned Piper release. Bump deliberately (and re-test the bundle).
PIPER_RELEASE = "2023.11.14-2"
_BASE = f"https://github.com/rhasspy/piper/releases/download/{PIPER_RELEASE}"

# Map a normalised platform key → (asset filename, archive kind, exe name).
_ASSETS = {
    "linux_x86_64":   ("piper_linux_x86_64.tar.gz",   "tar", "piper"),
    "linux_aarch64":  ("piper_linux_aarch64.tar.gz",  "tar", "piper"),
    "windows_amd64":  ("piper_windows_amd64.zip",     "zip", "piper.exe"),
    "macos_x64":      ("piper_macos_x64.tar.gz",      "tar", "piper"),
    "macos_aarch64":  ("piper_macos_aarch64.tar.gz",  "tar", "piper"),
}

_DEST = Path(__file__).resolve().parent / "piper"


def _detect_platform() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "windows":
        return "windows_amd64"
    if system == "darwin":
        return "macos_aarch64" if machine in ("arm64", "aarch64") else "macos_x64"
    # linux
    return "linux_aarch64" if machine in ("arm64", "aarch64") else "linux_x86_64"


def fetch(platform_key: str) -> Path:
    if platform_key not in _ASSETS:
        raise SystemExit(
            f"Unknown platform '{platform_key}'. Choose from: {', '.join(_ASSETS)}"
        )
    asset, kind, exe = _ASSETS[platform_key]
    exe_path = _DEST / exe
    if exe_path.exists():
        print(f"[fetch-piper] already present: {exe_path}")
        return exe_path

    url = f"{_BASE}/{asset}"
    print(f"[fetch-piper] downloading {url}")
    with urllib.request.urlopen(url) as resp:  # noqa: S310 — pinned github URL
        data = resp.read()

    _DEST.parent.mkdir(parents=True, exist_ok=True)
    # Archives contain a top-level `piper/` dir; extract into packaging/ so it
    # lands at packaging/piper/.
    if kind == "tar":
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            tf.extractall(_DEST.parent)  # noqa: S202 — trusted release artifact
    else:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(_DEST.parent)

    if not exe_path.exists():
        raise SystemExit(
            f"[fetch-piper] extraction did not yield {exe_path}; "
            f"inspect the archive layout for {asset}"
        )
    # Make it executable on POSIX.
    if exe != "piper.exe":
        exe_path.chmod(0o755)
    print(f"[fetch-piper] ready: {exe_path}")
    return exe_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the Piper binary for bundling.")
    parser.add_argument(
        "--platform", default=None,
        help=f"Override platform key ({', '.join(_ASSETS)}). Default: auto-detect.",
    )
    args = parser.parse_args()
    fetch(args.platform or _detect_platform())
    return 0


if __name__ == "__main__":
    sys.exit(main())
