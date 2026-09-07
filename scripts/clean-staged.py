#!/usr/bin/env python3
"""Remove empty files left in a pipeline staging directory."""

from __future__ import annotations

import argparse
from pathlib import Path


def remove_empty_files(staged: Path) -> list[Path]:
    removed = []
    if not staged.is_dir():
        return removed
    for path in staged.rglob("*"):
        if path.is_file() and path.stat().st_size == 0:
            path.unlink()
            removed.append(path.relative_to(staged))
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staged", type=Path)
    args = parser.parse_args()
    for path in remove_empty_files(args.staged):
        print(f"clean-staged: removed empty file {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
