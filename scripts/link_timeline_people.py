"""Put people on the cosmic timeline: add researchers, link them to epochs.

The Cosmic Timeline [DB] had relations to equations and theories but not to
people, so there was no way to say that someone's work is *about* an epoch
without calling them its proposer. Theories → Researchers is `Proponent`, and
that word means proposer here; a modern cosmologist who fits neutrino masses
to the CMB did not propose Big Bang cosmology. This adds a `Researchers`
relation to the timeline instead — "people whose work is about this epoch" —
and seeds it.

PEOPLE adds rows to the Researchers DB for anyone not already there. LINKS maps
event → researcher names; both directions are validated offline before this
touches Notion. The rule for a link is that the person's work is genuinely
about that epoch; an event with nobody on file who worked on it stays empty
rather than padded with names that merely sound relevant.

Lifespan is left empty where a birth year is not certain — better a blank than
a plausible number.

Idempotent, unions with anything already set, never overwrites a filled field.
Run on the VPS:  python3 scripts/link_timeline_people.py
"""
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, query_all, sync_rows, title_of  # noqa: E402

TIMELINE_DS = "3c1ab928-8ffa-48e7-b0bc-b90e16480a46"
RESEARCHER_DS = "4cc8d7c4-9008-4017-a09b-7087720aebd3"
PROP = "Researchers"

