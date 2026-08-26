"""Retitle "Mass–energy equivalence" to "Mass–Energy Equivalence".

The shelf's only title-case outlier — every other one of the 217 is Title Case,
and the one apparent exception, "Van der Waals Equation", is correct Dutch.

The slug does not move: slugify lower-cases before it hyphenates, so
/equations#mass-energy-equivalence and every deep link into it survive. What
does move is the title as a *key*: fifteen cross-link maps across seven seed
and link scripts name this equation by its title, and a rename without them is
fifteen relations that silently stop being drawn. They go in the same commit.

The French cache is keyed by the sha1 of the English, so the rename orphans
its translation. 'Équivalence masse–énergie' is carried over to the new key by
hand rather than paid for again; translate.py prunes the stale entry on its
next run.

Guarded: renames only if the title is still the old one. Idempotent.
Run on the VPS:  ./deploy.sh fix_mass_energy_name
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, query_all, title_of  # noqa: E402
from seed_engineering import EQ_DS  # noqa: E402

OLD = "Mass–energy equivalence"
NEW = "Mass–Energy Equivalence"


def main():
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
    if NEW in pages:
        print(f"  already titled {NEW!r}")
        return
    page = pages.get(OLD)
    if not page:
        sys.exit(f"  neither {OLD!r} nor {NEW!r} found — refusing to guess")
    call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
         {"properties": {"Name": {"title": [{"text": {"content": NEW}}]}}})
    print(f"  {OLD!r} -> {NEW!r}")


if __name__ == "__main__":
    main()
