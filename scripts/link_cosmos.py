"""Cross-link equations to the cosmos databases: spectral types, celestial
objects, instruments, and theories.

Adds four dual-property relations on the Equations [DB] (each target page gets
an "Equations" backlink), then sets each equation's lists from the curated
graphs below — union with anything already set in Notion.

Run on the VPS:  python3 scripts/link_cosmos.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from notion import token, call, query_all  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"
EQ_DB = "300fc8ac-ca04-429d-a732-406181d9f4b9"

# prop name -> (data source id, database id, title property, name->[equations] graph)
TARGETS = {
    "Spectral Types": {
        "ds": "6128c15c-25dd-47fb-bf00-ce737ca1d3e6", "db": "6d59bfde-5054-48f2-9d82-bd1ae6b28d8d",
        "title": "Name",
        # Saha explains the whole sequence — it links to every type
        "links": {
            "O-type Stars": ["Wien's Displacement Law", "Stefan–Boltzmann Law", "Planck's Law", "Chandrasekhar Limit", "Schwarzschild Radius", "Saha Ionization Equation"],
            "B-type Stars": ["Wien's Displacement Law", "Stefan–Boltzmann Law", "Rydberg Formula", "Saha Ionization Equation"],
            "A-type Stars": ["Rydberg Formula", "Bohr Model Energy Levels", "Wien's Displacement Law", "Chandrasekhar Limit", "Saha Ionization Equation"],
            "F-type Stars": ["Stefan–Boltzmann Law", "Wien's Displacement Law", "Saha Ionization Equation"],
            "G-type Stars": ["Stefan–Boltzmann Law", "Wien's Displacement Law", "Planck's Law", "Lawson Criterion", "Mass–Energy Equivalence", "Kirchhoff's Law of Thermal Radiation", "Saha Ionization Equation"],
            "K-type Stars": ["Wien's Displacement Law", "Stefan–Boltzmann Law", "Saha Ionization Equation"],
            "M-type Stars": ["Wien's Displacement Law", "Planck's Law", "Radioactive Decay Law", "Saha Ionization Equation"],
            "L-type Stars (L Dwarfs)": ["Planck's Law", "Wien's Displacement Law", "Fermi–Dirac Distribution", "Saha Ionization Equation"],
            "T-type Stars (T Dwarfs)": ["Planck's Law", "Wien's Displacement Law", "Boltzmann Distribution", "Saha Ionization Equation"],
            "Y-type Stars (Y Dwarfs)": ["Planck's Law", "Wien's Displacement Law", "Ideal Gas Law", "Saha Ionization Equation"],
        },
    },
    "Celestial Objects": {
        "ds": "f279dffc-9049-468d-8a5a-dbcdcf36f940", "db": "283ed7d8-efe7-48c3-bd46-bc7d79b4537e",
        "title": "Object ID",
        "links": {
            "Sun": ["Stefan–Boltzmann Law", "Wien's Displacement Law", "Planck's Law", "Lawson Criterion",
                    "Mass–Energy Equivalence", "Kepler's Third Law", "Law of Universal Gravitation",
                    "Escape Velocity", "Schwarzschild Radius", "Chandrasekhar Limit", "Alfvén Velocity",
                    "MHD Induction Equation", "Magnetic Reynolds Number", "Kirchhoff's Law of Thermal Radiation",
                    "Gravitational Time Dilation", "Hubble's Law", "Rydberg Formula", "Doppler Effect"],
        },
    },
    "Instruments": {
        "ds": "e72fed70-784c-42d2-be1a-3c833ac7fc63", "db": "22e7972d-5feb-4d58-82ee-918a2fcff08e",
        "title": "Name",
        "links": {
            "Planck Satellite": ["Planck's Law", "Wien's Displacement Law", "First Friedmann Equation", "Hubble's Law",
                                 "Second Friedmann Equation", "Cosmological Redshift", "Critical Density", "FLRW Metric",
                                 "Saha Ionization Equation", "Linear Perturbation Growth"],
            "Chandra X-ray Observatory": ["Bragg's Law", "Schwarzschild Radius", "Chandrasekhar Limit", "Planck–Einstein Relation"],
            "Hubble Space Telescope (HST)": ["Hubble's Law", "Doppler Effect", "Gaussian Beam Divergence",
                                             "Chandrasekhar Limit", "Cosmological Redshift"],
            "James Webb Space Telescope (JWST)": ["Wien's Displacement Law", "Planck's Law", "Hubble's Law",
                                                  "Diffraction Grating Equation", "Cosmological Redshift"],
            "Very Large Telescope (VLT)": ["Diffraction Grating Equation", "Snell's Law", "Schwarzschild Radius", "Gravitational Time Dilation"],
            "Keck Observatory": ["Diffraction Grating Equation", "Doppler Effect", "Kepler's Third Law", "Schwarzschild Radius"],
            "Atacama Large Millimeter/submillimeter Array (ALMA)": ["Planck's Law", "Fourier Transform", "Doppler Effect", "Kepler's First Law"],
            "Large Synoptic Survey Telescope (LSST)": ["Hubble's Law", "Chandrasekhar Limit", "Bayes' Theorem",
                                                       "Normal Distribution", "Kepler's Third Law",
                                                       "Linear Perturbation Growth"],
        },
    },
    "Theories": {
        "ds": "215048ed-e6a6-4b9a-858b-73e8c801629e", "db": "9485e2d1-1ceb-4754-90c2-6990ebf72ed0",
        "title": "Name",
        "links": {
            "Quantum Gravity": ["Einstein–Hilbert Action", "Einstein Field Equations", "Feynman Path Integral",
                                "Schwarzschild Radius", "Heisenberg Uncertainty Principle", "Standard Model Lagrangian",
                                "FLRW Metric"],
            "Unification Theories": ["Standard Model Lagrangian", "Higgs Potential", "Ampère–Maxwell Law",
                                     "Fine-Structure Constant", "Noether's Theorem", "Dirac Equation"],
        },
    },
}


H = {"Authorization": f"Bearer {token()}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}


def title_of(page, prop):
    p = page["properties"].get(prop, {})
    key = p.get("type")
    return "".join(x["plain_text"] for x in (p.get(key) or [])).strip() if key in ("title", "rich_text") else None


def ensure_relation(prop, target):
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{EQ_DS}")
    if prop in ds["properties"]:
        print(f"{prop}: relation exists")
        return
    for endpoint, body in [
        (f"https://api.notion.com/v1/data_sources/{EQ_DS}",
         {"properties": {prop: {"relation": {"data_source_id": target["ds"], "type": "dual_property",
                                             "dual_property": {"synced_property_name": "Equations"}}}}}),
        (f"https://api.notion.com/v1/databases/{EQ_DB}",
         {"properties": {prop: {"relation": {"database_id": target["db"], "type": "dual_property",
                                             "dual_property": {"synced_property_name": "Equations"}}}}}),
        (f"https://api.notion.com/v1/data_sources/{EQ_DS}",
         {"properties": {prop: {"relation": {"data_source_id": target["ds"], "type": "single_property",
                                             "single_property": {}}}}}),
    ]:
        try:
            call("PATCH", endpoint, body)
            print(f"{prop}: created ({body['properties'][prop]['relation']['type']})")
            return
        except urllib.error.HTTPError as e:
            print(f"  {prop}: attempt failed {e.code} {e.read().decode()[:120]}")
    sys.exit(f"could not create relation {prop}")


def main():
    for prop, t in TARGETS.items():
        ensure_relation(prop, t)

    eq_by_name = {}
    eq_pages = query_all(EQ_DS)
    for r in eq_pages:
        eq_by_name[title_of(r, "Name")] = r
    for prop, t in TARGETS.items():
        target_by_name = {}
        for r in query_all(t["ds"]):
            nm = title_of(r, t["title"])
            if nm:
                target_by_name[nm] = r["id"]
        # invert graph: equation -> set(target ids)
        want = {}
        bad_t = sorted(n for n in t["links"] if n not in target_by_name)
        bad_e = sorted({e for v in t["links"].values() for e in v if e not in eq_by_name})
        if bad_t or bad_e:
            sys.exit(f"{prop}: unknown targets {bad_t} / unknown equations {bad_e}")
        for tname, eqs in t["links"].items():
            for e in eqs:
                want.setdefault(e, set()).add(target_by_name[tname])
        changed, edges = 0, 0
        for ename, tids in want.items():
            page = eq_by_name[ename]
            cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
            new = cur | tids
            edges += len(new)
            if new != cur:
                call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
                     {"properties": {prop: {"relation": [{"id": x} for x in sorted(new)]}}})
                changed += 1
        print(f"{prop}: updated {changed} equations · {edges} links · {len(t['links'])} targets")


if __name__ == "__main__":
    main()
