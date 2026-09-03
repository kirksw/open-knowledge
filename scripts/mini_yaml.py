#!/usr/bin/env python3
"""Minimal YAML subset parser for OKF frontmatter validation.

Supports exactly the shapes used by this repository's templates:
- top-level scalar keys (``key: value``),
- one-level nested mappings (``generated:`` blocks),
- one-level sequences of mappings (``sources:`` blocks), and
- sequences of scalars (``tags:`` blocks).

Anything else raises MiniYAMLError so callers can fail closed. Standard
library only; the validator must run without network access.
"""

from __future__ import annotations


class MiniYAMLError(ValueError):
    pass


def _split_kv(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise MiniYAMLError(f"expected 'key: value', got {line!r}")
    key, value = line.split(":", 1)
    key = key.strip()
    if not key:
        raise MiniYAMLError(f"empty key in {line!r}")
    return key, value.strip()


def _scalar(text: str):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if text == "":
        return ""
    low = text.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low == "null" or text == "~":
        return None
    try:
        return int(text)
    except ValueError:
        return text


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse(text: str) -> dict:
    """Parse the YAML subset into a dict. Raises MiniYAMLError on anything unsupported."""
    if "\t" in text:
        raise MiniYAMLError("tabs are not supported in frontmatter")
    raw_lines = text.splitlines()
    lines: list[tuple[int, str]] = []
    for line in raw_lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
        lines.append((_indent_of(line), line))
    data: dict = {}
    i = 0
    n = len(lines)
    while i < n:
        indent, line = lines[i]
        if indent != 0:
            raise MiniYAMLError(f"unexpected indentation: {line!r}")
        if line.lstrip().startswith("- "):
            raise MiniYAMLError(f"top-level sequences are not supported: {line!r}")
        key, value = _split_kv(line)
        if value != "":
            data[key] = _scalar(value)
            i += 1
            continue
        # Empty value: nested mapping or sequence.
        if i + 1 >= n or lines[i + 1][0] <= 0:
            data[key] = None
            i += 1
            continue
        child_indent = lines[i + 1][0]
        if child_indent % 2 != 0:
            raise MiniYAMLError(f"odd indentation width: {lines[i + 1][1]!r}")
        if lines[i + 1][1].lstrip().startswith("- "):
            items = []
            i += 1
            while i < n and lines[i][0] == child_indent and lines[i][1].lstrip().startswith("- "):
                item_text = lines[i][1].lstrip()[2:]
                item_indent = child_indent + 2
                i += 1
                if item_text.strip() == "":
                    # Sequence of scalars written as "- value" is handled below;
                    # bare "-" followed by deeper keys is unsupported.
                    if i < n and lines[i][0] > child_indent:
                        raise MiniYAMLError("nested sequences are not supported")
                    items.append(None)
                    continue
                if ":" in item_text and not item_text.strip().startswith(("-", '"', "'")):
                    first_key, first_value = _split_kv(item_text)
                    item = {first_key: _scalar(first_value)}
                    while i < n and lines[i][0] >= item_indent:
                        if lines[i][0] != item_indent or lines[i][1].lstrip().startswith("- "):
                            raise MiniYAMLError(f"unsupported sequence item line: {lines[i][1]!r}")
                        k, v = _split_kv(lines[i][1].lstrip())
                        item[k] = _scalar(v)
                        i += 1
                    items.append(item)
                else:
                    items.append(_scalar(item_text))
            data[key] = items
            # Allow same-indent scalar sequence items "- value".
            continue
        nested: dict = {}
        i += 1
        while i < n and 0 < lines[i][0] and lines[i][0] >= child_indent:
            if lines[i][0] != child_indent or lines[i][1].lstrip().startswith("- "):
                raise MiniYAMLError(f"unsupported nested line: {lines[i][1]!r}")
            k, v = _split_kv(lines[i][1].lstrip())
            nested[k] = _scalar(v)
            i += 1
        data[key] = nested
    return data


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Split a Markdown file into (frontmatter dict or None, body).

    Returns (None, text) when the file does not start with a frontmatter
    block. Raises MiniYAMLError when a block exists but is unterminated or
    unparseable.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end = idx
            break
    if end is None:
        raise MiniYAMLError("unterminated frontmatter block")
    block = "\n".join(lines[1:end])
    return parse(block), "\n".join(lines[end + 1 :])
