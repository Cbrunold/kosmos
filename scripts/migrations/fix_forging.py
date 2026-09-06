"""One-off: replace the Forging skill's text with the deeper version, and add
the two equations it now rests on.

The original card was correct but shallow, and one sentence of it was wrong:
it said every blow work-hardens the surface and the next heat recrystallises
it. Above the recrystallisation temperature the steel recrystallises *while*
it is being deformed and does not work-harden at all — which is the whole
reason hot working exists. The rewrite carries the real constraints: the A₃
floor, the three separate ceilings, Zener–Hollomon, the contact-length ratio
that decides whether a blow reaches the core or opens it, hot shortness,
decarburisation, and why a cold shut can never become a weld.

The elastic chips went with it. Hooke's Law and Young's Modulus describe the
regime forging leaves behind on the first blow; the card now points at
Zener–Hollomon and Hall–Petch (added here), Arrhenius, Griffith,
Stefan–Boltzmann and Newton's cooling.

sync_rows never overwrites a filled field — a human may have edited it — so
this rewrites the seven text fields explicitly, and only where the superseded
sentence is still there. Safe to re-run; does nothing after the first time.
Run on the VPS:  ./deploy.sh fix_forging link_equations
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, chunks, ensure_props, query_all, sync_rows, title_of  # noqa: E402
from seed_engineering import EQUATIONS, EQ_DS, ELEMENTS_DS, SKILLS, SKILLS_DS  # noqa: E402

NEW_EQUATIONS = ["Zener–Hollomon Parameter", "Hall–Petch Relationship"]

# equation -> what it rests on, wired here because seed_engineering does not
# touch the Requires graph (seed_foundations creates it).
REQUIRES = {"Zener–Hollomon Parameter": ["Arrhenius Equation"]}

# field -> a phrase found only in the superseded text. Present means the field
# is still the seed's own words and may be replaced; absent means it has been
# rewritten already, here or by hand, and is left alone.
SUPERSEDED = {
    "Summary": "while it is soft enough to move and before it cools",
    "The Science": "Every blow work-hardens the surface a little",
    "Tools": "cross-pein hammer, tongs that fit the stock",
    "Steps": "you have thirty seconds of good heat",
    "Safety": "The forge is quiet and 1,200 °C",
    "How It Fails": "Cold shuts — folds hammered into the surface",
    "Done When": "the surface has hammer marks and no cracks or folds",
}

# The Equations relation is *replaced*, not unioned, so the elastic pair can
# go — but only if it is still exactly what the seed put there.
WAS_LINKED = {"Hooke's Law", "Young's Modulus", "Newton's Law of Cooling"}


def eq_index(wanted, tries=6):
    """Name -> page for the Equations DB, waiting for rows this run just made.

    A row created by sync_rows is not always in the next query's results: on
    2026-08-26 both equations were added and only one came back a second later.
    Re-query rather than fail, because failing here leaves the pair half-linked.
    """
    for attempt in range(tries):
        pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
        missing = [n for n in wanted if n not in pages]
        if not missing:
            return pages
        if attempt < tries - 1:
            print(f"  waiting for Notion to index {', '.join(missing)}")
            time.sleep(2 * (attempt + 1))
    sys.exit(f"  equations still missing after {tries} queries, refusing to half-link: {missing}")


def text_of(page, prop) -> str:
    return "".join(x["plain_text"] for x in page["properties"].get(prop, {}).get("rich_text", []))


def relation_names(page, prop, by_id) -> set:
    return {by_id[x["id"]] for x in (page["properties"].get(prop, {}).get("relation") or []) if x["id"] in by_id}


def main():
    skill = [s for s in SKILLS if s[0] == "Forging"][0]
    _, _, _, summary, science, tools, steps, safety, fails, done, syms, eqn, _ = skill
    want = {"Summary": summary, "The Science": science, "Tools": tools, "Steps": steps,
            "Safety": safety, "How It Fails": fails, "Done When": done}

    print("equations")
    eq_schema = ensure_props(EQ_DS, {}, "equations")
    sync_rows(EQ_DS, eq_schema,
              [{"Name": n, "Equation": e, "Field": f, "Named After": na, "Symbols": sy,
                "Significance": sig, "Year": y}
               for n, e, f, na, sy, sig, y in EQUATIONS if n in NEW_EQUATIONS], "equations")

    eq_pages = eq_index(sorted(set(eqn) | set(NEW_EQUATIONS)))

    for name, prereqs in REQUIRES.items():
        page = eq_pages[name]
        cur = {x["id"] for x in (page["properties"].get("Requires", {}).get("relation") or [])}
        new = cur | {eq_pages[q]["id"] for q in prereqs}
        if new != cur:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
                 {"properties": {"Requires": {"relation": [{"id": x} for x in sorted(new)]}}})
            print(f"  {name}: requires {', '.join(prereqs)}")

    print("\nforging")
    page = next((p for p in query_all(SKILLS_DS) if title_of(p, "Name") == "Forging"), None)
    if not page:
        sys.exit("  Forging not found — run seed_engineering first")

    payload = {}
    for prop, old in SUPERSEDED.items():
        if old in text_of(page, prop):
            payload[prop] = {"rich_text": chunks(want[prop])}
        else:
            print(f"  {prop}: already rewritten, left alone")
    if payload:
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
        print(f"  rewritten: {', '.join(sorted(payload))}")

    # ---- relations. Elements union (nothing to take away), Equations replaced.
    els = {}
    for p in query_all(ELEMENTS_DS):
        sym = "".join(x["plain_text"] for x in p["properties"].get("Notation", {}).get("rich_text", [])).strip()
        if sym:
            els[sym] = p["id"]
    unknown = [s for s in syms if s not in els]
    if unknown:
        sys.exit(f"  unresolved element symbols, refusing to link: {unknown}")

    page = call("GET", f"https://api.notion.com/v1/pages/{page['id']}")
    payload = {}
    cur = {x["id"] for x in (page["properties"].get("Elements", {}).get("relation") or [])}
    new = cur | {els[s] for s in syms}
    if new != cur:
        payload["Elements"] = {"relation": [{"id": x} for x in sorted(new)]}

    by_id = {p["id"]: n for n, p in eq_pages.items()}
    have = relation_names(page, "Equations", by_id)
    want_eq = set(eqn)
    if have == want_eq:
        pass
    elif have == WAS_LINKED:
        payload["Equations"] = {"relation": [{"id": eq_pages[n]["id"]} for n in sorted(want_eq)]}
        print(f"  equations: dropping {', '.join(sorted(WAS_LINKED - want_eq))} — elastic, and forging is past yield")
    else:
        merged = have | want_eq
        payload["Equations"] = {"relation": [{"id": eq_pages[n]["id"]} for n in sorted(merged)]}
        print(f"  equations: hand-edited since seeding ({', '.join(sorted(have))}) — adding, not replacing")
    if payload:
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
        print(f"  relations set: {', '.join(sorted(payload))}")
    else:
        print("  relations already correct")

    print("\nnow run: python3 scripts/link_equations.py, then fetch_all.py && build.py")


if __name__ == "__main__":
    main()
