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
    """Must produce exactly what the pages' JS slug() produces, since half the
    anchors on this site are written by Python and the other half by the
    browser, and search.json links from one to the other.

    They used to disagree. The old version went through .encode("ascii",
    "ignore"), which DELETES a character JS merely treats as a separator, so
    every unspaced dash collapsed: "Einstein–Hilbert Action" became
    einsteinhilbert-action in the search index and einstein-hilbert-action in
    the page. 96 anchors were wrong, and every one of them was a search result
    that landed on the right page and then failed to scroll to anything.

    Strip combining marks, lowercase, and let everything else become a hyphen —
    which is what the JS does."""
    import unicodedata
    s = unicodedata.normalize("NFD", s or "").lower()
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", s))


# Every page gets this, in both languages. vocab() translates the fixed vocabulary the
# pages filter and colour by — Field, kind, category, status, level, domain, era — for
# DISPLAY only: the data keeps the English values, so every comparison, colour lookup and
# grouping in the page scripts goes on working untouched. On an English page __VOCAB__ is
# absent and vocab() is the identity; scripts/i18n.py fills it on the French ones.
VOCAB_JS = ("<script>const VOCAB = window.__VOCAB__ || {};"
            " const vocab = (s) => (s == null ? s : (VOCAB[s] || s));</script>")


