"""Assemble every page of the site from web/ sources and the synced Notion data.

    python3 scripts/build.py

Inputs:  web/*.template.html + web/shared.css + web/analyzer.{css,html,js}
         data/chemistry/elements.json   (scripts/fetch_elements.py)
         data/notion-all.json           (scripts/fetch_all.py)
Outputs: public/index.html   (periodic table, served at /elements)
         public/home.html    (tile launcher, served at /)
         public/{minerals,cosmos,forces,theories,timeline}.html
         public/mines.html   (world map of flagship mines + extraction per element)
         public/machines.html, public/skills.html   (the engineering half)
         public/search.json  (flat index behind the home-page search bar)
"""
import json
import math
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


def term_pattern(term: str):
    """Whole words, any inflection (-s, -es, -ed, -ing); multiword with flexible
    spaces or hyphens. Used to trace glossary terms through prose, both ways:
    /glossary lists what uses a term, /explainers lists the terms it covers."""
    words = [re.escape(w) for w in re.split(r"[\s-]+", term.strip()) if w]
    return re.compile(r"\b" + r"[\s-]+".join(words) + r"(?:s|es|ed|ing)?\b", re.IGNORECASE)


def glossary_matchers():
    """[(term, slug, [patterns])] for every glossary term — its name and aliases."""
    out = []
    for t in notion.get("glossary", []):
        if not t.get("Term"):
            continue
        names = [t["Term"]] + [a.strip() for a in (t.get("Aliases") or "").split(",") if a.strip()]
        out.append((t["Term"], slugify(t["Term"]), [term_pattern(n) for n in names if len(n) >= 2]))
    return out


def slugify(s: str) -> str:
    """Same slug rule as the equations page (card anchors) — keep in sync."""
    import unicodedata
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s))


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
    eq_lookup = {e["id"]: {"name": e["Name"], "field": e.get("Field"), "slug": slugify(e["Name"])}
                 for e in notion.get("equations", [])}
    tpl = tpl.replace("__EQUATIONS__", compact(eq_lookup))
    tpl = tpl.replace("__MINERALS__", compact(ELEMENT_MINERALS))
    tpl = tpl.replace("__MINESITES__", compact(mine_lookup()))
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


ELEMENT_MINERALS = {}   # symbol -> {"n": count, "examples": [names]} — filled by build_minerals_page
ELEMENT_MINERALS_BY_NAME = {}   # mineral name -> "Fe O Si" — also filled there, for the search index


