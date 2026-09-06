"""Cross-link related equations in the Equations [DB] via a self-relation.

Idempotent: creates the "Related" self-relation property if missing, then sets
each equation's Related list to the curated graph below (union with anything
already set in Notion, so hand-added links survive). Notion mirrors the
relation on both ends automatically.

Cross-field links only — same-field entries already sit together under a chip.
Run on the VPS:  python3 scripts/link_equations.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from notion import token, call  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"   # Equations [DB] data source
DB = "300fc8ac-ca04-429d-a732-406181d9f4b9"   # Equations [DB] database


H = {"Authorization": f"Bearer {token()}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}


# --------------------------------------------------------------------------
# The graph. Each pair is undirected; Notion mirrors it on both pages.
# --------------------------------------------------------------------------
LINKS = [
    # foundations: least action / Euler-Lagrange / Noether -> everything
    ("Principle of Least Action", "Feynman Path Integral"),
    ("Principle of Least Action", "Einstein–Hilbert Action"),
    ("Principle of Least Action", "Standard Model Lagrangian"),
    ("Euler–Lagrange Equation", "Newton's Second Law"),
    ("Euler–Lagrange Equation", "Einstein Field Equations"),
    ("Euler–Lagrange Equation", "Standard Model Lagrangian"),
    ("Noether's Theorem", "First Law of Thermodynamics"),
    ("Noether's Theorem", "Kepler's Second Law"),
    ("Noether's Theorem", "Kirchhoff's Circuit Laws"),
    ("Noether's Theorem", "Standard Model Lagrangian"),
    ("Noether's Theorem", "Continuity Equation"),

    # mechanics <-> celestial mechanics <-> rocketry <-> GR
    ("Newton's Second Law", "Navier–Stokes Equations"),
    ("Newton's Second Law", "Elastic Wave Equation"),
    ("Newton's Second Law", "Hooke's Law"),
    ("Newton's Second Law", "Tsiolkovsky Rocket Equation"),
    ("Law of Universal Gravitation", "Kepler's Third Law"),
    ("Law of Universal Gravitation", "Coulomb's Law"),
    ("Law of Universal Gravitation", "Poisson's Equation"),
    ("Law of Universal Gravitation", "Vis-Viva Equation"),
    ("Law of Universal Gravitation", "Einstein Field Equations"),
    ("Kepler's First Law", "Geodesic Equation"),
    ("Kepler's Third Law", "Hohmann Transfer"),
    ("Vis-Viva Equation", "Hohmann Transfer"),
    ("Escape Velocity", "Schwarzschild Radius"),
    ("Escape Velocity", "Tsiolkovsky Rocket Equation"),

    # relativity chain
    ("Lorentz Transformations", "Mass–Energy Equivalence"),
    ("Lorentz Factor", "Gravitational Time Dilation"),
    ("Mass–Energy Equivalence", "Einstein Field Equations"),
    ("Mass–Energy Equivalence", "Klein–Gordon Equation"),
    ("Mass–Energy Equivalence", "Lawson Criterion"),
    ("Mass–Energy Equivalence", "Radioactive Decay Law"),
    ("Einstein Field Equations", "First Friedmann Equation"),
    ("Einstein Field Equations", "Schwarzschild Radius"),
    ("Einstein Field Equations", "Geodesic Equation"),
    ("Schwarzschild Radius", "Gravitational Time Dilation"),

    # cosmology
    ("First Friedmann Equation", "Hubble's Law"),
    ("Second Friedmann Equation", "Hubble's Law"),
    ("Hubble's Law", "Doppler Effect"),
    ("Hubble's Law", "Chandrasekhar Limit"),
    ("Wien's Displacement Law", "Hubble's Law"),
    # the FLRW spine: geometry -> dynamics -> observables
    ("FLRW Metric", "Einstein Field Equations"),
    ("FLRW Metric", "Geodesic Equation"),
    ("FLRW Metric", "Pythagorean Theorem"),
    ("Cosmological Redshift", "Doppler Effect"),
    ("Cosmological Redshift", "Wien's Displacement Law"),
    ("Cosmological Redshift", "Planck's Law"),
    ("Cosmological Redshift", "Rydberg Formula"),
    ("Cosmological Redshift", "Diffraction Grating Equation"),
    ("Critical Density", "Law of Universal Gravitation"),
    ("Critical Density", "Escape Velocity"),
    # the fluid equation is the first law of thermodynamics for an expanding volume
    ("Cosmological Fluid Equation", "First Law of Thermodynamics"),
    ("Cosmological Fluid Equation", "Continuity Equation"),
    ("Cosmological Fluid Equation", "Noether's Theorem"),
    # structure formation and recombination
    ("Linear Perturbation Growth", "Poisson's Equation"),
    ("Linear Perturbation Growth", "Law of Universal Gravitation"),
    ("Linear Perturbation Growth", "Continuity Equation"),
    ("Linear Perturbation Growth", "Navier–Stokes Equations"),
    ("Linear Perturbation Growth", "Normal Distribution"),
    ("Saha Ionization Equation", "Boltzmann Distribution"),
    ("Saha Ionization Equation", "Partition Function"),
    ("Saha Ionization Equation", "Ideal Gas Law"),
    ("Saha Ionization Equation", "Bohr Model Energy Levels"),
    ("Saha Ionization Equation", "Rydberg Formula"),
    ("Saha Ionization Equation", "Planck's Law"),
    ("Saha Ionization Equation", "Cosmological Redshift"),
    ("Saha Ionization Equation", "Wien's Displacement Law"),
    ("Saha Ionization Equation", "Linear Perturbation Growth"),
    ("Saha Ionization Equation", "Debye Length"),
    ("Saha Ionization Equation", "Plasma Frequency"),
    ("Saha Ionization Equation", "Stefan–Boltzmann Law"),

    ("Cosmological Equation of State", "Ideal Gas Law"),
    ("Cosmological Equation of State", "Van der Waals Equation"),
    ("Cosmological Equation of State", "Planck's Law"),
    ("Cosmological Equation of State", "Stefan–Boltzmann Law"),

    # electromagnetism family
    ("Coulomb's Law", "Electric Field"),
    ("Coulomb's Law", "Gauss's Law"),
    ("Coulomb's Law", "Rutherford Scattering"),
    ("Coulomb's Law", "Fine-Structure Constant"),
    ("Coulomb's Law", "Debye Length"),
    ("Electric Field", "Gauss's Law"),
    ("Poisson's Equation", "Gauss's Law"),
    ("Poisson's Equation", "Heat Equation"),
    ("Faraday's Law of Induction", "MHD Induction Equation"),
    ("Faraday's Law of Induction", "Electric Field"),
    ("Ampère–Maxwell Law", "Wave Equation"),
    ("Ampère–Maxwell Law", "Fine-Structure Constant"),
    ("Gauss's Law for Magnetism", "London Equations"),
    ("Ohm's Law", "Drude Conductivity"),
    ("Ohm's Law", "Fourier's Law of Heat Conduction"),
    ("Ohm's Law", "London Equations"),
    ("Joule Heating", "First Law of Thermodynamics"),
    ("Joule Heating", "Peltier Effect"),
    ("Kirchhoff's Circuit Laws", "Continuity Equation"),

    # thermodynamics <-> stat mech <-> chem thermo <-> heat
    ("Ideal Gas Law", "Boyle's Law"),
    ("Ideal Gas Law", "Charles's Law"),
    ("Ideal Gas Law", "Avogadro's Law"),
    ("Ideal Gas Law", "Van der Waals Equation"),
    ("Ideal Gas Law", "Equipartition Theorem"),
    ("Ideal Gas Law", "Newton–Laplace Speed of Sound"),
    ("First Law of Thermodynamics", "Bernoulli's Equation"),
    ("Second Law of Thermodynamics", "Boltzmann Entropy"),
    ("Second Law of Thermodynamics", "Gibbs Free Energy"),
    ("Second Law of Thermodynamics", "Shannon Entropy"),
    ("Second Law of Thermodynamics", "Heat Equation"),
    ("Third Law of Thermodynamics", "Fermi–Dirac Distribution"),
    ("Third Law of Thermodynamics", "BCS Energy Gap"),
    ("Boltzmann Entropy", "Partition Function"),
    ("Boltzmann Entropy", "Shannon Entropy"),
    ("Boltzmann Distribution", "Arrhenius Equation"),
    ("Boltzmann Distribution", "Fermi–Dirac Distribution"),
    ("Boltzmann Distribution", "Planck's Law"),
    ("Boltzmann Distribution", "Debye Length"),
    ("Boltzmann Distribution", "Einstein A and B Coefficients"),
    ("Partition Function", "Gibbs Free Energy"),
    ("Partition Function", "Feynman Path Integral"),
    ("Equipartition Theorem", "Planck's Law"),
    ("Gibbs Free Energy", "Eyring Equation"),
    ("Gibbs Free Energy", "Nernst Equation"),
    ("Reaction Isotherm", "Nernst Equation"),
    ("Reaction Isotherm", "Law of Mass Action"),
    ("Van 't Hoff Equation", "Arrhenius Equation"),
    ("Heat Equation", "Fourier Transform"),
    ("Heat Equation", "Radioactive Decay Law"),
    ("Heat Equation", "Fourier's Law of Heat Conduction"),
    ("Newton's Law of Cooling", "Radioactive Decay Law"),
    ("Fourier's Law of Heat Conduction", "Thermoelectric Figure of Merit"),
    ("Seebeck Effect", "Radioactive Decay Law"),
    ("Thermoelectric Figure of Merit", "Drude Conductivity"),

    # kinetics
    ("Law of Mass Action", "Michaelis–Menten Equation"),
    ("Law of Mass Action", "Logistic Map"),
    ("Eyring Equation", "Planck–Einstein Relation"),
    ("Arrhenius Equation", "Laser Rate Equations"),

    # quantum chain
    ("Planck's Law", "Planck–Einstein Relation"),
    ("Planck's Law", "Stefan–Boltzmann Law"),
    ("Planck's Law", "Wien's Displacement Law"),
    ("Planck's Law", "Einstein A and B Coefficients"),
    ("Kirchhoff's Law of Thermal Radiation", "Stefan–Boltzmann Law"),
    ("Planck–Einstein Relation", "De Broglie Wavelength"),
    ("Planck–Einstein Relation", "Bohr Model Energy Levels"),
    ("Planck–Einstein Relation", "Rydberg Formula"),
    ("De Broglie Wavelength", "Bragg's Law"),
    ("De Broglie Wavelength", "Bloch's Theorem"),
    ("De Broglie Wavelength", "Bohr Model Energy Levels"),
    ("Schrödinger Equation", "Klein–Gordon Equation"),
    ("Schrödinger Equation", "Dirac Equation"),
    ("Schrödinger Equation", "Bloch's Theorem"),
    ("Schrödinger Equation", "Qubit State"),
    ("Schrödinger Equation", "Bohr Model Energy Levels"),
    ("Schrödinger Equation", "Wave Equation"),
    ("Heisenberg Uncertainty Principle", "Fourier Transform"),
    ("Heisenberg Uncertainty Principle", "Gaussian Beam Divergence"),
    ("Heisenberg Uncertainty Principle", "No-Cloning Theorem"),
    ("Rydberg Formula", "Bohr Model Energy Levels"),
    ("Rydberg Formula", "Diffraction Grating Equation"),
    ("Rutherford Scattering", "Bohr Model Energy Levels"),
    ("Bohr Model Energy Levels", "Fine-Structure Constant"),
    ("Fermi–Dirac Distribution", "Chandrasekhar Limit"),
    ("Fermi–Dirac Distribution", "BCS Energy Gap"),
    ("Bloch's Theorem", "Bragg's Law"),
    ("Drude Conductivity", "Plasma Frequency"),
    ("Drude Conductivity", "London Equations"),

    # QFT / particle
    ("Dirac Equation", "Standard Model Lagrangian"),
    ("Klein–Gordon Equation", "Higgs Potential"),
    ("Klein–Gordon Equation", "Wave Equation"),
    ("Higgs Potential", "Standard Model Lagrangian"),
    ("Feynman Path Integral", "Standard Model Lagrangian"),
    ("Fine-Structure Constant", "Standard Model Lagrangian"),
    ("Josephson Effect", "Qubit State"),
    ("Bell State", "Qubit State"),
    ("Qubit State", "Shannon Entropy"),
    ("No-Cloning Theorem", "Shannon–Hartley Channel Capacity"),

    # waves / optics / acoustics / photonics
    ("Wave Equation", "Elastic Wave Equation"),
    ("Wave Equation", "Newton–Laplace Speed of Sound"),
    ("Wave Equation", "Alfvén Velocity"),
    ("Wave Equation", "Fourier Transform"),
    ("Snell's Law", "Gaussian Beam Divergence"),
    ("Diffraction Grating Equation", "Bragg's Law"),
    ("Diffraction Grating Equation", "Fourier Transform"),
    ("Diffraction Grating Equation", "Gaussian Beam Divergence"),
    ("Doppler Effect", "Lorentz Factor"),
    ("Einstein A and B Coefficients", "Laser Rate Equations"),
    ("Laser Rate Equations", "Gaussian Beam Divergence"),
    ("Plasma Frequency", "Snell's Law"),

    # fluids / MHD / geo / materials
    ("Navier–Stokes Equations", "MHD Induction Equation"),
    ("Navier–Stokes Equations", "Lorenz System"),
    ("Navier–Stokes Equations", "Continuity Equation"),
    ("Continuity Equation", "MHD Induction Equation"),
    ("Bernoulli's Equation", "Vis-Viva Equation"),
    ("Magnetic Reynolds Number", "Alfvén Velocity"),
    ("Alfvén Velocity", "Plasma Frequency"),
    ("Debye Length", "Nernst Equation"),
    ("Lawson Criterion", "Stefan–Boltzmann Law"),
    ("Elastic Wave Equation", "Cauchy's Stress Theorem"),
    ("Seismic Wave Speeds", "Young's Modulus"),
    ("Seismic Wave Speeds", "Cauchy's Stress Theorem"),
    ("Hooke's Law", "Cauchy's Stress Theorem"),
    ("Hooke's Law", "Young's Modulus"),
    ("Airy Diffraction Pattern", "Gaussian Beam Divergence"),
    ("Airy Diffraction Pattern", "Fourier Transform"),
    ("Zener–Hollomon Parameter", "Arrhenius Equation"),
    ("Hall–Petch Relationship", "Arrhenius Equation"),
    ("Griffith Fracture Criterion", "Young's Modulus"),
    ("Griffith Fracture Criterion", "Cauchy's Stress Theorem"),
    ("Cauchy's Stress Theorem", "Navier–Stokes Equations"),

    # nuclear / astro
    ("Radioactive Decay Law", "Half-Life"),
    ("Half-Life", "Chandrasekhar Limit"),
    ("Stefan–Boltzmann Law", "Wien's Displacement Law"),
    ("Chandrasekhar Limit", "Heisenberg Uncertainty Principle"),
    ("Schwarzschild Radius", "Chandrasekhar Limit"),

    # maths as glue
    ("Pythagorean Theorem", "Lorentz Transformations"),
    ("Pythagorean Theorem", "Geodesic Equation"),
    ("Euler's Identity", "Fourier Transform"),
    ("Euler's Identity", "Feynman Path Integral"),
    ("Euler's Identity", "Qubit State"),
    ("Bayes' Theorem", "Shannon Entropy"),
    ("Normal Distribution", "Heat Equation"),
    ("Normal Distribution", "Boltzmann Distribution"),
    ("Normal Distribution", "Gaussian Beam Divergence"),
    ("Fourier Transform", "Shannon–Hartley Channel Capacity"),

    # nonlinear
    ("Lorenz System", "Logistic Map"),
    ("Logistic Map", "Feigenbaum Constant"),
    ("Feigenbaum Constant", "Fine-Structure Constant"),

    # gas laws internal-to-chemistry are same field; link Graham/Dalton outward
    ("Graham's Law of Effusion", "Equipartition Theorem"),
    ("Dalton's Law of Partial Pressures", "Nernst Equation"),
    ("Gay-Lussac's Law", "Ideal Gas Law"),

    # biophysics
    ("Goldman–Hodgkin–Katz Equation", "Nernst Equation"),
    ("Michaelis–Menten Equation", "Eyring Equation"),

    # info theory
    ("Shannon–Hartley Channel Capacity", "Shannon Entropy"),

    # thermoelectrics
    ("Seebeck Effect", "Peltier Effect"),
    ("Peltier Effect", "Thermoelectric Figure of Merit"),

    # within-field cosmology spine (same chip, but the dependency is worth stating)
    ("FLRW Metric", "First Friedmann Equation"),
    ("FLRW Metric", "Second Friedmann Equation"),
    ("FLRW Metric", "Cosmological Redshift"),
    ("Cosmological Redshift", "Hubble's Law"),
    ("Cosmological Redshift", "First Friedmann Equation"),
    ("Critical Density", "First Friedmann Equation"),
    ("Critical Density", "Hubble's Law"),
    ("Critical Density", "Second Friedmann Equation"),
    ("Cosmological Fluid Equation", "First Friedmann Equation"),
    ("Cosmological Fluid Equation", "Second Friedmann Equation"),
    ("Cosmological Fluid Equation", "Cosmological Equation of State"),
    ("Cosmological Fluid Equation", "FLRW Metric"),
    ("Cosmological Equation of State", "Second Friedmann Equation"),
    ("Cosmological Equation of State", "Cosmological Redshift"),
    ("Cosmological Equation of State", "Critical Density"),
    ("Linear Perturbation Growth", "First Friedmann Equation"),
    ("Linear Perturbation Growth", "Critical Density"),
    ("Linear Perturbation Growth", "Cosmological Redshift"),
    ("Linear Perturbation Growth", "FLRW Metric"),
    ("Linear Perturbation Growth", "Hubble's Law"),
    ("Saha Ionization Equation", "Chandrasekhar Limit"),

    # orphans
    ("Specific Impulse", "Tsiolkovsky Rocket Equation"),
    ("Specific Impulse", "Newton's Second Law"),
    ("Zeroth Law of Thermodynamics", "Boltzmann Distribution"),
    ("Zeroth Law of Thermodynamics", "Newton's Law of Cooling"),

    # superconductivity
    ("London Equations", "BCS Energy Gap"),
    ("BCS Energy Gap", "Josephson Effect"),
    ("Josephson Effect", "Planck–Einstein Relation"),
]


def main():
    # 1. ensure the Related self-relation exists
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{DS}")
    if "Related" not in ds["properties"]:
        body = {"properties": {"Related": {"relation": {
            "data_source_id": DS, "type": "single_property", "single_property": {}}}}}
        try:
            call("PATCH", f"https://api.notion.com/v1/data_sources/{DS}", body)
        except urllib.error.HTTPError as e:
            print("data_source PATCH failed", e.code, e.read().decode()[:300], "— trying database endpoint")
            body = {"properties": {"Related": {"relation": {
                "database_id": DB, "type": "single_property", "single_property": {}}}}}
            call("PATCH", f"https://api.notion.com/v1/databases/{DB}", body)
        print("created Related relation")
    else:
        print("Related relation already exists")

    # 2. load all pages: name -> id, and current relations
    by_name, current = {}, {}
    cursor = None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        d = call("POST", f"https://api.notion.com/v1/data_sources/{DS}/query", body)
        for r in d["results"]:
            name = "".join(x["plain_text"] for x in r["properties"]["Name"]["title"])
            by_name[name] = r["id"]
            rel = r["properties"].get("Related", {}).get("relation", []) or []
            current[r["id"]] = {x["id"] for x in rel}
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]

    # 3. build desired adjacency (union with existing)
    missing = sorted({n for pair in LINKS for n in pair if n not in by_name})
    if missing:
        sys.exit(f"unknown equation names in LINKS: {missing}")
    want = {pid: set(rels) for pid, rels in current.items()}
    for a, b in LINKS:
        ia, ib = by_name[a], by_name[b]
        want[ia].add(ib)
        want[ib].add(ia)

    # 4. write only pages whose relation set changed
    changed = 0
    for pid, rels in want.items():
        if rels != current[pid]:
            call("PATCH", f"https://api.notion.com/v1/pages/{pid}",
                 {"properties": {"Related": {"relation": [{"id": x} for x in sorted(rels)]}}})
            changed += 1
    n_edges = sum(len(v) for v in want.values()) // 2
    print(f"updated {changed} pages · {n_edges} undirected links · "
          f"{sum(1 for v in want.values() if v)}/{len(want)} equations linked")


if __name__ == "__main__":
    main()