def write_page(template: str, out: str, data=None, extra: dict | None = None):
    tpl = (WEB / template).read_text()
    tpl = tpl.replace("__SHARED__", SHARED)
    tpl = tpl.replace("</style>", "</style>\n" + VOCAB_JS, 1)
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
            m.get("Biological Role"),    # only ~18 rows have one (scripts/seed_biology.py)
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
    "Ninety-Degree Rule": {
        "caption": "The numbers a pool table runs on — the same values the Pool Sauce engine "
                   "(pool-sauce-engine, poolsauce/constants.py) integrates with, so the shelf and "
                   "the engine never disagree on one.",
        "columns": ["Quantity", "Value", "Enters", "Note"],
        "rows": [
            ["Ball radius R", "28.575 mm", "ghost-ball aim, tip offset, slide-to-roll",
             "A 2¼-inch ball. Snooker's are 52.5 mm; carom 61.5 mm."],
            ["Ball mass m", "170 g", "speed transfer, momentum", "Phenolic resin; matched to a gram in a set."],
            ["Ball–ball restitution e", "0.92", "restitution, ninety-degree rule",
             "So a stun stop shot still creeps forward — a touch of draw fixes it."],
            ["Ball–ball friction μ", "≈ 0.06", "throw", "Clean balls. Chalk on the contact point can double it."],
            ["Cloth sliding friction μ_s", "0.2", "slide-to-roll, draw distance", "Worsted tournament cloth; napped cloth is higher."],
            ["Cloth rolling resistance μ_r", "0.01", "rolling resistance", "A ball at 1 m/s rolls about 5 m."],
            ["Cloth spinning friction", "0.044", "how long side spin lasts", "Torque on a ball spinning in place about a vertical axis."],
            ["Cushion efficiency", "0.75 of energy → 0.87 of speed", "cushion rebound",
             "Rubber; varies table to table and with speed. Test before a match."],
            ["9-ft playing surface", "2.54 × 1.27 m", "distance, speed control", "Inside the cushion noses; a 7-ft bar table is 1.98 × 0.99 m."],
        ],
        "note": "Where the engine and the literature differ the engine's value is quoted, because that is "
                "the number the shots on the channel are computed with.",
    },
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
    # the Sun is the one catalogued star; everything else in the DB is the Local
    # Group. Before the galaxies were seeded this loop took the last row it saw,
    # which was harmless with one row and wrong with forty-five.
    sun = None
    for o in notion["celestialObjects"]:
        if obj_name(o) and (o.get("Type") == "Star" or obj_name(o) == "Sun"):
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

    # The spectral sequence is a partition of the temperature line: every star
    # has exactly one class, so the bands must tile it with no gap and no
    # overlap. They did not -- M-type was written "< 3,700 K" with no floor,
    # which swallowed L, T and Y whole and gave a 1,000 K brown dwarf two
    # classes at once.
    def band(txt):
        if not txt:
            return None
        n = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+(?:\.\d+)?", txt)]
        if not n:
            return None
        if "<" in txt:
            return (0.0, n[0])
        if ">" in txt:
            return (n[0], float("inf"))
        return (min(n), max(n)) if len(n) > 1 else (n[0], n[0])

    for sp in spectral:
        sp["band"] = band(sp["temp"])
    ladder = sorted((sp for sp in spectral if sp["band"]), key=lambda sp: sp["band"][0])
    sp_gaps = []
    for a, b in zip(ladder, ladder[1:]):
        if b["band"][0] > a["band"][1]:
            sp_gaps.append(f"gap {a['band'][1]:g}–{b['band'][0]:g} K between {a['letter']} and {b['letter']}")
        elif b["band"][0] < a["band"][1]:
            sp_gaps.append(f"{a['letter']} and {b['letter']} overlap below {a['band'][1]:g} K")
    for g in sp_gaps:
        print(f"  cosmos: spectral sequence — {g}")

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

    # ---- the Local Group: everything catalogued that is not a star
    MSUN = 1.989e30
    local = []
    for o in notion["celestialObjects"]:
        nm = obj_name(o)
        if not nm or o.get("Type") == "Star" or o.get("Distance from Earth") is None:
            continue
        m_kg = o.get("Mass")
        row = {
            "name": nm, "slug": slugify(nm),
            "morph": o.get("Morphology"), "sub": o.get("Subgroup"),
            "dist": o.get("Distance from Earth"),
            "diam": o.get("Diameter (ly)"),
            "msun": round(m_kg / MSUN) if m_kg else None,
            "notes": o.get("Notes"),
        }
        # How big it looks, derived rather than stored — two numbers already in
        # the row determine it exactly, and it is the only one of the three a
        # person can picture. It doubles as the check: a wrong diameter or a
        # wrong distance puts a dwarf across half the sky.
        if row["diam"] and row["dist"]:
            row["deg"] = round(math.degrees(2 * math.atan(row["diam"] / 2 / row["dist"])), 3)
            row["moons"] = round(row["deg"] / 0.517, 2)      # the Moon, for scale
        # Mean density catches a unit slip in either column: everything from a
        # compact elliptical to a diffuse dwarf lives inside two orders of
        # magnitude, so anything outside that is arithmetic, not astronomy.
        if row["msun"] and row["diam"]:
            rho = row["msun"] / ((4 / 3) * math.pi * (row["diam"] / 2) ** 3)
            row["rho"] = float(f"{rho:.3g}")
            row["rhoOK"] = 1e-5 < rho < 1e0
        local.append(row)
    local.sort(key=lambda x: x["dist"])

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
            "missions": missions, "localGroup": local, "equations": eq_lookup_all(),
            "lgChecks": {"nDeg": sum(1 for r in local if "deg" in r),
                         "nRho": sum(1 for r in local if "rho" in r),
                         "nRhoOff": sum(1 for r in local if r.get("rhoOK") is False),
                         "spectralGaps": sp_gaps}}
    write_page("cosmos.template.html", "cosmos.html", data)
    return (len(types), len(spectral), len(instruments), len(observatories),
            len(discoveries), len(missions), len(local))


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
        e = events[-1]
        z, z_lo, z_hi = parse_z(r.get("Redshift"))
        t, T = e["secs"], e["temp"]

        # CHECK 1 -- T = T0(1 + z). Exact, and the easiest thing on this page
        # to get wrong. An epoch spanning a redshift range spans a temperature
        # range, so the row passes if its temperature lands anywhere inside it.
        if z and T:
            e["tempFromZ"] = round(T_CMB * (1 + z), 4)
            e["tLo"], e["tHi"] = round(T_CMB * (1 + z_lo), 4), round(T_CMB * (1 + z_hi), 4)
            e["tempRatio"] = round(T / e["tempFromZ"], 3)
            e["tempOK"] = e["tLo"] * 0.85 <= T <= e["tHi"] * 1.15

        # CHECK 2 -- the radiation era, where age follows from temperature
        # alone. Only applies once the universe is radiation-dominated AND
        # after reheating: between inflation and reheating the relation does
        # not hold at all, which is the whole reason reheating has a name.
        # Bounded above by the electroweak scale, not by inflation: above ~1 TeV
        # both the time and the temperature are model-dependent extrapolations,
        # and checking one against the other would only be checking an
        # assumption against itself. Bounded below by matter-radiation equality.
        if t and T and T < 1e16 and t <= 1e12:
            e["ageFromT"] = radiation_era_time(T)
            e["ageRatio"] = round(t / e["ageFromT"], 3)
            e["ageOK"] = 0.1 <= e["ageRatio"] <= 10        # g* steps make this order-of-magnitude
    # sort on the number, not the prose — that is what the column is for
    events.sort(key=lambda e: (e["secs"] is None, e["secs"] if e["secs"] is not None else 0))
    data = {"events": events, "equations": eq_lookup_all(), "theories": th_lookup,
            "people": people,
            "eras": [e for e in ERA_ORDER if any(x["era"] == e for x in events)]}
    bad_T = [e for e in events if e.get("tempOK") is False]
    bad_t = [e for e in events if e.get("ageOK") is False]
    for e in bad_T:
        print(f"  timeline: {e['event']} is {e['tempRatio']}x the temperature its redshift implies")
    for e in bad_t:
        print(f"  timeline: {e['event']} is {e['ageRatio']}x the age its temperature implies")
    data["checks"] = {
        "nTemp": sum(1 for e in events if "tempRatio" in e), "nTempOff": len(bad_T),
        "nAge": sum(1 for e in events if "ageRatio" in e), "nAgeOff": len(bad_t),
        "T0": T_CMB,
    }
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
    order = ["Joining", "Metalwork", "Making", "Electronics", "Building", "Rigging", "Measuring", "Cue sports"]
    rows.sort(key=lambda r: (order.index(r["cat"]) if r["cat"] in order else 99, r["name"]))
    write_page("skills.template.html", "skills.html", {"skills": rows, "cats": [c for c in order if any(r["cat"] == c for r in rows)]})
    return len(rows)


