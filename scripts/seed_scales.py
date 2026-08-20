"""Create and seed Cosmic Structures [DB]: the ladder of scale, Sun to horizon.

/cosmos maps the Local Group and stops at 8 million light-years. Everything
above that — the Virgo Cluster, the Local Supercluster, Laniakea, the walls and
voids, the cosmic web, the horizon itself — was missing, which is four more
orders of magnitude than the site covered.

Every row carries a Size and, where we are not inside it, a Distance, both in
light-years. The page converts to whatever unit suits the number (AU → ly →
thousand → million → billion, with parsecs alongside, since that is what the
literature quotes) — the unit changes down the ladder, the stored number never
does.

"Within" names the next structure up, so the nesting chain from the Solar
System to the observable universe can be walked without a relation.

Sizes for diffuse things — superclusters, voids, walls — are the figure usually
quoted for their longest extent, and they are soft: a supercluster has no edge,
and Laniakea's 520 million light-years is the span of a flow basin, not a wall.
Contested structures say so in their notes rather than being left out.

Idempotent: creates the database if missing, backfills empty fields only.
Run on the VPS:  ./deploy.sh seed_scales
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, sync_rows  # noqa: E402

PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"
TITLE = "Cosmic Structures [DB]"

KINDS = ["Local", "Galaxy", "Group", "Cluster", "Supercluster", "Filament", "Void", "Attractor", "Cosmological"]

KLY, MLY, GLY = 1e3, 1e6, 1e9

# name, kind, size ly, distance ly (None = we are inside it), redshift, population, within, year, notes
STRUCTURES = [
    ("Solar System (to the heliopause)", "Local", 0.0038, None, None, "1 star, 8 planets", "Oort Cloud", None,
     "Where the solar wind gives way to the interstellar medium, about 120 astronomical units out. Voyager 1 crossed it in 2012 and is the only object to have sent back a measurement from the other side."),
    ("Oort Cloud", "Local", 3.2, None, None, "perhaps a trillion comets", "Local Interstellar Cloud", 1950,
     "A shell of icy bodies half way to the nearest star, inferred entirely from where long-period comets come from — nothing in it has ever been seen directly."),
    ("Local Interstellar Cloud", "Local", 30, None, None, "gas at 0.3 atoms per cm³", "Local Bubble", None,
     "The wisp of warm interstellar gas the Sun happens to be passing through, and will leave in a few thousand years."),
    ("Local Bubble", "Local", 1000, None, None, "hot, thin gas; ~15 nearby stars", "Orion Arm", None,
     "A cavity blown in the interstellar medium by supernovae about 14 million years ago, which is why the sky nearby is unusually clear of dust. Its surface is where most nearby star formation is happening."),
    ("Orion Arm", "Local", 10000, None, None, "a minor spiral arm", "Milky Way", None,
     "The spur of the Milky Way's spiral we sit in, between the Sagittarius and Perseus arms — not a major arm, which was only established once radio surveys could map the gas."),
    ("Milky Way", "Galaxy", 105000, None, None, "100–400 billion stars", "Milky Way dark halo", None,
     "Our galaxy, seen edge-on from inside — the reason its shape took until the 1920s to settle. A supermassive black hole of 4.3 million solar masses sits at the centre."),
    ("Milky Way dark halo", "Galaxy", 2000000, None, None, "~1.2 × 10¹² solar masses", "Local Group", 1970,
     "The invisible mass the galaxy actually sits in, five times heavier than everything that shines and reaching far past the visible disc. Its size is inferred from how the outer satellites move."),
    ("Local Group", "Group", 10000000, None, None, "~80 galaxies, 3 of them spirals", "Local Sheet", 1936,
     "Everything gravitationally bound to us: the Milky Way, Andromeda, Triangulum and a swarm of dwarfs. Named by Hubble. It is falling toward Virgo at about 600 km/s."),

    ("Local Sheet", "Group", 23000000, None, None, "a flat wall of nearby galaxies", "Local Volume", 2008,
     "A flattened sheet of galaxies, only about 5 million light-years thick, that the Local Group sits inside and moves with. It faces the Local Void, which is pushing it."),
    ("Local Void", "Void", 150000000, 23000000, None, "almost nothing", "Local Supercluster (Virgo)", 1987,
     "An enormous emptiness beginning right at our doorstep and stretching away behind Sagittarius. Its lack of matter pushes the Local Sheet away at about 260 km/s — we are being repelled as much as attracted."),
    ("Local Volume", "Group", 33000000, None, None, "~600 known galaxies", "Local Supercluster (Virgo)", None,
     "The observational sphere of about 10 megaparsecs in which individual galaxies can be resolved into stars, which makes it the region where distances are measured rather than inferred."),
    ("Virgo Cluster", "Cluster", 15000000, 65000000, "0.0036", "~1,500 galaxies", "Local Supercluster (Virgo)", 1781,
     "The nearest large cluster and the gravitational anchor of our supercluster, with the giant elliptical M87 — and its imaged black hole — at the centre. Catalogued as a knot of nebulae by Messier long before anyone knew what it was."),
    ("Fornax Cluster", "Cluster", 6000000, 62000000, "0.0046", "~60 large galaxies", "Local Supercluster (Virgo)", None,
     "The second-nearest cluster, small but well studied because it sits in a clean part of the southern sky."),
    ("Local Supercluster (Virgo)", "Supercluster", 110000000, None, None, "~100 galaxy groups", "Laniakea Supercluster", 1953,
     "The flattened concentration of groups centred on the Virgo Cluster, mapped by Gérard de Vaucouleurs when the idea that clusters themselves cluster was still controversial. We are on its outskirts."),

    ("Laniakea Supercluster", "Supercluster", 520000000, None, None, "~100,000 galaxies, 10¹⁷ solar masses", "Pisces–Cetus Supercluster Complex", 2014,
     "Defined not by where galaxies are but by where they are going: Tully and colleagues mapped the peculiar velocities of 8,000 galaxies and drew the boundary where flows diverge. Everything inside falls toward the same place. The name is Hawaiian for 'immeasurable heaven'."),
    ("Great Attractor", "Attractor", 100000000, 250000000, "0.016", "the focus of Laniakea's flow", "Laniakea Supercluster", 1986,
     "The gravitational low point Laniakea drains toward, lying behind the plane of the Milky Way — the 'Zone of Avoidance' — which is why it took infrared and X-ray surveys to find at all."),
    ("Norma Cluster (Abell 3627)", "Cluster", 20000000, 220000000, "0.016", "a rich cluster", "Great Attractor", 1996,
     "The densest thing at the heart of the Great Attractor, hidden behind our own galaxy's dust and only properly measured in the 1990s."),
    ("Dipole Repeller", "Attractor", 300000000, 800000000, None, "an absence of galaxies", "—", 2017,
     "Not a thing but the lack of one: an underdense region on the opposite side of the sky from the Great Attractor, pushing us away as effectively as the Attractor pulls. Our motion relative to the microwave background is the sum of the two."),
    ("Centaurus Cluster", "Cluster", 15000000, 155000000, "0.0114", "a rich cluster", "Hydra–Centaurus Supercluster", None,
     "One of the nearest rich clusters, and one of the brightest X-ray sources in the sky because of the hot gas trapped between its galaxies."),
    ("Hydra–Centaurus Supercluster", "Supercluster", 300000000, 160000000, "0.011", "several clusters", "Laniakea Supercluster", None,
     "The nearest neighbouring supercluster, now understood as part of Laniakea rather than separate from it — the redrawing that Laniakea's flow map forced."),
    ("Pavo–Indus Supercluster", "Supercluster", 300000000, 200000000, None, "several groups and clusters", "Laniakea Supercluster", None,
     "A southern arm of Laniakea, running through the constellations Pavo, Indus and Telescopium."),
    ("Coma Cluster", "Cluster", 20000000, 320000000, "0.023", "over 1,000 galaxies", "Coma Supercluster", 1785,
     "Where dark matter was found. Zwicky weighed it in 1933 from how fast its galaxies move and concluded that most of its mass is invisible — a result ignored for forty years."),
    ("Coma Supercluster", "Supercluster", 300000000, 300000000, "0.023", "2 rich clusters", "CfA2 Great Wall", None,
     "Coma and Leo together, sitting at the densest point of the first great wall ever mapped."),
    ("Perseus–Pisces Supercluster", "Supercluster", 300000000, 250000000, "0.017", "a chain of clusters", "Pisces–Cetus Supercluster Complex", 1985,
     "One of the most striking filaments in the nearby universe: a chain of clusters strung out over 300 million light-years, nearly end-on to us."),
    ("Shapley Supercluster", "Supercluster", 650000000, 650000000, "0.048", "~8,600 galaxies", "—", 1930,
     "The largest concentration of mass in the nearby universe, and the direction Laniakea itself appears to be heading. Harlow Shapley found the over-density in the 1930s; its full extent took until the 1980s."),
    ("Hercules Superclusters", "Supercluster", 300000000, 500000000, "0.036", "several clusters", "CfA2 Great Wall", None,
     "A pair of superclusters embedded in the CfA2 Great Wall, at the far end from Coma."),
    ("Sculptor Supercluster", "Supercluster", 300000000, 500000000, None, "clusters and groups", "Pisces–Cetus Supercluster Complex", None,
     "A long southern filament, part of the complex that Laniakea itself belongs to."),
    ("Horologium Supercluster", "Supercluster", 550000000, 700000000, "0.063", "~5,000 galaxies", "—", None,
     "One of the largest superclusters known, in the far southern sky."),
    ("Corona Borealis Supercluster", "Supercluster", 100000000, 950000000, "0.07", "several rich clusters", "—", None,
     "Unusually compact and massive for its size, and probably still collapsing under its own gravity rather than expanding with everything else."),

    ("CfA2 Great Wall", "Filament", 500000000, 200000000, "0.02", "thousands of galaxies", "—", 1989,
     "The first structure found that was too big for anyone's model: Geller and Huchra's redshift survey turned up a sheet of galaxies 500 million light-years long and only 15 million thick. It ended the assumption that the universe was smooth on any scale you cared to look at."),
    ("Sloan Great Wall", "Filament", 1370000000, 1000000000, "0.08", "a wall of superclusters", "—", 2003,
     "Found in Sloan Digital Sky Survey data and nearly three times the length of the CfA2 wall — big enough that whether it counts as one structure or several is a question about definitions rather than observation."),
    ("South Pole Wall", "Filament", 1400000000, 500000000, None, "a wall of galaxies", "—", 2020,
     "Hidden behind the Milky Way in the southern sky and only mapped in 2020, by inferring where mass must be from how nearby galaxies move rather than by seeing it."),
    ("Quipu Superstructure", "Filament", 1300000000, 1900000000, "0.03–0.06", "~200 clusters, 2 × 10¹⁷ solar masses", "—", 2025,
     "Reported in 2025 as the most massive structure yet identified, named for the Andean knotted cords it resembles. As with every claimed 'largest structure', how much of it is one object depends on where you draw the line."),
    ("Hercules–Corona Borealis Great Wall", "Filament", 10000000000, 9800000000, "1.6–2.1", "a concentration of gamma-ray bursts", "—", 2013,
     "Claimed from a clustering of gamma-ray bursts and, at 10 billion light-years, far larger than the scale at which the universe is supposed to be uniform. Whether it is real or an artefact of how bursts are found is genuinely unsettled."),
    ("Boötes Void", "Void", 330000000, 700000000, "0.05", "about 60 galaxies where thousands were expected", "—", 1981,
     "The Great Nothing: a hole 330 million light-years across with almost nothing in it. As Greg Aldering put it, if the Milky Way had been in its centre we would not have known there were other galaxies until the 1960s."),
    ("Giant Void (Canes Venatici)", "Void", 1300000000, 1500000000, "0.116", "very few galaxies", "—", 1988,
     "One of the largest confirmed voids, and a reminder that most of the universe's volume is empty even though most of its mass is not."),
    ("Eridanus Supervoid", "Void", 1800000000, 3000000000, None, "an underdensity", "—", 2007,
     "Proposed to explain the CMB Cold Spot — an unusually cool patch of the microwave background — as light losing energy crossing a vast emptiness. The explanation is still argued over."),
    ("KBC Void (Local Hole)", "Void", 2000000000, None, None, "a 20 % underdensity", "—", 2013,
     "The claim that the Milky Way sits near the centre of a region emptier than average by about a fifth, which if true would bias every local measurement of the expansion rate — one proposed way out of the Hubble tension."),

    ("Pisces–Cetus Supercluster Complex", "Filament", 1000000000, None, None, "~60 galaxy clusters, 10¹⁸ solar masses", "The cosmic web", 1987,
     "The galaxy filament Laniakea itself is one strand of, about a billion light-years long — the largest structure we can say we are part of."),
    ("The cosmic web", "Cosmological", 1000000000, None, None, "all structure", "Observable universe", 1996,
     "The pattern everything above belongs to: matter drawn by gravity into sheets, then filaments, then knots at the intersections, with voids opening between them. Simulations grow it from the microwave background's faintest ripples and get the observed pattern back."),
    ("Homogeneity scale", "Cosmological", 1200000000, None, None, "the scale at which lumpiness stops", "Observable universe", None,
     "Above about 250–370 megaparsecs the universe stops looking clumpy and starts looking the same everywhere — the assumption cosmology is built on, and a measurement rather than an article of faith."),
    ("Hubble sphere", "Cosmological", 28800000000, None, "1", "the recession-speed-of-light radius", "Observable universe", None,
     "The distance at which space is receding from us at the speed of light — 14.4 billion light-years out. Counter-intuitively we can still see things beyond it, because the sphere itself grows."),
    ("Surface of last scattering", "Cosmological", 91200000000, 45600000000, "1100", "the oldest light", "Observable universe", 1965,
     "The shell we see the microwave background coming from: where the universe became transparent 380,000 years in. It is not an object, it is a time we are looking back at — and it is now 45.6 billion light-years away because space has stretched since."),
    ("Observable universe", "Cosmological", 93000000000, None, "∞ at the horizon", "~2 trillion galaxies", "—", None,
     "Everything whose light has had time to reach us: a sphere 46.5 billion light-years in radius, larger than the 13.8 billion years of travel would suggest because it expanded on the way. What lies beyond is not merely unseen but unseeable, and there is no reason to think it ends."),
]

NEW_PROPS = {
    "Kind": {"select": {"options": [{"name": k} for k in KINDS]}},
    "Size (ly)": {"number": {"format": "number"}},
    "Distance (ly)": {"number": {"format": "number"}},
    "Redshift": {"rich_text": {}},
    "Population": {"rich_text": {}},
    "Within": {"rich_text": {}},
    "Recognised": {"number": {"format": "number"}},
    "Notes": {"rich_text": {}},
}


def find_ds(title):
    d = call("POST", "https://api.notion.com/v1/search",
             {"query": title, "filter": {"property": "object", "value": "data_source"}, "page_size": 50})
    for r in d.get("results", []):
        if "".join(x.get("plain_text", "") for x in r.get("title", [])).strip() == title:
            return r["id"]
    return None


def main():
    ds = find_ds(TITLE)
    if not ds:
        db = call("POST", "https://api.notion.com/v1/databases", {
            "parent": {"type": "page_id", "page_id": PARENT_PAGE},
            "title": [{"type": "text", "text": {"content": TITLE}}],
            "initial_data_source": {"properties": {"Name": {"title": {}}, **NEW_PROPS}},
        })
        ds = db["data_sources"][0]["id"]
        print("created", TITLE, ds)
    else:
        print(TITLE, "exists:", ds)
    schema = ensure_props(ds, NEW_PROPS, "cosmic structures")
    ensure_select_options(ds, "Kind", KINDS, "cosmic structures")
    sync_rows(ds, schema,
              [{"Name": n, "Kind": k, "Size (ly)": sz, "Distance (ly)": di, "Redshift": z,
                "Population": pop, "Within": within, "Recognised": yr, "Notes": notes}
               for n, k, sz, di, z, pop, within, yr, notes in STRUCTURES],
              "cosmic structures")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
