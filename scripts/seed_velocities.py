"""Add radial velocity to the Celestial Objects DB, so /universe can move what moves.

/universe places everything by direction and distance and then holds still,
because a distance is all the catalogue gives. One object in it has a measured
approach speed sitting in its own Notes: Andromeda, closing at 110 km/s. This
turns that sentence into a number the map can use.

Sign is the astronomical convention — negative is approaching (blueshifted),
positive receding. The page animates any object carrying one, so filling more
rows in Notion extends the animation without touching code.

A radial velocity is easy to quote and easy to quote wrongly: most catalogues
give it heliocentric, which folds in the Sun's own ~220 km/s around the galactic
centre, and the number you want for "is it coming towards the Milky Way" is the
galactocentric one. Every figure here is that corrected value.

The transverse column matters more than it looks. Checking it is what stopped
the Magellanic Clouds being drawn as though they were falling in: the SMC's
radial velocity is 7 km/s and its sideways motion is 217, so a map that moved it
only along the line of sight would show it almost frozen while it is in fact
travelling at a fifth of a thousand kilometres a second. M31 turns out to be the
only member of the Local Group whose motion is mostly towards us. The rest are
in orbit, and Motion records which model applies so the page can refuse to
extrapolate the ones it would get wrong.

Idempotent: adds the property if missing, fills only rows that are empty.
Run on the VPS:  ./deploy.sh seed_velocities
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, query_all, title_of  # noqa: E402

CELESTIAL_DS = "f279dffc-9049-468d-8a5a-dbcdcf36f940"   # same id fetch_all.py uses
PROP = "Radial velocity (km/s)"
TPROP = "Transverse velocity (km/s)"
MPROP = "Motion"
MOTIONS = ["Infalling", "Bound orbit"]

# name -> (radial km/s, transverse km/s, motion)
# Radial is galactocentric and signed: negative approaches the Milky Way, positive
# recedes. Transverse is the sideways component — unsigned, because we store its
# size and not its direction, which is exactly why the map cannot draw it.
#
# The transverse column is not decoration. It decides whether moving a thing along
# its radial line is a picture or a lie. M31 is the only member of the Local Group
# where the radial part dominates; for the other three the sideways motion is
# several times larger, and they are not falling anywhere — they are going round.
VELOCITIES = {
    # radial 110 vs 17 sideways: near enough a head-on fall (van der Marel+ 2012)
    "Andromeda (M31)": (-110.0, 17.0, "Infalling"),
    # v_helio -179 km/s corrected to the galactic standard of rest; the 3D vector
    # from Gaia DR3 puts the total near 234 km/s, so most of it is sideways
    "Triangulum (M33)": (-44.0, 230.0, "Bound orbit"),
    # Kallivayalil+ 2013 give a total galactocentric speed of 321 +/- 24 km/s, of
    # which only about 64 is radial. Published radial values run 64-84 depending on
    # epoch and solar motion assumed; the conclusion does not move with them
    "Large Magellanic Cloud": (64.0, 314.0, "Bound orbit"),
    # total 217 +/- 26 km/s (same source) and a radial component near zero: the SMC
    # is neither coming nor going, which is what a circular orbit looks like
    "Small Magellanic Cloud": (7.0, 217.0, "Bound orbit"),
}


def main():
    ensure_props(CELESTIAL_DS, {PROP: {"number": {}}, TPROP: {"number": {}},
                                MPROP: {"select": {"options": [{"name": m} for m in MOTIONS]}}},
                 "celestialObjects")
    pages = {title_of(p, "Name"): p for p in query_all(CELESTIAL_DS) if title_of(p, "Name")}
    filled = missing = 0
    for name, (v, tv, motion) in VELOCITIES.items():
        page = pages.get(name)
        if not page:
            print(f"  ! no row named {name!r}")
            missing += 1
            continue
        props = {}
        if (page["properties"].get(PROP) or {}).get("number") is None:
            props[PROP] = {"number": v}
        if (page["properties"].get(TPROP) or {}).get("number") is None:
            props[TPROP] = {"number": tv}
        if not (page["properties"].get(MPROP) or {}).get("select"):
            props[MPROP] = {"select": {"name": motion}}
        if not props:
            continue                       # a human may have corrected it
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": props})
        print(f"  {name}: radial {v} km/s, transverse {tv} km/s, {motion}")
        filled += 1
    print(f"velocities: {filled} filled, {missing} not matched, {len(VELOCITIES)} defined")


if __name__ == "__main__":
    main()
