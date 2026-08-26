"""Fail the build on the inconsistencies a reader would notice before we do.

check_fr.py guards the French mirror; this guards the content itself. Both run
in deploy.sh between build and ship, so a bad page never reaches /opt/kosmos.

It only catches *mechanical* inconsistency — a number that disagrees with the
data behind it, a symbol decoded for the wrong equation, a relation pointing at
nothing. It cannot catch a sentence that is well-formed and wrong: "every blow
work-hardens the surface" passes every check here and was still false. That
still needs someone who knows the field to read the page.

    python3 scripts/check_content.py          # after build.py
    python3 scripts/check_content.py --warn    # report, exit 0

Checks, each named in its output so a failure says which rule it broke:

  typed-count       a template writes a count of one of the site's own
                    collections as a literal ("8 of 45 objects"). The data
                    moves, the sentence does not. Compute it instead.
  shared-symbols    two equations carry byte-identical Symbols. One of them is
                    decoding the other's formula: the First Friedmann equation
                    explained ä and p, which do not appear in it.
  orphan-symbol     Symbols decodes a symbol the Equation does not contain.
  dangling-relation a relation id in notion-all.json resolves to no row, so the
                    chip it should have drawn silently does not appear.
  empty-column      a property null for every row of a table — a column of
                    dashes. Declare it in DELIBERATELY_EMPTY or fill it.
  mojibake          UTF-8 read as Latin-1 somewhere upstream (Ã©, â€™).
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
PUB = ROOT / "public"

# Collections the site counts. A literal number in front of one of these words
# in a template is a claim about data that will move without it.
COUNTED = (r"objects|researchers|people|equations|skills|machines|minerals|elements|members|galaxies|"
           r"mines|observatories|missions|instruments|discoveries|theories|constants|terms|gemstones|rows|entries")
SPELLED = (r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
           r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety")
TYPED_COUNT = re.compile(
    rf"\b((?:\d[\d,]*|(?:{SPELLED})(?:-(?:{SPELLED}))?)\s+(?:of\s+\d[\d,]*\s+)?(?:{COUNTED}))\b", re.I)

# Columns that are blank on purpose. Each needs a reason, and the reason is the
# point: an undeclared empty column is a column nobody noticed was empty.
DELIBERATELY_EMPTY = {
    ("missions", "Mission_ID"): "COSPAR ids are to be copied from NSSDC, not recalled",
    # Years live in a Year number property. A date would invent a month and a day
    # for something known only to the year — the site's rule, and these three are
    # the date columns it was decided against.
    ("discoveries", "Discovery Date"): "superseded by the Year number",
    ("observatories", "Established"): "superseded by the Year number",
    ("theories", "Date Proposed"): "superseded by the Year number",
    # Relations nobody has wired. Seeding them means asserting links no one has
    # checked, and the pages draw what they need from the other side.
    ("celestialObjects", "Cosmology Events [DB]"): "unwired relation",
    ("celestialObjects", "Discoveries [DB]"): "unwired relation; /cosmos reads discoveries directly",
    ("celestialObjects", "Spectral Types"): "unwired relation; the spectral sequence stands alone",
    ("discoveries", "Celestial_Object"): "unwired relation",
    ("spectralTypes", "Celestial_Objects [DB]"): "unwired relation",
    ("gemstones", "$ per Carat"): "prices are not physics and move; deliberately off the site",
    ("crystalSystems", "Tags"): "a Notion default column, never used",
}

SKIP_BLOCKS = re.compile(r"(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<svg\b[^>]*>.*?</svg>)", re.S)
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
MOJIBAKE = re.compile(r"Ã[©¨¢¤ª«¬°±·»]|â€[™œ\x9d\x93\x94]|Â[°±·»]")

# A symbol, as Symbols writes one: a letter (Latin or Greek) with optional
# sub/superscripts, primes and dots. Anything wordier is prose, not a symbol.
SYMBOL = re.compile(r"^[A-Za-zΑ-Ωα-ωℏ∇][\w'′^_{}()/₀-₉⁰-ⁿ̀-ͯ·]{0,7}$")
# ...but "T absolute temperature" decodes T, not "absolute". A run of three or
# more plain ASCII letters is a word; a symbol carries a subscript, a diacritic,
# a Greek letter or an acronym's capitals.
WORDY = re.compile(r"^[a-z]{3,}$|^[A-Za-z]{5,}$")
ENGLISH = re.compile(r"^(the|a|an|its|it|of|and|or|in|at|to|for|is|are|be|with|per|each|both|all|that|"
                     r"this|from|net|one|two|gas|dry|cut|far|how|what|total|up|about|as|by|on|if|no|so|"
                     r"we|you|any|put|not)$", re.I)


# Two ways out of typed-count, and they are different things.
#
# A number that is a fact about the world, not about our data, is marked in the
# template with a `count-ok:` comment giving the reason — the SI defines exactly
# seven constants and will not quietly become eight.
#
# A number that IS a claim about our data stays in the prose, where it reads
# better than a placeholder, and is pinned here to the arithmetic that produced
# it. The sentence then cannot drift without failing the build.
WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen".split())}
WORDS.update({"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
              "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90})


def _n(word: str):
    w = word.strip().lower().replace(",", "")
    if w.isdigit():
        return int(w)
    if "-" in w:
        a, b = w.split("-", 1)
        return (WORDS.get(a, 0) + WORDS.get(b, 0)) if a in WORDS and b in WORDS else None
    return WORDS.get(w)


CLAIMS = [
    ("timeline.template.html", r"first second gets ([\w-]+) entries",
     lambda n: sum(1 for r in n["cosmicTimeline"]
                   if isinstance(r.get("Seconds After Big Bang"), (int, float))
                   and r["Seconds After Big Bang"] <= 1),
     "timeline entries at or before one second"),
    ("universe.template.html", r"([\w-]+) objects move, in three dimensions",
     lambda n: sum(1 for r in n["celestialObjects"] if r.get("Vx (km/s)") not in (None, "", [])),
     "celestial objects carrying a velocity vector"),
]


class Report:
    def __init__(self):
        self.items = defaultdict(list)

    def add(self, rule, where, msg):
        self.items[rule].append((where, msg))

    def show(self):
        n = sum(len(v) for v in self.items.values())
        for rule in sorted(self.items):
            print(f"\n{rule} — {len(self.items[rule])}")
            for where, msg in self.items[rule][:12]:
                print(f"    {where}: {msg}")
            if len(self.items[rule]) > 12:
                print(f"    … and {len(self.items[rule]) - 12} more")
        return n


def prose(html: str) -> str:
    """Tags blanked to spaces of the same length, so offsets still point at the source."""
    blank = lambda m: " " * len(m.group(0))            # noqa: E731
    return re.sub(r"<[^>]+>", blank, SKIP_BLOCKS.sub(blank, html))


FUNCS = {"ln", "log", "exp", "sin", "cos", "tan", "det", "erf", "max", "min", "d", "e"}
PARTS = re.compile(r"[A-Za-zΑ-Ωα-ωℏ∇][\w₀-₉⁰-ⁿ̀-ͯ]*")

# A clause may legitimately name a symbol the formula does not show, because it
# is explaining what one of the shown symbols is made of. Each of these was read
# and is correct; a new one has to be read too.
DECODES_BY_DEFINITION = {
    ("Heat Equation", "c_p"): "α = k/(ρ c_p) — the clause unpacks α",
    ("Peltier Effect", "T"): "Π = S·T — the clause unpacks Π",
    ("Lorentz Transformations", "y"): "y and z are named to say they are unchanged",
}


def symbol_heads(sym: str):
    """The symbols a Symbols string claims to decode, one clause at a time."""
    for clause in sym.split("·"):
        toks = clause.strip().split()
        for i, tok in enumerate(toks):
            tok = tok.strip(",;:()[]")
            if not tok or ENGLISH.match(tok) or "'" in tok or "’" in tok:
                break
            if tok in FUNCS:
                break
            if not SYMBOL.match(tok) or WORDY.match(tok):
                break
            # "H = ȧ/a Hubble parameter" defines H from what is in the formula;
            # it is not claiming H appears there.
            if i + 1 < len(toks) and toks[i + 1] == "=":
                break
            yield tok


def check_templates(rep, notion):
    pinned = defaultdict(list)
    for name, pat, fn, what in CLAIMS:
        f = WEB / name
        if not f.exists():
            rep.add("typed-count", f"web/{name}", "CLAIMS names a template that does not exist")
            continue
        raw = f.read_text()
        m = re.search(pat, prose(raw))
        if not m:
            rep.add("typed-count", f"web/{name}",
                    f"CLAIMS expects /{pat}/ and the sentence is gone — re-pin it or drop the claim")
            continue
        pinned[name].append(m.start())
        said, real = _n(m.group(1)), fn(notion)
        if said != real:
            line = raw.count("\n", 0, m.start()) + 1
            rep.add("typed-count", f"web/{name}:{line}",
                    f'"{m.group(0).strip()}" — the data says {real} {what}')

    for f in sorted(WEB.glob("*.template.html")):
        raw = f.read_text()
        lines = raw.split("\n")
        for m in TYPED_COUNT.finditer(prose(raw)):
            line = raw.count("\n", 0, m.start()) + 1
            if any("count-ok" in ln for ln in lines[max(0, line - 3):line]):
                continue
            if any(abs(p - m.start()) < 200 for p in pinned.get(f.name, ())):
                continue
            rep.add("typed-count", f"web/{f.name}:{line}",
                    f'"{m.group(0).strip()}" — compute it, pin it in CLAIMS, or mark the line count-ok')


def check_equations(rep, notion):
    eqs = [e for e in notion["equations"] if e.get("Name")]
    by_symbols = defaultdict(list)
    for e in eqs:
        if e.get("Symbols"):
            by_symbols[e["Symbols"].strip()].append(e["Name"])
    for sym, names in by_symbols.items():
        if len(names) > 1:
            rep.add("shared-symbols", ", ".join(sorted(names)),
                    "identical Symbols — at least one decodes a formula it is not attached to")
    for e in eqs:
        eq, sym = e.get("Equation") or "", e.get("Symbols") or ""
        if not eq or not sym:
            continue
        squashed = re.sub(r"\s+", "", eq)
        absent = []
        for h in symbol_heads(sym):
            parts = PARTS.findall(h) or [h]
            if all(pt in squashed for pt in parts):
                continue
            if (e["Name"], h) in DECODES_BY_DEFINITION:
                continue
            absent.append(h)
        if absent:
            rep.add("orphan-symbol", e["Name"], f"decodes {', '.join(absent)} — not in  {eq}")


def check_relations(rep, notion):
    where = {}
    for table, rows in notion.items():
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict) and r.get("id"):
                    where[r["id"]] = table
    # Several relations point at Notion databases the site does not fetch at all
    # (mines.Commodities -> the Raw Materials DB). Those are not dangling, they
    # are out of scope: a property resolves either mostly or not at all, and only
    # the mostly-resolving ones can have a hole in them.
    per_prop = defaultdict(lambda: [0, 0, []])
    for table, rows in notion.items():
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            for prop, val in r.items():
                if not isinstance(val, list) or not val:
                    continue
                ids = [v for v in val if isinstance(v, str) and UUID.match(v)]
                if not ids:
                    continue
                st = per_prop[f"{table}.{prop}"]
                for i in ids:
                    if i in where:
                        st[0] += 1
                    else:
                        st[1] += 1
                        st[2].append(r.get("Name") or r.get("id"))
    for prop, (ok, dead, rows_) in sorted(per_prop.items()):
        if dead and ok:
            rep.add("dangling-relation", prop,
                    f"{dead} of {ok + dead} ids resolve to no row "
                    f"({', '.join(sorted(set(rows_))[:3])}) — the chip silently does not draw")


def check_empty_columns(rep, notion):
    for table, rows in notion.items():
        if not isinstance(rows, list) or len(rows) < 5:
            continue
        props = {k for r in rows if isinstance(r, dict) for k in r}
        for p in sorted(props - {"id", "url", "lastEdited"}):
            vals = [r.get(p) for r in rows if isinstance(r, dict)]
            if all(v is None or v == [] or v == "" for v in vals):
                if (table, p) in DELIBERATELY_EMPTY:
                    continue
                rep.add("empty-column", f"{table}.{p}",
                        f"null for all {len(vals)} rows — fill it or declare it in DELIBERATELY_EMPTY")


def check_mojibake(rep):
    for f in sorted(list(PUB.glob("*.html")) + list((PUB / "fr").glob("*.html"))):
        for m in MOJIBAKE.finditer(f.read_text()):
            rep.add("mojibake", f"public/{f.relative_to(PUB)}", f"{m.group(0)!r} near {m.start()}")
            break


def main(argv):
    warn = "--warn" in argv
    notion = json.loads((ROOT / "data" / "notion-all.json").read_text())
    rep = Report()
    check_templates(rep, notion)
    check_equations(rep, notion)
    check_relations(rep, notion)
    check_empty_columns(rep, notion)
    check_mojibake(rep)
    n = rep.show()
    if not n:
        print("content ok — counts computed, symbols match their formulas, "
              "every relation resolves, no empty columns, no mojibake")
        return 0
    print(f"\n{n} finding(s)." + ("  (--warn: not failing)" if warn else ""))
    return 0 if warn else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
