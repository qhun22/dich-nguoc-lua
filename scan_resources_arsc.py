# -*- coding: utf-8 -*-
"""Scan resources.arsc for likely app-name strings."""

from __future__ import annotations

import os
import re

ARSCPATH = r"d:\FileD\dota\apk\resources.arsc"

# Keep ASCII-only keywords to match the editing constraints.
KEYWORDS = [
    "tmgame",
    "tmgame99",
    "dota",
    "dota truyen ky",
    "dotatruyenky",
    "truyen ky",
    "truyen",
    "7 sao",
    "game99",
    "app_name",
    "label",
]

PRINTABLE_RE = re.compile(rb"[\x20-\x7e]{4,}")


def extract_ascii_strings(data: bytes) -> list[tuple[int, str]]:
    results: list[tuple[int, str]] = []
    for match in PRINTABLE_RE.finditer(data):
        try:
            text = match.group(0).decode("ascii", errors="ignore")
            results.append((match.start(), text))
        except Exception:
            continue
    return results


def extract_utf16le_strings(data: bytes) -> list[tuple[int, str]]:
    results: list[tuple[int, str]] = []
    # UTF-16LE printable ASCII pattern: e.g. T\x00M\x00...
    pattern = re.compile(rb"(?:[\x20-\x7e]\x00){4,}")
    for match in pattern.finditer(data):
        try:
            text = match.group(0).decode("utf-16le", errors="ignore")
            results.append((match.start(), text))
        except Exception:
            continue
    return results


def find_keyword_hits(strings: list[tuple[int, str]], keywords: list[str]) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for offset, text in strings:
        lowered = text.lower()
        for kw in keywords:
            if kw in lowered:
                hits.append((offset, text))
                break
    return hits


def main() -> None:
    if not os.path.exists(ARSCPATH):
        print(f"resources.arsc not found: {ARSCPATH}")
        return

    with open(ARSCPATH, "rb") as f:
        data = f.read()

    ascii_strings = extract_ascii_strings(data)
    utf16_strings = extract_utf16le_strings(data)

    ascii_hits = find_keyword_hits(ascii_strings, KEYWORDS)
    utf16_hits = find_keyword_hits(utf16_strings, KEYWORDS)

    print("=== resources.arsc scan ===")
    print(f"Total ASCII strings: {len(ascii_strings)}")
    print(f"Total UTF-16LE strings: {len(utf16_strings)}")
    print()

    def dump_hits(title: str, hits: list[tuple[int, str]]) -> None:
        print(title)
        if not hits:
            print("  (no hits)")
            return
        for offset, text in hits:
            print(f"  0x{offset:08x}: {text}")

    dump_hits("ASCII hits:", ascii_hits)
    print()
    dump_hits("UTF-16LE hits:", utf16_hits)


if __name__ == "__main__":
    main()
