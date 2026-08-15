"""Populate the Minerals [DB] → Elements relation ("Chemical Properties") from
the per-element composition columns.

The Minerals database encodes composition as ~120 numeric columns, one per
element (plus ions like Carbonate). This decodes them into the existing
"Chemical Properties" relation, so Notion itself knows which elements each
mineral contains — and each element page gains a mirrored backlink.

Resumable and idempotent: pages whose relation already matches are skipped, so
re-running after an interruption only writes what's missing. ~3,100 pages at
Notion's rate limit takes roughly 20 minutes.

Run on the VPS:  python3 scripts/link_mineral_elements.py [--limit N] [--dry-run]
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIN_DS = "a2db78db-efb7-4952-b8bc-e4ab98d42264"   # Minerals [DB] data source
EL_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"    # All Periodical Elements data source
PROP = "Chemical Properties"

# columns that are not element amounts
NON_ELEMENT = {
    "id", "url", "lastEdited", "Name", "Formula", "Chemical Properties", "count", "Index",
    "Approval Year", "Molar Mass", "Molar Volume", "Calculated Density", "Specific Gravity",
    "Mohs Hardness", "Refractive Index", "Dispersion", "Optical", "Crystal Structure",
    "Diaphaneity", "Equations",
}
# ion columns -> constituent elements
ION_TO_SYMS = {
    "Ammonium": ["N", "H"], "Carbonate": ["C", "O"], "Cyanide": ["C", "N"],
    "Hydroxyl": ["O", "H"], "Nitrate": ["N", "O"], "Sulphate": ["S", "O"],
    "Phosphate": ["P", "O"], "Acetate": ["C", "H", "O"], "Hydrated Water": ["H", "O"],
}
NAME_FIXUPS = {"Aluminium": "Al", "Aluminum": "Al", "Cesium": "Cs", "Caesium": "Cs",
               "Sulphur": "S", "Nitrogen": "N"}


def token() -> str:
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    for p in (ROOT / ".env", Path("/srv/kosmos/.env")):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("NOTION_TOKEN="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("NOTION_TOKEN not set")


H = {"Authorization": f"Bearer {token()}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}


def call(method, url, body=None, tries=5):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                         headers=H, method=method)
            return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < tries - 1:
                wait = float(e.headers.get("Retry-After", 2 ** attempt))
                time.sleep(wait)
                continue
            raise


def query_all(ds):
    out, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        d = call("POST", f"https://api.notion.com/v1/data_sources/{ds}/query", body)
        out += d["results"]
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]
    return out


def prop_value(p):
    t = p["type"]
    if t == "number":
        return p["number"]
    if t == "title":
        return "".join(x["plain_text"] for x in p["title"])
    if t == "relation":
        return [r["id"] for r in p["relation"]]
    return None


def main():
    limit = None
    dry = "--dry-run" in sys.argv
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    # element symbol -> page id (Notation is the symbol; titles vary, e.g. "Nitrogen / Azote")
    el_by_sym, el_by_name = {}, {}
    for r in query_all(EL_DS):
        sym = "".join(x["plain_text"] for x in r["properties"]["Notation"]["rich_text"]).strip()
        name = "".join(x["plain_text"] for x in r["properties"]["Element"]["title"]).strip()
        if sym:
            el_by_sym[sym] = r["id"]
            el_by_name[name] = r["id"]

    def resolve(col):
        """column name -> list of element page ids"""
        if col in ION_TO_SYMS:
            return [el_by_sym[s] for s in ION_TO_SYMS[col] if s in el_by_sym]
        if col in NAME_FIXUPS and NAME_FIXUPS[col] in el_by_sym:
            return [el_by_sym[NAME_FIXUPS[col]]]
        if col in el_by_name:
            return [el_by_name[col]]
        return []

    minerals = query_all(MIN_DS)
    print(f"{len(minerals)} minerals · {len(el_by_sym)} elements", flush=True)

    todo = []
    unmapped = set()
    for m in minerals:
        want = set()
        for col, p in m["properties"].items():
            if col in NON_ELEMENT:
                continue
            v = prop_value(p)
            if not isinstance(v, (int, float)) or v <= 0:
                continue
            ids = resolve(col)
            if ids:
                want.update(ids)
            else:
                unmapped.add(col)
        cur = set(prop_value(m["properties"].get(PROP, {"type": "relation", "relation": []})) or [])
        if want and want != cur:
            todo.append((m["id"], "".join(x["plain_text"] for x in m["properties"]["Name"]["title"]), want | cur))

    if unmapped:
        print("unmapped columns ignored:", sorted(unmapped), flush=True)
    print(f"{len(todo)} minerals need updating", flush=True)
    if dry:
        for pid, name, want in todo[:5]:
            print(f"  would set {name}: {len(want)} elements")
        return

    done = 0
    for pid, name, want in todo[:limit] if limit else todo:
        call("PATCH", f"https://api.notion.com/v1/pages/{pid}",
             {"properties": {PROP: {"relation": [{"id": x} for x in sorted(want)]}}})
        done += 1
        if done % 100 == 0:
            print(f"  {done}/{len(todo)}…", flush=True)
    print(f"done · updated {done} minerals", flush=True)


if __name__ == "__main__":
    main()
