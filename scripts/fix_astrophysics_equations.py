"""Domain pass over the Astrophysics equations.

Four entries, read line by line. Saha is excellent and untouched — the
recombination argument in it (3,000 K rather than the 158,000 K that 13.6 eV
implies, because photons outnumber baryons a billion to one) is the good
version of that explanation. The three others each had something.

  1. Stefan–Boltzmann was stated only as L = 4πR²σT⁴. That is the law applied
     to a sphere, not the law: it is F = σT⁴, power per unit area, and the
     stellar form is one use of it. The distinction became load-bearing when
     the Forging skill was linked to this entry — what a bar of steel at
     1,200 °C does is the flux form, and the entry did not contain it. Both
     forms now, plus the two caveats that matter: T is an effective
     temperature, and a real surface radiates εF.
  2. Chandrasekhar said Type Ia supernovae "all detonate at the same mass and
     make trustworthy cosmic distance markers". That is the textbook picture
     of thirty years ago. They are standard*isable* — the Phillips relation
     corrects luminosity against light-curve width — and the single-degenerate
     route to the Chandrasekhar mass is no longer the only channel on the
     table, with sub-Chandrasekhar double detonations taken seriously. The
     limit still sets the scale; it does not make them identical.
  3. Schwarzschild Radius *required* Escape Velocity. Setting the Newtonian
     escape speed to c gives 2GM/c² by an arithmetic coincidence that misled
     people for two centuries — Michell's dark stars — and the entry's own
     text says it was derived from the field equations. Same defect as
     Cosmological Redshift requiring the Doppler Effect: a prerequisite that
     contradicts the sentence above it. It requires the field equations;
     escape velocity stays Related, which is exactly what it is.

Saha, Chandrasekhar and Stefan–Boltzmann also had no prerequisites at all,
so /equations showed them as foundations of physics rather than consequences
of statistical mechanics, quantum degeneracy and Planck's law.

Guarded on the superseded wording. Idempotent.
Run on the VPS:  ./deploy.sh fix_astrophysics_equations link_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

EDITS = {
    "Stefan–Boltzmann Law": {
        "Equation": ("L = 4πR²σT⁴", "F = σT⁴;   L = 4πR²σT⁴ for a sphere of radius R"),
        "Symbols": ("L luminosity (power radiated) · R radius of the star",
                    "F the power radiated per unit area by a black body · σ the Stefan–Boltzmann "
                    "constant · T absolute temperature · R the radius of the star · L its luminosity, "
                    "the same law over the whole sphere · a real surface radiates εF, with emissivity "
                    "ε below 1 — about 0.8 for oxidised steel"),
        "Significance": ("With a spectrum in hand, this is how astronomers weigh a star's output across light-years.",
                         "Power radiated per unit area goes as the fourth power of temperature, so a "
                         "modestly hotter body blazes enormously brighter — and over a sphere it gives a "
                         "star's brightness from its size and temperature alone, which is how astronomers "
                         "weigh a stellar output across light-years. Two cautions travel with it. The T of "
                         "a star is an effective temperature: the temperature of the black body that would "
                         "radiate the same, not a reading from anywhere in particular. And nothing real is "
                         "a black body — multiply by emissivity, which is where the same equation stops "
                         "being about stars and starts being about why a steel bar at 1,200 °C sheds a "
                         "quarter of a megawatt from every square metre and cools while you look at it."),
    },
    "Chandrasekhar Limit": {
        "Significance": ("it's why Type Ia supernovae all detonate at the same mass and make trustworthy cosmic distance markers",
                         "Above about 1.4 solar masses, electron degeneracy pressure can no longer hold a "
                         "dead star up against its own gravity, and collapse continues to a neutron star "
                         "or a black hole. Worked out by Chandrasekhar at 19, aboard the ship carrying him "
                         "to Cambridge, and disputed for a decade by Eddington, who thought the conclusion "
                         "absurd. It sets the scale for Type Ia supernovae, which is why they can be used "
                         "as distance markers at all — but the old line that they all detonate at exactly "
                         "this mass has not survived: they are standardised after the fact, by correcting "
                         "brightness against how fast the light curve fades, and a good part of them may "
                         "come from white dwarfs that never reached the limit."),
    },
}

REQUIRES = {
    "Schwarzschild Radius": (["Escape Velocity"], ["Einstein Field Equations"]),
    "Stefan–Boltzmann Law": ([], ["Planck's Law"]),
    "Saha Ionization Equation": ([], ["Boltzmann Distribution", "Partition Function"]),
    "Chandrasekhar Limit": ([], ["Fermi–Dirac Distribution", "Heisenberg Uncertainty Principle"]),
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
