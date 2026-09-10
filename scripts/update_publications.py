#!/usr/bin/env python3
"""Refresh data/publications.json from Rajneil Baruah's INSPIRE-HEP author record.

The workflow tries INSPIRE's documented author search syntax and a name-based
fallback. It refuses to replace an existing feed with an empty result.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "publications.json"
URL = "https://inspirehep.net/api/literature"

# INSPIRE recommends author-search syntax such as `a surname, first-name`.
# Keep the second query as a fallback for records with indexing/name variants.
QUERIES = [
    "a Baruah, Rajneil",
    'authors.full_name:"Rajneil Baruah"',
]


def clean_title(meta: dict[str, Any]) -> str:
    titles = meta.get("titles") or []
    return (titles[0].get("title") if titles else "") or "Untitled"


def pub_date(meta: dict[str, Any]) -> str:
    return meta.get("earliest_date") or ""


def venue(meta: dict[str, Any]) -> str:
    pinfo = meta.get("publication_info") or []
    if pinfo:
        p = pinfo[0] or {}
        journal = p.get("journal_title") or ""
        vol = p.get("journal_volume") or ""
        pages = p.get("page_start") or p.get("artid") or ""
        year = p.get("year") or ""
        bits = [journal, vol, pages, f"({year})" if year else ""]
        return " ".join(str(x) for x in bits if x)
    return "Preprint"


def arxiv_id(meta: dict[str, Any]) -> str | None:
    eprints = meta.get("arxiv_eprints") or []
    for e in eprints:
        if e.get("value"):
            return e["value"]
    return None


def doi(meta: dict[str, Any]) -> str | None:
    for d in meta.get("dois") or []:
        if d.get("value"):
            return d["value"]
    return None


def record_url(meta: dict[str, Any]) -> str | None:
    recid = meta.get("control_number")
    return f"https://inspirehep.net/literature/{recid}" if recid else None


def authors(meta: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"full_name": a.get("full_name") or ""}
        for a in (meta.get("authors") or [])
        if a.get("full_name")
    ]


def kind(meta: dict[str, Any]) -> str:
    # INSPIRE's publication_info is enough for the broad distinction needed by
    # the site. Keep proceedings identifiable but do not try to over-classify.
    pinfo = meta.get("publication_info") or []
    if pinfo:
        first = pinfo[0] or {}
        if first.get("journal_title"):
            return "Journal article"
        if first.get("book_title") or first.get("conference_record"):
            return "Conference / proceedings"
    return "Preprint" if arxiv_id(meta) else "Other"


def fetch(query: str) -> list[dict[str, Any]]:
    r = requests.get(
        URL,
        params={"size": 100, "sort": "mostrecent", "q": query, "page": 1},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    return (payload.get("hits") or {}).get("hits", [])


def main() -> None:
    hits: list[dict[str, Any]] = []
    used_query = None
    errors = []

    for query in QUERIES:
        try:
            candidate = fetch(query)
            if candidate:
                hits = candidate
                used_query = query
                break
            errors.append(f"{query}: 0 records")
        except Exception as exc:
            errors.append(f"{query}: {exc}")

    if not hits:
        print("ERROR: INSPIRE returned no records; refusing to overwrite publications.json.")
        for msg in errors:
            print(msg)
        raise SystemExit(1)

    out = []
    seen = set()
    for hit in hits:
        meta = hit.get("metadata") or {}
        recid = meta.get("control_number")
        if recid in seen:
            continue
        seen.add(recid)
        p = {
            "date": pub_date(meta),
            "title": clean_title(meta),
            "venue": venue(meta),
            "type": kind(meta),
            "authors": authors(meta),
            "doi": doi(meta),
            "arxiv": arxiv_id(meta),
            "inspire": record_url(meta),
        }
        p = {k: v for k, v in p.items() if v not in (None, "", [])}
        out.append(p)

    if not out:
        raise SystemExit("INSPIRE response contained no usable publication records.")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "INSPIRE-HEP",
        "query": used_query,
        "publications": out,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(out)} records to {OUT}")


if __name__ == "__main__":
    main()
