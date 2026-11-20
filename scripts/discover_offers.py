#!/usr/bin/env python3
"""Collect potential ChatGPT offer links into a manual-review inbox.

No secrets, paid APIs, account inspection, or automated acceptance of a promotion.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from open_ai_inspector.catalog import load_catalog
from open_ai_inspector.discovery import OFFICIAL_FEEDS, canonical_url, discover_candidates


def update_candidates(catalog_path: str, target: Path) -> tuple[int, int, list[str]]:
    catalog = load_catalog(catalog_path)
    previous: dict[str, dict] = {}
    if target.exists():
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValueError("Unsupported candidate inbox format")
        for item in data.get("candidates", []):
            if not isinstance(item, dict) or not isinstance(item.get("url"), str):
                raise ValueError("Malformed candidate inbox")
            key = canonical_url(item["url"])
            if key in previous:
                raise ValueError("Duplicate candidate URL")
            previous[key] = item
    proposals, errors, roots_ok = discover_candidates(
        catalog, previously_seen=set(previous), feed_roots=OFFICIAL_FEEDS
    )
    if not roots_ok:
        return 0, 0, errors
    for candidate in proposals:
        previous[candidate.url] = candidate.as_dict()
    if proposals:
        target.parent.mkdir(parents=True, exist_ok=True)
        document = {
            "schema_version": 1,
            "note": "Unverified link leads only; no individual eligibility claims.",
            "candidates": [previous[key] for key in sorted(previous)],
        }
        target.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    return len(proposals), roots_ok, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover official promotion leads for review")
    parser.add_argument("--catalog", default="src/open_ai_inspector/data/official.json")
    parser.add_argument("--out", default="data/discovered-candidates.json")
    args = parser.parse_args(argv)
    try:
        added, scanned, errors = update_candidates(args.catalog, Path(args.out))
    except (OSError, ValueError) as exc:
        print("Catalog or inbox error: " + type(exc).__name__, file=sys.stderr)
        return 2
    print(f"Scanned {scanned} official HTML/RSS sources; found {added} new candidate link(s).")
    for error in errors:
        print("Warning: " + error, file=sys.stderr)
    if scanned == 0:
        print("All official HTML/RSS sources unavailable. No candidates published.", file=sys.stderr)
        return 1
    if added:
        print("New links require human review; no offer has been activated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