# name, lifespan (None if not certain), nationality, field, known for
PEOPLE = [
    ("Julien Lesgourgues", None, "French", "Cosmology",
     "Co-author of CLASS, the Boltzmann code that turns a set of cosmological parameters into a "
     "predicted microwave background and matter power spectrum, and of MontePython for fitting them "
     "to data. A Planck collaboration member, and — with Sergio Pastor — the neutrino-cosmology "
     "bounds that make the CMB the tightest constraint on the sum of the neutrino masses."),
    ("Andrei Sakharov", "1921–1989", "Soviet", "Physics",
     "Set out in 1967 the three conditions any explanation of the matter–antimatter asymmetry must "
     "satisfy — baryon number violation, C and CP violation, departure from equilibrium — and they "
     "still frame the problem. Also the Soviet hydrogen bomb, and the Nobel Peace Prize for "
     "opposing what he had built."),
    ("Fred Adams", None, "American", "Astrophysics",
     "With Gregory Laughlin, 'A Dying Universe' (1997): the paper that laid out the five ages of "
     "the cosmos from the stelliferous era through the degenerate, black hole and dark eras — the "
     "source of most far-future chronologies, this one included."),
    ("Gregory Laughlin", None, "American", "Astrophysics",
     "The other author of 'A Dying Universe', and of the popular account that followed; also a "
     "planet-formation and exoplanet theorist."),

    # -- the JWST era: first galaxies, first stars, reionization, cosmic dawn
    ("Marcia Rieke", None, "American", "Astronomy",
     "Principal investigator of NIRCam, JWST's near-infrared camera — the instrument behind the "
     "deep-field images the first-galaxy results come from."),
    ("Brant Robertson", None, "American", "Astronomy",
     "Co-lead of JADES, the JWST deep survey that has spectroscopically confirmed galaxies within "
     "300–400 million years of the Big Bang; earlier, models of how galaxies alone could have "
     "reionized the universe."),
    ("Emma Curtis-Lake", None, "British", "Astronomy",
     "First author of the JADES paper that spectroscopically confirmed four galaxies beyond z = 10 "
     "— the first hard evidence that the JWST candidates were real and not nearby interlopers."),
    ("Rohan Naidu", None, None, "Astronomy",
     "First author of one of the earliest JWST papers on galaxy candidates at z ≈ 11–13, out within "
     "weeks of the first images — the start of the 'too bright, too early' argument."),
    ("Ivo Labbé", None, "Dutch", "Astronomy",
     "Lead author of the 2023 Nature paper on six candidate galaxies at z ≈ 7–9 that looked far too "
     "massive for their era — the 'universe breakers' — which forced a hard look at how stellar "
     "masses are inferred from early light."),
    ("Michael Boylan-Kolchin", None, "American", "Astrophysics",
     "Worked out how bright and how massive an early galaxy can possibly be under ΛCDM — the "
     "yardstick the JWST candidates are measured against, and by which a few looked impossible."),
    ("Garth Illingworth", None, "Australian-American", "Astronomy",
     "The Hubble deep-field campaigns that pushed the frontier to z ≈ 11 before JWST existed; "
     "GN-z11, found in 2016, held the distance record for six years."),
    ("Volker Bromm", None, "German", "Astrophysics",
     "The simulations that showed the first stars formed alone or in pairs inside dark-matter "
     "minihalos and were tens to hundreds of times the Sun's mass — the modern picture of "
     "Population III."),
    ("Tom Abel", None, "German", "Astrophysics",
     "With Bryan and Norman, the 2002 simulation that followed a single primordial cloud from "
     "cosmological scales down to a forming protostar — the first end-to-end model of a first star."),
    ("Naoki Yoshida", None, "Japanese", "Astrophysics",
     "Simulations of the first stars and the first supernovae, following primordial gas as it "
     "cooled and fragmented, and of the molecular-hydrogen chemistry that let it cool at all."),
    ("Abraham Loeb", None, "Israeli-American", "Astrophysics",
     "With Rennan Barkana, the 2001 review 'In the Beginning: the first sources of light and the "
     "reionization of the universe', which set the agenda for the first-stars and 21-cm fields."),
    ("Rennan Barkana", None, "Israeli", "Astrophysics",
     "The theory of the 21-cm signal from cosmic dawn — how the first stars' light would imprint on "
     "the neutral hydrogen around them — and the case that the EDGES dip, if real, needs new physics."),
    ("Judd Bowman", None, "American", "Radio Astronomy",
     "Led EDGES, a table-sized radio antenna in Western Australia that reported a 21-cm absorption "
     "dip at z ≈ 17 in 2018 — the first claimed signal from cosmic dawn, deeper than any model "
     "predicted, and still contested."),
    ("James Gunn", "1938–", "American", "Astronomy",
     "With Bruce Peterson, the 1965 prediction that neutral intergalactic hydrogen would blank out a "
     "quasar's spectrum shortward of Lyman-α — the test that dates the end of reionization. Later "
     "the architect of the Sloan Digital Sky Survey."),
    ("Bruce Peterson", None, None, "Astronomy",
     "The other name on the Gunn–Peterson trough: the 1965 calculation of how little neutral "
     "hydrogen a quasar's light could have passed through, given how much of it arrived."),
    ("Xiaohui Fan", None, "Chinese-American", "Astronomy",
     "Found the first quasars beyond z = 6 in Sloan data and watched the Gunn–Peterson trough "
     "finally appear in their spectra — the observation that pins the end of reionization to "
     "roughly a billion years."),
    ("Richard Ellis", "1950–", "British", "Astronomy",
     "Four decades on the most distant galaxies, from the Hubble Ultra Deep Field to JWST, and the "
     "case — 'When Galaxies Were Born' — that they are what reionized the universe."),
    ("Piero Madau", None, "Italian", "Astrophysics",
     "The Madau plot: cosmic star-formation rate against redshift, first drawn in 1996 from the "
     "Hubble Deep Field. Its peak at z ≈ 2 is what 'cosmic noon' means."),
    ("Simon Lilly", None, None, "Astronomy",
     "The Canada–France Redshift Survey, and the 1996 paper that first plotted star-formation "
     "density climbing with lookback time — the other half of the Lilly–Madau diagram."),
    ("Charles Steidel", None, "American", "Astronomy",
     "The Lyman-break technique: picking galaxies at z ≈ 3 out of deep images by their colours "
     "alone. It made cosmic noon observable in bulk rather than one object at a time."),
    ("Mark Dickinson", None, "American", "Astronomy",
     "With Madau, the 2014 review that consolidated the cosmic star-formation history into its "
     "modern form; before that, the Hubble Deep Field team."),

    # -- the solar system, and the empty far future
    ("Pierre-Simon Laplace", "1749–1827", "French", "Mathematics & Astronomy",
     "The nebular hypothesis: the solar system condensed from a rotating disc of gas, which is why "
     "the planets orbit in one plane and one direction. Still the picture, with the details filled in."),
    ("Viktor Safronov", "1917–1999", "Soviet", "Astronomy",
     "Planet growth by the accretion of planetesimals, set out in a 1969 monograph the West largely "
     "ignored until it was translated — the foundation of modern planet-formation theory."),
    ("Clair Patterson", "1922–1995", "American", "Geochemistry",
     "Dated the Earth and the solar system to 4.55 billion years in 1956, from lead isotopes in the "
     "Canyon Diablo meteorite — then spent the rest of his career getting lead out of petrol."),
    ("Lawrence Krauss", "1954–", "American", "Physics",
     "With Robert Scherrer, the 2007 paper showing that in 100 billion years an accelerating "
     "universe erases its own evidence — no receding galaxies, no microwave background, no way to "
     "infer that a Big Bang ever happened."),
    ("Robert Scherrer", None, "American", "Physics",
     "The other author of 'The Return of a Static Universe and the End of Cosmology'; also work on "
     "dark-energy models and Big Bang nucleosynthesis."),
]

