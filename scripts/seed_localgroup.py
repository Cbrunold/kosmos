"""Seed the Local Group into Celestial_Objects [DB] — the catalogue the site lacked.

/cosmos said "the catalogue so far" and listed one object: the Sun. Meanwhile
the timeline has Andromeda arriving in 4.5 billion years and the discoveries
list has Hubble proving M31 is a galaxy at all — the Local Group was referenced
everywhere and catalogued nowhere.

This adds ~44 members: the three spirals, the Magellanic Clouds, the satellites
of both large galaxies, the isolated dwarfs, and the outliers at the edge of the
group's gravitational reach. Distances are in light-years from the Sun,
diameters in light-years, masses in kilograms (total, including dark matter,
where it is known at all).

Where a quantity is genuinely uncertain — the mass of most dwarf spheroidals,
the diameter of the ultra-faints — it is left empty rather than guessed. The
site renders blanks as dashes.

Adds the properties the DB was missing: Notes, Subgroup, Morphology,
Diameter (ly). Idempotent; backfills empty fields only.
Run on the VPS:  ./deploy.sh seed_localgroup
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import ensure_props, ensure_select_options, sync_rows  # noqa: E402

OBJECTS_DS = "f279dffc-9049-468d-8a5a-dbcdcf36f940"

SUBGROUPS = ["Milky Way", "Andromeda", "Independent", "Outlying"]
MORPHOLOGIES = ["Barred spiral", "Spiral", "Irregular", "Dwarf irregular", "Dwarf spheroidal",
                "Dwarf elliptical", "Compact elliptical", "Ultra-faint dwarf"]

NEW_PROPS = {
    "Notes": {"rich_text": {}},
    "Subgroup": {"select": {"options": [{"name": s} for s in SUBGROUPS]}},
    "Morphology": {"select": {"options": [{"name": m} for m in MORPHOLOGIES]}},
    "Diameter (ly)": {"number": {"format": "number"}},
}

MSUN = 1.989e30

# name, morphology, subgroup, distance ly, diameter ly, mass (solar masses or None), notes
MEMBERS = [
    ("Milky Way", "Barred spiral", "Milky Way", 0, 105000, 1.2e12,
     "Our own galaxy: a barred spiral of a few hundred billion stars, with a 4.3-million-solar-mass black hole at the centre and a dark halo that outweighs everything visible by five to one. We see it edge-on from inside, which is why its shape took until the 1920s to establish."),
    ("Canis Major Dwarf", "Dwarf irregular", "Milky Way", 25000, None, None,
     "The closest claimed satellite, on the far side of the galactic disc and so obscured that its existence as a distinct galaxy is still disputed — it may be a warp in the Milky Way's own outer disc."),
    ("Sagittarius Dwarf Spheroidal", "Dwarf spheroidal", "Milky Way", 65000, 10000, None,
     "Caught mid-destruction: it is passing through the Milky Way's disc and being pulled into a stream of stars that wraps right around the sky. Found only in 1994, because it is behind the galactic centre."),
    ("Segue 1", "Ultra-faint dwarf", "Milky Way", 75000, None, None,
     "About a thousand times fainter than a normal dwarf galaxy and perhaps the most dark-matter-dominated object known — a few hundred stars held together by roughly a thousand times their own mass in something invisible."),
    ("Reticulum II", "Ultra-faint dwarf", "Milky Way", 100000, None, None,
     "Found in Dark Energy Survey images in 2015. Its stars are unusually rich in r-process elements, which is evidence that a single neutron-star merger enriched the whole galaxy."),
    ("Ursa Minor Dwarf", "Dwarf spheroidal", "Milky Way", 200000, 2000, None,
     "One of the original faint companions found on photographic plates in the 1950s; almost entirely old stars, with no gas and no recent star formation."),
    ("Large Magellanic Cloud", "Irregular", "Milky Way", 163000, 32200, 1.4e11,
     "The largest satellite, visible to the naked eye from the southern hemisphere as a detached piece of the Milky Way. It hosts the Tarantula Nebula, the most active star-forming region in the Local Group, and produced SN 1987A."),
    ("Small Magellanic Cloud", "Irregular", "Milky Way", 200000, 18900, 7e9,
     "The LMC's smaller companion, being torn apart by it: the Magellanic Stream of gas trailing both clouds is the evidence. Henrietta Leavitt found the Cepheid period–luminosity law in its stars."),
    ("Bootes I", "Ultra-faint dwarf", "Milky Way", 197000, None, None,
     "One of the Sloan Digital Sky Survey's haul of ultra-faint companions, found in 2006 by spotting a slight over-density of stars rather than by seeing anything."),
    ("Draco Dwarf", "Dwarf spheroidal", "Milky Way", 260000, 2700, None,
     "Very high mass-to-light ratio — its stars move far faster than their own gravity explains — which made it one of the first strong cases for dark matter in a small galaxy."),
    ("Sculptor Dwarf", "Dwarf spheroidal", "Milky Way", 290000, 1600, None,
     "The first dwarf spheroidal ever found, by Harlow Shapley in 1937 on plates from Boyden Observatory; the class was defined around it."),
    ("Sextans Dwarf", "Dwarf spheroidal", "Milky Way", 290000, 8400, None,
     "Extremely diffuse — spread over a degree of sky but so faint it went unnoticed until 1990."),
    ("Carina Dwarf", "Dwarf spheroidal", "Milky Way", 330000, 1600, None,
     "Unusual among the dwarf spheroidals for having formed stars in several distinct bursts rather than all at once, which its colour-magnitude diagram records as separate populations."),
    ("Crater 2", "Dwarf spheroidal", "Milky Way", 380000, 7000, None,
     "The 'feeble giant': one of the largest satellites by size but among the faintest, with stars moving so slowly that it appears to hold much less dark matter than its neighbours."),
    ("Fornax Dwarf", "Dwarf spheroidal", "Milky Way", 460000, 6000, None,
     "The brightest of the Milky Way's dwarf spheroidals, and the only one with its own globular clusters — six of them, which is hard to explain for a galaxy this small."),
    ("Leo II", "Dwarf spheroidal", "Milky Way", 690000, 4000, None,
     "A distant, old companion that stopped forming stars billions of years ago; almost all its light comes from stars older than 8 billion years."),
    ("Canes Venatici I", "Dwarf spheroidal", "Milky Way", 720000, None, None,
     "Found in Sloan data in 2006, out at the edge of the Milky Way's satellite system."),
    ("Leo I", "Dwarf spheroidal", "Milky Way", 820000, 2000, None,
     "The most distant satellite still bound to the Milky Way, and moving fast enough that its orbit is used to weigh the galaxy's dark halo."),

    ("NGC 185", "Dwarf elliptical", "Andromeda", 2080000, 8000, None,
     "A satellite of Andromeda with an unusual amount of gas and dust for a dwarf elliptical, and a small amount of ongoing star formation."),
    ("NGC 147", "Dwarf elliptical", "Andromeda", 2530000, 10000, None,
     "A companion to NGC 185 as well as to Andromeda; the pair orbit each other."),
    ("Andromeda (M31)", "Barred spiral", "Andromeda", 2540000, 152000, 1.5e12,
     "The largest galaxy in the Local Group and the most distant thing visible to the naked eye. Hubble's Cepheids in it proved in 1924 that the spiral nebulae are other galaxies; it is approaching us at 110 km/s and will merge with the Milky Way in about 4.5 billion years."),
    ("LGS 3", "Dwarf irregular", "Andromeda", 2600000, 5000, None,
     "A transitional object between a dwarf irregular and a dwarf spheroidal — it still holds gas but has nearly stopped forming stars."),
    ("M32", "Compact elliptical", "Andromeda", 2650000, 6500, 3e9,
     "A rare compact elliptical: extraordinarily dense, and probably the stripped core of a larger galaxy that Andromeda has already eaten."),
    ("M110 (NGC 205)", "Dwarf elliptical", "Andromeda", 2690000, 17000, 1e10,
     "Andromeda's other bright companion, with dust lanes and young stars in its core — unusual for a dwarf elliptical, and a sign of recent gas accretion."),

    ("Leo T", "Dwarf irregular", "Independent", 1400000, 2000, None,
     "The faintest known galaxy still holding neutral hydrogen, sitting right at the boundary where a galaxy's gas is stripped away by its surroundings."),
    ("Phoenix Dwarf", "Dwarf irregular", "Independent", 1400000, 3000, None,
     "Another transitional dwarf, with an old stellar body and a detached cloud of gas that may have been blown out of it."),
    ("NGC 6822 (Barnard's Galaxy)", "Dwarf irregular", "Independent", 1600000, 7000, 1.6e9,
     "Found by E. E. Barnard in 1884 with a 5-inch refractor. Hubble's 1925 study of its Cepheids was the first to place a galaxy firmly outside the Milky Way."),
    ("IC 10", "Dwarf irregular", "Independent", 2200000, 5000, None,
     "The only starburst galaxy in the Local Group — forming stars far faster than its size suggests — hidden behind the Milky Way's dust, which is why it was catalogued late."),
    ("IC 1613", "Dwarf irregular", "Independent", 2380000, 10000, None,
     "Unusually free of dust, which makes its stars easy to measure individually; it is one of the standard laboratories for calibrating the distance ladder."),
    ("Cetus Dwarf", "Dwarf spheroidal", "Independent", 2500000, 3000, None,
     "An isolated dwarf spheroidal — rare, since almost all of them orbit a large galaxy, and evidence that a galaxy can lose its gas without a big neighbour to strip it."),
    ("Leo A", "Dwarf irregular", "Independent", 2600000, 4000, None,
     "Very metal-poor and still forming stars, which makes it a nearby stand-in for the kind of galaxy that was common in the early universe."),
    ("Triangulum (M33)", "Spiral", "Independent", 2730000, 60000, 5e10,
     "The third-largest member and the smallest spiral, possibly a satellite of Andromeda on a long orbit. Under a dark sky it is at the edge of naked-eye visibility."),
    ("Pegasus Dwarf Irregular", "Dwarf irregular", "Independent", 3000000, 7000, None,
     "An isolated dwarf on the far side of the Local Group from the Milky Way."),
    ("WLM (Wolf–Lundmark–Melotte)", "Dwarf irregular", "Independent", 3040000, 8000, None,
     "One of the most isolated members, which makes it useful: whatever shaped it, it was not a large neighbour."),
    ("Aquarius Dwarf (DDO 210)", "Dwarf irregular", "Independent", 3200000, 3000, None,
     "A small, gas-rich dwarf far from either large galaxy, moving slowly enough that it may not be bound to the group at all."),
    ("Tucana Dwarf", "Dwarf spheroidal", "Independent", 3200000, 3000, None,
     "The most isolated dwarf spheroidal known, out at the far edge of the group with no obvious galaxy to have stripped it."),
    ("Sagittarius Dwarf Irregular (SagDIG)", "Dwarf irregular", "Independent", 3400000, 5000, None,
     "The most metal-poor galaxy in the Local Group — its stars formed from gas that has barely been enriched by earlier generations."),

    ("Antlia Dwarf", "Dwarf irregular", "Outlying", 4300000, 3000, None,
     "Paired with NGC 3109 out beyond the group's main body; the two may have passed close to each other in the past."),
    ("NGC 3109", "Dwarf irregular", "Outlying", 4300000, 25000, None,
     "Large enough to have a rotating disc, at the very edge of the Local Group — some analyses put it and its companions outside the group entirely, on their way past."),
    ("Leo P", "Dwarf irregular", "Outlying", 5300000, 3000, None,
     "Found in 2013 by a radio survey looking for gas rather than light. Extremely metal-poor and still forming stars — about as close to a pristine galaxy as anything nearby."),
    ("IC 5152", "Dwarf irregular", "Outlying", 5800000, 8000, None,
     "An outlying dwarf with a bright foreground star sitting almost on top of it, which complicated its study for decades."),
    ("ESO 294-010", "Dwarf spheroidal", "Outlying", 6100000, 3000, None,
     "A transitional dwarf on the group's outskirts, holding a small pocket of gas."),
    ("KKR 25", "Dwarf spheroidal", "Outlying", 6400000, 3000, None,
     "One of the most isolated dwarf spheroidals known, with no large galaxy within millions of light-years."),
    ("IC 4662", "Dwarf irregular", "Outlying", 8000000, 10000, None,
     "A starburst dwarf at the far edge of the group's gravitational reach, forming stars vigorously despite its isolation."),
]


def main():
    schema = ensure_props(OBJECTS_DS, NEW_PROPS, "celestial objects")
    ensure_select_options(OBJECTS_DS, "Subgroup", SUBGROUPS, "celestial objects")
    ensure_select_options(OBJECTS_DS, "Morphology", MORPHOLOGIES, "celestial objects")
    ensure_select_options(OBJECTS_DS, "Type", ["Star", "Planet", "Galaxy", "Moon"], "celestial objects")
    rows = [{
        "Name": n, "Type": "Galaxy", "Morphology": morph, "Subgroup": sub,
        "Distance from Earth": dist, "Diameter (ly)": diam,
        "Mass": round(msun * MSUN, 0) if msun else None,
        "Notes": notes,
    } for n, morph, sub, dist, diam, msun, notes in MEMBERS]
    sync_rows(OBJECTS_DS, schema, rows, "celestial objects")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
