"""Domain pass over the twenty-eight small fields — 84 equations, 3 or 4 apiece.

I expected the highest hit rate of any pass here, on the theory that each of
these was written in one sitting and never revisited. Wrong: they are the best
material on the shelf. Every number I could check held — Wien puts a 5,800 K
Sun at 500 nm and the 2.7 K background at a millimetre, Newton's isothermal
sound speed really is 15 % slow, the proton's electric force really is 10³⁶
times its weight, Feigenbaum's cascade really does accumulate at 3.5699,
Mars windows really are 26 months, and every "N years later" arithmetic in
the historical asides is right. Five things needed correcting.

  1. The Standard Model Lagrangian ended "Nothing it predicts has yet been
     caught being wrong." Neutrino masses. The model as written has them
     massless, and oscillation experiments settled otherwise in 1998. It is
     the one confirmed crack and the entry should be the place that says so.

  2. Its Symbols read "line 1: … line 2: … line 3: … line 4:" — the mug
     version has four lines, but the equation as stored here is one, so the
     decode pointed at a layout the reader could not see. Named by symbol now.

  3. The Doppler Effect said the same effect "applied to light" is "how Hubble
     read the expansion of the universe from galaxy redshifts". Cosmological
     Redshift, two fields away, opens by saying that is exactly what it is
     not. Both cannot stand. Hubble did read them as recession velocities, so
     the history survives; the physics is now stated the same way in both.

  4. The Heat Equation said Kelvin's age of the Earth was wrong "only because
     he didn't know about radioactivity". That is the popular version. His own
     former assistant John Perry showed in 1895 that a convecting interior
     alone stretches the answer by the factor required — the wrong model
     rather than a missing heat source.

  5. Planck–Einstein Relation was attributed to Planck alone, on an entry
     named for both of them.

And a currency note on the Lawson Criterion, after the dark-energy lesson from
the cosmology pass: it said the race continues, which is true of net facility
power and became misleading once the National Ignition Facility passed target
gain in December 2022. Both facts now.

Not changed, deliberately: "Mass–energy equivalence" is the shelf's only
title-case outlier, and its name is a key in four cross-link maps across
seed_timeline, link_equations and seed_engineering. The slug would not change,
so nothing would break for a reader — but it is a cosmetic edit with a real
blast radius, and it should be a decision rather than a side effect.
(Decided afterwards: done in fix_mass_energy_name.py, with all fifteen
references across seven scripts moved in the same commit.)

Guarded on the superseded wording. Idempotent.
Run on the VPS:  ./deploy.sh fix_small_fields_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

EDITS = {
    "Standard Model Lagrangian": {
        "Symbols": ("line 1: the force fields",
                    "F_μν the force fields — photon, W, Z and the gluons · ψ the matter fields, quarks "
                    "and leptons, in motion · yᵢⱼ the Yukawa couplings: matter meeting the Higgs and "
                    "taking mass from it · φ the Higgs field itself, shaped by its potential · D_μ the "
                    "covariant derivative, which is where the forces actually enter · h.c. the Hermitian "
                    "conjugate. Compact notation throughout — written out, it runs to pages"),
        "Significance": ("Nothing it predicts has yet been caught being wrong.",
                         "Every known particle and every force except gravity, in one very compressed "
                         "expression — the equation on CERN's coffee mugs. Assembled through the 1960s "
                         "and 70s out of electroweak unification and quantum chromodynamics; its last "
                         "missing piece, the Higgs boson, arrived in 2012. It is not unblemished: "
                         "neutrinos have mass, which the model as written forbids, and the oscillation "
                         "experiments that proved it in 1998 are the one confirmed crack in it. "
                         "Everything else it has predicted has so far survived every test aimed at it."),
    },
    "Doppler Effect": {
        "Significance": ("how Hubble read the expansion of the universe from galaxy redshifts",
                         "Motion squeezes waves ahead and stretches them behind — the siren that drops "
                         "in pitch as it passes. The same effect in light is how a radar gun catches a "
                         "speeder, how a star's wobble betrays an orbiting planet, and how Slipher and "
                         "Hubble first read the galaxy redshifts, as recession velocities. That last "
                         "reading is the useful approximation rather than the mechanism: a cosmological "
                         "redshift is space expanding underneath the light while it travels, not motion "
                         "through space."),
    },
    "Heat Equation": {
        "Significance": ("got it wrong only because he didn't know about radioactivity",
                         "Temperature smooths itself out: peaks flatten, dips fill, at a rate set by the "
                         "local curvature. Fourier invented his transform to solve exactly this, and the "
                         "same equation under other names governs diffusion, option prices "
                         "(Black–Scholes) and image blurring. Kelvin used it to date the Earth at twenty "
                         "to forty million years and was wrong — though not only for the reason usually "
                         "given. Radioactivity was indeed undiscovered, but his own former assistant "
                         "John Perry showed in 1895 that a convecting interior alone stretches the "
                         "answer by the factor needed. Conduction was the wrong model, not merely the "
                         "wrong number."),
    },
    "Planck–Einstein Relation": {
        "Named After": ("Max Planck", "Max Planck · Albert Einstein"),
    },
    "Lawson Criterion": {
        "Significance": ("seven decades on, the race against this one inequality continues",
                         "The finish line for fusion power: hold a plasma dense enough, hot enough, long "
                         "enough — achieve any two and the third gets you. Tokamaks chase confinement "
                         "time, laser fusion chases density. In December 2022 the National Ignition "
                         "Facility crossed it far enough to get more fusion energy out of the capsule "
                         "than the laser delivered to it, the first target gain above one; the facility "
                         "as a whole still draws far more from the wall than the shot returns, so the "
                         "race that matters is not over."),
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
            cur = text_of(page, prop)
            if old in cur and cur.strip() != new.strip():
                payload[prop] = {"rich_text": chunks(new)}
            else:
                print(f"  {name} · {prop}: already rewritten, left alone")
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
            print(f"  {name}: {', '.join(sorted(payload))} rewritten")


if __name__ == "__main__":
    main()