# ---------------- billiards ----------------
def build_billiards_page():
    """The physics of the pool table: the lab runs the equations in the browser; the page
    lists the Billiards-field rows plus the two Mechanics rows the game needs, the three
    Cue sports skills, and the constants table that quotes pool-sauce-engine."""
    GENERAL = {"Coefficient of Restitution", "Rolling Resistance"}
    eqs = [e for e in notion.get("equations", [])
           if e.get("Name") and (e.get("Field") == "Billiards" or e["Name"] in GENERAL)]
    eqs.sort(key=lambda e: (e.get("Field") != "Billiards", e.get("Year") or 9999, e["Name"]))
    skills = [{"name": s["Name"], "slug": slugify(s["Name"]), "summary": s.get("Summary"), "difficulty": s.get("Difficulty")}
              for s in notion.get("skills", []) if s.get("Category") == "Cue sports" and s.get("Name")]
    write_page("billiards.template.html", "billiards.html", {
        "equations": [{"name": e["Name"], "slug": slugify(e["Name"]), "field": e.get("Field"), "equation": e.get("Equation"),
                       "significance": e.get("Significance"), "year": e.get("Year"), "requires": len(e.get("Requires") or [])}
                      for e in eqs],
        "skills": skills,
        "table": EQUATION_TABLES.get("Ninety-Degree Rule"),
    })
    return len(eqs), len(skills)


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
    for r in notion.get("cosmicStructures", []):
        if r.get("Name") and r.get("Notes"):
            corpus.append(("structure", r["Name"], f"/scales#{slugify(r['Name'])}", " ".join([r["Name"], r["Notes"]])))
    for o in notion.get("celestialObjects", []):
        nm = obj_name(o)
        if nm and o.get("Notes"):
            corpus.append(("galaxy", nm, f"/cosmos#lg-{slugify(nm)}", " ".join([nm, o["Notes"]])))
    for e in elements:
        txt = " ".join(filter(None, [e.get("extraction"), e.get("oreMinerals"), e.get("bioRole")]))
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
    for m in notion.get("minerals", []):
        if m.get("Name") and m.get("Biological Role"):
            corpus.append(("mineral", m["Name"], f"/minerals?q={m['Name']}",
                           " ".join([m["Name"], m["Biological Role"]])))
    for rt in notion.get("rockTypes", []):
        if rt.get("Name") and rt.get("Comment"):
            corpus.append(("rock", rt["Name"], f"/minerals#rock-{slugify(rt['Name'])}", " ".join([rt["Name"], rt["Comment"]])))
    for x in notion.get("explainers", []):
        if x.get("Name") and x.get("Covers"):
            # Covers only, not the name: an explainer's name is a brand, not a
            # description, and "PBS Space Time" is not about spacetime. This also
            # keeps the trace identical to the chips /explainers computes.
            corpus.append(("explainer", x["Name"], f"/explainers#{slugify(x['Name'])}", x["Covers"]))
    for i in notion.get("impacts", []):
        if i.get("Name") and i.get("Mechanism"):
            corpus.append(("impact", i["Name"], f"/impacts#{slugify(i['Name'])}",
                           " ".join(filter(None, [i["Name"], i.get("Mechanism"), i.get("Mitigation"), i.get("Case")]))))
    # the databases left out have no prose to search: minerals, gemstones, units,
    # celestialTypes and spectralTypes are numeric or single-word lookup tables.
    KIND_ORDER = ["equation", "theory", "machine", "skill", "event", "element", "structure", "galaxy", "mine", "observatory",
                  "discovery", "mission", "constant", "researcher", "force", "instrument", "rock",
                  "explainer", "impact", "mineral"]
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
    DOMAIN_ORDER = ["Mechanics", "Waves & Fluids", "Cue sports", "Biology", "Thermodynamics",
                    "Electromagnetism", "Quantum", "Relativity", "Cosmology", "Astronomy",
                    "Nuclear & Particle", "Chemistry", "Mineralogy", "Mining & Metallurgy", "Machines",
                    "Workshop", "Mathematics", "Measurement"]
    domains = [d for d in DOMAIN_ORDER if any(x["domain"] == d for x in out)]
    # anything seeded in Notion that this list has not heard of still gets a chip,
    # at the end. The list used to be the only source, so a new domain arrived with
    # terms and no way to filter for them, and nothing said so — Biology did exactly
    # that on 2026-08-18 and only a domain count caught it
    domains += sorted({x["domain"] for x in out if x["domain"] and x["domain"] not in domains})
    write_page("glossary.template.html", "glossary.html", {"terms": out, "domains": domains})
    return len(out), total_links


# ---------------- explainers ----------------
# The Notion database /explainers is built from, linked in the page footer.
# Opens only for someone with access to the workspace — it is the source, not a
# public mirror, and the footer says "in Notion" so the reader knows that.
EXPLAINERS_DB = "https://app.notion.com/p/8bbd030a45214045ab0efc21852686ac"


def build_explainers_page():
    """The people, channels and organisations that explain what the rest of the
    site catalogues — distinct from the researchers, who did the work. "Covers"
    is prose on purpose: the same matcher the glossary uses turns it into term
    chips here, and puts each explainer under those terms over there. Two views
    of one computation, neither maintained by hand."""
    rows = [x for x in notion.get("explainers", []) if x.get("Name")]
    if not rows:
        write_page("explainers.template.html", "explainers.html",
                   {"explainers": [], "fields": [], "kinds": []},
                   extra={"__DBURL__": EXPLAINERS_DB})
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
               {"explainers": out, "fields": fields, "kinds": kinds},
               extra={"__DBURL__": EXPLAINERS_DB})
    return len(out), total_terms


