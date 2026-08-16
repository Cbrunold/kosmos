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
about that epoch — the dark ages, the first stars, reionization and cosmic
noon are left empty rather than padded, because nobody on file worked on them.

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
