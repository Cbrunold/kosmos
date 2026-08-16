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


def token() -> str:
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("NOTION_TOKEN="):
                return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("NOTION_TOKEN not set (env var or .env)")


HEADERS = {
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


def query(ds_id: str) -> list:
    url = f"https://api.notion.com/v1/data_sources/{ds_id}/query"
    results, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={**HEADERS, "Authorization": f"Bearer {token()}"})
        d = json.load(urllib.request.urlopen(req))
        results += d["results"]
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]
    return results


def value(p: dict):
    t = p["type"]
    if t == "title":
        return "".join(x["plain_text"] for x in p["title"]) or None
    if t == "rich_text":
        return "".join(x["plain_text"] for x in p["rich_text"]) or None
    if t == "number":
        return p["number"]
    if t == "select":
        return p["select"]["name"] if p["select"] else None
    if t == "status":
        return p["status"]["name"] if p["status"] else None
    if t == "multi_select":
        return [o["name"] for o in p["multi_select"]]
    if t == "date":
        return p["date"]["start"] if p["date"] else None
    if t == "relation":
        return [r["id"] for r in p["relation"]]
    if t == "formula":
        f = p["formula"]
        return f.get("string") if f.get("type") == "string" else f.get("number")
    if t in ("url", "email", "checkbox"):
        return p[t]
    return None


def flatten(page: dict) -> dict:
    row = {"id": page["id"], "url": page.get("url"), "lastEdited": page.get("last_edited_time")}
    for name, prop in page["properties"].items():
        row[name] = value(prop)
    return row


if __name__ == "__main__":
    out = {}
    for key, ds in SOURCES.items():
        rows = [flatten(p) for p in query(ds)]
        out[key] = rows
        print(f"{key}: {len(rows)} rows", file=sys.stderr)
    dest = ROOT / "data" / "notion-all.json"
    dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {dest.relative_to(ROOT)}", file=sys.stderr)
