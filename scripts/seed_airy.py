"""Add the Airy diffraction pattern — the row the optics shelf was missing.

The Rayleigh Criterion carries a 1.22 and, until the optics pass, required the
Diffraction Grating Equation for it. That was wrong twice over: a grating is
many-slit interference, and the 1.22 is not a grating number at all. It is the
first zero of the first-order Bessel function, 3.8317, divided by π — the first
dark ring of the pattern a *circular* aperture makes. A slit gives sin x / x and
a first zero at exactly 1.00 λ/D; the circle's 1.22 is the price of being round.

That row did not exist, so the optics pass left Rayleigh requiring the
small-angle approximation and the wave relation and said in its prose where
1.22 comes from. This adds the equation itself and puts Rayleigh on top of it.

Its own prerequisite is the Fourier Transform, which is the real content: a
far-field diffraction pattern is the Fourier transform of the aperture, and the
Airy pattern is what you get when you transform a disc.

Idempotent — sync_rows inserts only if missing and backfills only empty fields.
Run on the VPS:  ./deploy.sh seed_airy link_equations
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, query_all, sync_rows, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

# name, equation, field, named after, symbols, significance, year
AIRY = [
    ("Airy Diffraction Pattern",
     "I(θ) = I₀·[2J₁(x)/x]²,  x = πD sin θ / λ;  first zero at x = 3.8317 ⇒ sin θ = 1.22 λ/D",
     "Waves & Optics", "George Biddell Airy",
     "I(θ) intensity at angle θ from the axis · I₀ the intensity at the centre · J₁ the first-order "
     "Bessel function · D the aperture diameter · λ the wavelength · x = πD sin θ/λ · the first zero of "
     "J₁ lands at x = 3.8317, and 3.8317/π = 1.2197 — which is the 1.22 in Rayleigh's criterion",
     "A circular aperture cannot make a point. It makes a bright disc ringed by faint ones, and every "
     "star in every telescope image is this pattern rather than a star. About 84 % of the light lands in "
     "the central disc, the rest in the rings, and the first dark ring sits at 1.22 λ/D — a number that "
     "is not a fudge factor but the first zero of a Bessel function divided by π. The shape of the hole "
     "sets the constant: a long slit gives sin x / x and its first zero at exactly 1.00 λ/D, a square "
     "aperture the same, and only the circle pays 1.22 for being round. Airy worked it out in 1835 for "
     "telescope object-glasses, forty-four years before Rayleigh turned it into a rule for when two "
     "stars are two.", 1835),
]

REQUIRES = {
    "Airy Diffraction Pattern": ([], ["Fourier Transform", "Wave Speed"]),
    "Rayleigh Criterion": (["Small-Angle Approximation", "Wave Speed"],
                           ["Airy Diffraction Pattern", "Small-Angle Approximation"]),
}


def main():
    print("airy")
    schema = ensure_props(EQ_DS, {}, "equations")
    sync_rows(EQ_DS, schema,
              [{"Name": n, "Equation": e, "Field": f, "Named After": na, "Symbols": sy,
                "Significance": sig, "Year": y} for n, e, f, na, sy, sig, y in AIRY], "equations")

    pages = {}
    for attempt in range(6):                      # Notion indexes a new row late
        pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
        missing = [n for n, *_ in AIRY if n not in pages]
        if not missing:
            break
        print(f"  waiting for Notion to index {', '.join(missing)}")
        time.sleep(2 * (attempt + 1))
    else:
        sys.exit(f"  not indexed, refusing to half-wire the graph: {missing}")

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
