"""Domain pass over the Mechanics and Thermodynamics equations.

Thirty-five entries read. Most are in good shape and are untouched — the
Coriolis history on Work and Kinetic Energy, Watt's 550 foot-pounds a second,
Otto at r = 9 giving 58 % (it does), Carnot's 2,000 K to 300 K giving 85 % (it
does), the Merton mean-speed rule, Noether under conservation of momentum.
Three things were wrong.

  1. Coefficient of Restitution said "head-on, kinetic energy kept = e²", and
     that a 0.92 collision leaves the object ball with 85 % of the energy.
     e² is the energy kept in the *relative* motion — the collision's own
     energy, in the centre-of-mass frame. Total kinetic energy cannot fall
     that far, because the momentum the pair carries between them cannot be
     lost: for equal balls with one at rest it is (1 + e²)/2, so 92 %, and the
     object ball leaves with 96 % of the speed and 92 % of the energy. The
     old 85 % was e² read as if it were the total.

  2. Rolling Resistance quoted μ_r ≈ 0.01 on cloth and derived a tenth of a
     metre per second per second and five metres of roll from it. The shot lab
     on /billiards runs on MU_R = 0.025 out of pool-sauce-engine's constants,
     and that page's footer says its physics comes from this shelf. Two pages
     of the same site disagreeing by a factor of 2.5 about the same constant
     is worse than either number being wrong. Matched to 0.025, with the
     deceleration and the roll distance recomputed: a quarter of a metre per
     second per second, and a little over two metres from 1 m/s.

  3. The Zeroth Law was written "T₁ = T₃ and T₂ = T₃ ⟹ T₁ = T₂", which is
     transitivity of equality and true of any three numbers. The law is about
     thermal *equilibrium* being transitive, and that is exactly what earns
     the right to write a temperature at all — as stated it assumed what it
     exists to prove.

Also: Brayton decoded "p_2/p_1" while the formula shows p_1/p_2, which is
consistent but reads like a typo; both pressures are named individually now.

Named After was empty on fourteen Mechanics entries whose prose names a
discoverer, which looked like a gap until it didn't: Work, Torque, Power,
Kinetic Energy and the rest are not eponymous, and the field is for eponyms.
Left alone.

Guarded on the superseded wording. Idempotent.
Run on the VPS:  ./deploy.sh fix_mechanics_thermo_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

EDITS = {
    "Coefficient of Restitution": {
        "Equation": ("head-on, kinetic energy kept = e²",
                     "e = v_separation / v_approach;  energy of the relative motion kept = e²"),
        "Significance": ("the object ball with 85 % of the energy",
                         "Newton's experimental law of 1687: how much of the closing speed survives a "
                         "collision. What e² measures is the energy in the relative motion — the "
                         "collision's own energy, seen from the centre of mass — and not the total, "
                         "because the momentum the pair carries between them cannot be lost. For equal "
                         "balls, one at rest, the fraction of the original kinetic energy still there "
                         "afterwards is (1 + e²)/2. Phenolic pool balls run about 0.92: the object ball "
                         "leaves with 96 % of the cue ball's speed and 92 % of its energy, the cue ball "
                         "creeps forward carrying under a fifth of a percent, and about 8 % of the energy "
                         "has gone into sound and deformation. A cushion returns roughly 0.75 of the "
                         "energy, so the ball comes off at 87 % of its speed. Steel on steel is 0.9-ish, "
                         "a superball 0.9, a lump of clay near 0. It is why the ninety-degree rule is "
                         "really eighty-eight, and why a stop shot needs a touch of draw."),
    },
    "Rolling Resistance": {
        "Symbols": ("about 0.01 on worsted cloth",
                    "d the distance a rolling ball travels before stopping · v₀ its starting speed · "
                    "μ_r rolling resistance coefficient — 0.025 on worsted cloth, the figure the shot "
                    "lab runs on, and 0.002 for a steel wheel on rail · g gravitational acceleration"),
        "Significance": ("a tenth of a metre per second per second",
                         "A rolling body loses energy slowly, to the deformation of the surface and of "
                         "the ball, and the deceleration is nearly constant at μ_r g. On a pool table "
                         "that is about a quarter of a metre per second per second, so a ball at 1 m/s "
                         "rolls a little over two metres and speed control is a matter of a few percent. "
                         "Coulomb measured rolling friction in 1781; the work–energy theorem does the "
                         "rest."),
    },
    "Zeroth Law of Thermodynamics": {
        "Equation": ("T₁ = T₃ and T₂ = T₃ ⟹ T₁ = T₂",
                     "A ⇄ C  and  B ⇄ C  ⟹  A ⇄ B      (⇄ : in thermal equilibrium)"),
        "Symbols": ("T₁, T₂, T₃ temperatures of three systems",
                    "A, B, C any three systems · ⇄ in thermal equilibrium: put them in contact and no "
                    "net heat flows · the transitivity of that relation, not of equality, is what lets a "
                    "single number stand for it"),
        "Significance": ("So foundational it was named zeroth, after the first and second were taken.",
                         "If two systems each sit in equilibrium with a third, they are in equilibrium "
                         "with each other — the quiet assumption that makes 'temperature' a well-defined "
                         "number and thermometers meaningful. Written with equals signs it is a triviality "
                         "about numbers; the content is that thermal equilibrium is transitive, which is "
                         "what earns the right to write a temperature down in the first place. So "
                         "foundational it was named zeroth, after the first and second were taken."),
    },
    "Brayton Cycle Efficiency": {
        "Symbols": ("p_2/p_1 the pressure ratio across the compressor",
                    "p_1 the pressure at the compressor inlet · p_2 at its outlet — the ratio p_2/p_1 is "
                    "what a cycle is rated by · γ ratio of specific heats"),
    },
}


def text_of(page, prop):
    return "".join(x["plain_text"] for x in page["properties"].get(prop, {}).get("rich_text", []))


def main():
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
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


if __name__ == "__main__":
    main()
