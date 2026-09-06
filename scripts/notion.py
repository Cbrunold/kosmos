"""Everything the scripts share for talking to Notion — one copy, imported everywhere.

    from notion import call, query_all, find_ds, title_of, ensure_props, sync_rows

Auth is lazy: NOTION_TOKEN from the environment, else from .env next to the repo root
or /srv/kosmos/.env, read on the first request — so a seed's data tables can be
imported without a token. API version 2025-09-03: queries go to a *data source* id,
not a database id.

History: these grew inside seed_theories.py and were imported from there by
twenty-six scripts, while thirteen others carried their own copy of token(),
call() and the pagination loop. Now there is this file; seed_theories.py
re-exports it so its importers did not have to change, and a test refuses a
second definition of token() or query_all() anywhere else.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.notion.com/v1"
NOTION_VERSION = "2025-09-03"


def token() -> str:
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    for p in (ROOT / ".env", Path("/srv/kosmos/.env")):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("NOTION_TOKEN="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("NOTION_TOKEN not set")


def headers() -> dict:
    """Built on demand, so the data tables of a seed can be imported without a token."""
    return {"Authorization": f"Bearer {token()}", "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"}


def call(method, url, body=None, tries=5):
    """One request, decoded. A 429 or a 5xx is retried, honouring Retry-After (Notion's
    limit is about three requests a second, and a seed of a few hundred rows crosses
    it); anything else raises with the response intact."""
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                         headers=headers(), method=method)
            return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503, 504) and attempt < tries - 1:
                time.sleep(float(e.headers.get("Retry-After", 2 ** attempt)))
                continue
            raise


def query_all(ds):
    """Every page of a data source, paginated to the end."""
    out, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        d = call("POST", f"{API}/data_sources/{ds}/query", body)
        out += d["results"]
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]
    return out


def find_ds(title):
    """The id of the data source with exactly this title, or None — for databases a
    seed script creates, whose id is not known in advance."""
    d = call("POST", f"{API}/search",
             {"query": title, "filter": {"property": "object", "value": "data_source"},
              "page_size": 50})
    for r in d.get("results", []):
        if "".join(x.get("plain_text", "") for x in r.get("title", [])).strip() == title:
            return r["id"]
    return None


def title_of(page, prop="Name") -> str:
    p = page["properties"].get(prop) or {}
    return "".join(x["plain_text"] for x in p.get("title", [])).strip()


def is_empty(page, name) -> bool:
    """True if the property is absent, null, or an empty string/list."""
    p = page["properties"].get(name)
    if not p:
        return True
    v = p.get(p["type"])
    if v is None:
        return True
    if isinstance(v, list):
        return not v
    return False


def chunks(text: str, limit: int = 1900) -> list:
    """Split into rich_text objects under Notion's 2,000-character cap.

    fetch_all joins a property's text runs back together, so where the split
    falls does not matter — but prefer a line break, then a space, so a value
    read in Notion itself is not cut mid-word.
    """
    out, rest = [], text
    while len(rest) > limit:
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        out.append({"text": {"content": rest[:cut]}})
        rest = rest[cut:]
    out.append({"text": {"content": rest}})
    return out


def encode(kind: str, value):
    """Build a Notion property payload for a schema type we might encounter."""
    if value is None:
        return None
    if kind == "title":
        return {"title": [{"text": {"content": str(value)}}]}
    if kind == "rich_text":
        return {"rich_text": chunks(str(value))}
    if kind == "number":
        return {"number": value}
    if kind == "select":
        return {"select": {"name": str(value)}}
    if kind == "status":
        return {"status": {"name": str(value)}}
    if kind == "multi_select":
        vals = value if isinstance(value, list) else [value]
        return {"multi_select": [{"name": str(v)} for v in vals]}
    if kind == "date":
        return {"date": {"start": str(value)}}
    if kind == "url":
        return {"url": str(value)}
    return None


def ensure_props(ds_id: str, wanted: dict, label: str):
    """Add any missing properties to a data source. Returns the live schema."""
    ds = call("GET", f"{API}/data_sources/{ds_id}")
    missing = {k: v for k, v in wanted.items() if k not in ds["properties"]}
    if missing:
        call("PATCH", f"{API}/data_sources/{ds_id}", {"properties": missing})
        print(f"  {label}: added properties {', '.join(sorted(missing))}")
        ds = call("GET", f"{API}/data_sources/{ds_id}")
    return {k: v["type"] for k, v in ds["properties"].items()}


def ensure_select_options(ds_id: str, prop: str, options: list, label: str):
    """Union new choices into an existing select/status property."""
    ds = call("GET", f"{API}/data_sources/{ds_id}")
    spec = ds["properties"].get(prop)
    if not spec or spec["type"] != "select":
        return
    have = [o["name"] for o in spec["select"]["options"]]
    new = [o for o in options if o not in have]
    if not new:
        return
    body = {"properties": {prop: {"select": {"options": [{"name": n} for n in have + new]}}}}
    try:
        call("PATCH", f"{API}/data_sources/{ds_id}", body)
        print(f"  {label}: added {prop} options {', '.join(new)}")
    except urllib.error.HTTPError as e:
        print(f"  {label}: could not extend {prop}: {e.code} {e.read().decode()[:160]}")


def sync_rows(ds_id: str, schema: dict, rows: list, label: str, key="Name"):
    """Insert missing rows; backfill only the empty fields of existing ones."""
    existing = {title_of(p, key): p for p in query_all(ds_id) if title_of(p, key)}
    added = filled = 0
    for row in rows:
        name = row[key]
        payload = {}
        page = existing.get(name)
        for prop, val in row.items():
            kind = schema.get(prop)
            if kind is None or val is None:
                continue
            if page is not None and not is_empty(page, prop):
                continue           # a human already answered this one
            enc = encode(kind, val)
            if enc:
                payload[prop] = enc
        if page is None:
            call("POST", f"{API}/pages",
                 {"parent": {"type": "data_source_id", "data_source_id": ds_id}, "properties": payload})
            added += 1
        elif payload:
            call("PATCH", f"{API}/pages/{page['id']}", {"properties": payload})
            filled += 1
    print(f"{label}: {added} added, {filled} backfilled, {len(rows)} defined "
          f"({len(existing)} were already present)")


# ---------------------------------------------------------------- reading rows back
def value(p: dict):
    """A property as a plain value: text joined, selects by name, relations as id lists."""
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
    """{id, url, lastEdited, <property>: value} — the row shape data/notion-all.json holds."""
    row = {"id": page["id"], "url": page.get("url"), "lastEdited": page.get("last_edited_time")}
    for name, prop in page["properties"].items():
        row[name] = value(prop)
    return row
