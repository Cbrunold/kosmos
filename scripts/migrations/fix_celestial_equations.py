"""Domain pass over the Celestial Mechanics equations.

Five entries. The numbers are right — 11.2 km/s from Earth, 2.4 from the Moon,
617 from the Sun — and they agree with the Sun's mass as /cosmos carries it and
with /solar, which works in AU and years where Kepler's third law is just
T = a^(3/2) and so has no constant to disagree about. Escape Velocity's Michell
aside is also framed correctly, as a coincidence that produced 'dark stars' in
1783 rather than as a derivation of the Schwarzschild radius — which matters,
because the astrophysics pass took the opposite claim *out* of Schwarzschild
Radius, and these two now say the same thing.

Two things.

  1. Vis-Viva said 'vis viva' is Leibniz's name for "what we now call kinetic
     energy". Kinetic Energy, in Mechanics, says vis viva was mv² and the half
     arrived with Coriolis in 1829 — which is right, and makes these two
     entries disagree by a factor of two about the same 17th-century term.
     Second instance of two entries contradicting each other, after Doppler
     and Cosmological Redshift. Only reading both ever catches these.

  2. Kepler's First Law required nothing, while the Second requires angular
     momentum and the Third requires universal gravitation. Three sibling
     entries, three different depths of foundation, and the First is the one
     that most needs it: the ellipse is not an accident of the solar system.
     It now requires gravitation and angular momentum, and says why — an
     inverse-square attraction is one of only two force laws whose bound
     orbits close at all, so the shape falls out of Newton rather than having
     to be assumed.

Guarded on the superseded wording. Idempotent.
Run on the VPS:  ./deploy.sh fix_celestial_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

EDITS = {
    "Vis-Viva Equation": {
        "Significance": ("'vis viva' is Leibniz's name for what we now call kinetic energy",
                         "Speed anywhere along any orbit from energy bookkeeping alone. 'Vis viva' is "
                         "Leibniz's name for mv² — twice the kinetic energy, a century and a half before "
                         "Coriolis put the half in — and this equation is no more than the conserved sum "
                         "of that and the gravitational potential, rearranged for v. The everyday tool of "
                         "mission design: every Hohmann transfer, gravity assist and orbital insertion "
                         "burn starts from this line."),
    },
    "Kepler's First Law": {
        "Significance": ("Written as the polar equation of the orbit.",
                         "Planets travel ellipses with the Sun at one focus — not the perfect circles two "
                         "millennia of astronomy had insisted on. Kepler got there through Tycho's data "
                         "and eight arcminutes of Martian residual he refused to round away. The ellipse "
                         "is not a fact about the solar system: an inverse-square attraction is one of "
                         "only two force laws whose bound orbits close on themselves at all, so the shape "
                         "falls out of Newton's law rather than having to be assumed. Written here as the "
                         "polar equation of the orbit."),
    },
}

REQUIRES = {
    "Kepler's First Law": ([], ["Law of Universal Gravitation", "Angular Momentum"]),
}


def text_of(page, prop):
    return "".join(x["plain_text"] for x in page["properties"].get(prop, {}).get("rich_text", []))


def main():
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}

    print("text")
    for name, props in EDITS.items():
        page = pages.get(name)
        if not page:
            print(f"  {name}: not found"); continue
        payload = {}
        for prop, (old, new) in props.items():
            cur = text_of(page, prop)
            if old in cur and cur.strip() != new.strip():
                payload[prop] = {"rich_text": chunks(new)}
            else:
                print(f"  {name} · {prop}: already rewritten, left alone")
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
            print(f"  {name}: {', '.join(sorted(payload))} rewritten")

    print("\nrequires")
    for name, (was, want) in REQUIRES.items():
        page = pages.get(name)
        if not page:
            print(f"  {name}: not found"); continue
        unknown = [q for q in want if q not in pages]
        if unknown:
            sys.exit(f"  {name}: unresolved prerequisite {unknown} — refusing to link")
        cur_ids = {x["id"] for x in (page["properties"].get("Requires", {}).get("relation") or [])}
        cur = {n for n, p in pages.items() if p["id"] in cur_ids}
        if cur == set(want):
            print(f"  {name}: already correct"); continue
        if cur != set(was):
            print(f"  {name}: hand-edited since ({', '.join(sorted(cur)) or 'empty'}) — left alone"); continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {"Requires": {"relation": [{"id": pages[q]["id"]} for q in want]}}})
        print(f"  {name}: requires {', '.join(want)}")


if __name__ == "__main__":
    main()
