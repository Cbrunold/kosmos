"""Add a Nobel field to the Researchers DB and fill it for the laureates on file.

    ./deploy.sh seed_nobel                    # add the field, mark known laureates
    python3 scripts/seed_nobel.py --diff LIST # report which names in LIST are not researchers yet

LAUREATES marks the people already in the Researchers DB whose prizes are
certain — physics unless stated. It is a curated list, not the whole Nobel
roll, and it only ever fills an empty Nobel field. The site shows the prize
as a tag on the researcher card and offers a "Nobel laureates" filter.

--diff takes a file of names, one per line (or a CSV with a name column),
normalises them (accents, case, "J. J." vs "J.J.", "Marie Curie" vs "Curie,
Marie") and prints which are not in the Researchers DB, with near-misses so a
spelling difference is not reported as an absence. Nothing is written in
--diff mode; the report is what you use to decide who to add.
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RESEARCHER_DS = "4cc8d7c4-9008-4017-a09b-7087720aebd3"

# name -> "Physics 1921" style; multiple prizes joined with " · "
LAUREATES = {
    "Wilhelm Röntgen": "Physics 1901", "Hendrik Lorentz": "Physics 1902", "Henri Becquerel": "Physics 1903",
    "J. J. Thomson": "Physics 1906", "Ernest Rutherford": "Chemistry 1908", "Max Planck": "Physics 1918",
    "Albert Einstein": "Physics 1921", "Niels Bohr": "Physics 1922", "Louis de Broglie": "Physics 1929",
    "Werner Heisenberg": "Physics 1932", "Erwin Schrödinger": "Physics 1933", "Paul Dirac": "Physics 1933",
    "James Chadwick": "Physics 1935", "Victor Hess": "Physics 1936", "Enrico Fermi": "Physics 1938",
    "Felix Bloch": "Physics 1952", "Max Born": "Physics 1954", "John Bardeen": "Physics 1956 · Physics 1972",
    "Maria Goeppert Mayer": "Physics 1963", "Richard Feynman": "Physics 1965", "Julian Schwinger": "Physics 1965",
    "Sin-Itiro Tomonaga": "Physics 1965", "Murray Gell-Mann": "Physics 1969", "Leon Cooper": "Physics 1972",
    "Robert Schrieffer": "Physics 1972", "Andrei Sakharov": "Peace 1975", "Arno Penzias": "Physics 1978",
    "Robert Wilson": "Physics 1978", "Sheldon Glashow": "Physics 1979", "Abdus Salam": "Physics 1979",
    "Steven Weinberg": "Physics 1979", "William Fowler": "Physics 1983", "Russell Hulse": "Physics 1993",
    "Joseph Taylor": "Physics 1993", "Gerard 't Hooft": "Physics 1999", "David Gross": "Physics 2004",
    "Frank Wilczek": "Physics 2004", "George Smoot": "Physics 2006", "Saul Perlmutter": "Physics 2011",
    "Brian Schmidt": "Physics 2011", "Adam Riess": "Physics 2011", "François Englert": "Physics 2013",
    "Peter Higgs": "Physics 2013", "Rainer Weiss": "Physics 2017", "Barry Barish": "Physics 2017",
    "Kip Thorne": "Physics 2017", "James Peebles": "Physics 2019", "Michel Mayor": "Physics 2019",
    "Didier Queloz": "Physics 2019", "M. Stanley Whittingham": "Chemistry 2019", "John Goodenough": "Chemistry 2019",
    "Akira Yoshino": "Chemistry 2019", "Roger Penrose": "Physics 2020",
}


def norm(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    if "," in s:                                     # "Curie, Marie" -> "marie curie"
        last, first = s.split(",", 1)
        s = f"{first} {last}"
    s = re.sub(r"\b([a-z])\.\s*", r"\1 ", s)         # "j.j. thomson" -> "j j thomson"
    s = re.sub(r"[^a-z ]+", " ", s)
    return " ".join(s.split())


def surname(n: str) -> str:
    parts = n.split()
    return parts[-1] if parts else n


def diff(path: str):
    els = json.load(open(ROOT / "data" / "notion-all.json"))
    have = {r["Name"] for r in els["researchers"] if r.get("Name")}
    have_n = {norm(n): n for n in have}
    by_sur = {}
    for n in have:
        by_sur.setdefault(surname(norm(n)), []).append(n)
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    names = []
    if path.lower().endswith(".csv"):
        rows = list(csv.reader(text.splitlines()))
        head = [h.strip().lower() for h in rows[0]] if rows else []
        col = next((i for i, h in enumerate(head) if h in ("name", "laureate", "full name", "fullname")), 0)
        names = [r[col].strip() for r in rows[1:] if len(r) > col and r[col].strip()]
    else:
        names = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    present, missing, near = [], [], []
    for n in names:
        k = norm(n)
        if k in have_n:
            present.append((n, have_n[k]))
            continue
        cands = by_sur.get(surname(k), [])
        if cands:
            near.append((n, cands))
        else:
            missing.append(n)
    print(f"{len(names)} names in {path}: {len(present)} already researchers, {len(near)} probable spelling variants, {len(missing)} missing")
    if near:
        print("\nprobably present under another spelling (check by hand):")
        for n, c in near:
            print(f"  {n}  ~  {', '.join(c)}")
    if missing:
        print("\nnot in the Researchers DB:")
        for n in missing:
            print("  " + n)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--diff":
        diff(sys.argv[2])
        return
    from seed_theories import call, ensure_props, query_all, title_of  # lazy: needs the token
    schema = ensure_props(RESEARCHER_DS, {"Nobel": {"rich_text": {}}}, "researchers")
    pages = {title_of(p, "Name"): p for p in query_all(RESEARCHER_DS) if title_of(p, "Name")}
    filled = skipped = missing = 0
    for name, prize in LAUREATES.items():
        page = pages.get(name)
        if not page:
            missing += 1
            print("  not in Researchers DB:", name)
            continue
        cur = "".join(x["plain_text"] for x in (page["properties"].get("Nobel") or {}).get("rich_text", [])).strip()
        if cur:
            skipped += 1
            continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {"Nobel": {"rich_text": [{"text": {"content": prize}}]}}})
        filled += 1
    print(f"nobel: {filled} marked, {skipped} already marked, {missing} not found, {len(LAUREATES)} defined")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
