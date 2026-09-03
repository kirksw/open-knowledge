#!/usr/bin/env python3
import sys
from pathlib import Path

RESERVED = {"index.md", "log.md"}


def frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None
    for i, line in enumerate(lines[1:], 2):
        if line == "---":
            return lines[1 : i - 1]
    return []


def parse(lines):
    data = {}
    for line in lines or []:
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"\'')
    return data


def hidden(rel):
    return any(part.startswith(".") for part in rel.parts)


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    print("path\ttype\ttitle\tdescription")
    for path in sorted(root.rglob("*.md")):
        if hidden(path.relative_to(root)):
            continue
        if path.name in RESERVED:
            continue
        data = parse(frontmatter(path))
        print("\t".join([
            str(path.relative_to(root)),
            data.get("type", ""),
            data.get("title", ""),
            data.get("description", ""),
        ]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
