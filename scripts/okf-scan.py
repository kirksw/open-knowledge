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


def field(lines, name):
    prefix = name + ":"
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def hidden(rel):
    return any(part.startswith(".") for part in rel.parts)


def scan(root):
    errors = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if hidden(rel):
            continue
        fm = frontmatter(path)
        if path.name in RESERVED:
            if fm is not None:
                errors.append(f"{rel}: reserved OKF file must not have frontmatter")
            continue
        if fm is None:
            errors.append(f"{rel}: missing OKF frontmatter")
        elif fm == []:
            errors.append(f"{rel}: unterminated OKF frontmatter")
        elif not field(fm, "type"):
            errors.append(f"{rel}: missing non-empty OKF type")
    return errors


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"okf-scan: no such directory: {root}")
        return 2
    errors = scan(root)
    if errors:
        print("\n".join(errors))
        return 1
    print(f"okf-scan: ok ({root})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
