"""Domain pass over the Waves & Optics and Electromagnetism equations.

Fifteen entries. The four Maxwell equations, the Lorentz force and the
transformer are in good order and untouched, as are Snell (correctly credited
to Ibn Sahl in 984, not just to Snellius), Bragg, the thin lens, the
inverse-square law and the refractive index — whose numbers check out: glass
slows light by a third, water by a quarter, diamond by 2.4. Wave Speed's do
too: 440 Hz really is 78 cm of air, green light really is 5.5 × 10¹⁴ Hz.

Three things needed correcting.

  1. The Rayleigh Criterion said diffraction is "why JWST sees sharper in the
     infrared than Hubble does only because it is larger". JWST does not see
     sharper than Hubble. At 2 μm through 6.5 m it resolves about 0.077″;
     Hubble at 500 nm through 2.4 m manages 0.052″. Working four times redder
     costs a factor of four, and less than three times the aperture does not
     buy it back — JWST would need a 9.6 m mirror to match Hubble's angular
     resolution. What the infrared buys is dust penetration and redshifted
     light, not sharpness, and saying otherwise on a site with a /cosmos page
     is the kind of thing that gets noticed.

  2. The same entry *required* the Diffraction Grating Equation. The 1.22 is
     the first dark ring of the Airy pattern of a circular aperture, which is
     single-aperture diffraction; a grating is many-slit interference and a
     different phenomenon with a different constant. Fourth instance of this
     pattern in five passes. The entry now says where 1.22 comes from, which
     it never did — and a proper Airy-pattern entry is the missing row here,
     left for a decision rather than invented in passing.

  3. The grating equation itself required the Small-Angle Approximation, and a
     grating is the one optical instrument that specifically does not work in
     the small-angle limit: the whole point is to fling orders out to large
     angles where the dispersion is.

Also: Standing Waves gave f_n = n v / 2L for "the string or the pipe". True of
a string, and of a pipe open at both ends; a pipe stopped at one end goes as
n v / 4L with odd n only, which is why a clarinet overblows a twelfth and a
flute an octave. Stated now.

Guarded on the superseded wording. Idempotent.
Run on the VPS:  ./deploy.sh fix_optics_em_equations
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

EDITS = {
    "Rayleigh Criterion": {
        "Significance": ("why JWST sees sharper in the infrared than Hubble does only because it is larger",
                         "The finest detail any telescope, microscope or eye can resolve is set by "
                         "wavelength over aperture — diffraction, not workmanship, is the floor. The 1.22 "
                         "is the first dark ring of the Airy pattern that a circular aperture makes; a "
                         "slit or a square would carry a different constant. It is why telescopes are "
                         "big, why radio dishes are enormous and then combined into interferometers to "
                         "fake a bigger one, and why no visible-light microscope will ever show an atom. "
                         "It is also why JWST is not sharper than Hubble: working at 2 μm instead of "
                         "500 nm costs a factor of four, and 6.5 m of mirror against 2.4 m buys back less "
                         "than three, so JWST resolves about 0.08″ where Hubble manages 0.05″ and would "
                         "need a 9.6 m mirror to match it. What the infrared buys is not sharpness — it "
                         "is seeing through dust, and seeing light so redshifted that Hubble cannot see "
                         "it at all."),
    },
    "Standing Waves": {
        "Equation": ("f_n = n v / (2L)  (n = 1, 2, 3…)",
                     "f_n = n v / (2L),  n = 1, 2, 3…   (stopped pipe: f_n = n v / (4L), odd n only)"),
        "Significance": ("Sauveur named the harmonics in 1701.",
                         "Confine a wave and only those wavelengths that fit — a whole number of "
                         "half-waves — survive; the rest cancel. That is why a string, a pipe and a laser "
                         "cavity have a fundamental and overtones, why a bridge has modes, and why an "
                         "electron in an atom has discrete energies. A pipe stopped at one end fits "
                         "quarter-waves instead and keeps only the odd harmonics, which is why a "
                         "clarinet overblows a twelfth where a flute overblows an octave, and why it "
                         "sounds an octave lower than its length suggests. Sauveur named the harmonics "
                         "in 1701."),
    },
}

REQUIRES = {
    "Rayleigh Criterion": (["Diffraction Grating Equation", "Small-Angle Approximation"],
                           ["Small-Angle Approximation", "Wave Speed"]),
    "Diffraction Grating Equation": (["Trigonometric Ratios", "Small-Angle Approximation", "Wave Speed"],
                                     ["Trigonometric Ratios", "Wave Speed"]),
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
