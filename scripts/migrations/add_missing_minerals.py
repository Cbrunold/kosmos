"""Add four classic minerals missing from the Minerals [DB]: gold, diamond,
pyrite, galena. Sets composition columns, physical properties, and the
Chemical Properties relation to the element pages. Skips any that exist.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from notion import call, headers, query_all  # noqa: E402

H = headers()
MIN_DS = "a2db78db-efb7-4952-b8bc-e4ab98d42264"
EL_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"


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
