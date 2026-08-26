"""Domain pass over the Cosmology and General Relativity equations.

The formulas were all correct — both Friedmann equations, the fluid equation,
FLRW, critical density, redshift, the field equations, Einstein–Hilbert,
the geodesic equation, Lifshitz growth. What was wrong was around them.

  1. The Einstein–Hilbert action said "varying S yields the field equations".
     Varying it alone yields the *vacuum* equations; T_μν appears only when the
     matter action is added. On a page that decodes symbols one by one, that is
     the whole content of the entry.
  2. It also stated as fact that Hilbert reached the field equations days
     before Einstein. The proof sheets found in 1997 show the explicit
     equations were not in his November submission, and he credited Einstein.
     Stating the priority claim flatly is a well-known trap.
  3. The field equations decoded G_μν as "spacetime curvature". G_μν is the
     Einstein tensor — Ricci curvature with its trace removed — and the reason
     it is *that* combination is that its divergence vanishes identically,
     which is what lets it sit opposite a conserved T_μν.
  4. Dark energy was quoted at w = −1.03 ± 0.03, "maddeningly consistent with
     a plain cosmological constant". That is the Planck 2018 combination, and
     the baryon-acoustic-oscillation surveys since have pulled the other way.
     Left as it was, it reads as a page that stopped reading in 2018.
  5. GPS clocks were said to gain 45 microseconds a day. That is the
     gravitational term alone — correct for this equation and confusing beside
     the net 38 that GPS actually corrects for, so both are named now.
  6. The critical density is quoted at 8.5 × 10⁻²⁷ kg/m³, which is H₀ ≈ 67;
     Hubble's Law on the same page says about 70. Both are defensible and the
     page should say which it used.

And the Requires graph, which /equations advertises as "the full path down to
the foundations": the Friedmann equations, the fluid equation, critical
density and perturbation growth had *no* prerequisites at all, while the three
GR entries required "Curvature" — the Vectors & Geometry entry for κ = 1/R,
the curvature of a plane curve. That is not what curves in general relativity.
This adds the Riemann curvature tensor and wires the block onto it.

Cosmological Redshift required "Doppler Effect", which contradicts the entry's
own first sentence — that the shift is not a Doppler shift. It requires the
FLRW metric instead; Doppler stays a Related link, where it belongs.

Guarded on the superseded wording, so a hand edit in Notion wins. Idempotent.
Run on the VPS:  ./deploy.sh fix_cosmology_equations link_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, chunks, ensure_props, query_all, sync_rows, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

# name, equation, field, named after, symbols, significance, year
NEW = [
    ("Riemann Curvature Tensor",
     "R^ρ_σμν = ∂_μΓ^ρ_νσ − ∂_νΓ^ρ_μσ + Γ^ρ_μλΓ^λ_νσ − Γ^ρ_νλΓ^λ_μσ",
     "General Relativity", "Bernhard Riemann",
     "R^ρ_σμν the curvature tensor · Γ the Christoffel symbols, built from the metric and its first "
     "derivatives · ∂_μ partial derivative along coordinate μ · the tensor vanishes everywhere if and only "
     "if spacetime is flat",
     "What it means for spacetime to be curved, stated so that it cannot be argued away by a change of "
     "coordinates. Carry a vector around a small closed loop and it comes back rotated; this tensor is "
     "exactly that rotation per unit area, and it is zero in flat space in every coordinate system, "
     "including the accelerating ones where the Christoffel symbols are not. Contract it once and you have "
     "the Ricci tensor, again and you have the Ricci scalar — the two objects the field equations are "
     "written in. Riemann set it out in an 1854 lecture, sixty years before there was anything for it to "
     "describe.", 1854),
]

# field -> (phrase that must still be there, replacement)
EDITS = {
    "Einstein–Hilbert Action": {
        "Symbols": ("varying S yields the field equations",
                    "R the Ricci scalar, total curvature at each point · g determinant of the metric · "
                    "the integral runs over all of spacetime · varying S with respect to the metric gives "
                    "the vacuum field equations; the T_μν side appears only when the matter action is "
                    "added to it"),
        "Significance": ("Hilbert reached the field equations this way days before Einstein's own derivation",
                         "All of general relativity compressed into one thing to extremize. Vary it with "
                         "respect to the metric and the vacuum field equations fall out; add a matter "
                         "action and its variation is the stress-energy tensor, which is how any new field "
                         "is coupled to gravity at all — and why the action form is the doorway every "
                         "attempt at quantum gravity walks through. Hilbert presented a variational route "
                         "to the theory five days before Einstein's paper of 25 November 1915, and the "
                         "priority argument that grew out of it outlived both men; his surviving proof "
                         "sheets, found in 1997, do not contain the explicit field equations, and he "
                         "credited them to Einstein."),
    },
    "Einstein Field Equations": {
        "Symbols": ("G_μν spacetime curvature",
                    "G_μν the Einstein tensor — the Ricci curvature with its trace removed, which is the "
                    "one combination whose divergence vanishes identically, and therefore the only one "
                    "that can sit opposite a conserved T_μν · Λ the cosmological constant · g_μν the "
                    "metric · T_μν the stress-energy tensor: energy density, momentum flow and pressure"),
    },
    "Cosmological Equation of State": {
        "Significance": ("maddeningly consistent with a plain cosmological constant",
                         "One number per ingredient, and it decides everything. Feed w into the fluid "
                         "equation and the dilution law falls out: matter thins as a⁻³ (volume alone), "
                         "radiation as a⁻⁴ (volume plus redshift), and dark energy with w = −1 does not "
                         "thin at all — which is why the early universe was radiation-dominated, the "
                         "middle matter-dominated, and the present is being taken over by a constant. The "
                         "expansion accelerates once the *total* w falls below −1/3. Whether dark energy's "
                         "own w is exactly −1 is the open question of the subject: Planck's 2018 "
                         "combination gave −1.03 ± 0.03, indistinguishable from a cosmological constant, "
                         "and the baryon-acoustic-oscillation surveys since have pulled toward a w that "
                         "changes with time. Treat any single number here as dated."),
    },
    "Gravitational Time Dilation": {
        "Significance": ("GPS satellites' clocks gain 45 microseconds a day over yours",
                         "Clocks deeper in gravity run slower — predicted from the equivalence principle "
                         "years before the full theory existed. Not an abstraction: a GPS satellite's "
                         "clock gains about 46 microseconds a day on this term alone, loses about 7 to its "
                         "orbital speed, and the receiver in your pocket is corrected for the net 38. "
                         "Without it, positions would drift kilometres a day."),
    },
    "Critical Density": {
        "Significance": ("Today it is about 8.5 × 10⁻²⁷ kg/m³",
                         "The tipping-point density: above it space curves closed, below it open, exactly "
                         "at it flat. Today it is about 8.5 × 10⁻²⁷ kg/m³ taking H₀ = 67 km/s/Mpc — five "
                         "hydrogen atoms per cubic metre, a better vacuum than any laboratory can make, "
                         "and yet the density that decides the shape of the cosmos. Take H₀ = 73 instead "
                         "and it rises to 10 × 10⁻²⁷, which is one more way of saying the Hubble tension "
                         "is not a small argument. Measurements put the total at Ω = 1.000 ± 0.002, flat "
                         "to a fifth of a percent, which is the observation inflation was invented to "
                         "explain."),
    },
}

# Requires, set explicitly. The old value is named so a hand-edited graph wins.
REQUIRES = {
    "Einstein Field Equations": (["Curvature"], ["Riemann Curvature Tensor", "Einstein–Hilbert Action"]),
    "Geodesic Equation": (["Curvature"], ["Riemann Curvature Tensor"]),
    "FLRW Metric": (["Curvature"], ["Riemann Curvature Tensor"]),
    "First Friedmann Equation": ([], ["Einstein Field Equations", "FLRW Metric"]),
    "Second Friedmann Equation": ([], ["Einstein Field Equations", "FLRW Metric"]),
    "Cosmological Fluid Equation": ([], ["First Friedmann Equation", "First Law of Thermodynamics"]),
    "Cosmological Equation of State": ([], ["Cosmological Fluid Equation"]),
    "Critical Density": ([], ["First Friedmann Equation"]),
    "Linear Perturbation Growth": ([], ["First Friedmann Equation", "Poisson's Equation"]),
    "Hubble's Law": (["Cosmological Redshift"], ["First Friedmann Equation", "Cosmological Redshift"]),
    "Cosmological Redshift": (["Doppler Effect"], ["FLRW Metric"]),
    "Gravitational Time Dilation": ([], ["Einstein Field Equations"]),
}


def text_of(page, prop):
    return "".join(x["plain_text"] for x in page["properties"].get(prop, {}).get("rich_text", []))


def main():
    print("new equations")
    schema = ensure_props(EQ_DS, {}, "equations")
    sync_rows(EQ_DS, schema,
              [{"Name": n, "Equation": e, "Field": f, "Named After": na, "Symbols": sy,
                "Significance": sig, "Year": y} for n, e, f, na, sy, sig, y in NEW], "equations")

    pages = {}
    for attempt in range(6):                      # Notion indexes a new row late
        pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
        missing = [n for n, *_ in NEW if n not in pages]
        if not missing:
            break
        print(f"  waiting for Notion to index {', '.join(missing)}")
        __import__("time").sleep(2 * (attempt + 1))
    else:
        sys.exit(f"  not indexed, refusing to half-wire the graph: {missing}")

    print("\ntext")
    for name, props in EDITS.items():
        page = pages.get(name)
        if not page:
            print(f"  {name}: not found"); continue
        payload = {}
        for prop, (old, new) in props.items():
            if old in text_of(page, prop):
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
