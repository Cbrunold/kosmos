"""Correct glossary aliases that trace the wrong sense of a word.

The tracer matches whole words, so an alias is only as good as its rarity. A few
have turned out to be ordinary English and pulled in pages that have nothing to
do with the term. sync_rows in seed_glossary.py deliberately never overwrites a
populated field — that is what protects hand edits — so a correction needs its
own pass. This is it.

Each entry records what the alias was matching, because the reasoning is the
part worth keeping: the numbers are easy to re-derive, the judgement is not.

Idempotent: writes only where the stored value differs from the wanted one.
Run on the VPS:  ./deploy.sh fix_glossary_aliases
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_glossary import find_ds, TITLE  # noqa: E402
from seed_theories import call, query_all, title_of  # noqa: E402

# term -> (corrected alias string, why)
FIXES = {
    "Cut angle": ("",
        "'cut' added 14 entities and 12 were the ordinary verb — Forging, Sharpening "
        "an Edge, Tapping a Thread, Chicago Pile-1, Cigar Lake, 'the area cut from a "
        "sphere', 'laminations to cut eddy currents'. The bare term already finds the "
        "billiards pages that name a cut angle."),
    "Curvature": ("curved",
        "'curve' added 14 and 13 were plot curves — a bell curve, a cooling curve, a "
        "p-V curve, galaxy rotation curves. Only 'space curves closed' was curvature. "
        "The bare term finds the Einstein Field Equations, the FLRW metric, both "
        "Friedmann equations and the geodesic equation on its own."),
}


def main():
    ds = find_ds(TITLE)
    if not ds:
        sys.exit(f"{TITLE} not found")
    pages = {title_of(p, "Term"): p for p in query_all(ds) if title_of(p, "Term")}
    fixed = 0
    for term, (want, why) in FIXES.items():
        page = pages.get(term)
        if not page:
            print(f"  ! no term named {term!r}")
            continue
        cur = "".join(x.get("plain_text", "") for x in
                      (page["properties"].get("Aliases") or {}).get("rich_text", []))
        if cur == want:
            continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {"Aliases": ({"rich_text": [{"type": "text", "text": {"content": want}}]}
                                         if want else {"rich_text": []})}})
        print(f"  {term}: {cur!r} -> {want!r}\n      {why}")
        fixed += 1
    print(f"aliases: {fixed} corrected, {len(FIXES)} defined")


if __name__ == "__main__":
    main()
