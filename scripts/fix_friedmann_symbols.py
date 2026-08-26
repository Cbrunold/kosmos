"""One-off: give the two Friedmann equations their own symbol lists.

Both carried the same generic decode, so /equations explained ä and p under the
first Friedmann equation — which contains neither — and k under the second,
which contains that neither. Anyone who reads cosmology would see it at once.

Found by scripts/check_content.py, which fails the build on two equations
sharing a Symbols string and on a symbol decoded that the formula does not
contain. Those two rules stay on after this, so it cannot come back quietly.

The equations themselves are correct and are not touched. Guarded on the old
shared text, so a hand edit in Notion wins. Safe to re-run.
Run on the VPS:  ./deploy.sh fix_friedmann_symbols
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, chunks, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

SHARED = "a scale factor of the universe · ȧ, ä its first and second time derivatives"

WANT = {
    "First Friedmann Equation":
        "a the scale factor of the universe · ȧ its rate of change · H = ȧ/a the Hubble parameter · "
        "G gravitational constant · ρ the total energy density, matter and radiation together · "
        "k spatial curvature (−1 open, 0 flat, +1 closed) · Λ the cosmological constant · c speed of light",
    "Second Friedmann Equation":
        "a the scale factor of the universe · ä its second time derivative, the acceleration of the "
        "expansion · G gravitational constant · ρ energy density · p pressure — it is the 3p term that "
        "makes radiation slow the expansion harder than matter does, and a negative enough p that "
        "reverses the sign · Λ the cosmological constant · c speed of light",
}


def main():
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
    for name, sym in WANT.items():
        page = pages.get(name)
        if not page:
            print(f"  {name}: not found"); continue
        cur = "".join(x["plain_text"] for x in page["properties"].get("Symbols", {}).get("rich_text", []))
        if SHARED not in cur:
            print(f"  {name}: already rewritten, left alone"); continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {"Symbols": {"rich_text": chunks(sym)}}})
        print(f"  {name}: Symbols rewritten")


if __name__ == "__main__":
    main()
