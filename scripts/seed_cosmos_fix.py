"""Close the two holes in the spectral sequence on Spectral Types [DB].

The sequence is a partition of the temperature line -- every star has exactly
one class -- so the bands have to tile it with no gap and no overlap. The check
now runs at build time in build.py:build_cosmos_page and found they did not:

  M-type Stars   "< 3,700 K" -> "2,400 - 3,700 K"

    Written with no floor, so it swallowed L, T and Y whole. A 1,000 K brown
    dwarf was simultaneously M-type and T-type according to this database.

  L-type Stars   "1,300 - 2,000 K" -> "1,300 - 2,400 K"

    Once M has a floor at 2,400 K, L's ceiling of 2,000 leaves a 400 K band
    belonging to nothing. 2,400 K is where the M/L boundary is conventionally
    drawn, so the ceiling moves rather than the floor.

Everything else on the ladder was already correct and contiguous: O above
30,000, B 10,000-30,000, A 7,500-10,000, F 6,000-7,500, G 5,200-6,000,
K 3,700-5,200, T 700-1,300, Y below 700.

Unlike sync_rows this OVERWRITES. Idempotent.
Run on the VPS:  ./deploy.sh seed_cosmos_fix
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, query_all  # noqa: E402

DS = "6128c15c-25dd-47fb-bf00-ce737ca1d3e6"      # Spectral Types [DB]

FIXES = {
    "M-type Stars": "2,400 - 3,700 K",
    "L-type Stars (L Dwarfs)": "1,300 - 2,400 K",
}


def title_of(page):
    for p in page["properties"].values():
        if p.get("type") == "title":
            return "".join(x["plain_text"] for x in p["title"]) or None
    return None


def text_of(page, prop):
    p = page["properties"].get(prop, {})
    return "".join(x["plain_text"] for x in p.get("rich_text", [])) or None


if __name__ == "__main__":
    pages = {title_of(p): p for p in query_all(DS) if title_of(p)}
    missing = [n for n in FIXES if n not in pages]
    if missing:
        sys.exit(f"rows not in the database: {missing} (have: {sorted(pages)})")

    fixed = skipped = 0
    for name, want in FIXES.items():
        page = pages[name]
        was = text_of(page, "Temperature")
        if was == want:
            skipped += 1
            print(f"  ok       {name}")
            continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {"Temperature": {"rich_text": [{"text": {"content": want}}]}}})
        fixed += 1
        print(f"  FIXED    {name} · Temperature: {was!r} -> {want!r}")
    print(f"spectral fix: {fixed} rows corrected, {skipped} already correct")