# timeline event -> researchers whose work is about it
LINKS = {
    # the very early universe
    "Planck Epoch": ["Max Planck", "Roger Penrose", "Stephen Hawking", "Carlo Rovelli", "Abhay Ashtekar"],
    "Grand Unification": ["Howard Georgi", "Sheldon Glashow"],
    "Inflation": ["Alan Guth", "Andrei Linde", "Alexei Starobinsky"],
    "Reheating": ["Andrei Linde", "Alexei Starobinsky"],
    "Electroweak Symmetry Breaking": ["Peter Higgs", "François Englert", "Steven Weinberg",
                                      "Abdus Salam", "Sheldon Glashow"],
    "Baryogenesis": ["Andrei Sakharov"],
    "Quark Epoch": ["Murray Gell-Mann", "David Gross", "Frank Wilczek"],
    "Quark Confinement": ["Murray Gell-Mann", "David Gross", "Frank Wilczek"],
    "Neutrino Decoupling": ["Julien Lesgourgues"],
    # the radiation era
    "Electron–Positron Annihilation": ["Paul Dirac"],
    "Big Bang Nucleosynthesis": ["George Gamow", "Ralph Alpher", "James Peebles"],
    "Matter–Radiation Equality": ["James Peebles", "Julien Lesgourgues"],
    "Recombination": ["James Peebles", "Julien Lesgourgues"],
    "Photon Decoupling — the CMB": ["George Gamow", "Ralph Alpher", "Arno Penzias", "Robert Wilson",
                                    "George Smoot", "James Peebles", "Julien Lesgourgues"],
    # structure and the present
    "Dark Energy Takes Over": ["Albert Einstein", "Saul Perlmutter", "Brian Schmidt", "Adam Riess"],
    "Present Day": ["Edwin Hubble", "Georges Lemaître", "Fritz Zwicky", "Vera Rubin", "Adam Riess"],
    # the far future — Adams & Laughlin's chronology, plus the physics each step rests on
    "Andromeda Arrives": ["Vesto Slipher", "Edwin Hubble"],
    "The Sun Dies": ["Arthur Eddington", "Cecilia Payne-Gaposchkin"],
    "Star Formation Ends": ["Fred Adams", "Gregory Laughlin"],
    "Proton Decay, If It Happens": ["Howard Georgi", "Sheldon Glashow", "Fred Adams", "Gregory Laughlin"],
    "Black Holes Evaporate": ["Stephen Hawking", "Jacob Bekenstein", "Fred Adams", "Gregory Laughlin"],
    "The Last Black Holes Go": ["Stephen Hawking", "Jacob Bekenstein", "Leonard Susskind", "Gerard 't Hooft"],
    "Heat Death": ["Rudolf Clausius", "Ludwig Boltzmann", "Fred Adams", "Gregory Laughlin"],
    # the stretch between the CMB and the present — the JWST era, and what led up to it
    "The Dark Ages": ["Rennan Barkana", "Abraham Loeb", "Judd Bowman"],
    "The First Stars": ["Volker Bromm", "Tom Abel", "Naoki Yoshida", "Abraham Loeb"],
    "The First Galaxies": ["Marcia Rieke", "Brant Robertson", "Emma Curtis-Lake", "Rohan Naidu",
                           "Ivo Labbé", "Michael Boylan-Kolchin", "Garth Illingworth"],
    "Reionization": ["James Gunn", "Bruce Peterson", "Xiaohui Fan", "Richard Ellis",
                     "Rennan Barkana", "Abraham Loeb"],
    "Cosmic Noon": ["Piero Madau", "Simon Lilly", "Charles Steidel", "Mark Dickinson"],
    "The Solar System Forms": ["Pierre-Simon Laplace", "Viktor Safronov", "Clair Patterson",
                               "Gregory Laughlin"],
    "The Local Group Is Alone": ["Lawrence Krauss", "Robert Scherrer", "Fred Adams", "Gregory Laughlin"],
}


def ensure_relation():
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{TIMELINE_DS}")
    if PROP in ds["properties"]:
        print(f"  relation {PROP} already exists on the timeline")
        return
    for body in (
        {"properties": {PROP: {"relation": {"data_source_id": RESEARCHER_DS, "type": "dual_property",
                                            "dual_property": {"synced_property_name": "Timeline"}}}}},
        {"properties": {PROP: {"relation": {"data_source_id": RESEARCHER_DS, "type": "single_property",
                                            "single_property": {}}}}},
    ):
        try:
            call("PATCH", f"https://api.notion.com/v1/data_sources/{TIMELINE_DS}", body)
            print(f"  created relation {PROP} on the timeline")
            return
        except urllib.error.HTTPError as e:
            print(f"  attempt failed: {e.code} {e.read().decode()[:160]}")


def main():
    print("researchers")
    schema = ensure_props(RESEARCHER_DS, {}, "researchers")
    sync_rows(RESEARCHER_DS, schema,
              [{"Name": n, "Lifespan": ls, "Nationality": nat, "Field": f, "Known For": k}
               for n, ls, nat, f, k in PEOPLE],
              "researchers")

    print("\ntimeline")
    ensure_relation()
    people = {title_of(p, "Name"): p["id"] for p in query_all(RESEARCHER_DS) if title_of(p, "Name")}
    events = {title_of(p, "Event"): p for p in query_all(TIMELINE_DS) if title_of(p, "Event")}
    changed, edges, missing = 0, 0, set()
    for event, names in LINKS.items():
        page = events.get(event)
        if not page:
            missing.add(f"event: {event}")
            continue
        ids = set()
        for n in names:
            if n in people:
                ids.add(people[n])
            else:
                missing.add(n)
        cur = {x["id"] for x in (page["properties"].get(PROP, {}).get("relation") or [])}
        new = cur | ids
        edges += len(new)
        if new != cur:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
                 {"properties": {PROP: {"relation": [{"id": x} for x in sorted(new)]}}})
            changed += 1
    if missing:
        print("  unresolved names ignored:", sorted(missing))
    print(f"  updated {changed} events · {edges} event→researcher links")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
