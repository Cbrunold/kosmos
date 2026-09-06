"""One-off: correct the throw advice in two Cue sports skills already seeded.

seed_billiards shipped "aim a hair fuller" for cut-induced throw. Wrong way round:
friction drags the object ball toward the cue ball's line, so the shot plays fuller
than aimed and the correction is to aim thinner. sync_rows never overwrites a filled
field (a human may have edited it), so this rewrites the two Steps fields explicitly,
and only if they still contain the wrong sentence. Safe to re-run; does nothing after
the first time. The seed's own text is corrected too, for a fresh database.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # scripts/, one up from migrations/
from seed_theories import call, query_all, title_of  # noqa: E402
from seed_billiards import SKILLS, SKILLS_DS  # noqa: E402

WRONG = {
    "The Cut Shot": "aim a hair fuller than the geometry says",
    "Using Side": "then aim a touch thicker for the throw",
}


def main():
    want = {s[0]: s[6] for s in SKILLS}          # name -> corrected Steps text
    pages = {title_of(p, "Name"): p for p in query_all(SKILLS_DS) if title_of(p, "Name")}
    for name, bad in WRONG.items():
        page = pages.get(name)
        if not page:
            print(f"  {name}: not found"); continue
        cur = "".join(x["plain_text"] for x in page["properties"].get("Steps", {}).get("rich_text", []))
        if bad not in cur:
            print(f"  {name}: already correct"); continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {"Steps": {"rich_text": [{"text": {"content": want[name]}}]}}})
        print(f"  {name}: Steps rewritten")


if __name__ == "__main__":
    main()
