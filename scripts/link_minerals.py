"""Cross-link equations to the minerals that famously embody them.

Adds a "Minerals" dual-property relation from the Equations [DB] to the Minerals
[DB] (Notion mirrors it as an "Equations" backlink on each linked mineral page),
then sets each equation's mineral list from the curated graph below — union with
anything already set in Notion, so hand-added links survive.

Only minerals actually present in the Notion database are used (the DB is a
subset of the IMA list — no diamond, pyrite, or galena, for instance).

Run on the VPS:  python3 scripts/link_minerals.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"   # Equations [DB] data source
EQ_DB = "300fc8ac-ca04-429d-a732-406181d9f4b9"   # Equations [DB] database
MIN_DS = "a2db78db-efb7-4952-b8bc-e4ab98d42264"  # Minerals [DB] data source
MIN_DB = "99fb5f7e-d7f2-4bfb-bd7a-979465bd87e2"  # Minerals [DB] database
PROP = "Minerals"


def token() -> str:
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    for p in (ROOT / ".env", Path("/srv/kosmos/.env")):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("NOTION_TOKEN="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("NOTION_TOKEN not set")


H = {"Authorization": f"Bearer {token()}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}


def call(method, url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=H, method=method)
    return json.load(urllib.request.urlopen(req))


def query_all(ds):
    out, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        d = call("POST", f"https://api.notion.com/v1/data_sources/{ds}/query", body)
        out += d["results"]
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]
    return out


# --------------------------------------------------------------------------
# equation name -> mineral names it concerns (all present in the Minerals DB)
# --------------------------------------------------------------------------
LINKS = {
    # crystallography & diffraction
    "Bragg's Law": ["Halite", "Sylvite", "Calcite", "Fluorite", "Quartz", "Diamond", "Pyrite"],
    "Diffraction Grating Equation": ["Calcite"],
    "Snell's Law": ["Calcite", "Fluorite", "Quartz", "Cryolite"],
    "Bloch's Theorem": ["Quartz", "Halite"],
    # hardness, stiffness, fracture
    "Griffith Fracture Criterion": ["Quartz", "Calcite", "Halite", "Diamond"],
    "Rutherford Scattering": ["Gold"],
    "Coulomb's Law": ["Gold", "Halite"],
    "Young's Modulus": ["Corundum", "Quartz", "Talc", "Diamond"],
    "Hooke's Law": ["Quartz", "Muscovite", "Diamond"],
    "Cauchy's Stress Theorem": ["Olivine", "Quartz"],
    # seismology & the mantle
    "Seismic Wave Speeds": ["Olivine", "Forsterite", "Bridgmanite", "Ringwoodite", "Wadsleyite", "Periclase"],
    "Elastic Wave Equation": ["Olivine", "Bridgmanite"],
    "Heat Equation": ["Olivine", "Bridgmanite"],
    # magnetism, MHD, geodynamo
    "MHD Induction Equation": ["Magnetite"],
    "Magnetic Reynolds Number": ["Magnetite", "Hematite"],
    "Gauss's Law for Magnetism": ["Magnetite"],
    "Faraday's Law of Induction": ["Magnetite"],
    "Alfvén Velocity": ["Magnetite"],
    # thermodynamics & phase stability
    "Gibbs Free Energy": ["Calcite", "Aragonite", "Kyanite", "Andalusite", "Sillimanite"],
    "Van 't Hoff Equation": ["Calcite", "Aragonite"],
    "Second Law of Thermodynamics": ["Gypsum", "Anhydrite"],
    "Third Law of Thermodynamics": ["Corundum"],
    "Boltzmann Entropy": ["Feldspar", "Orthoclase", "Albite"],
    "Partition Function": ["Quartz", "Cristobalite", "Tridymite"],
    "Nernst Equation": ["Halite", "Sylvite"],
    "Debye Length": ["Halite", "Montmorillonite"],
    # radioactivity & dating
    "Radioactive Decay Law": ["Zircon", "Monazite", "Autunite", "Carnotite", "Torbernite"],
    "Half-Life": ["Zircon", "Monazite", "Muscovite", "Biotite"],
    "Seebeck Effect": ["Magnetite"],
    # optics of gems and glass
    "Kirchhoff's Law of Thermal Radiation": ["Corundum"],
    "Einstein A and B Coefficients": ["Corundum"],
    "Laser Rate Equations": ["Corundum"],           # ruby is chromium-doped corundum
    "Rydberg Formula": ["Corundum"],
    "Fermi–Dirac Distribution": ["Cassiterite", "Cuprite", "Galena", "Diamond", "Pyrite"],
    "Bloch's Theorem": ["Quartz", "Halite", "Diamond", "Galena"],
    "Drude Conductivity": ["Nickel", "Magnetite", "Gold"],
    "Plasma Frequency": ["Nickel", "Gold"],
    "Ohm's Law": ["Nickel", "Galena", "Gold"],
    "Snell's Law": ["Calcite", "Fluorite", "Quartz", "Cryolite", "Diamond"],
    # pressure & high-pressure phases
    "Ideal Gas Law": ["Halite"],
    "Van der Waals Equation": ["Talc"],
    "Boyle's Law": ["Stishovite", "Coesite"],
    "Kepler's Third Law": ["Olivine"],               # chondritic meteorites; olivine as the solar system's stone
    "Chandrasekhar Limit": ["Olivine", "Nickel"],
    "Stefan–Boltzmann Law": ["Olivine"],             # peridot in pallasites forged in early bodies
    # chemistry
    "Law of Mass Action": ["Calcite", "Malachite", "Azurite"],
    "Arrhenius Equation": ["Kaolinite", "Calcite"],
    "Reaction Isotherm": ["Calcite", "Gypsum"],
    "Michaelis–Menten Equation": ["Calcite"],        # biomineralization
    "Goldman–Hodgkin–Katz Equation": ["Halite", "Sylvite"],
    # crystal chemistry
    "Fine-Structure Constant": ["Corundum"],
    "Schrödinger Equation": ["Corundum", "Spinel"],
    "Bohr Model Energy Levels": ["Cuprite", "Malachite", "Azurite"],
    "Planck's Law": ["Corundum"],
    "Wien's Displacement Law": ["Corundum"],
    # borates & lithium — pegmatite chemistry
    "Avogadro's Law": ["Borax"],
    "Graham's Law of Effusion": ["Cryolite"],
    "Lawson Criterion": ["Spodumene", "Lepidolite", "Petalite", "Amblygonite"],  # lithium for fusion
    "Specific Impulse": ["Spodumene"],
}


def main():
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{EQ_DS}")
    if PROP not in ds["properties"]:
        created = False
        for endpoint, body in [
            (f"https://api.notion.com/v1/data_sources/{EQ_DS}",
             {"properties": {PROP: {"relation": {"data_source_id": MIN_DS, "type": "dual_property",
                                                 "dual_property": {"synced_property_name": "Equations"}}}}}),
            (f"https://api.notion.com/v1/databases/{EQ_DB}",
             {"properties": {PROP: {"relation": {"database_id": MIN_DB, "type": "dual_property",
                                                 "dual_property": {"synced_property_name": "Equations"}}}}}),
            (f"https://api.notion.com/v1/data_sources/{EQ_DS}",
             {"properties": {PROP: {"relation": {"data_source_id": MIN_DS, "type": "single_property",
                                                 "single_property": {}}}}}),
        ]:
            try:
                call("PATCH", endpoint, body)
                created = True
                print("created relation via", endpoint.split("/v1/")[1].split("/")[0],
                      "|", body["properties"][PROP]["relation"]["type"])
                break
            except urllib.error.HTTPError as e:
                print("  attempt failed:", e.code, e.read().decode()[:160])
        if not created:
            sys.exit("could not create the Minerals relation")
    else:
        print("Minerals relation already exists")

    min_by_name = {}
    for r in query_all(MIN_DS):
        name = "".join(x["plain_text"] for x in r["properties"]["Name"]["title"]).strip()
        if name and name not in min_by_name:
            min_by_name[name] = r["id"]
    eq_by_name, current = {}, {}
    for r in query_all(EQ_DS):
        name = "".join(x["plain_text"] for x in r["properties"]["Name"]["title"])
        eq_by_name[name] = r["id"]
        rel = r["properties"].get(PROP, {}).get("relation", []) or []
        current[r["id"]] = {x["id"] for x in rel}

    bad_eq = sorted(n for n in LINKS if n not in eq_by_name)
    bad_min = sorted({m for v in LINKS.values() for m in v if m not in min_by_name})
    if bad_eq or bad_min:
        sys.exit(f"unknown equations {bad_eq} / unknown minerals {bad_min}")

    changed, edges = 0, 0
    for name, mins in LINKS.items():
        pid = eq_by_name[name]
        want = current[pid] | {min_by_name[m] for m in mins}
        edges += len(want)
        if want != current[pid]:
            call("PATCH", f"https://api.notion.com/v1/pages/{pid}",
                 {"properties": {PROP: {"relation": [{"id": x} for x in sorted(want)]}}})
            changed += 1
    touched = {m for v in LINKS.values() for m in v}
    print(f"updated {changed} equations · {edges} equation→mineral links · "
          f"{len(LINKS)} equations · {len(touched)} distinct minerals")


if __name__ == "__main__":
    main()