def build_minerals_page():
    rows, contains = [], Counter()
    by_symbol = defaultdict(list)
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
        name = m.get("Name") or "?"
        ELEMENT_MINERALS_BY_NAME[name] = " ".join(syms)   # for the search index
        # sorted, not set order: string hashing is randomised per process, so an
        # unsorted set here makes the mineral lookups shuffle on every rebuild and
        # public/index.html churn with a diff that means nothing
        for s in sorted(set(syms)):
            contains[s] += 1
            # verified (has a Formula from the source) first, then hardest — so the
            # examples on the periodic table are ones whose membership is trustworthy
            by_symbol[s].append((bool(m.get("Formula")), m.get("Mohs Hardness") or 0, name))
        # Specific Gravity is a measurement; Calculated Density and Molar Mass were
        # derived from the broken import and are only trustworthy on rows that carry a
        # Formula (i.e. that seed_minerals_fix.py has rewritten from the source)
        sg = m.get("Specific Gravity") or None
        verified = bool(m.get("Formula"))
        rows.append([
            m.get("Name") or "?",
            m.get("Mohs Hardness"),
            round(sg, 2) if sg is not None else None,
            round(m["Molar Mass"], 1) if verified and m.get("Molar Mass") else None,
            " ".join(syms),
            m.get("Equations") or [],   # equation page ids (mirrored relation)
        ])
    if unmapped:
        print("  note: unmapped mineral columns ignored:", sorted(unmapped))
    rows.sort(key=lambda r: r[0])
    # per-element mineral summary for the periodic table's detail panel:
    # count plus a few examples (hardest first — the recognizable ones)
    for sym, entries in by_symbol.items():
        entries.sort(key=lambda t: (not t[0], -t[1], t[2]))
        ELEMENT_MINERALS[sym] = {"n": len(entries), "examples": [n for _, _, n in entries[:6]]}

    sys_name = {r["id"]: r.get("Name") for r in notion["crystalSystems"]}
    gems = [{
        "name": g.get("Name"),
        "hardness": g.get("Hardness"),
        "price": g.get("$ per Carat"),
        "kind": g.get("Select"),
        "system": sys_name.get((g.get("Crystal System") or [None])[0]),
    } for g in notion["gemstones"] if g.get("Name")]

    eq_lookup = {e["id"]: {"name": e["Name"], "field": e.get("Field"), "slug": slugify(e["Name"])}
                 for e in notion.get("equations", [])}
    data = {
        "minerals": rows,
        "equations": eq_lookup,
        "topElements": contains.most_common(24),
        "gems": gems,
        # slug: the glossary links here, so the cards need anchors to land on
        "rocks": [{"name": r.get("Name"), "comment": r.get("Comment"), "slug": slugify(r.get("Name") or "")}
                  for r in notion["rockTypes"]],
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


def obj_name(o) -> str | None:
    """Celestial object title. Renamed Object ID -> Name in Notion; read both."""
    return o.get("Name") or o.get("Object ID")


def eq_lookup_all():
    return {e["id"]: {"name": e["Name"], "field": e.get("Field"), "slug": slugify(e["Name"])}
            for e in notion.get("equations", [])}


# ---------------- per-equation lookup tables ----------------
# Some equations are only usable with a table of values beside them. Keyed by
# equation name; rendered under the significance text on the equations page.
# "rule" marks a row after which a labelled divider is drawn.
EQUATION_TABLES = {
    "Cosmological Equation of State": {
        "caption": "Every ingredient of the universe is one number, w. It fixes how that "
                   "ingredient dilutes as space expands, and so which era it dominates.",
        "columns": ["Component", "w", "ρ ∝", "Why"],
        "rows": [
            ["Stiff fluid", "1", "a⁻⁶", "The causal limit — sound travels at c. Hypothetical, "
                                        "and only ever in the first instants."],
            ["Radiation", "1/3", "a⁻⁴", "Photons and neutrinos. Volume dilution, plus one more "
                                        "factor of a as every wavelength is stretched."],
            ["Matter", "0", "a⁻³", "Baryons and cold dark matter. Pressureless, so it thins by "
                                   "volume alone."],
            ["Curvature", "−1/3", "a⁻²", "Not a fluid at all, but it enters the Friedmann equation "
                                         "as though it were one."],
            ["Cosmological constant", "−1", "a⁰", "Dark energy. Does not thin at all: the energy "
                                                  "density of space itself, unchanged as more space appears."],
            ["Phantom energy", "< −1", "grows", "Density rises as the universe expands. Ends in a "
                                                "Big Rip, and is not excluded by the data."],
        ],
        "rule_after": 3,
        "rule_text": "expansion accelerates below w = −1/3",
        "note": "Measured for dark energy: w = −1.03 ± 0.03 — maddeningly consistent with a plain "
                "cosmological constant. Radiation dominated until roughly 50,000 years, matter until "
                "about 9 billion; the constant has the upper hand from here.",
    },
}


def equation_tables():
    """Keyed by slug, so the page can look a table up from the card it belongs to."""
    names = {e["Name"] for e in notion.get("equations", [])}
    missing = sorted(set(EQUATION_TABLES) - names)
    if missing:
        print("  warning: lookup tables for unknown equations:", missing)
    return {slugify(n): t for n, t in EQUATION_TABLES.items() if n in names}


def build_cosmos_page():
    sun = None
    for o in notion["celestialObjects"]:
        # "Object ID" was the title property until it was renamed to "Name" on
        # 2026-08-15; accept either so a stale data snapshot still builds
        if obj_name(o):
            mass = o.get("Mass")
            exp = int(f"{mass:e}".split("e")[1]) if mass else None
            mant = mass / 10 ** exp if mass else None
            sup = str(exp).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")) if exp else ""
            sun = {
                "name": obj_name(o),
                "mass": f"{mant:g} × 10{sup}" if mass else "?",
                "diameter": o.get("Diameter (km)") or 0,
                "type": o.get("Type") or "?",
                "equations": o.get("Equations") or [],
            }
    spectral = []
    for s in notion["spectralTypes"]:
        name = s.get("Name") or ""
        letter = name[0].upper() if name else "?"
        spectral.append({
            "letter": letter, "name": name, "temp": s.get("Temperature"),
            "char": s.get("Characteristics"), "colors": s.get("Color") or [],
            "equations": s.get("Equations") or [],
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
        "equations": i.get("Equations") or [],
    } for i in notion["instruments"] if i.get("Name")]

    researchers = sorted(
        ({"name": r["Name"], "slug": slugify(r["Name"]), "life": r.get("Lifespan"),
          "field": r.get("Field"), "known": r.get("Known For"), "nobel": r.get("Nobel")}
         for r in notion["researchers"] if r.get("Name")),
        key=lambda r: r["name"].split()[-1])   # by surname, as a card index would be

    obs_by_id = {}
    observatories = []
    for o in notion.get("observatories", []):
        if not o.get("Name"):
            continue
        row = {"name": o["Name"], "type": o.get("Type"), "founded": o.get("Founded"),
               "where": o.get("Location"), "alt": o.get("Altitude (m)"),
               "notes": o.get("Notes"),
               "instruments": o.get("Primary_Instruments [DB]") or []}
        obs_by_id[o["id"]] = o["Name"]
        observatories.append(row)
    observatories.sort(key=lambda o: (o["founded"] is None, o["founded"] or 0))

    people_by_id = {r["id"]: r["Name"] for r in notion["researchers"] if r.get("Name")}
    instr_by_id = {i["id"]: i["Name"] for i in notion["instruments"] if i.get("Name")}
    for o in observatories:
        o["instruments"] = sorted(filter(None, (instr_by_id.get(i) for i in o["instruments"])))

    discoveries = []
    for x in notion.get("discoveries", []):
        if not x.get("Name"):
            continue
        discoveries.append({
            "name": x["Name"],
            "year": x.get("Year"),
            "what": x.get("Description"),
            "who": sorted(filter(None, (people_by_id.get(i) for i in (x.get("Discoverer") or [])))),
            "where": next((obs_by_id[i] for i in (x.get("Observatory") or []) if i in obs_by_id), None),
        })
    discoveries.sort(key=lambda d: (d["year"] is None, d["year"] or 0))

    missions = [{
        "name": m["Name"],
        "launch": m.get("Launch Date"),
        "end": m.get("End Date"),
        "status": m.get("Status"),
        "agency": m.get("Agency"),
        "dest": m.get("Destination"),
        "objective": m.get("Objective"),
    } for m in notion.get("missions", []) if m.get("Name")]
    missions.sort(key=lambda m: (m["launch"] is None, m["launch"] or ""))

    data = {"sun": sun, "spectral": spectral, "types": types,
            "instruments": instruments, "researchers": researchers,
            "observatories": observatories, "discoveries": discoveries,
            "missions": missions, "equations": eq_lookup_all()}
    write_page("cosmos.template.html", "cosmos.html", data)
    return (len(types), len(spectral), len(instruments), len(observatories),
            len(discoveries), len(missions))


# ---------------- cosmic timeline ----------------
ERA_ORDER = ["Very Early Universe", "Radiation Era", "Dark Ages",
             "Structure Formation", "Present", "Far Future"]


def build_timeline_page():
    """The history of the universe, ordered on a log axis of seconds after t = 0."""
    rows = notion.get("cosmicTimeline", [])
    th_lookup = {t["id"]: {"name": t["Name"], "slug": slugify(t["Name"]), "status": t.get("Status")}
                 for t in notion["theories"] if t.get("Name")}
    # people whose work is about an epoch — chips link to their card on /cosmos
    people = {r["id"]: {"name": r["Name"], "slug": slugify(r["Name"]), "life": r.get("Lifespan"),
                        "field": r.get("Field"), "known": r.get("Known For")}
              for r in notion["researchers"] if r.get("Name")}
    events = []
    for r in rows:
        if not r.get("Event"):
            continue
        events.append({
            "event": r["Event"],
            "era": r.get("Era"),
            "secs": r.get("Seconds After Big Bang"),
            "when": r.get("When"),
            "temp": r.get("Temperature (K)"),
            "z": r.get("Redshift"),
            "what": r.get("What Happened"),
            "equations": r.get("Equations") or [],
            "theories": r.get("Theories") or [],
            "people": r.get("Researchers") or [],
        })
    # sort on the number, not the prose — that is what the column is for
    events.sort(key=lambda e: (e["secs"] is None, e["secs"] if e["secs"] is not None else 0))
    data = {"events": events, "equations": eq_lookup_all(), "theories": th_lookup,
            "people": people,
            "eras": [e for e in ERA_ORDER if any(x["era"] == e for x in events)]}
    write_page("timeline.template.html", "timeline.html", data)
    secs = [e["secs"] for e in events if isinstance(e["secs"], (int, float)) and e["secs"] > 0]
    decades = (math.ceil(math.log10(max(secs))) - math.floor(math.log10(min(secs)))) if len(secs) > 1 else 0
    return len(events), decades


# ---------------- mines ----------------
def mine_lookup():
    """Mine page id -> {name, country, type, slug}, for chips on the element panel."""
    return {m["id"]: {"name": m["Name"], "country": m.get("Country") or "", "type": m.get("Type") or "",
                      "slug": slugify(m["Name"])}
            for m in notion.get("mines", []) if m.get("Name")}


def build_mines_page():
    """A world map of the flagship mines, plus each element's extraction story."""
    by_id = {e["pageId"]: e for e in elements}
    mines = []
    for m in notion.get("mines", []):
        if not m.get("Name") or m.get("Latitude") is None or m.get("Longitude") is None:
            continue
        syms = sorted({by_id[i]["notation"] for i in (m.get("Commodities") or []) if i in by_id},
                      key=lambda x: x)
        mines.append({
            "name": m["Name"], "slug": slugify(m["Name"]),
            "country": m.get("Country"), "region": m.get("Region"),
            "lat": m["Latitude"], "lon": m["Longitude"],
            "type": m.get("Type"), "status": m.get("Status"),
            "opened": m.get("Opened"), "notes": m.get("Notes"),
            "syms": syms,
        })
    mines.sort(key=lambda m: m["name"])
    # per-element extraction, only for elements that have any of it
    ext = {}
    for e in elements:
        if e.get("minedAs") or e.get("extraction") or e.get("oreGrade") is not None:
            f = (e["oreGrade"] / e["abundance"]) if e.get("oreGrade") is not None and e.get("abundance") else None
            ext[e["notation"]] = {
                "name": e["name"], "minedAs": e.get("minedAs"), "grade": e.get("oreGrade"),
                "abundance": e.get("abundance"), "factor": f,
                "minerals": e.get("oreMinerals"), "text": e.get("extraction"),
                "n": sum(1 for m in mines if e["notation"] in m["syms"]),
            }
    land = (WEB / "land-110m.svgpath").read_text()
    write_page("mines.template.html", "mines.html",
               {"mines": mines, "extraction": ext},
               extra={"__LAND__": land})
    return len(mines), sum(1 for v in ext.values() if v["minedAs"] == "Primary")


# ---------------- machines & skills ----------------
GAMMA = 1.4


def _adiabat(p1, v1, v2, n=28):
    return [(v1 + (v2 - v1) * i / n, p1 * (v1 / (v1 + (v2 - v1) * i / n)) ** GAMMA) for i in range(n + 1)]


def _isotherm(p1, v1, v2, n=28):
    return [(v1 + (v2 - v1) * i / n, p1 * v1 / (v1 + (v2 - v1) * i / n)) for i in range(n + 1)]


def cycle_diagram(cycle: str):
    """A p–V loop for a named thermodynamic cycle, as normalised points the page
    draws with SVG. Ideal cycles with textbook parameters, chosen so the loop is
    legible rather than to match any particular machine — the note says which.
    Returns None for machines that have no cycle."""
    G = GAMMA
    if cycle == "Otto":
        r, k = 8.0, 3.0
        p2 = r ** G
        seg = [("1→2 adiabatic compression", _adiabat(1, 1, 1 / r)),
               ("2→3 heat added at constant volume (the spark)", [(1 / r, p2), (1 / r, k * p2)]),
               ("3→4 adiabatic expansion — the power stroke", _adiabat(k * p2, 1 / r, 1)),
               ("4→1 exhaust at constant volume", [(1, k), (1, 1)])]
        note = f"ideal η = 1 − r^(1−γ) = {1 - r ** (1 - G):.0%} at r = {r:g}, γ = {G}"
        logx = False
    elif cycle == "Diesel":
        r, a = 16.0, 2.0
        p2 = r ** G
        seg = [("1→2 adiabatic compression of air alone", _adiabat(1, 1, 1 / r)),
               ("2→3 fuel injected: heat added at constant pressure", [(1 / r, p2), (a / r, p2)]),
               ("3→4 adiabatic expansion", _adiabat(p2, a / r, 1)),
               ("4→1 exhaust at constant volume", [(1, p2 * (a / r) ** G), (1, 1)])]
        eta = 1 - (1 / r ** (G - 1)) * (a ** G - 1) / (G * (a - 1))
        note = f"ideal η = {eta:.0%} at r = {r:g}, cut-off α = {a:g}"
        logx = False
    elif cycle == "Brayton":
        rp, k = 8.0, 2.5
        v2 = rp ** (-1 / G)
        v3 = k * v2
        v4 = v3 * rp ** (1 / G)
        seg = [("1→2 adiabatic compression (compressor)", _adiabat(1, 1, v2)),
               ("2→3 heat added at constant pressure (combustor)", [(v2, rp), (v3, rp)]),
               ("3→4 adiabatic expansion (turbine, then nozzle)", _adiabat(rp, v3, v4)),
               ("4→1 heat rejected at constant pressure (the exhaust)", [(v4, 1), (1, 1)])]
        note = f"ideal η = 1 − (1/r_p)^((γ−1)/γ) = {1 - (1 / rp) ** ((G - 1) / G):.0%} at pressure ratio {rp:g}"
        logx = False
    elif cycle == "Carnot":
        t = 1.3    # T_h/T_c — small, so the loop is visible; real engines are 3–7
        v2 = 2.0
        v3 = v2 * t ** (1 / (G - 1))
        v4 = 1.0 * t ** (1 / (G - 1))
        p1 = 4.0
        p2 = p1 * 1 / v2
        p3 = p2 * (v2 / v3) ** G
        p4 = p3 * v3 / v4
        seg = [("1→2 isothermal expansion at T_h, taking heat in", _isotherm(p1, 1, v2)),
               ("2→3 adiabatic expansion, cooling to T_c", _adiabat(p2, v2, v3)),
               ("3→4 isothermal compression at T_c, rejecting heat", _isotherm(p3, v3, v4)),
               ("4→1 adiabatic compression back to T_h", _adiabat(p4, v4, 1))]
        note = f"ideal η = 1 − T_c/T_h = {1 - 1 / t:.0%} at T_h/T_c = {t} — drawn small so the loop shows; a real engine's ratio is 3–7"
        logx = False
    elif cycle == "Stirling":
        t, v2, p1 = 2.0, 2.5, 4.0
        p2 = p1 / v2
        p3 = p2 / t
        p4 = p3 * v2
        seg = [("1→2 isothermal expansion at T_h", _isotherm(p1, 1, v2)),
               ("2→3 cooling at constant volume — through the regenerator", [(v2, p2), (v2, p3)]),
               ("3→4 isothermal compression at T_c", _isotherm(p3, v2, 1)),
               ("4→1 heating at constant volume — the regenerator gives it back", [(1, p4), (1, p1)])]
        note = f"ideal η equals Carnot's, 1 − T_c/T_h = {1 - 1 / t:.0%} at T_h/T_c = {t:g}"
        logx = False
    elif cycle == "Rankine":
        v4 = 0.32 * (1.0 / 0.05) ** (1 / G)      # where the adiabat from state 3 meets condenser pressure
        seg = [("1→2 pump: liquid water to boiler pressure", [(0.02, 0.05), (0.02, 1.0)]),
               ("2→3 boiler: heat, boil, superheat at constant pressure", [(0.02, 1.0), (0.04, 1.0), (0.22, 1.0), (0.32, 1.0)]),
               ("3→4 turbine: adiabatic expansion to condenser pressure", _adiabat(1.0, 0.32, v4)),
               ("4→1 condenser: back to liquid at constant pressure", [(v4, 0.05), (0.02, 0.05)])]
        note = "schematic, volume on a log axis — steam expands about a thousandfold, which no linear plot can show"
        logx = True
    elif cycle == "Vapour-compression":
        g = 1.15
        v2 = (1 / 4.0) ** (1 / g)
        seg = [("1→2 compressor: vapour squeezed to condenser pressure", [(1 + (v2 - 1) * i / 28, (1 / (1 + (v2 - 1) * i / 28)) ** g) for i in range(29)]),
               ("2→3 condenser: gives up heat and liquefies at constant pressure", [(v2, 4.0), (0.02, 4.0)]),
               ("3→4 expansion valve: pressure drops, some liquid flashes", [(0.02, 4.0), (0.25, 1.0)]),
               ("4→1 evaporator: boils, taking heat from the cold side", [(0.25, 1.0), (1.0, 1.0)])]
        note = "run clockwise it is a refrigerator or heat pump; the same loop backwards is a Rankine engine. Schematic, log volume"
        logx = True
    else:
        return None
    pts = []
    for _, ps in seg:
        pts += ps if not pts else ps[1:]
    xs = [v for v, _ in pts]
    ys = [pp for _, pp in pts]
    if logx:
        lx = [math.log10(x) for x in xs]
        x0, x1 = min(lx), max(lx)
        nx = [(v - x0) / (x1 - x0) for v in lx]
    else:
        x0, x1 = min(xs), max(xs)
        nx = [(v - x0) / (x1 - x0) for v in xs]
    y0, y1 = 0.0, max(ys)
    ny = [(pp - y0) / (y1 - y0) for pp in ys]
    norm = [(round(a, 4), round(b, 4)) for a, b in zip(nx, ny)]
    # a state is the first point of each segment
    states, i = [], 0
    for k, (_, ps) in enumerate(seg):
        states.append([str(k + 1), *norm[i]])
        i += len(ps) - 1
    return {"pts": norm, "states": states, "procs": [name for name, _ in seg], "note": note, "logx": logx}


def build_machines_page():
    by_id_eq = eq_lookup_all()
    el_by_id = {e["pageId"]: {"sym": e["notation"], "name": e["name"]} for e in elements}
    people = {r["id"]: {"name": r["Name"], "slug": slugify(r["Name"]), "life": r.get("Lifespan"),
                        "known": r.get("Known For")} for r in notion["researchers"] if r.get("Name")}
    skills_by_id = {s["id"]: {"name": s["Name"], "slug": slugify(s["Name"])}
                    for s in notion.get("skills", []) if s.get("Name")}
    rows = []
    for m in notion.get("machines", []):
        if not m.get("Name"):
            continue
        rows.append({
            "name": m["Name"], "slug": slugify(m["Name"]), "kind": m.get("Kind"), "cycle": m.get("Cycle"),
            "year": m.get("Year"), "how": m.get("How It Works"), "eff": m.get("Efficiency"),
            "pd": m.get("Power Density"), "materials": m.get("Materials"), "used": m.get("Used In"),
            "inventors": [people[i] for i in (m.get("Inventors") or []) if i in people],
            "elements": [el_by_id[i] for i in (m.get("Elements") or []) if i in el_by_id],
            "equations": [by_id_eq[i] for i in (m.get("Equations") or []) if i in by_id_eq],
            "skills": [skills_by_id[i] for i in (m.get("Skills") or []) if i in skills_by_id],
            "diagram": cycle_diagram(m.get("Cycle")) if m.get("Cycle") and m.get("Cycle") != "None" else None,
        })
    rows.sort(key=lambda r: (r["year"] is None, r["year"] or 0))
    write_page("machines.template.html", "machines.html", {"machines": rows})
    return len(rows), sum(1 for r in rows if r["diagram"])


def build_skills_page():
    by_id_eq = eq_lookup_all()
    el_by_id = {e["pageId"]: {"sym": e["notation"], "name": e["name"]} for e in elements}
    machines_by_id = {m["id"]: {"name": m["Name"], "slug": slugify(m["Name"])}
                      for m in notion.get("machines", []) if m.get("Name")}
    rows = []
    for s in notion.get("skills", []):
        if not s.get("Name"):
            continue
        rows.append({
            "name": s["Name"], "slug": slugify(s["Name"]), "cat": s.get("Category"), "level": s.get("Difficulty"),
            "summary": s.get("Summary"), "science": s.get("The Science"), "tools": s.get("Tools"),
            "steps": [x.strip() for x in (s.get("Steps") or "").split("\n") if x.strip()],
            "safety": s.get("Safety"), "fails": s.get("How It Fails"), "done": s.get("Done When"),
            "elements": [el_by_id[i] for i in (s.get("Elements") or []) if i in el_by_id],
            "equations": [by_id_eq[i] for i in (s.get("Equations") or []) if i in by_id_eq],
            "machines": [machines_by_id[i] for i in (s.get("Machines") or []) if i in machines_by_id],
        })
    order = ["Joining", "Metalwork", "Making", "Electronics", "Building", "Rigging", "Measuring"]
    rows.sort(key=lambda r: (order.index(r["cat"]) if r["cat"] in order else 99, r["name"]))
    write_page("skills.template.html", "skills.html", {"skills": rows, "cats": [c for c in order if any(r["cat"] == c for r in rows)]})
    return len(rows)


# ---------------- glossary ----------------
def build_glossary_page():
    """Every term traced through every entity's text on the site, at build time.
    A term added in Notion traces itself; a page added anywhere shows up under
    the terms it uses. Nothing here is maintained by hand."""
    terms = [t for t in notion.get("glossary", []) if t.get("Term")]
    if not terms:
        write_page("glossary.template.html", "glossary.html", {"terms": [], "domains": []})
        return 0, 0
    # the corpus: (kind, name, href, text)
    corpus = []
    for q in notion.get("equations", []):
        if q.get("Name"):
            corpus.append(("equation", q["Name"], f"/equations#{slugify(q['Name'])}",
                           " ".join(filter(None, [q["Name"], q.get("Significance"), q.get("Symbols")]))))
    for t in notion["theories"]:
        if t.get("Name"):
            corpus.append(("theory", t["Name"], f"/theories#{slugify(t['Name'])}", " ".join(filter(None, [t["Name"], t.get("Summary")]))))
    for m in notion.get("machines", []):
        if m.get("Name"):
            corpus.append(("machine", m["Name"], f"/machines#{slugify(m['Name'])}",
                           " ".join(filter(None, [m["Name"], m.get("How It Works"), m.get("Materials"), m.get("Efficiency"), m.get("Used In")]))))
    for k in notion.get("skills", []):
        if k.get("Name"):
            corpus.append(("skill", k["Name"], f"/skills#{slugify(k['Name'])}",
                           " ".join(filter(None, [k["Name"], k.get("Summary"), k.get("The Science"), k.get("How It Fails")]))))
    for ev in notion.get("cosmicTimeline", []):
        if ev.get("Event"):
            corpus.append(("event", ev["Event"], f"/timeline#{slugify(ev['Event'])}", " ".join(filter(None, [ev["Event"], ev.get("What Happened")]))))
    for m in notion.get("mines", []):
        if m.get("Name"):
            corpus.append(("mine", m["Name"], f"/mines#{slugify(m['Name'])}", " ".join(filter(None, [m["Name"], m.get("Notes"), m.get("Type")]))))
    for o in notion.get("observatories", []):
        if o.get("Name"):
            corpus.append(("observatory", o["Name"], f"/cosmos#obs-{slugify(o['Name'])}", " ".join(filter(None, [o["Name"], o.get("Notes"), o.get("Type")]))))
    for x in notion.get("discoveries", []):
        if x.get("Name"):
            corpus.append(("discovery", x["Name"], f"/cosmos#disc-{slugify(x['Name'])}", " ".join(filter(None, [x["Name"], x.get("Description")]))))
    for m in notion.get("missions", []):
        if m.get("Name"):
            corpus.append(("mission", m["Name"], f"/cosmos#mission-{slugify(m['Name'])}", " ".join(filter(None, [m["Name"], m.get("Objective")]))))
    for e in elements:
        txt = " ".join(filter(None, [e.get("extraction"), e.get("oreMinerals")]))
        if txt:
            corpus.append(("element", e["name"], f"/elements#{e['notation']}", txt))
    for c in notion.get("constants", []):
        if c.get("Name") and c.get("Note"):
            corpus.append(("constant", c["Name"], "/constants#" + slugify(f"{c.get('Symbol')}-{c['Name']}" if c.get("Symbol") and c["Symbol"] != "—" else c["Name"]),
                           " ".join([c["Name"], c["Note"]])))
    for r in notion.get("researchers", []):
        if r.get("Name") and r.get("Known For"):
            corpus.append(("researcher", r["Name"], f"/cosmos#{slugify(r['Name'])}", " ".join([r["Name"], r["Known For"]])))
    for f in notion.get("forces", []):
        nm = f.get("Force Name")
        if nm:
            corpus.append(("force", nm, f"/forces#{slugify(nm)}",
                           " ".join(filter(None, [nm, f.get("Description"), f.get("Relative Strength")]))))
    for i in notion.get("instruments", []):
        if i.get("Name") and i.get("Description"):
            corpus.append(("instrument", i["Name"], f"/cosmos#instr-{slugify(i['Name'])}", " ".join([i["Name"], i["Description"]])))
    for rt in notion.get("rockTypes", []):
        if rt.get("Name") and rt.get("Comment"):
            corpus.append(("rock", rt["Name"], f"/minerals#rock-{slugify(rt['Name'])}", " ".join([rt["Name"], rt["Comment"]])))
    for x in notion.get("explainers", []):
        if x.get("Name") and x.get("Covers"):
            # Covers only, not the name: an explainer's name is a brand, not a
            # description, and "PBS Space Time" is not about spacetime. This also
            # keeps the trace identical to the chips /explainers computes.
            corpus.append(("explainer", x["Name"], f"/explainers#{slugify(x['Name'])}", x["Covers"]))
    # the databases left out have no prose to search: minerals, gemstones, units,
    # celestialTypes and spectralTypes are numeric or single-word lookup tables.
    KIND_ORDER = ["equation", "theory", "machine", "skill", "event", "element", "mine", "observatory",
                  "discovery", "mission", "constant", "researcher", "force", "instrument", "rock", "explainer"]
    PER_KIND = 8
    pattern = term_pattern

    out = []
    total_links = 0
    for t in terms:
        names = [t["Term"]] + [a.strip() for a in (t.get("Aliases") or "").split(",") if a.strip()]
        pats = [pattern(n) for n in names if len(n) >= 2]
        hits = {}
        for kind, name, href, text in corpus:
            if any(p.search(text) for p in pats):
                hits.setdefault(kind, []).append({"name": name, "href": href})
        appears = []
        for kind in KIND_ORDER:
            lst = hits.get(kind)
            if lst:
                lst.sort(key=lambda x: x["name"])
                appears.append({"kind": kind, "n": len(lst), "items": lst[:PER_KIND]})
                total_links += len(lst)
        out.append({"term": t["Term"], "slug": slugify(t["Term"]), "domain": t.get("Domain"),
                    "definition": t.get("Definition"), "aliases": names[1:], "appears": appears,
                    "n": sum(a["n"] for a in appears)})
    out.sort(key=lambda x: x["term"].lower())
    domains = [d for d in ["Thermodynamics", "Electromagnetism", "Quantum", "Relativity", "Cosmology", "Astronomy",
                           "Nuclear & Particle", "Chemistry", "Mineralogy", "Mining & Metallurgy", "Machines",
                           "Workshop", "Mathematics", "Measurement"] if any(x["domain"] == d for x in out)]
    write_page("glossary.template.html", "glossary.html", {"terms": out, "domains": domains})
    return len(out), total_links


# ---------------- explainers ----------------
def build_explainers_page():
    """The people, channels and organisations that explain what the rest of the
    site catalogues — distinct from the researchers, who did the work. "Covers"
    is prose on purpose: the same matcher the glossary uses turns it into term
    chips here, and puts each explainer under those terms over there. Two views
    of one computation, neither maintained by hand."""
    rows = [x for x in notion.get("explainers", []) if x.get("Name")]
    if not rows:
        write_page("explainers.template.html", "explainers.html",
                   {"explainers": [], "fields": [], "kinds": []})
        return 0, 0
    matchers = glossary_matchers()
    out, total_terms = [], 0
    for x in rows:
        covers = x.get("Covers") or ""
        terms = [{"term": t, "slug": s} for t, s, pats in matchers if any(p.search(covers) for p in pats)]
        terms.sort(key=lambda t: t["term"].lower())
        total_terms += len(terms)
        out.append({"name": x["Name"], "slug": slugify(x["Name"]), "kind": x.get("Kind"),
                    "field": x.get("Field"), "media": x.get("Medium") or [],
                    "behind": x.get("Behind It"), "covers": covers,
                    "url": x.get("URL"), "terms": terms})
    out.sort(key=lambda x: x["name"].lower())
    FIELD_ORDER = ["Physics", "Astronomy & Cosmology", "Chemistry", "Earth & Mining",
                   "Engineering", "Workshop", "Mathematics", "General science", "AI safety"]
    fields = [f for f in FIELD_ORDER if any(x["field"] == f for x in out)]
    fields += sorted({x["field"] for x in out if x["field"] and x["field"] not in fields})
    kinds = [k for k in ["Person", "Channel", "Organisation"] if any(x["kind"] == k for x in out)]
    write_page("explainers.template.html", "explainers.html",
               {"explainers": out, "fields": fields, "kinds": kinds})
    return len(out), total_terms


# ---------------- search index ----------------
def _clip(s, n=170) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def build_search_index():
    """One flat index of everything the site renders, fetched lazily by the
    search bar on the home page. Rows are [kind, name, sub, text, href] —
    arrays, not objects, because there are ~4,000 rows and the minerals alone
    would double the size as keyed JSON. Every href is a deep link the target
    page already understands (see each page's openHash / goTo)."""
    rows = []

    def add(kind, name, sub, text, href):
        if name:
            rows.append([kind, name, sub or "", _clip(text), href])

    # the sections themselves, so "timeline" or "constants" lands on the page
    for route, name, sub in [
        ("/elements", "Periodic Table", "118 elements · lenses · photo analyzer"),
        ("/minerals", "Minerals & Gemstones", "3,000+ minerals · gemstone shelf · rock families"),
        ("/cosmos", "Cosmic Exploration", "object classes · spectral types · observatories · discoveries · missions"),
        ("/forces", "Forces", "the four fundamental interactions"),
        ("/theories", "Theories", "the theory shelf, with standing and proponents"),
        ("/timeline", "Timeline of the Universe", "Planck epoch to heat death on a log axis"),
        ("/constants", "Constants & Units", "CODATA constants · SI units · prefixes"),
        ("/equations", "Equations", "canonical equations with symbols decoded"),
        ("/mines", "Mines & Extraction", "a world map of flagship mines, and how each raw material is won"),
        ("/machines", "Machines", "the canonical engines and machines: how each works, its cycle, efficiency, materials"),
        ("/skills", "Skills", "hands-on techniques with the science behind them: tools, steps, safety, how it fails"),
        ("/glossary", "Glossary", "the terms the site uses, each traced to every page that uses it"),
        ("/explainers", "Explainers", "the people, channels and organisations that explain this material"),
    ]:
        add("page", name, sub, "", route)

    for e in elements:
        add("element", e["name"], f"{e['notation']} · Z {e['atomicNumber']}",
            " ".join([*(e.get("categories") or []), e.get("occurrence") or ""]).replace("#", ""),
            f"/elements#{e['notation']}")

    for m in notion["minerals"]:
        if m.get("Name"):
            syms = ELEMENT_MINERALS_BY_NAME.get(m["Name"], "")
            add("mineral", m["Name"], m.get("Formula") or "", syms, f"/minerals#{m['Name'].lower()}")

    for g in notion["gemstones"]:
        if g.get("Name"):
            add("gemstone", g["Name"], g.get("Select") or "gemstone", "", f"/minerals#{g['Name'].lower()}")

    for q in notion.get("equations", []):
        yr = q.get("Year")
        add("equation", q["Name"],
            " · ".join(filter(None, [q.get("Field"), f"c. {-yr} BCE" if yr and yr < 0 else (str(yr) if yr else None)])),
            " — ".join(filter(None, [q.get("Equation"), q.get("Significance")])),
            f"/equations#{slugify(q['Name'])}")

    for c in notion.get("constants", []):
        if c.get("Name"):
            sym = c.get("Symbol") or ""
            add("constant", c["Name"],
                " ".join(filter(None, [sym, "=" if sym else "", c.get("Value") or "", c.get("Unit") or ""])).strip(),
                " · ".join(filter(None, [c.get("Category"), c.get("Note")])),
                "/constants#" + slugify(f"{sym}-{c['Name']}" if sym and sym != "—" else c["Name"]))

    for u in notion.get("units", []):
        if u.get("Name"):
            add("unit", u["Name"], " · ".join(filter(None, [u.get("Symbol"), u.get("Kind")])),
                " — ".join(filter(None, [u.get("Quantity"), u.get("Definition")])),
                "/constants#prefixes" if u.get("Kind") == "SI prefix" else "/constants#units")

    for t in notion["theories"]:
        if t.get("Name"):
            add("theory", t["Name"], " · ".join(filter(None, [t.get("Status"), str(t["Year"]) if t.get("Year") else None])),
                t.get("Summary"), f"/theories#{slugify(t['Name'])}")

    for r in notion["researchers"]:
        if r.get("Name"):
            add("researcher", r["Name"], " · ".join(filter(None, [r.get("Lifespan"), r.get("Field")])),
                r.get("Known For"), f"/cosmos#{slugify(r['Name'])}")

    for ev in notion.get("cosmicTimeline", []):
        if ev.get("Event"):
            add("event", ev["Event"], " · ".join(filter(None, [ev.get("When"), ev.get("Era")])),
                ev.get("What Happened"), f"/timeline#{slugify(ev['Event'])}")

    for o in notion.get("observatories", []):
        if o.get("Name"):
            add("observatory", o["Name"],
                " · ".join(filter(None, [o.get("Type"), str(o["Founded"]) if o.get("Founded") else None, o.get("Location")])),
                o.get("Notes"), f"/cosmos#obs-{slugify(o['Name'])}")

    people_by_id = {r["id"]: r["Name"] for r in notion["researchers"] if r.get("Name")}
    for x in notion.get("discoveries", []):
        if x.get("Name"):
            who = [people_by_id[i] for i in (x.get("Discoverer") or []) if i in people_by_id]
            add("discovery", x["Name"], " · ".join(filter(None, [str(x["Year"]) if x.get("Year") else None, ", ".join(who)])),
                x.get("Description"), f"/cosmos#disc-{slugify(x['Name'])}")

    for m in notion.get("missions", []):
        if m.get("Name"):
            add("mission", m["Name"],
                " · ".join(filter(None, [(m.get("Launch Date") or "")[:4], m.get("Agency"), m.get("Destination"), m.get("Status")])),
                m.get("Objective"), f"/cosmos#mission-{slugify(m['Name'])}")

    for i in notion["instruments"]:
        if i.get("Name"):
            add("instrument", i["Name"], " · ".join(filter(None, [i.get("Type"), ", ".join(i.get("Wavelength_Range") or [])])),
                i.get("Description"), f"/cosmos#instr-{slugify(i['Name'])}")

    for s in notion["spectralTypes"]:
        if s.get("Name"):
            add("spectral type", s["Name"], s.get("Temperature") or "", s.get("Characteristics"),
                f"/cosmos#spec-{s['Name'][0].lower()}")

    for o in notion["celestialObjects"]:
        if obj_name(o):
            mass = o.get("Mass")
            add("object", obj_name(o),
                " · ".join(filter(None, [o.get("Type"), f"{mass:.3g} kg" if mass else None])),
                "", "/cosmos#catalogue")

    for t in notion["celestialTypes"]:
        if t.get("Name"):
            add("object class", t["Name"], t.get("Type") or "", "", f"/cosmos#class-{slugify(t.get('Type') or 'other')}")

    for m in notion.get("mines", []):
        if m.get("Name"):
            add("mine", m["Name"], " · ".join(filter(None, [m.get("Country"), m.get("Type")])),
                m.get("Notes"), f"/mines#{slugify(m['Name'])}")

    for m in notion.get("machines", []):
        if m.get("Name"):
            add("machine", m["Name"], " · ".join(filter(None, [m.get("Kind"), str(m["Year"]) if m.get("Year") else None,
                                                             None if (m.get("Cycle") in (None, "None")) else f"{m['Cycle']} cycle"])),
                m.get("How It Works"), f"/machines#{slugify(m['Name'])}")

    for g in notion.get("glossary", []):
        if g.get("Term"):
            add("term", g["Term"], g.get("Domain") or "", g.get("Definition"), f"/glossary#{slugify(g['Term'])}")

    for x in notion.get("explainers", []):
        if x.get("Name"):
            add("explainer", x["Name"], " · ".join(filter(None, [x.get("Kind"), x.get("Field")])),
                x.get("Covers"), f"/explainers#{slugify(x['Name'])}")

    for sk in notion.get("skills", []):
        if sk.get("Name"):
            add("skill", sk["Name"], " · ".join(filter(None, [sk.get("Category"), sk.get("Difficulty")])),
                sk.get("Summary"), f"/skills#{slugify(sk['Name'])}")

    for f in notion["forces"]:
        nm = f.get("Force Name")
        if nm:
            add("force", nm, " · ".join(filter(None, [f.get("Range"), f.get("Relative Strength")])),
                f.get("Description"), f"/forces#{slugify(nm)}")

    out = {"built": max((r["lastEdited"] for rows_ in notion.values() for r in rows_ if r.get("lastEdited")), default="")[:10],
           "kinds": sorted({r[0] for r in rows}), "items": rows}
    text = compact(out)
    (PUB / "search.json").write_text(text)
    print(f"wrote {len(text):>7} bytes -> public/search.json  ({len(rows)} entries)")
    return len(rows)


# ---------------- home ----------------
def theory_span() -> str:
    """Earliest→latest year across the theory shelf, e.g. '150 CE – 1998'."""
    years = []
    for t in notion["theories"]:
        y = t.get("Year")
        if y is None and t.get("Date Proposed"):
            try:
                y = int(str(t["Date Proposed"])[:4])
            except ValueError:
                y = None
        if isinstance(y, (int, float)):
            years.append(int(y))
    if not years:
        return "—"
    lo, hi = min(years), max(years)
    lo_s = f"{-lo} BCE" if lo < 0 else (f"{lo} CE" if lo < 1000 else str(lo))
    return f"{lo_s}–{hi}"


def build_home(n_min, n_gems, n_classes, n_spectral, n_instr, n_timeline, tl_decades,
               n_obs, n_disc, n_miss, n_search, n_mines, n_mined, n_mach, n_diag, n_skills, n_terms, n_traces,
               n_expl, n_expl_terms):
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
        "__N_ACCEPTED__": sum(1 for t in notion["theories"] if t.get("Status") == "Accepted"),
        "__TH_SPAN__": theory_span(),
        "__N_PEOPLE__": sum(1 for r in notion["researchers"] if r.get("Name")),
        "__N_TIMELINE__": n_timeline,
        "__N_OBS__": n_obs,
        "__N_DISC__": n_disc,
        "__N_MISS__": n_miss,
        "__N_SEARCH__": f"{n_search:,}",
        "__N_MINES__": n_mines,
        "__N_MINED__": n_mined,
        "__N_MACHINES__": n_mach,
        "__N_DIAGRAMS__": n_diag,
        "__N_SKILLS__": n_skills,
        "__N_TERMS__": n_terms,
        "__N_TRACES__": f"{n_traces:,}",
        "__N_EXPL__": n_expl,
        "__N_EXPLTERMS__": f"{n_expl_terms:,}",
        "__TL_DECADES__": tl_decades,
        "__N_EQ__": len(eqs),
        "__N_EQFIELDS__": len({e.get("Field") for e in eqs if e.get("Field")}),
        "__EQ_OLDEST__": oldest_str,
        "__N_CONST__": len(notion.get("constants", [])),
        "__N_EXACT__": sum(1 for c in notion.get("constants", []) if c.get("Exact")),
        "__N_UNITS__": sum(1 for u in notion.get("units", []) if u.get("Kind") != "SI prefix"),
        "__SYNC_DATE__": sync,
    })


