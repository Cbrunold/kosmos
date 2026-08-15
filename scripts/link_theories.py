"""Wire the Theories [DB] relations: Proponent → Researchers, Equations → Equations.

Both relations already exist on the Theories data source but are empty; this
fills them from the maps in seed_theories.py. Names that do not resolve are
reported rather than silently dropped, so a typo shows up as output instead of
a missing chip on the site.

Idempotent: unions with whatever is already set, never removes a link.
Run on the VPS, after seed_theories.py:  python3 scripts/link_theories.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import THEORIES, THEORY_EQUATIONS, EXISTING_PROPONENTS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
THEORY_DS = "215048ed-e6a6-4b9a-858b-73e8c801629e"
RESEARCHER_DS = "4cc8d7c4-9008-4017-a09b-7087720aebd3"
EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"


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
    return {"Authorization": f"Bearer {token()}", "Notion-Version": "2025-09-03",
            "Content-Type": "application/json"}


def call(method, url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers=headers(), method=method)
    return json.load(urllib.request.urlopen(req))


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


def title_of(page, prop="Name") -> str:
    p = page["properties"].get(prop) or {}
    return "".join(x["plain_text"] for x in p.get("title", [])).strip()


def ensure_relation(ds_id, prop, target_ds, synced_name):
    """Create the relation property if it is missing, dual-property if allowed."""
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{ds_id}")
    if prop in ds["properties"]:
        print(f"  relation {prop} already exists")
        return True
    for body in (
        {"properties": {prop: {"relation": {"data_source_id": target_ds, "type": "dual_property",
                                            "dual_property": {"synced_property_name": synced_name}}}}},
        {"properties": {prop: {"relation": {"data_source_id": target_ds, "type": "single_property",
                                            "single_property": {}}}}},
    ):
        try:
            call("PATCH", f"https://api.notion.com/v1/data_sources/{ds_id}", body)
            print(f"  created relation {prop}")
            return True
        except urllib.error.HTTPError as e:
            print(f"  attempt failed: {e.code} {e.read().decode()[:160]}")
    return False


def apply_links(theories, prop, wanted_by_theory, target_by_name, label):
    changed, edges = 0, 0
    missing = set()
    for page in theories:
        name = title_of(page)
        wanted = wanted_by_theory.get(name)
        if not wanted:
            continue
        ids = set()
        for w in wanted:
            if w in target_by_name:
                ids.add(target_by_name[w])
            else:
                missing.add(w)
        cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
        new = cur | ids
        edges += len(new)
        if new != cur:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
                 {"properties": {prop: {"relation": [{"id": x} for x in sorted(new)]}}})
            changed += 1
    if missing:
        print(f"  unresolved {label} names ignored: {sorted(missing)}")
    print(f"  {label}: updated {changed} theories · {edges} links")


def main():
    proponents = {name: props for name, _, _, _, props in THEORIES}
    proponents.update(EXISTING_PROPONENTS)

    print("relations")
    ensure_relation(THEORY_DS, "Proponent", RESEARCHER_DS, "Theories [DB]")
    ensure_relation(THEORY_DS, "Equations", EQ_DS, "Theories")

    theories = query_all(THEORY_DS)
    researchers = {title_of(p): p["id"] for p in query_all(RESEARCHER_DS) if title_of(p)}
    equations = {title_of(p): p["id"] for p in query_all(EQ_DS) if title_of(p)}
    print(f"\nresolved {len(theories)} theories, {len(researchers)} researchers, {len(equations)} equations")

    apply_links(theories, "Proponent", proponents, researchers, "proponent")
    apply_links(theories, "Equations", THEORY_EQUATIONS, equations, "equation")

    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
