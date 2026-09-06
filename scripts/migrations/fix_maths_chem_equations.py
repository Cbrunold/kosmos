"""Domain pass over the last eight fields: maths, chemistry, materials, billiards.

Fifty-three entries, and they are in the best shape of anything on the shelf.
Everything checkable checked: a football is 60 − 90 + 32 = 2, Archimedes really
did squeeze π between 3 10/71 and 3 1/7, sin θ ≈ θ really is half a percent
wrong at 10° and five at 30°, a quarter-ball hit really is 48.6°, cos²30° really
is the 75 % of the energy the ninety-degree rule sends on, and ΔG° of −40 kJ/mol
really does mean K of ten million. The eight billiards entries agree with the
shot lab constant for constant — 170 g, μ_s 0.2, e_c 0.87 from three quarters of
the energy, the miscue limit at half a radius — which is the cross-page check
that caught Rolling Resistance, run again and passing.

Two corrections and one debt of my own.

  1. Sphere: Surface and Volume said "the r³ is why a planet's mass, and its
     gravity, are set by its radius cubed". Mass is. Surface gravity is not:
     GM/R² with M going as R³ leaves g proportional to R itself, which is the
     more interesting fact and is now the one stated.

  2. Throw quoted ball-to-ball friction as "about 0.06 for clean phenolic" flat,
     while /billiards runs on Alciatore's measured fit μ = 0.01 + 0.108·e^(−1.088v)
     precisely because it is not a constant. The entry's prose already says slow
     shots throw more; the symbol line now names the fit the lab uses, so the
     two pages quote the same thing.

  3. Curvature still said "the geodesic equation and the FLRW metric are
     curvature statements". They were, when they required this entry. The
     cosmology pass moved them onto the Riemann curvature tensor — correctly,
     since κ = 1/R is the curvature of a plane curve — and left this sentence
     pointing at a relationship that no longer exists. My mess; cleaned up, and
     it now hands off to Riemann by name.

The Requires graph in chemistry and materials had eight entries whose own prose
names their parent while requiring nothing: Van der Waals is "the ideal gas law
with reality patched in", Eyring is "Arrhenius's barrier given a physical face",
Young's Modulus is "Hooke's law made a property of matter", Griffith has E in
the formula. All eight were already *Related* to the parent — which is why the
obvious check for this (an entry naming an equation it has no edge to) returns
zero across all 216 and would have caught none of them. Related versus Requires
is a judgement, not a rule. Wired by hand.

Guarded on the superseded wording. Idempotent.
Run on the VPS:  ./deploy.sh fix_maths_chem_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

EDITS = {
    "Sphere: Surface and Volume": {
        "Significance": ("The r³ is why a planet's mass, and its gravity, are set by its radius cubed.",
                         "The result Archimedes asked to have carved on his tomb: a sphere has two-thirds "
                         "the volume and two-thirds the surface of the cylinder that just contains it. The "
                         "4πr² is why every inverse-square law is inverse-square — light, gravity and "
                         "electric flux spread over a spherical shell whose area grows as r². The r³ is why "
                         "a planet's mass goes as the cube of its radius, and why its surface gravity, "
                         "which is that mass over the radius squared, goes only as the first power of it: "
                         "a world twice the size of another at the same density pulls twice as hard, not "
                         "eight times."),
    },
    "Throw": {
        "Symbols": ("μ ball-to-ball friction, about 0.06 for clean phenolic",
                    "μ ball-to-ball friction — not a constant: the shot lab uses Alciatore's measured fit "
                    "μ = 0.01 + 0.108·e^(−1.088 v), which runs from about 0.12 at a crawl to 0.02 at "
                    "speed · v_t the relative speed of the two surfaces across the contact — from the cut "
                    "angle, from side spin, or both · v_n the closing speed along the line of centres"),
    },
    "Curvature": {
        "Significance": ("the geodesic equation and the FLRW metric are curvature statements",
                         "How sharply a path bends: the reciprocal of the radius of the circle that hugs "
                         "it. A straight line has zero, a tight corner a lot. Huygens needed it in 1673 to "
                         "make a pendulum keep exact time; a road engineer needs it to bank a bend. Gauss "
                         "showed a surface's curvature can be measured from within it, without ever "
                         "leaving — and it is that intrinsic reading, generalised to four dimensions as "
                         "the Riemann curvature tensor, that general relativity is written in. This is the "
                         "one-dimensional ancestor of it, not the thing itself."),
    },
}

REQUIRES = {
    "Van der Waals Equation": ([], ["Ideal Gas Law"]),
    "Gibbs Free Energy": ([], ["First Law of Thermodynamics", "Second Law of Thermodynamics"]),
    "Reaction Isotherm": ([], ["Gibbs Free Energy"]),
    "Van 't Hoff Equation": ([], ["Reaction Isotherm"]),
    "Arrhenius Equation": ([], ["Boltzmann Distribution"]),
    "Eyring Equation": ([], ["Arrhenius Equation"]),
    "Young's Modulus": ([], ["Hooke's Law"]),
    "Griffith Fracture Criterion": ([], ["Young's Modulus"]),
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