if __name__ == "__main__":
    n_min, n_gems = build_minerals_page()   # fills ELEMENT_MINERALS
    build_elements_page()
    n_classes, n_spectral, n_instr, n_obs, n_disc, n_miss = build_cosmos_page()
    write_page("forces.template.html", "forces.html",
               [{k: v for k, v in f.items() if k != "id"} for f in notion["forces"]])
    # theories carry a Proponent relation into the Researchers DB — resolve it to
    # names and one-line credentials so the page can show who stood behind each idea
    people = {r["id"]: {"name": r["Name"], "life": r.get("Lifespan"),
                        "field": r.get("Field"), "known": r.get("Known For")}
              for r in notion["researchers"] if r.get("Name")}
    write_page("theories.template.html", "theories.html",
               {"theories": [{k: v for k, v in t.items() if k != "id"} for t in notion["theories"]],
                "equations": eq_lookup_all(),
                "people": people})
    # equations keep their Notion page id — the Related relation targets it;
    # __ELEMENTS__ is a pageId -> {sym,name} lookup for the Elements relation
    el_lookup = {e["pageId"]: {"sym": e["notation"], "name": e["name"], "z": e["atomicNumber"]}
                 for e in elements}
    linked = {mid for e in notion.get("equations", []) for mid in (e.get("Minerals") or [])}
    min_lookup = {m["id"]: m["Name"] for m in notion["minerals"] if m.get("Name") and m["id"] in linked}
    # cosmos lookup: page id -> {name, kind, anchor} across spectral types, objects, instruments, theories
    cosmos_lookup = {}
    for s in notion["spectralTypes"]:
        if s.get("Name"):
            cosmos_lookup[s["id"]] = {"name": s["Name"], "kind": "spectral", "href": "/cosmos#spectral"}
    for o in notion["celestialObjects"]:
        if obj_name(o):
            cosmos_lookup[o["id"]] = {"name": obj_name(o), "kind": "object", "href": "/cosmos#catalogue"}
    for i in notion["instruments"]:
        if i.get("Name"):
            cosmos_lookup[i["id"]] = {"name": i["Name"], "kind": "instrument", "href": "/cosmos#instruments"}
    for t in notion["theories"]:
        if t.get("Name"):
            cosmos_lookup[t["id"]] = {"name": t["Name"], "kind": "theory", "href": "/theories#" + slugify(t["Name"])}
    # constants & units
    order = ["Defining (SI)", "Universal", "Electromagnetic", "Atomic & nuclear",
             "Thermodynamic", "Astronomical", "Cosmological", "Mathematical"]
    consts = sorted(
        [{k: v for k, v in c.items() if k not in ("url", "lastEdited", "id")} | {"Equations": c.get("Equations") or []}
         for c in notion.get("constants", [])],
        key=lambda c: (order.index(c["Category"]) if c.get("Category") in order else 99, c.get("Name") or ""))
    write_page("constants.template.html", "constants.html",
               {"constants": consts,
                "units": [{k: v for k, v in u.items() if k not in ("url", "lastEdited", "id")}
                          for u in notion.get("units", [])],
                "equations": eq_lookup_all()})

    write_page("equations.template.html", "equations.html",
               [{k: v for k, v in e.items() if k not in ("url", "lastEdited")}
                for e in notion.get("equations", [])],
               extra={"__ELEMENTS__": compact(el_lookup), "__MINERALS__": compact(min_lookup),
                      "__COSMOS__": compact(cosmos_lookup), "__TABLES__": compact(equation_tables())})
    n_timeline, tl_decades = build_timeline_page()
    n_mines, n_mined = build_mines_page()
    n_mach, n_diag = build_machines_page()
    n_skills = build_skills_page()
    n_terms, n_traces = build_glossary_page()
    n_expl, n_expl_terms = build_explainers_page()
    n_search = build_search_index()
    build_home(n_min, n_gems, n_classes, n_spectral, n_instr, n_timeline, tl_decades,
               n_obs, n_disc, n_miss, n_search, n_mines, n_mined, n_mach, n_diag, n_skills, n_terms, n_traces,
               n_expl, n_expl_terms)
