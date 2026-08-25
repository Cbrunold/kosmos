"""Create and seed Solar System [DB]: orbital elements, so the planets can be computed.

Everything else on the site is a fact you look up. This is a fact you *run*: six
Keplerian elements and their per-century rates per body, and from them /solar
computes where each planet is at any date — no positions are stored, because
storing positions would mean storing one instant and calling it the truth.

Source: E. M. Standish, "Keplerian Elements for Approximate Positions of the
Major Planets" (JPL Solar System Dynamics), Table 1, fitted to the interval
1800-2050 AD. Nominal error over that window runs from ~10 arcsec of heliocentric
longitude for Neptune to ~600 for Saturn. Earth's row is really the Earth/Moon
barycentre, which is what the table gives and what the page says.

Pluto is not in the current JPL table — it was removed when the definition of
planet changed — so its row comes from Standish's earlier 3000 BC-3000 AD table.
It is also the one body here where a fixed ellipse is a poor long-range model:
it is locked in a 3:2 resonance with Neptune and its motion is chaotic on
million-year timescales. Fine for the centuries the page will show, wrong if
anyone extrapolates it far.

Idempotent: creates the database if missing, backfills empty fields, never
overwrites an edit made in Notion.
Run on the VPS:  ./deploy.sh seed_solar
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_glossary import find_ds  # noqa: E402
from seed_theories import call, ensure_props, ensure_select_options, sync_rows  # noqa: E402

PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"   # Physical Sciences
TITLE = "Solar System [DB]"
KINDS = ["Star", "Planet", "Dwarf planet"]

# name, kind, radius km, mass kg, period yr,
#   (a, e, I, L, long.peri, long.node), (rates per Julian century), notes
BODIES = [
    ("Sun", "Star", 695700.0, 1.989e30, None, None, None,
     "The origin of the frame, holding 99.86 % of the system's mass — which is why every other body here can be treated as a two-body problem and solved exactly."),
    ("Mercury", "Planet", 2439.7, 3.301e23, 0.2408,
     (0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
     (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081),
     "The most eccentric planetary orbit and the fastest — 88 days a lap. Its perihelion advances 43 arcsec/century faster than Newton allows, which general relativity accounted for in 1915."),
    ("Venus", "Planet", 6051.8, 4.867e24, 0.6152,
     (0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
     (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418),
     "The roundest orbit in the system, eccentricity 0.0068 — near enough a circle that the drawn ellipse looks like one."),
    ("Earth", "Planet", 6371.0, 5.972e24, 1.0000,
     (1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
     (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0),
     "Strictly the Earth/Moon barycentre, which is what the source table gives — a point about 4,670 km from Earth's centre, still inside the planet."),
    ("Mars", "Planet", 3389.5, 6.417e23, 1.8808,
     (1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
     (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343),
     "Eccentric enough that Kepler could not fit it to a circle, which is why the first law was found here and not somewhere easier."),
    ("Jupiter", "Planet", 69911.0, 1.898e27, 11.862,
     (5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
     (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106),
     "Two and a half times the mass of everything else in orbit combined. The Sun–Jupiter barycentre sits just outside the Sun's surface, so the Sun visibly orbits it."),
    ("Saturn", "Planet", 58232.0, 5.683e26, 29.457,
     (9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
     (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794),
     "The least dense planet — it would float in water, if there were an ocean big enough. Also the largest nominal error in this table, about 600 arcsec of longitude."),
    ("Uranus", "Planet", 25362.0, 8.681e25, 84.011,
     (19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503),
     (-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589),
     "Tipped 98° onto its side, so it rolls along its orbit rather than spinning upright. The tilt is of the planet, not the orbit, which stays within 0.8° of the ecliptic."),
    ("Neptune", "Planet", 24622.0, 1.024e26, 164.79,
     (30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574),
     (0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664),
     "Found in 1846 by predicting it from Uranus's misbehaviour and pointing a telescope where the arithmetic said — within a degree of where Le Verrier put it."),
    ("Pluto", "Dwarf planet", 1188.3, 1.303e22, 247.94,
     (39.48211675, 0.24882730, 17.14001206, 238.92903833, 224.06891629, 110.30393684),
     (-0.00031596, 0.00005170, 0.00004818, 145.20780515, -0.04062942, -0.01183482),
     "Inclined 17° to everyone else and eccentric enough to come inside Neptune's orbit for 20 years of its 248. The two never meet: a 3:2 resonance keeps them apart, and it makes Pluto's long-term motion chaotic."),
]

EL = ["a", "e", "I", "L", "peri", "node"]


def row(b):
    name, kind, rad, mass, per, el, rate, notes = b
    r = {"Name": name, "Kind": kind, "Radius (km)": rad, "Mass (kg)": mass,
         "Period (yr)": per, "Notes": notes}
    for i, k in enumerate(EL):
        r[k] = el[i] if el else None
        r["d" + k] = rate[i] if rate else None
    return r


def main():
    props = {"Kind": {"select": {"options": [{"name": k} for k in KINDS]}},
             "Radius (km)": {"number": {}}, "Mass (kg)": {"number": {}},
             "Period (yr)": {"number": {}}, "Notes": {"rich_text": {}}}
    for k in EL:
        props[k] = {"number": {}}
        props["d" + k] = {"number": {}}
    ds = find_ds(TITLE)
    if not ds:
        db = call("POST", "https://api.notion.com/v1/databases", {
            "parent": {"type": "page_id", "page_id": PARENT_PAGE},
            "title": [{"type": "text", "text": {"content": TITLE}}],
            "initial_data_source": {"properties": {"Name": {"title": {}}, **props}},
        })
        ds = db["data_sources"][0]["id"]
        print("created", TITLE, ds)
    else:
        print(TITLE, "exists:", ds)
    schema = ensure_props(ds, props, "solar")
    ensure_select_options(ds, "Kind", KINDS, "solar")
    sync_rows(ds, schema, [row(b) for b in BODIES], "solar", key="Name")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
