"""Pull formula, molecular weight, density, hardness and elemental composition
for every mineral from webmineral.com into data/chemistry/webmineral.json.

    python3 scripts/fetch_webmineral.py            # every mineral in notion-all.json + EXTRA
    python3 scripts/fetch_webmineral.py Hematite   # just these names

Why: the Minerals DB was imported from a webmineral-derived dataset whose
per-element columns are a broken parse of the formula (hematite Fe:O = 1:1,
gypsum containing tungsten), and whose Molar Mass and Calculated Density were
computed from those broken counts — so they are wrong for most of the 3,116
rows, and the site was displaying them. Only Specific Gravity and Mohs are
independent measurements. Webmineral is the origin of that dataset and still
serves each mineral's page with the true formula, molecular weight, measured
density and a mass-% composition table, so this goes back to the source.

Output per mineral: {"formula", "mw", "density", "hardness", "pct": {"Fe": 69.94, ...},
"url"} — or {"error": ...} for names webmineral does not have (IMA names newer
than the site, mostly). Resumable: names already in the file are skipped.
Four threads, a real User-Agent, ~0.5 s per page — about eight minutes for
the whole table.
"""
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "chemistry" / "webmineral.json"
UA = "kosmos-portal/1.0 (personal science site; mineral formula lookup; contact via github.com/Cbrunold/kosmos)"

# ore minerals named in the extraction texts that the Minerals DB does not have
EXTRA = [
    "Chalcopyrite", "Bornite", "Chalcocite", "Malachite", "Azurite", "Chrysocolla", "Sphalerite",
    "Pentlandite", "Uraninite", "Coffinite", "Carnotite", "Bastnäsite-(Ce)", "Monazite-(Ce)",
    "Xenotime-(Y)", "Ilmenite", "Rutile", "Ferberite", "Hübnerite", "Scheelite", "Molybdenite",
    "Pyrolusite", "Braunite", "Rhodochrosite", "Petalite", "Lepidolite", "Stibnite", "Cinnabar",
    "Bertrandite", "Beryl", "Celestine", "Barite", "Borax", "Kernite", "Colemanite", "Ulexite",
    "Sylvite", "Carnallite", "Fluorapatite", "Boehmite", "Diaspore", "Goethite", "Heterogenite",
    "Carrollite", "Pyrochlore", "Tantalite-(Fe)", "Columbite-(Fe)", "Arsenopyrite", "Acanthite",
    "Sperrylite", "Cooperite", "Zircon", "Graphite", "Dolomite", "Magnesite", "Greenockite",
    "Wolframite", "Magnetite", "Hematite", "Cassiterite", "Chromite", "Spodumene", "Gibbsite",
    "Halite", "Calcite", "Quartz", "Gypsum", "Fluorite", "Galena", "Pyrite", "Corundum",
]

ELEMENT_NAMES = {}   # "Iron" -> "Fe", filled from elements.json, plus the spellings webmineral uses


def load_names():
    els = json.load(open(ROOT / "data" / "chemistry" / "elements.json"))
    for e in els:
        ELEMENT_NAMES[e["name"]] = e["notation"]
    ELEMENT_NAMES.update({"Aluminum": "Al", "Aluminium": "Al", "Sulfur": "S", "Sulphur": "S",
                          "Cesium": "Cs", "Caesium": "Cs", "Nitrogen": "N", "Potassium": "K",
                          "Sodium": "Na", "Iron": "Fe", "Copper": "Cu", "Silver": "Ag", "Gold": "Au",
                          "Tin": "Sn", "Lead": "Pb", "Mercury": "Hg", "Antimony": "Sb", "Tungsten": "W"})


def wm_slug(name: str) -> str:
    return unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().replace(" ", "")


def parse(page: str) -> dict:
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    out = {}
    m = re.search(r"Chemical Formula: (.+?) Composition:", t)
    if m:
        out["formula"] = m.group(1).strip()
    m = re.search(r"Molecular Weight = ([\d,]+\.?\d*) gm", t)
    if m:
        out["mw"] = float(m.group(1).replace(",", ""))
    m = re.search(r"Density: ([\d.]+)", t)
    if m:
        try:
            out["density"] = float(m.group(1))
        except ValueError:
            pass
    m = re.search(r"Hardness: ([\d.]+)", t)
    if m:
        try:
            out["hardness"] = float(m.group(1))
        except ValueError:
            pass
    # composition table: "Iron 69.94 % Fe ..." between the weight and the empirical formula
    a = t.find("Molecular Weight")
    b = t.find("Empirical Formula", a)
    seg = t[a:b] if a >= 0 and b > a else ""
    pct = {}
    for name, val, sym in re.findall(r"([A-Z][a-z]+) ([\d.]+) % ([A-Z][a-z]?)\b", seg):
        if ELEMENT_NAMES.get(name) == sym:
            pct[sym] = round(pct.get(sym, 0) + float(val), 2)
    if pct:
        out["pct"] = pct
    return out


def fetch(name: str) -> tuple:
    url = f"http://webmineral.com/data/{wm_slug(name)}.shtml"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            page = urllib.request.urlopen(req, timeout=25).read().decode("latin-1")
            d = parse(page)
            d["url"] = url
            if "formula" not in d and "mw" not in d:
                d = {"error": "page has no formula/weight", "url": url}
            return name, d
        except urllib.error.HTTPError as e:
            return name, {"error": f"HTTP {e.code}", "url": url}
        except Exception as e:  # noqa: BLE001 — network hiccup; retry
            if attempt == 2:
                return name, {"error": str(e)[:120], "url": url}
            time.sleep(1.5 * (attempt + 1))
    return name, {"error": "unreachable", "url": url}


def main():
    load_names()
    have = json.load(open(OUT)) if OUT.exists() else {}
    if len(sys.argv) > 1:
        names = sys.argv[1:]
    else:
        notion = json.load(open(ROOT / "data" / "notion-all.json"))
        names = [m["Name"] for m in notion["minerals"] if m.get("Name")] + EXTRA
    todo = [n for n in dict.fromkeys(names) if n not in have or (len(sys.argv) > 1)]
    print(f"{len(names)} names, {len(have)} already fetched, {len(todo)} to go")
    done = 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, d in pool.map(fetch, todo):
            have[name] = d
            done += 1
            if done % 100 == 0 or done == len(todo):
                OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False, sort_keys=True))
                errs = sum(1 for v in have.values() if "error" in v)
                print(f"  {done}/{len(todo)}  ({time.time() - t0:.0f}s)  errors so far: {errs}", flush=True)
    OUT.write_text(json.dumps(have, indent=1, ensure_ascii=False, sort_keys=True))
    ok = sum(1 for v in have.values() if "formula" in v)
    errs = [(k, v["error"]) for k, v in have.items() if "error" in v]
    print(f"done: {ok} with formula, {len(errs)} errors -> {OUT.relative_to(ROOT)}")
    if errs:
        print("  errors:", errs[:15], "..." if len(errs) > 15 else "")


if __name__ == "__main__":
    main()
