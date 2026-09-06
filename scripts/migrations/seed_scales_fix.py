"""Correct four distances on Cosmic Structures [DB], overwriting what seed_scales wrote.

Found by cross-checking every row that carries both a redshift and a distance
against flat LCDM (Planck 2018) — the check now runs at build time in
build.py:lcdm_comoving and is shown on the page. Three rows failed it and one
was simply out of date:

  Quipu Superstructure   1900 -> 650 Mly.  The 1900 was its ~1.3 Gly LENGTH
                         leaking into the distance column. Bohringer et al.
                         (2025) find the superstructures at z = 0.03-0.06,
                         which is 425-850 Mly comoving.

  Hercules-Corona        9800 -> 15200 Mly. 9.8 Gly is the LIGHT-TRAVEL
  Borealis Great Wall    distance at z ~ 1.6; every other row on the page is
                         comoving (the last-scattering surface at 45.6 Gly
                         could not be anything else). Mixing the two
                         conventions in one column is the error most worth
                         not making on a page about distance.

  CfA2 Great Wall        200 -> 300 Mly. 200 Mly is the near edge; the wall
                         spans z ~ 0.015-0.03 and the Coma Supercluster sits
                         inside it at 300 Mly, so the old pair had a component
                         further away than the structure containing it.

  Virgo Cluster          65 -> 54 Mly. 16.5 Mpc is the Cepheid/TRGB distance
                         and has been for two decades. Its redshift still
                         disagrees with it by ~25%, which is real physics --
                         we are falling into Virgo, so its recession velocity
                         understates the distance. The page says so rather
                         than hiding it.

Redshifts are text, not numbers, because real structures span a range. The
build-time check parses the range and uses its midpoint.

Unlike sync_rows this OVERWRITES: the values it replaces are wrong, so
"a human already answered this one" is not a reason to keep them.
Idempotent: a row already holding the corrected value is skipped.
Run on the VPS:  ./deploy.sh seed_scales_fix
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from notion import find_ds  # noqa: E402
from seed_theories import call, query_all, title_of  # noqa: E402

TITLE = "Cosmic Structures [DB]"

# name -> {property: corrected value}
FIXES = {
    "Quipu Superstructure": {
        "Distance (ly)": 650_000_000,
        "Redshift": "0.03–0.06",
        "Notes": "Reported in 2025 as the most massive structure yet identified, named for the Andean knotted cords it resembles. As with every claimed 'largest structure', how much of it is one object depends on where you draw the line. Its 1.3-billion-light-year length is more than twice its distance from us, which is the clearest sign of how little the word 'object' is doing here.",
    },
    "Hercules–Corona Borealis Great Wall": {
        "Distance (ly)": 15_200_000_000,
        "Notes": "Claimed from a clustering of gamma-ray bursts and far larger than the scale at which the universe is supposed to be uniform. Whether it is real or an artefact of how bursts are found is genuinely unsettled. Usually quoted as '10 billion light-years away' — that is the light-travel distance; the comoving distance given here is 15.2 billion, and the two are not interchangeable at z = 1.6.",
    },
    "CfA2 Great Wall": {
        "Distance (ly)": 300_000_000,
        "Redshift": "0.015–0.03",
    },
    "Virgo Cluster": {
        "Distance (ly)": 54_000_000,
        "Notes": "The nearest large cluster and the gravitational anchor of our supercluster, with the giant elliptical M87 — and its imaged black hole — at the centre. Catalogued as a knot of nebulae by Messier long before anyone knew what it was. Its distance is measured directly, by Cepheids and the tip of the red giant branch, and disagrees with its redshift by about a quarter: we are falling toward it at some 300 km/s, which subtracts from its apparent recession.",
    },
}


def current(page, prop):
    p = page["properties"].get(prop, {})
    if p.get("type") == "number":
        return p["number"]
    if p.get("type") == "rich_text":
        return "".join(x["plain_text"] for x in p["rich_text"]) or None
    return None


def encode_value(v):
    if isinstance(v, (int, float)):
        return {"number": v}
    return {"rich_text": [{"text": {"content": v}}]}


if __name__ == "__main__":
    ds = find_ds(TITLE)
    if not ds:
        sys.exit(f"{TITLE} not found — run seed_scales first")
    pages = {title_of(p): p for p in query_all(ds) if title_of(p)}

    missing = [n for n in FIXES if n not in pages]
    if missing:
        sys.exit(f"rows not in the database: {missing}")

    fixed = skipped = 0
    for name, props in FIXES.items():
        page = pages[name]
        payload = {k: encode_value(v) for k, v in props.items() if current(page, k) != v}
        if not payload:
            skipped += 1
            print(f"  ok       {name}")
            continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
        fixed += 1
        for k, v in props.items():
            was = current(page, k)
            if was != v:
                shown = f"{was:,} -> {v:,}" if isinstance(v, (int, float)) else "text rewritten"
                print(f"  FIXED    {name} · {k}: {shown}")
    print(f"scales fix: {fixed} rows corrected, {skipped} already correct")
