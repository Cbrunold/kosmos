"""Repair the Minerals DB from webmineral data, and add the missing ore minerals.

The audit (2026-08-16): the per-element columns were a broken parse of the
formula — hematite Fe:O = 1:1, gypsum containing tungsten, one mineral
containing moscovium — and Molar Mass, Molar Volume and Calculated Density had
been computed from those broken counts, so 85 % of the rows that could be
checked against a measured Specific Gravity disagreed with it. Only Specific
Gravity and Mohs Hardness were independent measurements. Only 5 of 3,116 rows
had a Formula at all.

What this writes, from data/chemistry/webmineral.json (scripts/fetch_webmineral.py):
  Formula            — the mineral's formula, where empty
  Molar Mass         — the true molecular weight (overwritten: the old value was derived garbage)
  Specific Gravity   — webmineral's measured density, only where the DB had none
  Mohs Hardness      — only where the DB had none
  <Element> columns  — MASS PERCENT of each element, replacing the old counts;
                       columns for elements the mineral does not contain are cleared
  Ion columns        — (Ammonium, Carbonate, …) cleared: redundant under mass %
  Calculated Density, Molar Volume — cleared: derived from the broken counts, and
                       the site no longer reads them

So the semantics of the element columns change from "atom count" (wrong) to
"mass %" (right, and what the site describes as elemental makeup). Everything
on the site that read them treated them as weights and sorted by size, so
nothing downstream needs to change meaning — the sort order just becomes true.

Rows webmineral does not know (IMA names newer than the site) are left as
they were and counted; build.py hides Molar Mass for any row without a Formula.

Missing ore minerals named in the extraction texts (chalcopyrite, sphalerite,
uraninite, pentlandite, bastnäsite…) are added as new rows from the same source.

Idempotent: a row whose Formula and Molar Mass already match is skipped, so a
re-run costs a query, not 3,000 writes. First run is ~3,100 PATCHes — about
twenty minutes at Notion's rate limit.
Run on the VPS:  ./deploy.sh seed_minerals_fix
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, query_all, title_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MINERALS_DS = "a2db78db-efb7-4952-b8bc-e4ab98d42264"
WM = json.load(open(ROOT / "data" / "chemistry" / "webmineral.json"))

ION_COLUMNS = {"Ammonium", "Carbonate", "Cyanide", "Hydroxyl", "Nitrate", "Sulphate",
               "Phosphate", "Acetate", "Hydrated Water"}
DERIVED_COLUMNS = {"Calculated Density", "Molar Volume"}

# the ore minerals the extraction texts name and the DB lacked — added as rows
NEW_ROWS = [
    "Chalcopyrite", "Bornite", "Chalcocite", "Malachite", "Azurite", "Chrysocolla", "Sphalerite",
    "Pentlandite", "Uraninite", "Coffinite", "Carnotite", "Bastnäsite-(Ce)", "Monazite-(Ce)",
    "Xenotime-(Y)", "Ilmenite", "Rutile", "Ferberite", "Hübnerite", "Scheelite", "Molybdenite",
    "Pyrolusite", "Rhodochrosite", "Petalite", "Lepidolite", "Stibnite", "Cinnabar",
    "Bertrandite", "Beryl", "Celestine", "Barite", "Borax", "Kernite", "Colemanite", "Ulexite",
    "Sylvite", "Carnallite", "Fluorapatite", "Boehmite", "Diaspore", "Goethite", "Heterogenite",
    "Carrollite", "Pyrochlore", "Tantalite-(Fe)", "Columbite-(Fe)", "Arsenopyrite", "Acanthite",
    "Sperrylite", "Cooperite", "Zircon", "Graphite", "Dolomite", "Magnesite", "Greenockite",
]
# webmineral files a few of these under a different name; Braunite it does not have at all
SOURCE_ALIAS = {"Fluorapatite": "Apatite-(CaF)", "Heterogenite": "Heterogenite-3R"}


def element_columns(schema: dict) -> dict:
    """Column name -> symbol, for the number columns that are elements."""
    els = json.load(open(ROOT / "data" / "chemistry" / "elements.json"))
    names = {e["name"]: e["notation"] for e in els}
    names.update({"Aluminium": "Al", "Aluminum": "Al", "Sulfur": "S", "Sulphur": "S",
                  "Cesium": "Cs", "Caesium": "Cs", "Nitrogen": "N"})
    return {col: names[col] for col, kind in schema.items() if kind == "number" and col in names}


def num(page, prop):
    p = page["properties"].get(prop) or {}
    return p.get("number")


def text(page, prop):
    p = page["properties"].get(prop) or {}
    return "".join(x["plain_text"] for x in p.get("rich_text", [])).strip()


def payload_for(page, d, cols, schema, is_new=False):
    """Properties to write for one mineral given its webmineral record. None = nothing to do."""
    props = {}
    if d.get("formula") and (is_new or not text(page, "Formula")):
        props["Formula"] = {"rich_text": [{"text": {"content": d["formula"]}}]}
    if d.get("mw") is not None and (is_new or num(page, "Molar Mass") != d["mw"]):
        props["Molar Mass"] = {"number": d["mw"]}
    if d.get("density") is not None and (is_new or not num(page, "Specific Gravity")):
        props["Specific Gravity"] = {"number": d["density"]}
    if d.get("hardness") is not None and (is_new or num(page, "Mohs Hardness") is None):
        props["Mohs Hardness"] = {"number": d["hardness"]}
    pct = d.get("pct") or {}
    if pct:
        by_sym = {}
        for col, sym in cols.items():
            by_sym.setdefault(sym, col)          # first column for a symbol wins (Aluminium vs Aluminum)
        for col, sym in cols.items():
            want = pct.get(sym) if by_sym.get(sym) == col else None
            cur = None if is_new else num(page, col)
            if want is not None:
                if cur != want:
                    props[col] = {"number": want}
            elif cur:                              # element the mineral does not contain — clear
                props[col] = {"number": None}
        for col in ION_COLUMNS | DERIVED_COLUMNS:
            if col in schema and (is_new is False and num(page, col)):
                props[col] = {"number": None}
    return props or None


def main():
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{MINERALS_DS}")
    schema = {k: v["type"] for k, v in ds["properties"].items()}
    cols = element_columns(schema)
    print(f"minerals schema: {len(schema)} properties, {len(cols)} element columns")

    pages = {title_of(p, "Name"): p for p in query_all(MINERALS_DS) if title_of(p, "Name")}
    print(f"{len(pages)} minerals in Notion, {len(WM)} webmineral records")

    updated = skipped = nodata = 0
    t0 = time.time()
    for i, (name, page) in enumerate(pages.items(), 1):
        d = WM.get(name)
        if not d or "error" in d:
            nodata += 1
            continue
        props = payload_for(page, d, cols, schema)
        if props:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": props})
            updated += 1
        else:
            skipped += 1
        if i % 250 == 0:
            print(f"  {i}/{len(pages)}  updated {updated}, unchanged {skipped}, no source {nodata}  ({time.time() - t0:.0f}s)", flush=True)
    print(f"repair: {updated} rows rewritten, {skipped} already right, {nodata} with no webmineral record (left as they were)")

    added = present = missing_src = 0
    for name in NEW_ROWS:
        if name in pages:
            present += 1
            continue
        d = WM.get(SOURCE_ALIAS.get(name, name))
        if not d or "error" in d:
            missing_src += 1
            print("  no webmineral record for new row:", name)
            continue
        props = payload_for({"properties": {}}, d, cols, schema, is_new=True) or {}
        props["Name"] = {"title": [{"text": {"content": name}}]}
        call("POST", "https://api.notion.com/v1/pages",
             {"parent": {"type": "data_source_id", "data_source_id": MINERALS_DS}, "properties": props})
        added += 1
    print(f"ore minerals: {added} added, {present} already present, {missing_src} without a source record")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
