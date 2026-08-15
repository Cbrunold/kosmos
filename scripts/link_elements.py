"""Cross-link equations to the elements they concern.

Adds an "Elements" relation on the Equations [DB] pointing at the All Periodical
Elements database (Notion mirrors it onto each element page as a backlink), then
sets each equation's element list from the curated graph below — union with
anything already set in Notion, so hand-added links survive.

Run on the VPS:  python3 scripts/link_elements.py
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
EL_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"   # All Periodical Elements data source
EL_DB = "7e97fd4c-8266-46b6-80f9-cb4494817914"   # All Periodical Elements database
PROP = "Elements"


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
# equation name -> element symbols it concerns
# --------------------------------------------------------------------------
LINKS = {
    # hydrogen and the atom
    "Rydberg Formula": ["H"],
    "Bohr Model Energy Levels": ["H"],
    "Schrödinger Equation": ["H", "He"],
    "Fine-Structure Constant": ["H"],
    "Rutherford Scattering": ["Au", "He"],
    "Planck–Einstein Relation": ["H"],
    "De Broglie Wavelength": ["Ni"],          # Davisson–Germer, nickel crystal
    "Dirac Equation": ["H"],
    # nuclear
    "Radioactive Decay Law": ["U", "Ra", "Th", "Po", "Rn"],
    "Half-Life": ["C", "U", "K", "Rb", "Pu"],
    "Mass–energy equivalence": ["U", "H", "He"],
    "Lawson Criterion": ["H", "He", "Li"],
    "Seebeck Effect": ["Bi", "Te", "Sb"],
    "Peltier Effect": ["Bi", "Te"],
    "Thermoelectric Figure of Merit": ["Bi", "Te", "Pb", "Pu"],
    # gases
    "Ideal Gas Law": ["He", "Ne", "Ar", "N", "O"],
    "Boyle's Law": ["N", "O"],
    "Charles's Law": ["H", "N", "O"],
    "Gay-Lussac's Law": ["N", "O"],
    "Avogadro's Law": ["H", "N", "O", "Cl"],
    "Dalton's Law of Partial Pressures": ["N", "O", "Ar"],
    "Graham's Law of Effusion": ["H", "He", "U"],
    "Van der Waals Equation": ["He", "N", "C", "O"],
    "Newton–Laplace Speed of Sound": ["N", "O", "He"],
    "Equipartition Theorem": ["He", "Ar", "N", "O"],
    # condensed matter / circuits / superconductivity
    "Drude Conductivity": ["Cu", "Ag", "Au", "Al"],
    "Ohm's Law": ["Cu"],
    "Joule Heating": ["W", "Ni", "Cr"],
    "Bloch's Theorem": ["Cu", "Si"],
    "Fermi–Dirac Distribution": ["Si", "Ge", "Cu"],
    "London Equations": ["Hg", "Pb", "Nb"],
    "BCS Energy Gap": ["Hg", "Pb", "Nb", "Al"],
    "Josephson Effect": ["Nb", "Al"],
    "Plasma Frequency": ["Ag", "Au", "Cu"],
    # materials / geo
    "Young's Modulus": ["Fe", "Al", "C", "W"],
    "Griffith Fracture Criterion": ["Si", "O"],
    "Hooke's Law": ["Fe"],
    "Seismic Wave Speeds": ["Fe", "Ni", "Si", "O", "Mg"],
    "Elastic Wave Equation": ["Fe", "Si"],
    "Magnetic Reynolds Number": ["Fe", "Ni"],
    "MHD Induction Equation": ["Fe", "H"],
    # optics / photonics
    "Bragg's Law": ["Na", "Cl", "C", "Cu"],
    "Diffraction Grating Equation": ["Na", "H"],
    "Snell's Law": ["Si", "O"],
    "Einstein A and B Coefficients": ["Ne", "Cr", "Nd"],
    "Laser Rate Equations": ["Cr", "Nd", "He", "Ne"],
    "Gaussian Beam Divergence": ["He", "Ne"],
    # astro / cosmo
    "Stefan–Boltzmann Law": ["H", "He"],
    "Chandrasekhar Limit": ["C", "O", "Ni", "Fe"],
    "Wien's Displacement Law": ["H"],
    "Hubble's Law": ["H", "Ca"],
    "Doppler Effect": ["H", "Ca", "Na"],
    "First Friedmann Equation": ["H", "He"],
    "Kirchhoff's Law of Thermal Radiation": ["Na", "Fe"],
    # chemistry proper
    "Arrhenius Equation": ["H", "O", "N"],
    "Eyring Equation": ["H", "C"],
    "Law of Mass Action": ["H", "N"],
    "Van 't Hoff Equation": ["N", "H", "Fe"],
    "Reaction Isotherm": ["N", "H"],
    "Gibbs Free Energy": ["H", "O", "C"],
    "Nernst Equation": ["K", "Na", "Cl", "Ca", "Zn", "Cu"],
    "Goldman–Hodgkin–Katz Equation": ["K", "Na", "Cl"],
    "Michaelis–Menten Equation": ["C", "H", "O", "N"],
    "Debye Length": ["Na", "Cl", "H"],
    # rocketry / heat
    "Tsiolkovsky Rocket Equation": ["H", "O"],
    "Specific Impulse": ["H", "O", "Xe", "Al"],
    "Fourier's Law of Heat Conduction": ["Cu", "Ag", "C"],
    "Heat Equation": ["Fe", "Cu"],
    "Third Law of Thermodynamics": ["He"],
    "Boltzmann Entropy": ["Ar"],
    # quantum computing
    "Qubit State": ["Nb", "Al", "Ca", "Yb"],
    "Bell State": ["Ca", "Yb"],
    "No-Cloning Theorem": ["Ca"],
    # info theory / mathematics: no elements
}


def main():
    # 1. ensure the relation property exists on the equations DB
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{EQ_DS}")
    if PROP not in ds["properties"]:
        created = False
        for endpoint, body in [
            (f"https://api.notion.com/v1/data_sources/{EQ_DS}",
             {"properties": {PROP: {"relation": {"data_source_id": EL_DS, "type": "dual_property",
                                                 "dual_property": {"synced_property_name": "Equations"}}}}}),
            (f"https://api.notion.com/v1/databases/{EQ_DB}",
             {"properties": {PROP: {"relation": {"database_id": EL_DB, "type": "dual_property",
                                                 "dual_property": {"synced_property_name": "Equations"}}}}}),
            (f"https://api.notion.com/v1/data_sources/{EQ_DS}",
             {"properties": {PROP: {"relation": {"data_source_id": EL_DS, "type": "single_property",
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
            sys.exit("could not create the Elements relation")
    else:
        print("Elements relation already exists")

    # 2. maps
    el_by_sym = {}
    for r in query_all(EL_DS):
        sym = "".join(x["plain_text"] for x in r["properties"]["Notation"]["rich_text"]).strip()
        if sym:
            el_by_sym[sym] = r["id"]
    eq_by_name, current = {}, {}
    for r in query_all(EQ_DS):
        name = "".join(x["plain_text"] for x in r["properties"]["Name"]["title"])
        eq_by_name[name] = r["id"]
        rel = r["properties"].get(PROP, {}).get("relation", []) or []
        current[r["id"]] = {x["id"] for x in rel}

    bad_eq = sorted(n for n in LINKS if n not in eq_by_name)
    bad_sym = sorted({s for v in LINKS.values() for s in v if s not in el_by_sym})
    if bad_eq or bad_sym:
        sys.exit(f"unknown equations {bad_eq} / unknown symbols {bad_sym}")

    # 3. write (union with existing)
    changed, edges = 0, 0
    for name, syms in LINKS.items():
        pid = eq_by_name[name]
        want = current[pid] | {el_by_sym[s] for s in syms}
        edges += len(want)
        if want != current[pid]:
            call("PATCH", f"https://api.notion.com/v1/pages/{pid}",
                 {"properties": {PROP: {"relation": [{"id": x} for x in sorted(want)]}}})
            changed += 1
    touched = {s for v in LINKS.values() for s in v}
    print(f"updated {changed} equations · {edges} equation→element links · "
          f"{len(LINKS)} equations · {len(touched)} distinct elements")


if __name__ == "__main__":
    main()