# ---------------- mining impacts ----------------
def build_impacts_page():
    """What extraction costs, mechanism by mechanism. Where links each impact to
    the mine Types the Mines DB already records, so the count of sites on this
    site that it applies to is computed here rather than maintained by hand —
    and the glossary matcher reads the mechanism prose, same as /explainers."""
    rows = [i for i in notion.get("impacts", []) if i.get("Name")]
    if not rows:
        write_page("impacts.template.html", "impacts.html",
                   {"impacts": [], "categories": [], "timescales": []})
        return 0, 0
    # a mine typed "Open pit + underground" is both, so it counts under each —
    # otherwise the 9 combined sites vanish from every impact that names one method
    by_type = Counter()
    for m in notion.get("mines", []):
        t = m.get("Type")
        if not t:
            continue
        by_type[t] += 1
        if t == "Open pit + underground":
            by_type["Open pit"] += 1
            by_type["Underground"] += 1
    matchers = glossary_matchers()
    eq_lk = eq_lookup_all()
    out, total_terms = [], 0
    for i in rows:
        prose = " ".join(filter(None, [i.get("Mechanism"), i.get("Mitigation"), i.get("Case")]))
        terms = [{"term": t, "slug": s} for t, s, pats in matchers if any(p.search(prose) for p in pats)]
        terms.sort(key=lambda t: t["term"].lower())
        total_terms += len(terms)
        # a Where value that names a mine Type carries the count of such mines on
        # the site; the rest (Smelter, Artisanal, Tailings storage) have no Type
        # to join to and stay plain labels
        where = [{"name": w, "n": by_type.get(w, 0)} for w in (i.get("Where") or [])]
        out.append({"name": i["Name"], "slug": slugify(i["Name"]), "category": i.get("Category"),
                    "timescale": i.get("Timescale"), "where": where,
                    "mechanism": i.get("Mechanism"), "mitigation": i.get("Mitigation"),
                    "case": i.get("Case"), "terms": terms,
                    # the Equations relation (seed_fluids_waves): Darcy on drainage, Stokes on tailings…
                    "equations": [eq_lk[x] for x in (i.get("Equations") or []) if x in eq_lk]})
    out.sort(key=lambda x: x["name"].lower())
    CAT_ORDER = ["Water", "Air", "Land", "Health", "Ground", "Energy"]
    cats = [c for c in CAT_ORDER if any(x["category"] == c for x in out)]
    cats += sorted({x["category"] for x in out if x["category"] and x["category"] not in cats})
    scales = [t for t in ["During operation", "After closure", "Both"] if any(x["timescale"] == t for x in out)]
    write_page("impacts.template.html", "impacts.html",
               {"impacts": out, "categories": cats, "timescales": scales})
    return len(out), total_terms


# ---------------- the ladder of scale ----------------
# Planck 2018 TT,TE,EE+lowE+lensing+BAO. Named here rather than buried, because
# every distance derived below moves with it: swap in SH0ES (73.0) and the whole
# ladder above z ~ 0.01 stretches by about 8%.
COSMOLOGY = {"name": "Planck 2018", "H0": 67.36, "Om": 0.3153, "OL": 0.6847}
C_KMS = 299792.458
LY_PER_MPC = 3.26156e6


def lcdm_comoving(z: float, H0=None, Om=None) -> float:
    """Comoving distance to redshift z in light-years, flat LCDM, by Simpson.

    The page quotes comoving distances throughout. This recomputes them from the
    redshift so the two columns can be checked against each other instead of
    both being taken on trust -- which is how the Hercules-Corona Borealis wall
    was caught being quoted as a light-travel distance.

    Matter and Lambda only: radiation is neglected, which is worth less than
    0.1% everywhere on this page except the last-scattering surface, where it
    makes the computed distance about 0.5% too large. The page says so."""
    H0 = H0 or COSMOLOGY["H0"]
    Om = Om if Om is not None else COSMOLOGY["Om"]
    n = 2000                                    # even; Simpson over [0, z]
    h = z / n
    def E(zz):
        return 1.0 / math.sqrt(Om * (1 + zz) ** 3 + (1 - Om))
    total = E(0) + E(z)
    for i in range(1, n):
        total += E(i * h) * (4 if i % 2 else 2)
    return (C_KMS / H0) * (h / 3) * total * LY_PER_MPC


def parse_z(v):
    """Redshift is text, because a real structure or epoch spans a range
    ("1.6-2.1", "1100 - 20"). Returns (midpoint, lo, hi) or (None, None, None).

    Checking a range at its midpoint is what made the Dark Ages look like a
    hundredfold error when it is simply an epoch: z from 1100 to 20 means a
    temperature from 3000 K to 57 K, and 60 K sits inside that. Callers get
    the bounds so they can test containment rather than a point."""
    if isinstance(v, (int, float)):
        return float(v), float(v), float(v)
    if not isinstance(v, str):
        return None, None, None
    nums = re.findall(r"\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", v.replace("\u2212", "-"))
    if not nums:
        return None, None, None                 # "\u221e at the horizon", "\u2014"
    vals = sorted(float(x) for x in nums)
    return sum(vals) / len(vals), vals[0], vals[-1]


