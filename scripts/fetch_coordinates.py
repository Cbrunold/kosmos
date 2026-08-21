"""Resolve sky coordinates for the catalogued objects, from CDS Sesame.

The Coordinates column on Celestial Objects [DB] was empty for all 45 rows,
which is why nothing on the site could be placed in three dimensions -- a
distance alone puts an object on a sphere, not at a point.

Typing 45 right ascensions from memory is exactly the kind of thing that
looks fine and is quietly wrong, so this asks the name resolver at Strasbourg
instead. Sesame queries SIMBAD, then NED, then VizieR, and returns the ICRS
position of whatever the name resolves to. What it cannot resolve is reported,
not guessed.

Writes data/astro/coordinates.json:  {site name: {ra, dec, resolver, id}}
    ra, dec   degrees, ICRS
    resolver  which service answered (S = SIMBAD, N = NED, V = VizieR)

Run:  python3 scripts/fetch_coordinates.py
Then: python3 scripts/seed_coordinates.py     (writes them into Notion)
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "astro" / "coordinates.json"

# site name -> names to try, in order. The first that resolves wins.
TARGETS = {
    "Andromeda (M31)": ["M 31", "NGC 224"],
    "Antlia Dwarf": ["Antlia Dwarf", "PGC 29194"],
    "Aquarius Dwarf (DDO 210)": ["DDO 210"],
    "Bootes I": ["Bootes I", "Bootes dSph"],
    "Canes Venatici I": ["Canes Venatici I dSph", "Canes Venatici I"],
    "Canis Major Dwarf": ["Canis Major Dwarf"],
    "Carina Dwarf": ["Carina dSph"],
    "Cetus Dwarf": ["Cetus dSph"],
    "Crater 2": ["Crater II"],
    "Draco Dwarf": ["Draco dSph"],
    "ESO 294-010": ["ESO 294-10"],
    "Fornax Dwarf": ["Fornax dSph"],
    "IC 10": ["IC 10"],
    "IC 1613": ["IC 1613"],
    "IC 4662": ["IC 4662"],
    "IC 5152": ["IC 5152"],
    "KKR 25": ["KKR 25"],
    "LGS 3": ["LGS 3", "Pisces Dwarf"],
    "Large Magellanic Cloud": ["LMC"],
    "Leo A": ["Leo A"],
    "Leo I": ["Leo I dSph", "Leo I"],
    "Leo II": ["Leo II dSph", "Leo II"],
    "Leo P": ["Leo P"],
    "Leo T": ["Leo T"],
    "M110 (NGC 205)": ["NGC 205"],
    "M32": ["M 32", "NGC 221"],
    "NGC 147": ["NGC 147"],
    "NGC 185": ["NGC 185"],
    "NGC 3109": ["NGC 3109"],
    "NGC 6822 (Barnard's Galaxy)": ["NGC 6822"],
    "Pegasus Dwarf Irregular": ["DDO 216"],
    "Phoenix Dwarf": ["Phoenix Dwarf Galaxy", "Phoenix Dwarf"],
    "Reticulum II": ["Reticulum II"],
    "Sagittarius Dwarf Irregular (SagDIG)": ["SagDIG"],
    "Sagittarius Dwarf Spheroidal": ["Sgr dSph"],
    "Sculptor Dwarf": ["Sculptor dSph"],
    "Segue 1": ["Segue 1"],
    "Sextans Dwarf": ["Sextans dSph"],
    "Small Magellanic Cloud": ["SMC"],
    "Triangulum (M33)": ["M 33", "NGC 598"],
    "Tucana Dwarf": ["Tucana Dwarf"],
    "Ursa Minor Dwarf": ["UMi dSph", "Ursa Minor dSph"],
    "WLM (Wolf–Lundmark–Melotte)": ["DDO 221", "UGCA 444"],   # bare "WLM" resolves to nothing
    # the two we are inside or on: a direction is meaningless, and the seed
    # script writes them as the origin rather than asking Sesame
}

# The large-scale structures on /scales. Clusters have catalogue entries and
# resolve cleanly; superclusters, walls and voids mostly do not, and the ones
# that fail stay unresolved -- the map draws those as shells at the right
# radius in no particular direction, which is exactly what is known about them.
STRUCTURES = {
    "Virgo Cluster": ["Virgo Cluster"],
    "Local Supercluster (Virgo)": ["Virgo Cluster"],          # the supercluster is named for its core
    "Fornax Cluster": ["Fornax Cluster"],
    "Coma Cluster": ["Coma Cluster", "ACO 1656"],
    "Coma Supercluster": ["Coma Supercluster", "Coma Cluster"],
    "Centaurus Cluster": ["Centaurus Cluster"],
    "Norma Cluster (Abell 3627)": ["ACO 3627"],
    "Great Attractor": ["Great Attractor"],
    "Shapley Supercluster": ["Shapley Supercluster"],
    "Hydra–Centaurus Supercluster": ["Hydra-Centaurus Supercluster", "Hydra Cluster"],
    "Perseus–Pisces Supercluster": ["Perseus-Pisces Supercluster", "Perseus Cluster"],
    "Hercules Superclusters": ["Hercules Supercluster"],
    "Corona Borealis Supercluster": ["Corona Borealis Supercluster"],
    "Horologium Supercluster": ["Horologium Supercluster", "Horologium-Reticulum Supercluster"],
    "Sculptor Supercluster": ["Sculptor Supercluster"],
    "Boötes Void": ["Bootes Void"],
    "Sloan Great Wall": ["Sloan Great Wall"],
    "CfA2 Great Wall": ["CfA2 Great Wall", "Great Wall"],
    "Pisces–Cetus Supercluster Complex": ["Pisces-Cetus Supercluster"],
    "Ursa Major Supercluster": ["Ursa Major Supercluster"],
    "Leo Supercluster": ["Leo Supercluster"],
    "Columba Supercluster": ["Columba Supercluster"],
}

SESAME = "https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV?"


def resolve(name: str):
    """(ra, dec, resolver, resolved-id) in ICRS degrees, or None."""
    try:
        txt = urllib.request.urlopen(SESAME + urllib.parse.quote(name), timeout=30).read().decode(errors="replace")
    except Exception as e:                       # noqa: BLE001 -- report, do not crash the run
        print(f"    {name}: {type(e).__name__}", file=sys.stderr)
        return None
    # Sesame returns one <Resolver> block per service it tried; take the first
    # that actually carries a position rather than assuming SIMBAD answered.
    for block in re.findall(r"<Resolver[^>]*>.*?</Resolver>", txt, re.S):
        m = re.search(r"<jradeg>\s*([-+\d.eE]+)\s*</jradeg>\s*<jdedeg>\s*([-+\d.eE]+)\s*</jdedeg>", block, re.S)
        if not m:
            continue
        who = re.search(r'name="([^"=]+)', block)
        oid = re.search(r"<oname>([^<]+)</oname>", block) or re.search(r"<otype>([^<]+)</otype>", block)
        return float(m.group(1)), float(m.group(2)), (who.group(1) if who else "?"), (oid.group(1).strip() if oid else name)
    return None


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out, missing = {}, []
    for site, names in {**TARGETS, **STRUCTURES}.items():
        for n in names:
            got = resolve(n)
            if got:
                ra, dec, who, oid = got
                out[site] = {"ra": round(ra, 5), "dec": round(dec, 5), "resolver": who, "id": oid, "queried": n}
                print(f"  {site[:38]:40} {n:22} RA {ra:9.4f}  Dec {dec:+9.4f}  [{who}]")
                break
            time.sleep(0.2)
        else:
            missing.append(site)
            print(f"  {site[:38]:40} UNRESOLVED")
        time.sleep(0.2)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"\nresolved {len(out)} of {len(TARGETS) + len(STRUCTURES)}; wrote {OUT.relative_to(ROOT)}")
    if missing:
        print("unresolved (left blank rather than guessed):", missing)
