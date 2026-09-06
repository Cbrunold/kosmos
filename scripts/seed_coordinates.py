"""Write the resolved sky coordinates into Notion, from data/astro/coordinates.json.

The Coordinates column on Celestial Objects [DB] existed and was empty for all
45 rows, so nothing on the site could be placed in three dimensions: a distance
alone puts an object on a sphere, not at a point. Cosmic Structures [DB] had no
coordinate column at all.

This adds "RA (deg)" and "Dec (deg)" as numbers to both -- the map needs to
compute with them, and sexagesimal text cannot be computed with -- and fills
the existing free-text Coordinates column with the readable form alongside.

Positions come from the CDS name resolver at Strasbourg (scripts/
fetch_coordinates.py), not from anybody's memory, and each row records which
service answered. What Sesame could not resolve stays empty: the Sloan and
CfA2 Great Walls and the Columba Supercluster have no single position to
resolve, being tens of degrees across, and the map draws them as shells at
the right radius in no particular direction. That is what is known about them.

The Sun and the Milky Way are written as the origin. A direction to something
you are inside is not a small measurement problem, it is a category error.

Idempotent: a row already holding the value is skipped.
Run on the VPS:  ./deploy.sh seed_coordinates
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notion import find_ds  # noqa: E402
from seed_theories import call, ensure_props, query_all  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "astro" / "coordinates.json"

OBJECTS_DS = "f279dffc-9049-468d-8a5a-dbcdcf36f940"      # Celestial Objects [DB]
STRUCTURES_TITLE = "Cosmic Structures [DB]"

PROPS = {"RA (deg)": {"number": {}}, "Dec (deg)": {"number": {}}, "Coordinates": {"rich_text": {}}}

# we are inside these; the origin is the honest answer, not a direction
ORIGIN = {"Sun", "Milky Way", "Milky Way dark halo", "Solar System (to the heliopause)",
          "Oort Cloud", "Local Interstellar Cloud", "Local Bubble", "Orion Arm",
          "Local Group", "Local Sheet", "Local Volume", "The cosmic web", "Observable universe"}


def sexagesimal(ra: float, dec: float) -> str:
    h = ra / 15.0
    hh = int(h); mm = int((h - hh) * 60); ss = ((h - hh) * 60 - mm) * 60
    sign = "+" if dec >= 0 else "−"
    a = abs(dec)
    dd = int(a); am = int((a - dd) * 60); asec = ((a - dd) * 60 - am) * 60
    return f"{hh:02d}h {mm:02d}m {ss:04.1f}s  {sign}{dd:02d}° {am:02d}′ {asec:04.1f}″"


def title_of(page):
    for p in page["properties"].values():
        if p.get("type") == "title":
            return "".join(x["plain_text"] for x in p["title"]) or None
    return None


def num_of(page, prop):
    p = page["properties"].get(prop, {})
    return p.get("number") if p.get("type") == "number" else None


def fill(ds_id, label, coords):
    ensure_props(ds_id, PROPS, label)
    pages = {title_of(p): p for p in query_all(ds_id) if title_of(p)}
    wrote = same = blank = 0
    for name, page in pages.items():
        if name in ORIGIN:
            ra, dec, note = 0.0, 0.0, "origin — we are inside it"
        elif name in coords:
            c = coords[name]
            ra, dec = c["ra"], c["dec"]
            note = f"{sexagesimal(ra, dec)}  ·  {c['id']} via {c['resolver']}"
        else:
            blank += 1
            continue
        if num_of(page, "RA (deg)") == ra and num_of(page, "Dec (deg)") == dec:
            same += 1
            continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": {
            "RA (deg)": {"number": ra},
            "Dec (deg)": {"number": dec},
            "Coordinates": {"rich_text": [{"text": {"content": note}}]},
        }})
        wrote += 1
    print(f"{label}: {wrote} written, {same} already correct, {blank} left blank (no position to resolve)")


if __name__ == "__main__":
    if not SRC.exists():
        sys.exit(f"{SRC.relative_to(ROOT)} missing — run scripts/fetch_coordinates.py first")
    coords = json.loads(SRC.read_text())
    print(f"{len(coords)} resolved positions on file")
    fill(OBJECTS_DS, "celestial objects", coords)
    ds = find_ds(STRUCTURES_TITLE)
    if ds:
        fill(ds, "cosmic structures", coords)
    else:
        print(f"{STRUCTURES_TITLE} not found — run seed_scales first")
