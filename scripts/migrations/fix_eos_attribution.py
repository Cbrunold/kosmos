"""Blank the Cosmological Equation of State's attribution.

It was credited to "Georges Lemaître · Howard Robertson". The dilution law
ρ ∝ a^(−3(1+w)) does follow from the fluid equation Lemaître had in 1927, so the
1933 year is defensible and stays — but w itself, as a parameter you quote a
number for, is a later convention that came in with quintessence in the 1990s,
and no source I could find puts either name on it. Where the provenance is not
known, the site's rule is that blank renders as a dash and that is correct;
inventing a plausible pair of names is the failure mode this whole review has
been about.

54 of the 217 equations already carry no Named After — the shelf's own
convention for a result nobody in particular is named for — and /equations
simply omits the line rather than printing an empty one.

A sentence goes into the significance to say why it is blank, so the gap reads
as a decision rather than an oversight. No seed script defines this row, so
nothing will quietly refill the field on the next run.

Guarded on the old value. Idempotent.
Run on the VPS:  ./deploy.sh fix_eos_attribution
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

NAME = "Cosmological Equation of State"
OLD_ATTRIB = "Georges Lemaître · Howard Robertson"
OLD_SIG = "Treat any single number here as dated."
NEW_SIG = (
    "One number per ingredient, and it decides everything. Feed w into the fluid equation and the "
    "dilution law falls out: matter thins as a⁻³ (volume alone), radiation as a⁻⁴ (volume plus "
    "redshift), and dark energy with w = −1 does not thin at all — which is why the early universe was "
    "radiation-dominated, the middle matter-dominated, and the present is being taken over by a "
    "constant. The expansion accelerates once the total w falls below −1/3. Whether dark energy's own w "
    "is exactly −1 is the open question of the subject: Planck's 2018 combination gave −1.03 ± 0.03, "
    "indistinguishable from a cosmological constant, and the baryon-acoustic-oscillation surveys since "
    "have pulled toward a w that changes with time. Treat any single number here as dated. The relation "
    "is Lemaître's, from the fluid equation of 1927; w as a parameter one quotes a value for is a much "
    "later convention, which is why no name sits on this entry."
)


def text_of(page, prop):
    return "".join(x["plain_text"] for x in page["properties"].get(prop, {}).get("rich_text", []))


def main():
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
    page = pages.get(NAME)
    if not page:
        sys.exit(f"  {NAME}: not found")

    payload = {}
    if text_of(page, "Named After").strip() == OLD_ATTRIB:
        payload["Named After"] = {"rich_text": []}
    else:
        print("  Named After: already blank or hand-edited, left alone")

    sig = text_of(page, "Significance")
    if OLD_SIG in sig and sig.strip() != NEW_SIG.strip():
        payload["Significance"] = {"rich_text": chunks(NEW_SIG)}
    else:
        print("  Significance: already rewritten, left alone")

    if payload:
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
        print(f"  {NAME}: {', '.join(sorted(payload))} updated")


if __name__ == "__main__":
    main()
