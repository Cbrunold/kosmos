"""Pull the "All Periodical Elements" database out of Notion into data/chemistry/elements.json.

Auth: set NOTION_TOKEN in the environment, or put NOTION_TOKEN=... in a .env
file next to this repo's root. One-way sync, Notion -> repo; never writes back.

Usage:  python3 scripts/fetch_elements.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_SOURCE_ID = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"  # All Periodical Elements
NOTION_VERSION = "2025-09-03"


def token() -> str:
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("NOTION_TOKEN="):
                return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("NOTION_TOKEN not set (env var or .env)")


def fetch_all() -> list:
    url = f"https://api.notion.com/v1/data_sources/{DATA_SOURCE_ID}/query"
    headers = {
        "Authorization": f"Bearer {token()}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }
    results, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
        d = json.load(urllib.request.urlopen(req))
        results += d["results"]
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]
    return results


def normalise(results: list) -> list:
    out = []
    for r in results:
        p = r["properties"]

        def sel(k):
            s = p.get(k, {}).get("select")
            return s["name"] if s else None

        def num(k):
            return p.get(k, {}).get("number")

        def rich(k):
            return "".join(x["plain_text"] for x in p.get(k, {}).get("rich_text", [])) or None

        formula = p.get("State at 20°C", {}).get("formula", {}) or {}
        equations = [x["id"] for x in (p.get("Equations", {}).get("relation") or [])]
        out.append({
            "name": "".join(x["plain_text"] for x in p.get("Element", {}).get("title", [])),
            "atomicNumber": num("Atomic Number"),
            "atomicMass": num("Atomic Mass"),
            "notation": rich("Notation"),
            "group": sel("Group"),
            "period": sel("Period"),
            "categories": [t["name"] for t in p.get("Categories", {}).get("multi_select", [])],
            "state0C": sel("0°C State"),
            "state20C": formula.get("string"),
            "occurrence": sel("Nat. Occurrence"),
            "density": num("Density"),
            "meltingPt": num("Melting Pt"),
            "boilingPt": num("Boiling Pt"),
            "discovered": num("Discovered"),
            "abundance": num("Crustal Abundance"),   # ppm by mass (scripts/seed_abundance.py)
            # extraction data (scripts/seed_mining.py); the concentration factor is derived at build time
            "oreGrade": num("Ore Grade (ppm)"),
            "oreMinerals": rich("Ore Minerals"),
            "minedAs": sel("Mined As"),
            "extraction": rich("Extraction"),
            "mines": [x["id"] for x in (p.get("Mines", {}).get("relation") or [])],
            "machines": [x["id"] for x in (p.get("Machines", {}).get("relation") or [])],
            "skills": [x["id"] for x in (p.get("Skills", {}).get("relation") or [])],
            "equations": equations,   # page ids in the Equations [DB] (mirrored relation)
            "pageId": r["id"],
            "pageUrl": r.get("url"),
            "lastEdited": r.get("last_edited_time"),
        })
    out.sort(key=lambda e: (e["atomicNumber"] is None, e["atomicNumber"]))
    return out


if __name__ == "__main__":
    elements = normalise(fetch_all())
    dest = ROOT / "data" / "chemistry" / "elements.json"
    dest.write_text(json.dumps(elements, indent=2) + "\n")
    print(f"wrote {len(elements)} elements -> {dest.relative_to(ROOT)}")