T_CMB = 2.7255                    # K, FIRAS. The one number the whole timeline hangs off.
MEV_K = 1.1605e10                 # K per MeV


def gstar(T_k: float) -> float:
    """Relativistic degrees of freedom, Standard Model, as a step function of
    temperature. Crude on purpose: it enters t as g*^-1/2, so even getting a
    threshold wrong moves the answer by tens of percent, not orders."""
    mev = T_k / MEV_K
    if mev > 3e5:                 # above the top quark: everything
        return 106.75
    if mev > 1e2:                 # above the QCD transition
        return 96.25
    if mev > 1e0:                 # hadrons gone, muons still around
        return 61.75
    if mev > 0.5:                 # e+e- pairs still around
        return 10.75
    return 3.36                   # photons and three neutrino species


def radiation_era_time(T_k: float) -> float:
    """Age in seconds when the universe was at temperature T, radiation-
    dominated. t = 2.42 g*^-1/2 (1 MeV / T)^2."""
    return 2.42 * gstar(T_k) ** -0.5 * (MEV_K / T_k) ** 2


def build_scales_page():
    """Everything from the heliopause to the horizon on one log axis. Sizes and
    distances stay in light-years in the data; the page picks the unit."""
    rows = []
    for r in notion.get("cosmicStructures", []):
        if not r.get("Name") or r.get("Size (ly)") is None:
            continue
        z, z_lo, z_hi = parse_z(r.get("Redshift"))
        row = {
            "name": r["Name"], "slug": slugify(r["Name"]), "kind": r.get("Kind"),
            "size": r["Size (ly)"], "dist": r.get("Distance (ly)"),
            "z": r.get("Redshift"), "zNum": z, "zRange": z_lo != z_hi, "pop": r.get("Population"),
            "within": r.get("Within") if r.get("Within") not in (None, "\u2014") else None,
            "year": r.get("Recognised"), "notes": r.get("Notes"),
        }
        # the check: a row quoting both a redshift and a distance is making a
        # claim that LCDM can test. Recompute and keep the residual, pass or fail.
        if z and z > 0 and row["dist"]:
            row["dLCDM"] = round(lcdm_comoving(z))
            row["ratio"] = round(row["dist"] / row["dLCDM"], 3)
            # a structure spanning a redshift range spans a distance range;
            # the row passes if its stated distance lands anywhere inside it
            lo, hi = lcdm_comoving(z_lo), lcdm_comoving(z_hi)
            row["dLo"], row["dHi"] = round(lo), round(hi)
            row["inBand"] = lo * 0.75 <= row["dist"] <= hi * 1.25
        rows.append(row)
    rows.sort(key=lambda x: x["size"])
    by_name = {r["name"]: r for r in rows}
    for r in rows:
        r["withinSlug"] = by_name[r["within"]]["slug"] if r["within"] in by_name else None
    # the "you are here" spine: walk Within upward from the smallest thing on the ladder
    chain, seen = [], set()
    cur = rows[0]["name"] if rows else None
    while cur and cur in by_name and cur not in seen:
        seen.add(cur)
        chain.append({"name": cur, "slug": by_name[cur]["slug"], "size": by_name[cur]["size"]})
        cur = by_name[cur]["within"]
    kinds = [k for k in ["Local", "Galaxy", "Group", "Cluster", "Supercluster", "Filament",
                         "Void", "Attractor", "Cosmological"] if any(r["kind"] == k for r in rows)]
    checked = [r for r in rows if "ratio" in r]
    # 25% is the band inside which quoted literature distances, peculiar
    # velocities and the redshift range of an extended structure all live.
    # Outside it, something is wrong or something is interesting -- either way
    # the page names the row rather than quietly rounding it into line.
    off = sorted((r for r in checked if not r["inBand"]),
                 key=lambda r: abs(math.log10(r["ratio"])), reverse=True)
    for r in off:
        print(f"  scales: {r['name']} is {r['ratio']}x the LCDM distance for z={r['z']}")
    write_page("scales.template.html", "scales.html",
               {"structures": rows, "chain": chain, "kinds": kinds,
                "cosmology": COSMOLOGY, "nChecked": len(checked),
                "nOff": len(off), "offSlugs": [r["slug"] for r in off]})
    span = math.log10(rows[-1]["size"] / rows[0]["size"]) if len(rows) > 1 else 0
    return len(rows), round(span)


# ---------------- the universe in three dimensions ----------------
# ---------------- the solar system, for the 3-D map ----------------
# Semi-major axes in astronomical units, J2000 mean elements. These are reference
# numbers, not authored content, so they live here rather than in Notion — like the
# CODATA values the constants page quotes, but too few and too fixed to be worth a
# database. What the map draws from them is a circle in the ecliptic plane, which
# leaves out two things the page says out loud rather than implying:
#   eccentricity — every orbit is drawn at its mean distance. Mercury's 0.21 is the
#     only one a reader would notice: it actually runs between 0.31 and 0.47 AU.
#   inclination  — Mercury 7.0°, Venus 3.4°, the rest under 2.5°, all to the ecliptic.
# Both are far smaller than the thickness of the line at any zoom this page allows.
AU_PER_LY = 63241.077
SOLAR_ORBITS = [
    ("Mercury", 0.38710), ("Venus", 0.72333), ("Earth", 1.00000), ("Mars", 1.52371),
    ("Jupiter", 5.20288), ("Saturn", 9.53667), ("Uranus", 19.18916), ("Neptune", 30.06992),
]
# Inner and outer edge in AU. Both are populations rather than objects, so they are
# drawn as bands: a belt has no orbit, and a single ring would claim one.
# The heliopause and the Oort cloud are deliberately absent — they are already on the
# page, as shells, from the Cosmic Structures database, like every other shell here.
SOLAR_BANDS = [
    ("Asteroid belt", 2.1, 3.3),
    ("Kuiper belt", 30.0, 50.0),
]


