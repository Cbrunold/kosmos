"""Seed the Cosmic Timeline [DB] in Notion — the history of the universe.

The existing Cosmology Events [DB] could not hold this: its `Type` select offers
Collision and Supernova, and its time field is a calendar `Date`. That schema
describes observed transients — a supernova, at an object, on a date — which is
a different kind of thing from an epoch of cosmic history. Recombination
happened 380,000 years after the Big Bang; inflation ended at 10⁻³² seconds.
Neither is a date, so this database sorts on `Seconds After Big Bang`, a number
spanning 1e-43 to 1e110.

(That database's title property was also called `Force ID`, copied from the
Forces DB. Renamed to `Event` on 2026-08-15 — it is still empty, and still
meant for transients rather than epochs.)

Times and temperatures follow the standard ΛCDM chronology (Planck 2018
parameters). The far-future entries are order-of-magnitude projections from
Adams & Laughlin's "dying universe" work, not measurements, and the entries
themselves say so.

Unlike the other seeds this one links as it goes — equations and theories are
listed per event rather than in a separate map, so a second script would only
be re-reading the same table.

Idempotent, and never overwrites a field already filled in.
Run on the VPS:  python3 scripts/seed_timeline.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path
from notion import token, headers, call, query_all, title_of, find_ds  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"   # Physical Sciences
TIMELINE_DS = "3c1ab928-8ffa-48e7-b0bc-b90e16480a46"
EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"
THEORY_DS = "215048ed-e6a6-4b9a-858b-73e8c801629e"

ERAS = ["Very Early Universe", "Radiation Era", "Dark Ages",
        "Structure Formation", "Life on Earth", "Present", "Far Future"]

YR = 3.155693e7   # seconds in a Julian year


def E(event, era, secs, when, temp, z, what, eqs=(), ths=()):
    return {"Event": event, "Era": era, "Seconds After Big Bang": secs, "When": when,
            "Temperature (K)": temp, "Redshift": z, "What Happened": what,
            "_eq": list(eqs), "_th": list(ths)}


EVENTS = [
    E("Planck Epoch", "Very Early Universe", 1e-43, "0 – 10⁻⁴³ s", 1.417e32, "—",
      "The one interval no physics describes. Gravity is as strong as the other three forces and "
      "spacetime itself should be quantised, so general relativity and quantum mechanics both apply "
      "and neither survives the encounter.",
      ["Einstein Field Equations", "Heisenberg Uncertainty Principle", "Einstein–Hilbert Action"],
      ["Quantum Gravity", "String Theory", "Loop Quantum Gravity"]),

    E("Grand Unification", "Very Early Universe", 1e-36, "10⁻⁴³ – 10⁻³⁶ s", 1e28, "—",
      "Gravity has separated; the strong, weak and electromagnetic forces are still a single "
      "interaction. The symmetry breaks at the end of this interval, and the energy released may be "
      "what drives what happens next.",
      ["Standard Model Lagrangian", "Fine-Structure Constant"],
      ["Grand Unified Theories", "Unification Theories"]),

    E("Inflation", "Very Early Universe", 1e-33, "10⁻³⁶ – 10⁻³² s", 1e27, "—",
      "Space expands by a factor of at least 10²⁶ in less time than light takes to cross a proton. "
      "It flattens the geometry, dilutes away the monopoles nobody can find, and stretches quantum "
      "fluctuations to cosmic size — those fluctuations become every galaxy that will ever exist.",
      ["First Friedmann Equation", "FLRW Metric", "Linear Perturbation Growth",
       "Cosmological Equation of State"],
      ["Cosmic Inflation"]),

    E("Reheating", "Very Early Universe", 1e-32, "≈ 10⁻³² s", 1e27, "—",
      "The inflaton field decays and dumps its energy into a bath of particles. This — not t = 0 — "
      "is the actual 'hot' of the hot Big Bang: everything that now exists was created here.",
      ["Mass–Energy Equivalence", "Standard Model Lagrangian"],
      ["Cosmic Inflation", "Big Bang Cosmology"]),

    E("Electroweak Symmetry Breaking", "Very Early Universe", 1e-12, "10⁻¹² s", 1e15, "—",
      "The Higgs field settles into its non-zero value. The W and Z bosons acquire mass, the photon "
      "does not, and one force becomes two: the weak force and electromagnetism.",
      ["Higgs Potential", "Standard Model Lagrangian"],
      ["Higgs Mechanism", "Electroweak Unification"]),

    E("Baryogenesis", "Very Early Universe", 1e-11, "before 10⁻¹¹ s", 1e15, "—",
      "Some process favoured matter over antimatter by about one part in a billion. Everything made "
      "of atoms is that leftover; the other billion parts annihilated into the photons now arriving "
      "as the microwave background. How it happened is unsolved.",
      ["Standard Model Lagrangian", "Mass–Energy Equivalence"],
      ["The Standard Model", "Grand Unified Theories"]),

    E("Quark Epoch", "Very Early Universe", 1e-9, "10⁻¹² – 10⁻⁶ s", 1e13, "—",
      "A quark–gluon plasma too hot for the strong force to hold anything together. Briefly "
      "recreated at RHIC and the LHC, which makes this the earliest era ever reproduced in a "
      "laboratory.",
      ["Standard Model Lagrangian", "Fermi–Dirac Distribution"],
      ["Quantum Chromodynamics"]),

    E("Quark Confinement", "Very Early Universe", 1e-6, "10⁻⁶ s", 1e13, "—",
      "The plasma cools enough for quarks to bind into protons and neutrons, and they never come "
      "apart again. Every proton in your body dates from this moment.",
      ["Standard Model Lagrangian"],
      ["Quantum Chromodynamics", "The Standard Model"]),

    E("Neutrino Decoupling", "Very Early Universe", 1.0, "1 second", 1e10, "—",
      "Neutrinos stop interacting with anything and stream freely. They are still here — a cosmic "
      "neutrino background now at 1.95 K, colder than the CMB, and still not detected directly.",
      ["Fermi–Dirac Distribution", "Boltzmann Distribution"],
      ["Big Bang Cosmology"]),

    E("Electron–Positron Annihilation", "Radiation Era", 10.0, "1 – 10 s", 5e9, "—",
      "Electrons and positrons annihilate, leaving only the one-in-a-billion excess of matter and "
      "heating the photons relative to the neutrinos that had already left.",
      ["Mass–Energy Equivalence", "Planck–Einstein Relation"],
      ["Big Bang Cosmology", "Quantum Electrodynamics"]),

    E("Big Bang Nucleosynthesis", "Radiation Era", 180.0, "10 s – 20 minutes", 1e9, "—",
      "Protons and neutrons fuse into deuterium, helium-4 and a trace of lithium-7, then stop as the "
      "universe cools below the fusion threshold. It freezes in about 24% helium by mass — a "
      "prediction that matches observation to two decimal places, and one of the three pillars.",
      ["Saha Ionization Equation", "First Friedmann Equation", "Boltzmann Distribution",
       "Radioactive Decay Law"],
      ["Big Bang Nucleosynthesis", "Big Bang Cosmology"]),

    E("Matter–Radiation Equality", "Radiation Era", 5e4 * YR, "≈ 50,000 years", 9300, "z ≈ 3400",
      "Matter density overtakes radiation density. Gravity can finally begin assembling structure, "
      "because until now radiation pressure smoothed out every clump as fast as it formed.",
      ["Cosmological Equation of State", "Linear Perturbation Growth", "First Friedmann Equation",
       "Cosmological Fluid Equation"],
      ["Big Bang Cosmology", "Dark Matter"]),

    E("Recombination", "Radiation Era", 3.8e5 * YR, "380,000 years", 3000, "z ≈ 1100",
      "Electrons and protons combine into neutral hydrogen. The Saha equation puts this at 3000 K — "
      "far below hydrogen's 13.6 eV binding energy — because photons outnumber baryons a billion to "
      "one, and the rare energetic ones keep breaking atoms apart long past the naive temperature.",
      ["Saha Ionization Equation", "Bohr Model Energy Levels", "Rydberg Formula",
       "Boltzmann Distribution"],
      ["Big Bang Cosmology", "Bohr Model of the Atom"]),

    E("Photon Decoupling — the CMB", "Radiation Era", 3.8e5 * YR + 1, "380,000 years", 2970,
      "z ≈ 1100",
      "With the free electrons gone the universe turns transparent and the photons fly free. They "
      "are still arriving, stretched by a factor of 1100 into microwaves at 2.725 K: the oldest "
      "light there is, and the most perfect black body ever measured.",
      ["Planck's Law", "Cosmological Redshift", "Wien's Displacement Law",
       "Kirchhoff's Law of Thermal Radiation"],
      ["Big Bang Cosmology", "Steady State Theory"]),

    E("The Dark Ages", "Dark Ages", 1e6 * YR, "380,000 years – 150 million years", 60,
      "z ≈ 1100 – 20",
      "No stars, and nothing to see but the fading afterglow. Neutral hydrogen fills space while "
      "gravity quietly assembles the dark matter halos everything else will later fall into.",
      ["Linear Perturbation Growth", "Law of Universal Gravitation"],
      ["Dark Matter", "Big Bang Cosmology"]),

    E("The First Stars", "Dark Ages", 1.8e8 * YR, "≈ 180 million years", 50, "z ≈ 20",
      "Metal-free hydrogen and helium collapse into stars hundreds of times the Sun's mass, burning "
      "furiously and dying young. Not one has ever been observed — Population III is the great "
      "missing chapter of astrophysics.",
      ["Chandrasekhar Limit", "Stefan–Boltzmann Law", "Saha Ionization Equation"],
      ["Stellar Nucleosynthesis"]),

    E("The First Galaxies", "Structure Formation", 4e8 * YR, "≈ 400 million years", 33, "z ≈ 11",
      "Small, clumpy and furiously star-forming. JWST keeps finding them brighter and earlier than "
      "the models allow, which is an open problem rather than a solved one.",
      ["Linear Perturbation Growth", "Law of Universal Gravitation", "Hubble's Law"],
      ["Dark Matter", "Big Bang Cosmology"]),

    E("Reionization", "Structure Formation", 5e8 * YR, "150 million – 1 billion years", 30,
      "z ≈ 20 – 6",
      "Ultraviolet light from the first stars and quasars strips the electrons back off the "
      "intergalactic hydrogen it took recombination so long to assemble. The universe becomes "
      "transparent to ultraviolet for the second and final time.",
      ["Saha Ionization Equation", "Planck's Law", "Einstein A and B Coefficients"],
      ["Stellar Nucleosynthesis", "Big Bang Cosmology"]),

    E("Cosmic Noon", "Structure Formation", 3.5e9 * YR, "≈ 3.5 billion years", 9, "z ≈ 2",
      "Star formation peaks: the universe builds stars about ten times faster than it does now. "
      "Most stars that have ever existed were born around this time.",
      ["Stefan–Boltzmann Law", "Chandrasekhar Limit", "Saha Ionization Equation"],
      ["Stellar Nucleosynthesis"]),

    E("The Solar System Forms", "Structure Formation", 9.2e9 * YR,
      "9.2 billion years — 4.6 billion years ago", 3.8, "z ≈ 0.4",
      "A molecular cloud enriched by earlier supernovae collapses. Every element in the Earth "
      "heavier than helium was manufactured inside a star that died before the Sun existed.",
      ["Kepler's Third Law", "Law of Universal Gravitation", "Vis-Viva Equation",
       "Chandrasekhar Limit"],
      ["Stellar Nucleosynthesis", "Heliocentrism", "Newtonian Mechanics"]),

    E("Dark Energy Takes Over", "Structure Formation", 9.8e9 * YR, "≈ 9.8 billion years", 3.6,
      "z ≈ 0.4",
      "Matter has thinned enough that the cosmological constant dominates the energy budget, and the "
      "expansion stops slowing and starts speeding up. Found in 1998 by noticing that distant "
      "supernovae were fainter than they had any right to be.",
      ["Second Friedmann Equation", "Cosmological Equation of State", "Hubble's Law",
       "Critical Density"],
      ["Dark Energy", "Big Bang Cosmology"]),

    # ---- life on Earth. Its own era, and not out of sentiment: every other row on
    # this timeline is something the whole universe did, and these are things that
    # happened in one place. The label says so rather than filing them under
    # Structure Formation, which would quietly claim they were cosmic events.
    # Ages are the conventional ones, converted against the same 13.797 Gyr the
    # Present Day row uses; redshifts and CMB temperatures follow from the age.
    E("Life Leaves Its First Trace", "Life on Earth", (13.797 - 3.5) * 1e9 * YR,
      "10.3 billion years — 3.5 billion years ago", 3.5, "z ≈ 0.3",
      "Stromatolites in the Pilbara: layered mats built by microbes that were already doing "
      "chemistry. Carbon-isotope ratios in Greenland push the first sign back to 3.7 billion years "
      "and disputed structures further still, which is the honest state of it — life is older than "
      "the oldest thing anyone can hold up as proof of it.",
      ["Michaelis–Menten Equation", "Arrhenius Equation"], []),

    E("Oxygenic Photosynthesis", "Life on Earth", (13.797 - 2.7) * 1e9 * YR,
      "11.1 billion years — 2.7 billion years ago", 3.3, "z ≈ 0.22",
      "Cyanobacteria learn to split water rather than something easier, using a cluster of four "
      "manganese atoms to prise apart a molecule that does not want to come apart. Every oxygen "
      "atom in the air has been through that cluster. It is the single most consequential chemical "
      "innovation in the planet's history, and it poisoned the world that produced it.",
      ["Planck–Einstein Relation", "Gibbs Free Energy"], []),

    E("The Great Oxidation", "Life on Earth", (13.797 - 2.4) * 1e9 * YR,
      "11.4 billion years — 2.4 billion years ago", 3.3, "z ≈ 0.2",
      "Free oxygen finally outruns everything that had been consuming it, and the atmosphere "
      "changes composition. Dissolved iron rusts out of the oceans and settles as the banded iron "
      "formations that most of the world's iron ore still comes from. Mineralogy changes with it: "
      "up to two-thirds of the five thousand mineral species now recognised are consequences of "
      "this, because oxygen gives elements like iron, copper and uranium a second oxidation state "
      "to form compounds in. Most of the minerals on this site exist because something respired.",
      ["Gibbs Free Energy", "Nernst Equation"], []),

    E("Eukaryotes", "Life on Earth", (13.797 - 1.8) * 1e9 * YR,
      "12.0 billion years — 1.8 billion years ago", 3.1, "z ≈ 0.14",
      "One cell ends up inside another and neither digests the other. The guest becomes the "
      "mitochondrion and keeps its own genome, which is why the evidence survives. Everything "
      "larger than a microbe is descended from that one accident.",
      [], []),

    E("The Cambrian Explosion", "Life on Earth", (13.797 - 0.5388) * 1e9 * YR,
      "13.26 billion years — 539 million years ago", 2.8, "z ≈ 0.04",
      "Animal body plans appear over a few tens of millions of years, and — for the first time — "
      "so do hard parts. Calcite, aragonite and calcium phosphate get recruited into shells, "
      "spines and teeth, which is both why the fossil record starts here and why biomineralisation "
      "is a subject at all.",
      [], []),

    E("Life Moves Onto Land", "Life on Earth", (13.797 - 0.47) * 1e9 * YR,
      "13.33 billion years — 470 million years ago", 2.8, "z ≈ 0.035",
      "Plants colonise the continents, and their roots begin breaking rock into soil. Silicate "
      "weathering accelerates, drawing down carbon dioxide, and the atmosphere and the climate "
      "have been partly under biological control ever since.",
      [], []),

    E("The Great Dying", "Life on Earth", (13.797 - 0.2519) * 1e9 * YR,
      "13.55 billion years — 252 million years ago", 2.8, "z ≈ 0.018",
      "The worst extinction in the record: about 81 % of marine species gone. The Siberian Traps "
      "erupt through coal measures and vent carbon dioxide and sulfur for perhaps a million years, "
      "and the ocean warms, acidifies and loses its oxygen. It took life ten million years to "
      "recover.",
      [], []),

    E("Chicxulub", "Life on Earth", (13.797 - 0.066) * 1e9 * YR,
      "13.73 billion years — 66 million years ago", 2.7, "z ≈ 0.005",
      "A ten-kilometre asteroid strikes what is now Yucatán. The evidence that settled it was "
      "chemical: a worldwide clay layer enriched in iridium, an element the crust has almost none "
      "of and meteorites have plenty of. Non-avian dinosaurs end there and mammals get the room.",
      ["Kinetic Energy", "Momentum and Impulse"], []),

    E("Homo sapiens", "Life on Earth", (13.797 - 0.0003) * 1e9 * YR,
      "13.7967 billion years — 300,000 years ago", 2.73, "z ≈ 0",
      "Anatomically modern humans, on a timeline where the interval since is thinner than the line "
      "drawn to represent it. Everything catalogued on this site — every element named, every "
      "equation written, every mine dug — happens inside that last sliver.",
      [], []),

    E("Present Day", "Present", 13.797e9 * YR, "13.797 billion years", 2.72548, "z = 0",
      "68% dark energy, 27% dark matter, 5% ordinary matter — and of that 5%, only a fraction has "
      "ever been seen. The two ways of measuring the expansion rate disagree by 5σ and nobody knows "
      "which one is wrong.",
      ["Hubble's Law", "Critical Density", "First Friedmann Equation", "FLRW Metric"],
      ["Big Bang Cosmology", "Dark Energy", "Dark Matter"]),

    E("Andromeda Arrives", "Far Future", 18e9 * YR, "≈ 18 billion years — 4.5 billion years from now",
      2.4, "—",
      "The Milky Way and Andromeda merge into a single elliptical galaxy. Almost no stars collide: "
      "galaxies are overwhelmingly empty, and only the spiral structure is destroyed.",
      ["Law of Universal Gravitation", "Escape Velocity", "Vis-Viva Equation"],
      ["Newtonian Mechanics", "Dark Matter"]),

    E("The Sun Dies", "Far Future", 18.8e9 * YR, "≈ 18.8 billion years — 5 billion years from now",
      2.3, "—",
      "The Sun exhausts its hydrogen, swells into a red giant reaching roughly Earth's orbit, and "
      "collapses into a white dwarf: half its present mass packed into an Earth-sized ball, cooling "
      "for the rest of time.",
      ["Chandrasekhar Limit", "Stefan–Boltzmann Law", "Wien's Displacement Law"],
      ["Stellar Nucleosynthesis"]),

    E("The Local Group Is Alone", "Far Future", 1e11 * YR, "≈ 100 billion years", 0.014, "—",
      "Accelerating expansion carries every other galaxy beyond the horizon. Astronomers then would "
      "see one merged galaxy in an empty static void, with no redshifted galaxies and no microwave "
      "background — no evidence the Big Bang ever happened.",
      ["Cosmological Redshift", "Hubble's Law", "Second Friedmann Equation", "FLRW Metric"],
      ["Dark Energy", "Big Bang Cosmology"]),

    E("Star Formation Ends", "Far Future", 1e14 * YR, "≈ 100 trillion years", 1e-5, "—",
      "The last gas is spent and the smallest red dwarfs — which burn for ten trillion years — "
      "finally go out. The stelliferous era closes; only degenerate remnants are left.",
      ["Chandrasekhar Limit", "Stefan–Boltzmann Law"],
      ["Stellar Nucleosynthesis"]),

    E("Proton Decay, If It Happens", "Far Future", 1e36 * YR, "≈ 10³⁶ years, if at all", 1e-14, "—",
      "Grand unified theories predict the proton decays, with a lifetime now known to exceed 10³⁴ "
      "years. Experiments have watched tens of thousands of tonnes of water for decades and seen "
      "nothing, so this entry may simply never occur.",
      ["Half-Life", "Radioactive Decay Law", "Standard Model Lagrangian"],
      ["Grand Unified Theories", "The Standard Model"]),

    E("Black Holes Evaporate", "Far Future", 1e67 * YR, "≈ 10⁶⁷ years", 1e-20, "—",
      "Stellar-mass black holes finish radiating themselves away. A solar-mass hole is far colder "
      "than today's microwave background, so it cannot even begin to shrink until the universe has "
      "cooled below its own temperature.",
      ["Schwarzschild Radius", "Planck's Law", "Boltzmann Entropy", "Stefan–Boltzmann Law"],
      ["Black Hole Thermodynamics", "General Relativity"]),

    E("The Last Black Holes Go", "Far Future", 1e100 * YR, "≈ 10¹⁰⁰ years", 1e-29, "—",
      "The largest supermassive black holes finally evaporate. Whether the information that fell "
      "into them comes back out is still argued over, and is the sharpest clue anyone has about "
      "quantum gravity.",
      ["Schwarzschild Radius", "Boltzmann Entropy", "Shannon Entropy"],
      ["Black Hole Thermodynamics", "Holographic Principle", "Quantum Gravity"]),

    E("Heat Death", "Far Future", 1e110 * YR, "beyond 10¹⁰⁰ years", 0.0, "—",
      "Maximum entropy: no gradients, no structure, no work possible anywhere. Expansion and cooling "
      "continue toward absolute zero forever — unless dark energy turns out to be something other "
      "than a constant, in which case this ending is wrong.",
      ["Second Law of Thermodynamics", "Boltzmann Entropy", "Third Law of Thermodynamics",
       "Cosmological Equation of State"],
      ["Statistical Mechanics", "Dark Energy", "Big Bang Cosmology"]),
]


def create_db():
    db = call("POST", "https://api.notion.com/v1/databases", {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE},
        "title": [{"type": "text", "text": {"content": "Cosmic Timeline [DB]"}}],
        "initial_data_source": {"properties": {
            "Event": {"title": {}},
            "Era": {"select": {"options": [{"name": e} for e in ERAS]}},
            "Seconds After Big Bang": {"number": {"format": "number"}},
            "When": {"rich_text": {}},
            "Temperature (K)": {"number": {"format": "number"}},
            "Redshift": {"rich_text": {}},
            "What Happened": {"rich_text": {}},
            "Equations": {"relation": {"data_source_id": EQ_DS, "type": "dual_property",
                                       "dual_property": {"synced_property_name": "Timeline"}}},
            "Theories": {"relation": {"data_source_id": THEORY_DS, "type": "dual_property",
                                      "dual_property": {"synced_property_name": "Timeline"}}},
        }},
    })
    return db["data_sources"][0]["id"]


def encode(kind, value):
    if value is None:
        return None
    if kind == "title":
        return {"title": [{"text": {"content": str(value)}}]}
    if kind == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}]}
    if kind == "number":
        return {"number": value}
    if kind == "select":
        return {"select": {"name": str(value)}}
    return None


def is_empty(page, name) -> bool:
    p = page["properties"].get(name)
    if not p:
        return True
    v = p.get(p["type"])
    if v is None:
        return True
    return not v if isinstance(v, list) else False


def main():
    ds_id = TIMELINE_DS
    try:
        ds = call("GET", f"https://api.notion.com/v1/data_sources/{ds_id}")
    except Exception:
        ds_id = find_ds("Cosmic Timeline [DB]")
        if not ds_id:
            ds_id = create_db()
            print("created Cosmic Timeline [DB]:", ds_id)
        ds = call("GET", f"https://api.notion.com/v1/data_sources/{ds_id}")
    print("Cosmic Timeline [DB]:", ds_id)
    schema = {k: v["type"] for k, v in ds["properties"].items()}

    existing = {title_of(p, "Event"): p for p in query_all(ds_id) if title_of(p, "Event")}
    added = filled = 0
    for ev in EVENTS:
        page = existing.get(ev["Event"])
        payload = {}
        for prop, val in ev.items():
            if prop.startswith("_") or val is None or prop not in schema:
                continue
            if page is not None and not is_empty(page, prop):
                continue
            enc = encode(schema[prop], val)
            if enc:
                payload[prop] = enc
        if page is None:
            call("POST", "https://api.notion.com/v1/pages",
                 {"parent": {"type": "data_source_id", "data_source_id": ds_id},
                  "properties": payload})
            added += 1
        elif payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
            filled += 1
    print(f"events: {added} added, {filled} backfilled, {len(EVENTS)} defined")

    # ---- relations, unioned with anything already set
    pages = {title_of(p, "Event"): p for p in query_all(ds_id) if title_of(p, "Event")}
    eqs = {title_of(p, "Name"): p["id"] for p in query_all(EQ_DS) if title_of(p, "Name")}
    ths = {title_of(p, "Name"): p["id"] for p in query_all(THEORY_DS) if title_of(p, "Name")}
    print(f"resolved {len(eqs)} equations, {len(ths)} theories")

    changed, edges, missing = 0, 0, set()
    for ev in EVENTS:
        page = pages.get(ev["Event"])
        if not page:
            continue
        payload = {}
        for prop, wanted, lookup in (("Equations", ev["_eq"], eqs), ("Theories", ev["_th"], ths)):
            if prop not in schema:
                continue
            ids = set()
            for n in wanted:
                if n in lookup:
                    ids.add(lookup[n])
                else:
                    missing.add(n)
            cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
            new = cur | ids
            edges += len(new)
            if new != cur:
                payload[prop] = {"relation": [{"id": x} for x in sorted(new)]}
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
            changed += 1
    if missing:
        print("  unresolved names ignored:", sorted(missing))
    print(f"relations: updated {changed} events · {edges} links")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
