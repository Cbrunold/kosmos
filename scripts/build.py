"""Assemble every page of the site from web/ sources and the synced Notion data.

    python3 scripts/build.py

Inputs:  web/*.template.html + web/shared.css + web/analyzer.{css,html,js}
         data/chemistry/elements.json   (scripts/fetch_elements.py)
         data/notion-all.json           (scripts/fetch_all.py)
Outputs: public/index.html   (periodic table, served at /elements)
         public/home.html    (tile launcher, served at /)
         public/{minerals,cosmos,forces,theories}.html
"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
PUB = ROOT / "public"
SHARED = (WEB / "shared.css").read_text()

elements = json.load(open(ROOT / "data" / "chemistry" / "elements.json"))
notion = json.load(open(ROOT / "data" / "notion-all.json"))


def compact(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")


def write_page(template: str, out: str, data=None, extra: dict | None = None):
    tpl = (WEB / template).read_text()
    tpl = tpl.replace("__SHARED__", SHARED)
    if data is not None:
        tpl = tpl.replace("__DATA__", compact(data))
    for k, v in (extra or {}).items():
        tpl = tpl.replace(k, str(v))
    (PUB / out).write_text(tpl)
    print(f"wrote {len(tpl):>7} bytes -> public/{out}")


# ---------------- periodic table (public/index.html) ----------------
def build_elements_page():
    tpl = (WEB / "periodic-table.template.html").read_text()
    css = (WEB / "analyzer.css").read_text()
    html = (WEB / "analyzer.html").read_text()
    js = (WEB / "analyzer.js").read_text()
    for old, new in [
        ("q.addEventListener('input', paint);", "q.addEventListener('input', () => paint());"),
        ("matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paint);",
         "matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => paint());"),
    ]:
        assert old in tpl, f"template drifted, marker missing: {old}"
        tpl = tpl.replace(old, new)
    tpl = tpl.replace("</style>", css + "</style>", 1)
    tpl = tpl.replace('<div class="layout">', html + '\n<div class="layout">', 1)
    head, sep, _ = tpl.rpartition("</script>")
    tpl = head + js + sep + "\n"
    tpl = tpl.replace("__DATA__", compact(elements))
    # equation lookup for the element detail panel: pageId -> {name, field, slug}
    import re as _re
    def _slug(s):
        import unicodedata
        s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
        return _re.sub(r"^-|-$", "", _re.sub(r"[^a-z0-9]+", "-", s))
    eq_lookup = {e["id"]: {"name": e["Name"], "field": e.get("Field"), "slug": _slug(e["Name"])}
                 for e in notion.get("equations", [])}
    tpl = tpl.replace("__EQUATIONS__", compact(eq_lookup))
    (PUB / "index.html").write_text(tpl)
    print(f"wrote {len(tpl):>7} bytes -> public/index.html")


# ---------------- element-name -> symbol mapping for minerals ----------------
NAME_TO_SYM = {e["name"]: e["notation"] for e in elements}
NAME_TO_SYM.update({"Aluminium": "Al", "Aluminum": "Al", "Cesium": "Cs", "Caesium": "Cs",
                    "Sulphur": "S", "Nitrogen": "N"})  # Notion titles it "Nitrogen / Azote"
ION_TO_SYMS = {
    "Ammonium": ["N", "H"], "Carbonate": ["C", "O"], "Cyanide": ["C", "N"],
    "Hydroxyl": ["O", "H"], "Nitrate": ["N", "O"], "Sulphate": ["S", "O"],
    "Phosphate": ["P", "O"], "Acetate": ["C", "H", "O"], "Hydrated Water": ["H", "O"],
}
NON_ELEMENT = {
    "id", "url", "lastEdited", "Name", "Formula", "Chemical Properties", "count", "Index",
    "Approval Year", "Molar Mass", "Molar Volume", "Calculated Density", "Specific Gravity",
    "Mohs Hardness", "Refractive Index", "Dispersion", "Optical", "Crystal Structure", "Diaphaneity",
}


def build_minerals_page():
    rows, contains = [], Counter()
    unmapped = set()
    for m in notion["minerals"]:
        weights = {}
        for col, v in m.items():
            if col in NON_ELEMENT or not isinstance(v, (int, float)) or v <= 0:
                continue
            if col in ION_TO_SYMS:
                for s in ION_TO_SYMS[col]:
                    weights[s] = weights.get(s, 0) + v
            elif col in NAME_TO_SYM:
                s = NAME_TO_SYM[col]
                weights[s] = weights.get(s, 0) + v
            else:
                unmapped.add(col)
        syms = [s for s, _ in sorted(weights.items(), key=lambda kv: -kv[1])]
        for s in set(syms):
            contains[s] += 1
        sg = m.get("Specific Gravity")
        if sg is None and m.get("Calculated Density"):
            sg = round(m["Calculated Density"], 2)
        rows.append([
            m.get("Name") or "?",
            m.get("Mohs Hardness"),
            round(sg, 2) if sg is not None else None,
            round(m["Molar Mass"], 1) if m.get("Molar Mass") else None,
            " ".join(syms),
        ])
    if unmapped:
        print("  note: unmapped mineral columns ignored:", sorted(unmapped))
    rows.sort(key=lambda r: r[0])

    sys_name = {r["id"]: r.get("Name") for r in notion["crystalSystems"]}
    gems = [{
        "name": g.get("Name"),
        "hardness": g.get("Hardness"),
        "price": g.get("$ per Carat"),
        "kind": g.get("Select"),
        "system": sys_name.get((g.get("Crystal System") or [None])[0]),
    } for g in notion["gemstones"] if g.get("Name")]

    data = {
        "minerals": rows,
        "topElements": contains.most_common(24),
        "gems": gems,
        "rocks": [{"name": r.get("Name"), "comment": r.get("Comment")} for r in notion["rockTypes"]],
        "silicates": [{
            "name": s.get("Name"),
            "structure": ", ".join(s.get("Structure") or []),
            "formula": s.get("Formula"),
            "examples": s.get("examples"),
        } for s in notion["silicateMinerals"]],
    }
    write_page("minerals.template.html", "minerals.html", data)
    return len(rows), len(gems)


# ---------------- cosmos ----------------
SPECTRAL_ORDER = "OBAFGKMLTY"
TYPE_ORDER = [
    "Stars", "Planets", "Exoplanets", "Moons (Natural Satellites)", "Asteroids", "Comets",
    "Meteoroids Meteors & Meteorites", "Nebulae", "Star Clusters", "Galaxies",
    "Quasars & Active Galactic Nuclei (AGN)", "Black Holes", "Pulsars and Magnetars",
    "Protostars & Pre-Main Sequence Stars", "Accretion Disks", "Gravitational Waves Sources",
    "Cosmic Structures", "Dark Matter &  Dark Energy",
]


def build_cosmos_page():
    sun = None
    for o in notion["celestialObjects"]:
        if o.get("Object ID"):
            mass = o.get("Mass")
            exp = int(f"{mass:e}".split("e")[1]) if mass else None
            mant = mass / 10 ** exp if mass else None
            sup = str(exp).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")) if exp else ""
            sun = {
                "name": o["Object ID"],
                "mass": f"{mant:g} × 10{sup}" if mass else "?",
                "diameter": o.get("Diameter (km)") or 0,
                "type": o.get("Type") or "?",
            }
    spectral = []
    for s in notion["spectralTypes"]:
        name = s.get("Name") or ""
        letter = name[0].upper() if name else "?"
        spectral.append({
            "letter": letter, "name": name, "temp": s.get("Temperature"),
            "char": s.get("Characteristics"), "colors": s.get("Color") or [],
        })
    spectral.sort(key=lambda s: SPECTRAL_ORDER.index(s["letter"]) if s["letter"] in SPECTRAL_ORDER else 99)

    groups = defaultdict(list)
    for t in notion["celestialTypes"]:
        if t.get("Name"):
            groups[t.get("Type") or "Other"].append(t["Name"])
    types = [{"type": k, "entries": sorted(groups[k])} for k in
             sorted(groups, key=lambda k: TYPE_ORDER.index(k) if k in TYPE_ORDER else 99)]

    instruments = [{
        "name": i.get("Name"), "type": i.get("Type"), "desc": i.get("Description"),
        "wavelengths": i.get("Wavelength_Range") or [],
    } for i in notion["instruments"] if i.get("Name")]

    researchers = sorted(r["Name"] for r in notion["researchers"] if r.get("Name"))

    data = {"sun": sun, "spectral": spectral, "types": types,
            "instruments": instruments, "researchers": researchers}
    write_page("cosmos.template.html", "cosmos.html", data)
    return len(types), len(spectral), len(instruments)


# ---------------- home ----------------
def build_home(n_min, n_gems, n_classes, n_spectral, n_instr):
    gaps = sum(1 for e in elements
               if e["meltingPt"] is None or e["boilingPt"] is None
               or e["density"] is None or e["occurrence"] is None)
    dates = [e["lastEdited"] for e in elements if e.get("lastEdited")]
    for rows in notion.values():
        dates += [r["lastEdited"] for r in rows if r.get("lastEdited")]
    sync = max(dates)[:10] if dates else "?"
    eqs = notion.get("equations", [])
    years = [e["Year"] for e in eqs if e.get("Year")]
    oldest = min(years) if years else None
    oldest_str = "?" if oldest is None else (f"{-oldest} BCE" if oldest < 0 else str(oldest))
    write_page("home.template.html", "home.html", extra={
        "__N_GAPS__": gaps,
        "__N_MINERALS__": f"{n_min:,}",
        "__N_GEMS__": n_gems,
        "__N_CLASSES__": n_classes,
        "__N_SPECTRAL__": n_spectral,
        "__N_INSTR__": n_instr,
        "__N_THEORIES__": len(notion["theories"]),
        "__N_EQ__": len(eqs),
        "__N_EQFIELDS__": len({e.get("Field") for e in eqs if e.get("Field")}),
        "__EQ_OLDEST__": oldest_str,
        "__SYNC_DATE__": sync,
    })


if __name__ == "__main__":
    build_elements_page()
    n_min, n_gems = build_minerals_page()
    n_classes, n_spectral, n_instr = build_cosmos_page()
    write_page("forces.template.html", "forces.html",
               [{k: v for k, v in f.items() if k != "id"} for f in notion["forces"]])
    write_page("theories.template.html", "theories.html",
               [{k: v for k, v in t.items() if k != "id"} for t in notion["theories"]])
    # equations keep their Notion page id — the Related relation targets it;
    # __ELEMENTS__ is a pageId -> {sym,name} lookup for the Elements relation
    el_lookup = {e["pageId"]: {"sym": e["notation"], "name": e["name"], "z": e["atomicNumber"]}
                 for e in elements}
    write_page("equations.template.html", "equations.html",
               [{k: v for k, v in e.items() if k not in ("url", "lastEdited")}
                for e in notion.get("equations", [])],
               extra={"__ELEMENTS__": compact(el_lookup)})
    build_home(n_min, n_gems, n_classes, n_spectral, n_instr)