def build_universe_page():
    """Everything catalogued, placed by direction and distance on one log-radial
    axis: heliopause to horizon in a single scene you can turn over.

    Three renderings, and which one a thing gets is a statement about what is
    known, not a style choice:
      point  -- we are outside it and know which way it lies
      shell  -- we are outside it but not which way (a distance alone is a
                sphere, not a place), so it is drawn as that sphere
      shell  -- we are inside it, drawn at half its extent around us
    """
    items = []

    def add(name, kind, dist, size, ra, dec, href, notes, inside=False, vel=None, tvel=None,
            motion=None, vec=None, mass=None):
        if not dist or dist <= 0:
            return
        it = {
            "name": name, "kind": kind, "dist": dist, "size": size,
            "ra": ra, "dec": dec, "href": href, "inside": inside,
            "form": "point" if (ra is not None and not inside) else "shell",
            "notes": (notes or "")[:180],
        }
        # negative is approaching. Only objects carrying one move when the clock
        # runs; everything else has no measured velocity in the data and stays put
        if vel:
            it["vel"] = vel
            it["tvel"] = tvel
            if mass:
                it["mass"] = mass / 1.989e30          # kg -> solar masses
            if vec and it.get("form") == "point":
                # galactocentric position and velocity in the map's axes, in ly and
                # ly/yr — the page integrates p + v*t and re-derives distance and
                # direction from it, so an object moves sideways as well as nearer
                u = [math.cos(dec * math.pi / 180) * math.cos(ra * math.pi / 180),
                     math.cos(dec * math.pi / 180) * math.sin(ra * math.pi / 180),
                     math.sin(dec * math.pi / 180)]
                it["p0"] = [round(u[i] * dist + SUN_EQ_LY[i], 3) for i in range(3)]
                it["v3"] = [round(c * KMS_TO_LY_PER_YR, 12) for c in _eq_from_gal(vec)]
            # "Bound orbit" tells the page not to extrapolate far: a satellite's
            # velocity turns, so a straight line is qualitatively wrong past a
            # small fraction of its orbit, not merely imprecise
            it["motion"] = motion or "Infalling"
        items.append(it)

    for o in notion.get("celestialObjects", []):
        nm = obj_name(o)
        if not nm or o.get("Type") == "Star":
            continue
        d = o.get("Distance from Earth")
        if not d:
            continue                              # the Milky Way itself sits at the origin
        add(nm, "galaxy", d, o.get("Diameter (ly)"), o.get("RA (deg)"), o.get("Dec (deg)"),
            f"/cosmos#lg-{slugify(nm)}", o.get("Notes"), vel=o.get("Radial velocity (km/s)"),
            tvel=o.get("Transverse velocity (km/s)"), motion=o.get("Motion"),
            vec=([o.get("Vx (km/s)"), o.get("Vy (km/s)"), o.get("Vz (km/s)")]
                 if o.get("Vx (km/s)") is not None else None),
            mass=o.get("Mass"))

    for r in notion.get("cosmicStructures", []):
        nm = r.get("Name")
        if not nm or not r.get("Size (ly)"):
            continue
        dist, inside = r.get("Distance (ly)"), r.get("Distance (ly)") is None
        # inside it: there is no distance to it, so draw it around us at half
        # its extent -- which is where its edge actually is from here
        add(nm, (r.get("Kind") or "structure").lower(), dist or r["Size (ly)"] / 2,
            r["Size (ly)"], r.get("RA (deg)"), r.get("Dec (deg)"),
            f"/scales#{slugify(nm)}", r.get("Notes"), inside=inside)

    items.sort(key=lambda i: i["dist"])
    for i in items:
        i["slug"] = slugify(i["name"])
    solar = {
        # "home" rather than a name test in the page: the names are translated on /fr
        "orbits": [{"name": n, "au": a, "ly": a / AU_PER_LY, "home": n == "Earth"}
                   for n, a in SOLAR_ORBITS],
        "bands": [{"name": n, "au0": a0, "au1": a1, "ly0": a0 / AU_PER_LY, "ly1": a1 / AU_PER_LY}
                  for n, a0, a1 in SOLAR_BANDS],
        "obliquity": 23.4393,          # of the ecliptic to the equator, the frame everything else uses
    }
    # the axis has to reach the innermost orbit, or Mercury is drawn on top of the Sun
    inner = min([i["dist"] for i in items] + [o["ly"] for o in solar["orbits"]])
    lo = math.floor(math.log10(inner)) if items else 0
    hi = math.ceil(math.log10(items[-1]["dist"])) if items else 1
    n_point = sum(1 for i in items if i["form"] == "point")
    write_page("universe.template.html", "universe.html",
               {"items": items, "lo": lo, "hi": hi, "solar": solar,
                "nPoint": n_point, "nShell": len(items) - n_point,
                "nOrbit": len(solar["orbits"]),
                "nMoving": sum(1 for i in items if i.get("vel")),
                "n3d": sum(1 for i in items if i.get("v3")),
                "mwMass": next((o["Mass"] / 1.989e30 for o in notion.get("celestialObjects", [])
                                if o.get("Name") == "Milky Way" and o.get("Mass")), 1.5e12),
                "sunEq": [round(c, 3) for c in SUN_EQ_LY]})
    return len(items), n_point



