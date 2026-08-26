"""Domain pass over the Fluid Dynamics equations.

Sixteen entries. Fourteen are sound and untouched, and the numbers in them
check out: a hundred metres of head at a cubic metre a second really is about
a megawatt, water's viscosity really is about fifty times air's, halving a bore
really does cut Poiseuille flow to a sixteenth, and the Betz ceiling quoted
here agrees with the one on the Wind Turbine machine card. Two did not.

  1. Bernoulli's Equation said it is "why airplane wings lift". That is the
     most-corrected sentence in fluid dynamics. The popular version behind it
     has air taking equal time over a longer upper surface, which is not what
     air does; lift comes from circulation and from the mass of air the wing
     turns downward. Bernoulli holds over a wing — the pressure on top really
     is lower — but it describes the flow rather than causing it, and there
     are better examples of what it does explain, so the entry uses those.

  2. The Betz Limit *required* the Drag Equation. Betz's argument is an
     actuator disc: mass in equals mass out, the thrust is the momentum the
     stream loses, and the power is the kinetic energy it loses. There is no
     drag coefficient anywhere in it — no aerodynamics at all, which is
     precisely why the limit binds whatever the blade looks like. It requires
     conservation of momentum instead, and the significance now says why that
     matters, because "16/27 regardless of blade design" is the interesting
     part and the entry did not explain where it comes from.

This is the third prerequisite in four passes that contradicted the entry it
sat under, after Cosmological Redshift ← Doppler Effect and Schwarzschild
Radius ← Escape Velocity. The pattern is consistent enough to be worth a rule,
but it needs a person to see it: all three are defensible-looking edges that
happen to be the exact misconception the entry warns against.

Guarded on the superseded wording. Idempotent.
Run on the VPS:  ./deploy.sh fix_fluids_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

EDITS = {
    "Bernoulli's Equation": {
        "Significance": ("Why airplane wings lift, carburetors draw fuel, and a shower curtain billows inward.",
                         "Where a fluid speeds up along a streamline its pressure drops — energy "
                         "bookkeeping for steady, frictionless, incompressible flow. It is why a "
                         "carburettor and a scent atomiser draw liquid up into a fast stream, why a "
                         "Venturi meter reads a flow rate from nothing but a pressure difference, why a "
                         "roof lifts off in a gale rather than being pushed in, and why two ships running "
                         "close alongside are drawn together. What it is not is the reason a wing lifts. "
                         "The popular account has air taking equal time over a longer upper surface, "
                         "which is not what air does; lift is circulation, and the mass of air the wing "
                         "throws downward. Bernoulli holds perfectly well over a wing — the pressure on "
                         "top really is lower — but it is describing the flow, not causing it."),
    },
    "Betz Limit": {
        "Significance": ("the improvements now are in size and reliability, not the physics",
                         "No turbine can take more than 59.3 % of the energy in the wind passing through "
                         "it, because air that had given up all its energy would stop and block the "
                         "rotor. What makes the number worth knowing is how little goes into it: Betz "
                         "treats the rotor as an actuator disc and does nothing but bookkeeping — mass in "
                         "equals mass out, thrust is the momentum the stream loses, power is the kinetic "
                         "energy it loses — with no aerofoil, no drag coefficient and no blade count "
                         "anywhere in the derivation. That is why 16/27 binds every design ever proposed. "
                         "Good modern turbines reach 45–50 %, close enough to the ceiling that the "
                         "improvements now are in size and reliability, not the physics."),
    },
}

REQUIRES = {
    "Betz Limit": (["Continuity Equation", "Kinetic Energy", "Drag Equation"],
                   ["Continuity Equation", "Kinetic Energy", "Conservation of Momentum"]),
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
