"""Add radial velocity to the Celestial Objects DB, so /universe can move what moves.

/universe places everything by direction and distance and then holds still,
because a distance is all the catalogue gives. One object in it has a measured
approach speed sitting in its own Notes: Andromeda, closing at 110 km/s. This
turns that sentence into a number the map can use.

Sign is the astronomical convention — negative is approaching (blueshifted),
positive receding. The page animates any object carrying one, so filling more
rows in Notion extends the animation without touching code.

Only M31 is filled here, and deliberately. A radial velocity is easy to quote
and easy to quote wrongly: most catalogues give it heliocentric, which folds in
the Sun's own 220 km/s around the galactic centre, and the number you want for
"is it coming towards the Milky Way" is the galactocentric one. -110 km/s is
that corrected figure. The rest of the Local Group can be added when each value
has been checked the same way.

Idempotent: adds the property if missing, fills only rows that are empty.
Run on the VPS:  ./deploy.sh seed_velocities
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, query_all, title_of  # noqa: E402

CELESTIAL_DS = "f279dffc-9049-468d-8a5a-dbcdcf36f940"   # same id fetch_all.py uses
PROP = "Radial velocity (km/s)"

# name -> km/s, negative = approaching the Milky Way (galactocentric)
VELOCITIES = {
    "Andromeda (M31)": -110.0,
}


def main():
    ensure_props(CELESTIAL_DS, {PROP: {"number": {}}}, "celestialObjects")
    pages = {title_of(p, "Name"): p for p in query_all(CELESTIAL_DS) if title_of(p, "Name")}
    filled = missing = 0
    for name, v in VELOCITIES.items():
        page = pages.get(name)
        if not page:
            print(f"  ! no row named {name!r}")
            missing += 1
            continue
        if (page["properties"].get(PROP) or {}).get("number") is not None:
            continue                       # a human may have corrected it
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {PROP: {"number": v}}})
        print(f"  {name}: {v} km/s")
        filled += 1
    print(f"velocities: {filled} filled, {missing} not matched, {len(VELOCITIES)} defined")


if __name__ == "__main__":
    main()