# ---- galactocentric frame, for the objects on /universe that move ----------------
# The map's axes are equatorial (its direction vectors come from RA/Dec), while the
# measured velocities are galactic Cartesian: +x from the Sun through the centre, +y
# along rotation, +z to the north galactic pole. These rotate one into the other, so
# the page can do plain vector arithmetic in a single frame.
_EQ_FROM_GAL = [[-0.0548755604, 0.4941094279, -0.8676661490],   # transpose of the
                [-0.8734370902, -0.4448296300, -0.1980763734],  # ICRS -> galactic
                [-0.4838350155, 0.7469822445, 0.4559837762]]    # rotation (J2000)
LY_PER_KPC = 3261.564
SUN_GAL_KPC = (-8.122, 0.0, 0.0208)      # Sun's place in the galactocentric frame


def _eq_from_gal(v):
    return [sum(_EQ_FROM_GAL[i][j] * v[j] for j in range(3)) for i in range(3)]


SUN_EQ_LY = [c * LY_PER_KPC for c in _eq_from_gal(SUN_GAL_KPC)]
KMS_TO_LY_PER_YR = 3.15576e7 / 9.4607304725808e12


# ---------------- solar system ----------------
def build_solar_page():
    """Nothing here is a stored position. Each body carries six Keplerian elements
    and their per-century rates, and the page solves Kepler's equation in the
    browser to place it at whatever date is on the dial — so it is a model you
    run, not a snapshot someone saved.

    a**1.5 against the observed period is carried through as a check: Kepler's
    third law holds to better than a tenth of a percent for every body, and a bad
    element edit in Notion would show up here first."""
    rows = [b for b in notion.get("solar", []) if b.get("Name")]
    if not rows:
        write_page("solar.template.html", "solar.html", {"bodies": [], "sun": None})
        return 0
    sun, bodies = None, []
    for b in rows:
        base = {"name": b["Name"], "slug": slugify(b["Name"]), "kind": b.get("Kind"),
                "radius": b.get("Radius (km)"), "mass": b.get("Mass (kg)"),
                "notes": b.get("Notes")}
        if b.get("a") is None:
            sun = base
            continue
        el = {k: b.get(k) for k in ["a", "e", "I", "L", "peri", "node"]}
        rate = {k: b.get("d" + k) or 0.0 for k in ["a", "e", "I", "L", "peri", "node"]}
        p_obs = b.get("Period (yr)")
        p_kep = el["a"] ** 1.5
        base.update({"el": el, "rate": rate, "period": p_obs or p_kep,
                     "kepler": round(p_kep, 4),
                     "drift": round(abs(p_kep - p_obs) / p_obs * 100, 3) if p_obs else None})
        bodies.append(base)
    bodies.sort(key=lambda x: x["el"]["a"])
    write_page("solar.template.html", "solar.html", {"bodies": bodies, "sun": sun})
    return len(bodies)


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
        ("/universe", "The Universe in Three Dimensions",
         "every catalogued object placed by direction and distance on one log-radial map you can turn over, from the heliopause to the horizon"),
        ("/scales", "The Ladder of Scale", "from the heliopause to the horizon on one log axis: clusters, superclusters, Laniakea, the walls and voids, the observable universe"),
        ("/explainers", "Explainers", "the people, channels and organisations that explain this material"),
        ("/solar", "Solar System", "the nine orbits, computed live from Keplerian elements"),
        ("/impacts", "Mining Impacts", "what extraction costs — mechanism, mitigation and documented cases"),
        ("/billiards", "Billiards", "the physics of the pool table — a live shot lab, the cushion, and the numbers Pool Sauce runs on"),
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

    for o in notion.get("celestialObjects", []):
        nm = obj_name(o)
        if nm and o.get("Type") != "Star" and o.get("Distance from Earth") is not None:
            d = o["Distance from Earth"]
            when = f"{d/1e6:.2f} million ly" if d >= 1e6 else (f"{d/1000:,.0f} thousand ly" if d else "here")
            add("galaxy", nm, " · ".join(filter(None, [o.get("Morphology"), when])),
                o.get("Notes"), f"/cosmos#lg-{slugify(nm)}")

    for m in notion.get("machines", []):
        if m.get("Name"):
            add("machine", m["Name"], " · ".join(filter(None, [m.get("Kind"), str(m["Year"]) if m.get("Year") else None,
                                                             None if (m.get("Cycle") in (None, "None")) else f"{m['Cycle']} cycle"])),
                m.get("How It Works"), f"/machines#{slugify(m['Name'])}")

    for r in notion.get("cosmicStructures", []):
        if r.get("Name") and r.get("Size (ly)") is not None:
            v = r["Size (ly)"]
            sz = (f"{v/1e9:g} billion ly" if v >= 1e9 else f"{v/1e6:g} million ly" if v >= 1e6
                  else f"{v/1e3:g} thousand ly" if v >= 1e3 else f"{v:g} ly" if v >= 0.05
                  else f"{v*63241.077:.0f} AU")   # same unit ladder the page uses
            add("structure", r["Name"], " \u00b7 ".join(filter(None, [r.get("Kind"), sz])),
                r.get("Notes"), f"/scales#{slugify(r['Name'])}")

    for g in notion.get("glossary", []):
        if g.get("Term"):
            add("term", g["Term"], g.get("Domain") or "", g.get("Definition"), f"/glossary#{slugify(g['Term'])}")

    for x in notion.get("explainers", []):
        if x.get("Name"):
            add("explainer", x["Name"], " · ".join(filter(None, [x.get("Kind"), x.get("Field")])),
                x.get("Covers"), f"/explainers#{slugify(x['Name'])}")

    for i in notion.get("impacts", []):
        if i.get("Name"):
            add("impact", i["Name"], " · ".join(filter(None, [i.get("Category"), i.get("Timescale")])),
                i.get("Mechanism"), f"/impacts#{slugify(i['Name'])}")

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
               n_expl, n_expl_terms, n_imp, n_imp_terms, n_bill_eq=0, n_bill_skills=0):
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
        "__N_BILL_EQ__": n_bill_eq,
        "__N_BILL_SKILLS__": n_bill_skills,
        "__N_TERMS__": n_terms,
        "__N_TRACES__": f"{n_traces:,}",
        "__N_LOCAL__": n_local,
        "__N_SCALES__": n_scales,
        "__N_UNI__": n_uni,
        "__N_UNI_PLACED__": n_uni_placed,
        "__N_ORDERS__": n_orders,
        "__N_EXPL__": n_expl,
        "__N_EXPLTERMS__": f"{n_expl_terms:,}",
        "__N_SOLAR__": n_solar,
        "__N_IMPACTS__": n_imp,
        "__N_IMPTERMS__": f"{n_imp_terms:,}",
        "__TL_DECADES__": tl_decades,
        "__N_EQ__": len(eqs),
        "__N_EQFIELDS__": len({e.get("Field") for e in eqs if e.get("Field")}),
        "__EQ_OLDEST__": oldest_str,
        "__N_CONST__": len(notion.get("constants", [])),
        "__N_EXACT__": sum(1 for c in notion.get("constants", []) if c.get("Exact")),
        "__N_UNITS__": sum(1 for u in notion.get("units", []) if u.get("Kind") != "SI prefix"),
        "__SYNC_DATE__": sync,
    })


