#!/usr/bin/env python3
"""Refresh data/publications.json from the Rajneil Baruah INSPIRE-HEP record search."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "publications.json"
URL = "https://inspirehep.net/api/literature"
PARAMS = {
    "size": 100,
    "sort": "mostrecent",
    "q": 'authors.full_name:"Rajneil Baruah"',
}


def clean_title(meta: dict[str, Any]) -> str:
    titles = meta.get("titles") or []
    return (titles[0].get("title") if titles else "") or "Untitled"


def pub_date(meta: dict[str, Any]) -> str:
    return meta.get("earliest_date") or ""


def venue(meta: dict[str, Any]) -> str:
    pinfo = meta.get("publication_info") or []
    if pinfo:
        p = pinfo[0] or {}
        journal = p.get("journal_title") or p.get("journal_issue") or ""
        vol = p.get("journal_volume") or ""
        year = p.get("year") or ""
        pages = p.get("page_start") or p.get("artid") or ""
        bits = [journal, vol, pages, f"({year})" if year else ""]
        return " ".join(str(x) for x in bits if x)
    return "Conference / preprint"


def arxiv_id(meta: dict[str, Any]) -> str | None:
    eprints = meta.get("arxiv_eprints") or []
    if not eprints:
        return None
    return eprints[0].get("value")


def doi(meta: dict[str, Any]) -> str | None:
    dois = meta.get("dois") or []
    for d in dois:
        if d.get("value"):
            return d["value"]
    return None


def record_url(meta: dict[str, Any]) -> str | None:
    recid = meta.get("control_number")
    return f"https://inspirehep.net/literature/{recid}" if recid else None


def authors(meta: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for a in meta.get("authors") or []:
        result.append({"full_name": a.get("full_name") or a.get("raw_affiliations", [{}])[0].get("value", "")})
    return result


def kind(meta: dict[str, Any]) -> str:
    pinfo = meta.get("publication_info") or []
    docs = {str(x).lower() for x in (meta.get("document_type") or [])}
    if pinfo and any("conference" not in d for d in docs):
        return "Journal article"
    if arxiv_id(meta):
        return "Preprint"
    return "Conference / proceedings"


def main() -> None:
    r = requests.get(URL, params=PARAMS, timeout=30)
    r.raise_for_status()
    data = r.json()

    out = []
    for hit in (data.get("hits") or {}).get("hits", []):
        meta = hit.get("metadata") or {}
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
        p = {k: v for k, v in p.items() if v not in (None, "")}
        out.append(p)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "INSPIRE-HEP",
        "query": PARAMS["q"],
        "publications": out,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(out)} records to {OUT}")


if __name__ == "__main__":
    main()
