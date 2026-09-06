"""Pull every Kosmos-relevant Notion data source into data/notion-all.json.

Generic one-way sync (Notion -> repo). Auth like fetch_elements.py: NOTION_TOKEN
env var or .env. Output: {sourceKey: [{id, url, lastEdited, <property>: value}]}
with properties flattened to plain values (relations become lists of page ids).
"""
import json
import os
import sys
import urllib.request
from pathlib import Path
from notion import token, query_all, find_ds, value, flatten  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
NOTION_VERSION = "2025-09-03"

SOURCES = {
    "celestialObjects": "f279dffc-9049-468d-8a5a-dbcdcf36f940",
    "celestialTypes": "93d5da9c-57f0-4884-9bdc-1d11cb4a0cd6",
    "missions": "6c10e82f-8044-43f2-b936-58bf54d4873b",
    "discoveries": "01fd23ec-32da-466d-89cc-5095269805b7",
    "observatories": "e4113ed3-07af-4167-8145-183389eb39e1",
    "instruments": "e72fed70-784c-42d2-be1a-3c833ac7fc63",
    "researchers": "4cc8d7c4-9008-4017-a09b-7087720aebd3",
    "theories": "215048ed-e6a6-4b9a-858b-73e8c801629e",
    "forces": "46546d3d-29db-4906-8bca-c2265332efcb",
    "cosmologyEvents": "d9a53e88-f4a5-4476-9a8f-94c6f72443ea",
    "cosmicTimeline": "3c1ab928-8ffa-48e7-b0bc-b90e16480a46",
    "mines": "dd711986-067e-43f9-9a74-dd471ac4bcc6",
    "machines": "f6c4e3cc-bfe0-4fb8-b807-3693cbcf4e88",
    "skills": "804e17aa-435b-4306-acbb-2ec926b87b10",
    "glossary": {"title": "Glossary [DB]"},
    "cosmicStructures": {"title": "Cosmic Structures [DB]"},   # created by seed_scales.py; resolved by title at fetch time
    "explainers": {"title": "Explainers [DB]"},   # created by seed_explainers.py; likewise
    "impacts": {"title": "Mining Impacts [DB]"},   # created by seed_impacts.py; likewise
    "solar": {"title": "Solar System [DB]"},   # created by seed_solar.py; likewise
    "life": {"title": "Life [DB]"},   # created by seed_life.py; likewise
    "spectralTypes": "6128c15c-25dd-47fb-bf00-ce737ca1d3e6",
    "gemstones": "e4fe83d2-0365-4dc6-935e-e5b6ce967778",
    "minerals": "a2db78db-efb7-4952-b8bc-e4ab98d42264",
    "crystalSystems": "72a0360b-a17a-42bc-b404-9c3b5cc2ed09",
    "silicateMinerals": "e43f9009-2f39-4aef-94ba-09b3dc3d0ce9",
    "rockTypes": "5680d212-c2dd-4668-be9e-2065b850110b",
    "equations": "638fda32-4a6d-4d65-8349-433ce4f0b698",
    "constants": "22e47e69-84c2-44e7-ae04-f1bf3dc80ebe",
    "units": "a18aa2b7-8300-4ea0-9da4-04f39b3afcc8",
}


def query(ds_id: str) -> list:
    return query_all(ds_id)


def resolve(ds) -> str | None:
    """A source may be given as an id, or as {"title": ...} to look up by name —
    for databases a seed script creates, whose id is not known in advance."""
    return ds if isinstance(ds, str) else find_ds(ds["title"])


if __name__ == "__main__":
    out = {}
    for key, ds in SOURCES.items():
        ds_id = resolve(ds)
        if not ds_id:
            print(f"{key}: not found (not created yet) — 0 rows", file=sys.stderr)
            out[key] = []
            continue
        rows = [flatten(p) for p in query(ds_id)]
        out[key] = rows
        print(f"{key}: {len(rows)} rows", file=sys.stderr)
    dest = ROOT / "data" / "notion-all.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {dest.relative_to(ROOT)}", file=sys.stderr)
