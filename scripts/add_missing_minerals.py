"""Add four classic minerals missing from the Minerals [DB]: gold, diamond,
pyrite, galena. Sets composition columns, physical properties, and the
Chemical Properties relation to the element pages. Skips any that exist.
"""
import json
import urllib.request

TOKEN = None
for line in open("/srv/kosmos/.env"):
    if line.startswith("NOTION_TOKEN="):
        TOKEN = line.split("=", 1)[1].strip().strip("\"'")
assert TOKEN

H = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}
MIN_DS = "a2db78db-efb7-4952-b8bc-e4ab98d42264"
EL_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"


def call(m, u, b=None):
    req = urllib.request.Request(u, data=json.dumps(b).encode() if b else None, headers=H, method=m)
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


el_id = {}
for r in query_all(EL_DS):
    sym = "".join(x["plain_text"] for x in r["properties"]["Notation"]["rich_text"]).strip()
    if sym:
        el_id[sym] = r["id"]

existing = {"".join(x["plain_text"] for x in r["properties"]["Name"]["title"]).strip()
            for r in query_all(MIN_DS)}

# name, formula, {element column: atoms per formula}, mohs, specific gravity,
# molar mass, refractive index (None if opaque), dispersion, element symbols
NEW = [
    ("Gold", "Au", {"Gold": 1}, 2.75, 19.3, 196.9666, None, None, ["Au"]),
    ("Diamond", "C", {"Carbon": 1}, 10.0, 3.51, 12.011, 2.418, 0.044, ["C"]),
    ("Pyrite", "FeS2", {"Iron": 1, "Sulfur": 2}, 6.25, 5.01, 119.975, None, None, ["Fe", "S"]),
    ("Galena", "PbS", {"Lead": 1, "Sulfur": 1}, 2.5, 7.6, 239.266, None, None, ["Pb", "S"]),
]

for name, formula, comp, mohs, sg, mm, ri, disp, syms in NEW:
    if name in existing:
        print("  exists, skipping:", name)
        continue
    props = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Formula": {"rich_text": [{"text": {"content": formula}}]},
        "Mohs Hardness": {"number": mohs},
        "Specific Gravity": {"number": sg},
        "Molar Mass": {"number": mm},
        "Calculated Density": {"number": sg},
        "count": {"number": sum(comp.values())},
        "Chemical Properties": {"relation": [{"id": el_id[s]} for s in syms]},
    }
    for col, n in comp.items():
        props[col] = {"number": n}
    if ri is not None:
        props["Refractive Index"] = {"number": ri}
    if disp is not None:
        props["Dispersion"] = {"number": disp}
    call("POST", "https://api.notion.com/v1/pages",
         {"parent": {"type": "data_source_id", "data_source_id": MIN_DS}, "properties": props})
    print(f"  added: {name} ({formula}) · Mohs {mohs} · SG {sg} · elements {syms}")