# ---------------- French mirror ----------------
def build_fr():
    """public/fr/*.html from public/*.html, through scripts/i18n.py and data/i18n/fr.json —
    and the EN · FR switch onto the English pages. Needs no API key: a string the cache
    lacks stays English and is counted, and scripts/translate.py fills the cache."""
    import i18n
    tr = i18n.Translator()
    (PUB / "fr").mkdir(exist_ok=True)
    n = 0
    for page in i18n.PAGE_FILES:
        src = PUB / page
        if not src.exists():
            continue
        html = src.read_text()
        en = i18n.add_switch(html, page, "en")
        if en != html:
            src.write_text(en)
        (PUB / "fr" / page).write_text(i18n.apply(html, page, tr))
        n += 1
    print(f"wrote {n} French pages -> public/fr/"
          + (f"  ({tr.misses} strings not yet in data/i18n/fr.json stay English — run scripts/translate.py)" if tr.misses else ""))


if __name__ == "__main__":
    n_min, n_gems = build_minerals_page()   # fills ELEMENT_MINERALS
    build_elements_page()
    n_classes, n_spectral, n_instr, n_obs, n_disc, n_miss, n_local = build_cosmos_page()
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
                      "__COSMOS__": compact(cosmos_lookup), "__TABLES__": compact(equation_tables()),
                      "__IMPACTS__": compact({i["id"]: {"name": i["Name"], "slug": slugify(i["Name"])}
                                              for i in notion.get("impacts", []) if i.get("Name")})})
    n_timeline, tl_decades = build_timeline_page()
    n_mines, n_mined = build_mines_page()
    n_mach, n_diag = build_machines_page()
    n_skills = build_skills_page()
    n_scales, n_orders = build_scales_page()
    n_uni, n_uni_placed = build_universe_page()
    n_terms, n_traces = build_glossary_page()
    n_expl, n_expl_terms = build_explainers_page()
    n_imp, n_imp_terms = build_impacts_page()
    n_solar = build_solar_page()
    n_bill_eq, n_bill_skills = build_billiards_page()
    n_search = build_search_index()
    build_home(n_min, n_gems, n_classes, n_spectral, n_instr, n_timeline, tl_decades,
               n_obs, n_disc, n_miss, n_search, n_mines, n_mined, n_mach, n_diag, n_skills, n_terms, n_traces,
               n_expl, n_expl_terms, n_imp, n_imp_terms, n_bill_eq, n_bill_skills)
    build_fr()
