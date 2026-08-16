"""Put people on the cosmic timeline: add researchers, link them to epochs.

The Cosmic Timeline [DB] had relations to equations and theories but not to
people, so there was no way to say that someone's work is *about* an epoch
without calling them its proposer. Theories → Researchers is `Proponent`, and
that word means proposer here; a modern cosmologist who fits neutrino masses
to the CMB did not propose Big Bang cosmology. This adds a `Researchers`
relation to the timeline instead — "people whose work is about this epoch" —
and seeds it.

PEOPLE adds rows to the Researchers DB for anyone not already there (the seeds
so far brought the theorists and the observers; contemporary working
cosmologists are thin). LINKS maps event → researcher names; both directions
are validated offline before this touches Notion.

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
]

# timeline event -> researchers whose work is about it
LINKS = {
    "Neutrino Decoupling": ["Julien Lesgourgues"],
    "Matter–Radiation Equality": ["Julien Lesgourgues"],
    "Recombination": ["Julien Lesgourgues"],
    "Photon Decoupling — the CMB": ["Julien Lesgourgues"],
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
