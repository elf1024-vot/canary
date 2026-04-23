#!/usr/bin/env python3
"""Pack canary/ into canary.skill (a .zip bundle).

Run from the repo root:

    python scripts/pack-skill.py

The output is canary.skill in the repo root. The packer is deterministic:
file order is sorted, external attributes are normalized to regular-file
rw-r--r-- (0o100644), and the __pycache__ / *.pyc cruft is excluded.

Use this after any edit to files under canary/ to keep the packed bundle
in sync with the unpacked source of truth.
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "canary"
OUT_PATH = REPO_ROOT / "canary.skill"

EXCLUDE_DIRS = {"__pycache__"}
EXCLUDE_NAMES = {"_ok", "_test", ".DS_Store", "Thumbs.db"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".tmp", ".swp", ".swo"}


def _should_include(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    if path.name in EXCLUDE_NAMES:
        return False
    if path.suffix in EXCLUDE_SUFFIXES:
        return False
    return True


def collect_files(src_dir: Path) -> list[tuple[Path, str]]:
    """Return sorted (absolute_path, archive_name) pairs."""
    items: list[tuple[Path, str]] = []
    for root, dirs, files in os.walk(src_dir):
        # Mutate dirs in place to prune traversal into excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in files:
            full = Path(root) / name
            if not _should_include(full):
                continue
            # Archive path is relative to the parent of SRC_DIR (so zip entries
            # start with "canary/..."). This preserves the Claude Code skill
            # layout convention.
            arc = full.relative_to(src_dir.parent).as_posix()
            items.append((full, arc))
    items.sort(key=lambda pair: pair[1])
    return items


def pack(src_dir: Path, out_path: Path) -> int:
    if not src_dir.is_dir():
        print(f"error: source directory not found: {src_dir}", file=sys.stderr)
        return 2

    files = collect_files(src_dir)
    if not files:
        print(f"error: no files to pack from {src_dir}", file=sys.stderr)
        return 3

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for full, arc in files:
            zi = zipfile.ZipInfo(arc)
            # Normalize external attributes to regular-file rw-r--r--. This
            # prevents platform-specific perms from baking into the bundle and
            # causing the "cannot remove, operation not permitted" extraction
            # behavior observed on some filesystems.
            zi.external_attr = (0o100644) << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            with full.open("rb") as fh:
                data = fh.read()
            z.writestr(zi, data)

    size_kb = out_path.stat().st_size / 1024.0
    print(f"packed {len(files)} files into {out_path} ({size_kb:.1f} KB)")
    return 0


def main(argv: list[str]) -> int:
    return pack(SRC_DIR, OUT_PATH)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
