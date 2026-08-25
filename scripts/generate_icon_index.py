#!/usr/bin/env python3
"""Generate the Poomicon subscription index from repository PNG assets."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import struct
from urllib.parse import quote


RAW_BASE_URL = "https://raw.githubusercontent.com/pengpoom/poomicon/master"
INDEX_FILENAME = "Poomicon.json"
EXCLUDED_FILES = {"Hand-Painted-icon.png"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ICON_SIZE = (108, 108)


def png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError(f"Not a valid PNG: {path}")
    return struct.unpack(">II", header[16:24])


def discover_icons(root: Path) -> list[Path]:
    icons: list[Path] = []
    for path in root.rglob("*.png"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if relative.as_posix() in EXCLUDED_FILES:
            continue
        if png_size(path) != ICON_SIZE:
            raise ValueError(
                f"Icon must be {ICON_SIZE[0]}x{ICON_SIZE[1]}: {relative.as_posix()}"
            )
        icons.append(relative)
    return sorted(icons, key=lambda path: path.as_posix().casefold())


def display_names(paths: list[Path]) -> dict[Path, str]:
    stem_counts = Counter(path.stem for path in paths)
    names: dict[Path, str] = {}
    for path in paths:
        if stem_counts[path.stem] == 1:
            names[path] = path.stem
        else:
            names[path] = " / ".join(path.with_suffix("").parts)
    return names


def build_index(root: Path) -> dict[str, object]:
    paths = discover_icons(root)
    names = display_names(paths)
    return {
        "name": "Poomicon",
        "description": "Personal hand-painted icon library by pengpoom",
        "time": date.today().isoformat(),
        "icons": [
            {
                "name": names[path],
                "url": f"{RAW_BASE_URL}/{quote(path.as_posix(), safe='/')}",
            }
            for path in paths
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of scripts/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=f"Output path (defaults to ROOT/{INDEX_FILENAME})",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / INDEX_FILENAME
    index = build_index(root)
    output.write_text(
        json.dumps(index, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(index['icons'])} icons to {output}")


if __name__ == "__main__":
    main()
