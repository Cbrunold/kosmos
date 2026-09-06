"""Link constants to the equations they appear in.

Adds an "Equations" dual-property relation on the Constants [DB] (each equation
page gains a "Constants" backlink), using the CONST_EQUATIONS map in
seed_constants.py. Idempotent; unions with anything already set in Notion.

Run on the VPS:  python3 scripts/link_constants.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notion import token, call, query_all  # noqa: E402
from seed_constants import CONST_EQUATIONS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"
EQ_DB = "300fc8ac-ca04-429d-a732-406181d9f4b9"
C_DS = "22e47e69-84c2-44e7-ae04-f1bf3dc80ebe"
PROP = "Equations"


H = {"Authorization": f"Bearer {token()}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}


def main():
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{C_DS}")
    if PROP not in ds["properties"]:
        for endpoint, body in [
            (f"https://api.notion.com/v1/data_sources/{C_DS}",
             {"properties": {PROP: {"relation": {"data_source_id": EQ_DS, "type": "dual_property",
                                                 "dual_property": {"synced_property_name": "Constants"}}}}}),
            (f"https://api.notion.com/v1/data_sources/{C_DS}",
             {"properties": {PROP: {"relation": {"data_source_id": EQ_DS, "type": "single_property",
                                                 "single_property": {}}}}}),
        ]:
            try:
                call("PATCH", endpoint, body)
                print("created Equations relation on Constants [DB]")
                break
            except urllib.error.HTTPError as e:
                print("  attempt failed:", e.code, e.read().decode()[:160])
    else:
        print("Equations relation already exists")

    eq_by_name = {}
    for r in query_all(EQ_DS):
        eq_by_name["".join(x["plain_text"] for x in r["properties"]["Name"]["title"])] = r["id"]

    consts = query_all(C_DS)
    changed, edges, missing = 0, 0, set()
    for c in consts:
        sym = "".join(x["plain_text"] for x in c["properties"]["Symbol"]["rich_text"]).strip()
        wanted_names = CONST_EQUATIONS.get(sym, [])
        if not wanted_names:
            continue
        ids = set()
        for n in wanted_names:
            if n in eq_by_name:
                ids.add(eq_by_name[n])
            else:
                missing.add(n)
        cur = {x["id"] for x in (c["properties"].get(PROP, {}).get("relation") or [])}
        new = cur | ids
        edges += len(new)
        if new != cur:
            call("PATCH", f"https://api.notion.com/v1/pages/{c['id']}",
                 {"properties": {PROP: {"relation": [{"id": x} for x in sorted(new)]}}})
            changed += 1
    if missing:
        print("unknown equation names ignored:", sorted(missing))
    print(f"updated {changed} constants · {edges} constant→equation links")


if __name__ == "__main__":
    main()
