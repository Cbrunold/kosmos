"""French mirror of the site: extract, translate (cached), apply.

The English pages are the source of truth, built by build.py from the templates and
the Notion data. The French pages are derived from the *built* English HTML, so no
template has to know about languages:

  extract(html, page)  -> the translatable spans in one built page —
      · static text between tags, in runs that keep inline markup (<em>, <a>, <code>…)
        together so a sentence is translated as a sentence
      · the attributes a reader sees: title, placeholder, alt, aria-label
      · JS string literals in the contexts that reach the screen — textContent =,
        innerHTML =, .title =, placeholder, label:, blurb:, plus a few hand-listed
        spots per template (KIND_LABEL maps, preset names, dl labels)
      · the embedded JSON data blocks, by per-page rules: prose fields and entity
        names are translated, enum-like fields that the page JS keys colours and
        filters on (field, kind, category, status…) are not, slugs and ids never.
        Where a template computes an anchor from a name client-side, the English is
        kept beside the French (NameEN) and the template prefers it — see build.py.
  Translator           -> data/i18n/fr.json, keyed by the sha1 of the English string.
      translate.py fills it through the Claude API (claude-opus-5, batched, stdlib
      urllib like every other script here); build.py only ever reads it, so a build
      is deterministic and needs no key. A string with no cached translation stays
      English and is counted, so the build can say how much is untranslated.
  apply(html, page, tr) -> the French page: spans replaced, internal links
      rewritten to /fr/…, <html lang>, and the EN · FR switch that the English page
      also gets.

Why post-process rather than template-level i18n: 20 templates with prose in HTML,
in JS, and in Notion data; a dictionary per template would rot the day a page
changed. This way a new page is French the next time translate.py runs, and a
changed sentence costs one string.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "i18n" / "fr.json"

ROUTES = ["elements", "minerals", "cosmos", "forces", "theories", "timeline", "mines", "machines", "skills",
          "glossary", "explainers", "impacts", "equations", "constants", "billiards", "scales", "universe", "solar", "life"]
PAGE_FILES = {  # built file -> route (for the language switch)
    "home.html": "/", "index.html": "/elements", "minerals.html": "/minerals", "cosmos.html": "/cosmos",
    "forces.html": "/forces", "theories.html": "/theories", "timeline.html": "/timeline", "mines.html": "/mines",
    "machines.html": "/machines", "skills.html": "/skills", "glossary.html": "/glossary",
    "explainers.html": "/explainers", "impacts.html": "/impacts", "equations.html": "/equations",
    "constants.html": "/constants", "billiards.html": "/billiards", "scales.html": "/scales",
    "universe.html": "/universe", "solar.html": "/solar", "life.html": "/life",
}


# ---------------------------------------------------------------- cache
def key_of(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


class Translator:
    def __init__(self, path: Path = CACHE_PATH):
        self.path = path
        self.cache: dict[str, str] = {}
        self.source: dict[str, str] = {}   # sha -> English, kept so the file is reviewable
        if path.exists():
            d = json.loads(path.read_text())
            self.cache = d.get("fr", {})
            self.source = d.get("en", {})
        self.pending: dict[str, str] = {}   # sha -> English
        self.kinds: dict[str, str] = {}     # sha -> "prose" | "vocab", to pick the prompt
        self.misses = 0

    def get(self, s: str) -> str | None:
        return self.cache.get(key_of(s))

    def want(self, s: str, kind: str = "prose"):
        k = key_of(s)
        if k not in self.cache and k not in self.pending:
            self.pending[k] = s
        # a word that is both a filter label and prose is asked for as vocabulary: the
        # vocabulary prompt is the one that needs the context, and one translation serves both
        if kind == "vocab":
            self.kinds[k] = kind
        else:
            self.kinds.setdefault(k, kind)

    def lookup(self, s: str) -> str:
        """French if cached, else the English unchanged (counted as a miss)."""
        t = self.cache.get(key_of(s))
        if t is None:
            self.misses += 1
            return s
        return t

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        keys = sorted(self.cache)
        out = {"_": "English -> French, keyed by sha1 of the English. Edit a French value by hand and it sticks "
                    "until the English changes. Written by scripts/translate.py; read by scripts/build.py.",
               "en": {k: self.source[k] for k in keys if k in self.source},
               "fr": {k: self.cache[k] for k in keys}}
        self.path.write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n")

    def prune(self, live: set[str]):
        """Drop cached strings no page uses any more."""
        dead = [k for k in self.cache if k not in live]
        for k in dead:
            self.cache.pop(k, None); self.source.pop(k, None)
        return len(dead)


# ---------------------------------------------------------------- extraction
INLINE = {"a", "em", "strong", "b", "i", "code", "kbd", "span", "small", "sup", "sub", "br", "abbr", "mark",
          "var", "time", "u", "s", "wbr"}
SKIP_BLOCKS = re.compile(r"(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<svg\b[^>]*>.*?</svg>)", re.S)
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9-]*)([^>]*)>")
ATTR = re.compile(r"""\b(title|placeholder|alt|aria-label|data-label)=(")([^"]*)(")""")
HAS_LETTERS = re.compile(r"[A-Za-zÀ-ÿ]{2,}")


def _html_spans(html: str):
    """Text runs between block-level tags, outside script/style/svg. Yields (start, end, text)."""
    out = []
    pos = 0
    for m in SKIP_BLOCKS.finditer(html):
        out += _runs(html, pos, m.start())
        pos = m.end()
    out += _runs(html, pos, len(html))
    return out


def _runs(html: str, lo: int, hi: int):
    spans = []
    run_start = None
    i = lo
    for m in TAG.finditer(html, lo, hi):
        name = m.group(2).lower()
        if name in INLINE:
            if run_start is None:
                run_start = i
            continue
        if run_start is None:
            run_start = i
        spans.append((run_start, m.start()))
        run_start = None
        i = m.end()
    spans.append((i if run_start is None else run_start, hi))
    out = []
    for a, b in spans:
        seg = html[a:b]
        la = len(seg) - len(seg.lstrip()); lb = len(seg) - len(seg.rstrip())
        a2, b2 = a + la, b - lb
        txt = html[a2:b2]
        if not txt or not HAS_LETTERS.search(re.sub(r"<[^>]+>", "", txt)):
            continue
        out.append((a2, b2, txt, None))
    return out


def _attr_spans(html: str):
    out = []
    pos = 0
    for m in SKIP_BLOCKS.finditer(html):
        out += _attrs_in(html, pos, m.start()); pos = m.end()
    out += _attrs_in(html, pos, len(html))
    return out


def _attrs_in(html, lo, hi):
    out = []
    for t in TAG.finditer(html, lo, hi):
        for a in ATTR.finditer(t.group(3)):
            if HAS_LETTERS.search(a.group(3)):
                s = t.start(3) + a.start(3)
                out.append((s, s + len(a.group(3)), a.group(3), '"attr'))
    return out


def keep_placeholders(en: str, fr: str) -> str:
    """A translation that lost or altered a ${…} would render as literal text or throw.
    The translator is told to keep them; this makes sure of it, and keeps the English if not.
    Order may legitimately change — French word order — so compare as a multiset."""
    if "${" not in en:
        return fr
    return fr if sorted(SUBST.findall(en)) == sorted(SUBST.findall(fr)) else en


def escape_for(text: str, ctx: str | None) -> str:
    """Make a translation safe for the context it is dropped into.

    French is full of apostrophes — l'énergie, d'un, qu'il — and the first full run put
    one inside a single-quoted JS literal, which took the page's whole script down with
    a SyntaxError. So a JS literal gets its own delimiter escaped (and any backslash,
    and newlines); ${...} placeholders are left live, because the translations are asked
    to keep them and the templates need them. An attribute value gets its double quote
    escaped. HTML text gets nothing: translations legitimately carry <em>, links and
    entities, and escaping those would print the markup."""
    if ctx is None:
        return text
    if ctx == '"attr':
        return text.replace('"', "&quot;")
    # A JS literal, delimited by q. The text is raw source, so it may already carry \' or \`
    # from the English; escape only a delimiter that is not escaped already, and never touch
    # backslashes — doubling them would corrupt every \n and \' that was correct to begin with.
    if ctx == "`":
        # Nothing: a template literal may hold another one inside a ${…} expression
        # (`${x ? `a ${y}` : ''}`), and escaping those backticks would break the expression.
        # What protects this one is keep_placeholders — the ${…} come back unaltered or the
        # English is kept — and check_fr, which parses every built page before it ships.
        return text
    out = re.sub(r"(?<!\\)" + re.escape(ctx), "\\\\" + ctx, text)
    return out.replace("\r", "\\r").replace("\n", "\\n")


# JS string literals that reach the screen. Each pattern's first group is the opening
# quote and the second the body; only those spans are replaced, never the same
# literal elsewhere, so 'theory' as a label can change while x.kind === 'theory' cannot.
JS_CONTEXTS = [
    r"""(?:\.textContent|\.innerHTML|\.title|\.placeholder|\.alt|\.ariaLabel)\s*=\s*(['"`])((?:\\.|(?!\1).)*?)\1""",
    r"""\b(?:label|blurb|caption|hint|note|title|placeholder)\s*:\s*(['"`])((?:\\.|(?!\1).)*?)\1""",
    r"""setAttribute\(\s*['"](?:aria-label|title|placeholder)['"]\s*,\s*(['"`])((?:\\.|(?!\1).)*?)\1""",
    r"""\.(?:textContent|innerHTML)\s*\+=\s*(['"`])((?:\\.|(?!\1).)*?)\1""",
    r"""document\.createTextNode\(\s*(['"`])((?:\\.|(?!\1).)*?)\1""",
]
JS_CONTEXT_RE = [re.compile(p, re.S) for p in JS_CONTEXTS]

# ---- template literals. Most of the interactive prose is in them — "${shown} of ${E.length}
# equations", "${n} rail${…} touched" — and no context pattern can see them, because they are
# assigned inside ternaries, returned from helpers or pushed into arrays. A regex cannot read
# them either: their ${…} may hold quotes and further template literals. So walk the source.
QUOTED = re.compile(r"""(['"])((?:\\.|(?!\1).)*)\1""")
SUBST = re.compile(r"\$\{(?:[^{}]|\{[^{}]*\})*\}")
WORDY = re.compile(r"[A-Za-z]{3,}")
CODEY = re.compile(r"""^\s*(?:[.#][\w-]+[\[\.#]|[a-z-]+\(|translate|matrix|rgba?\()""")


def template_literals(js: str):
    """(start, end, text) for every complete template literal, nesting-aware. Nested ones live
    inside a ${…} of the outer, so only the outermost is returned — it is the whole sentence."""
    out = []
    i, n = 0, len(js)
    stack, start = [], None
    while i < n:
        c = js[i]
        if not stack:
            if c == "`":
                stack.append("`"); start = i
            elif c in "'\"":
                q = c; i += 1
                while i < n and js[i] != q:
                    i += 2 if js[i] == "\\" else 1
            elif c == "/" and i + 1 < n and js[i + 1] == "/":
                while i < n and js[i] != "\n":
                    i += 1
            elif c == "/" and i + 1 < n and js[i + 1] == "*":
                j = js.find("*/", i + 2); i = j + 1 if j > 0 else n
            i += 1
            continue
        if c == "\\":
            i += 2; continue
        if stack[-1] == "`":
            if c == "`":
                stack.pop()
                if not stack:
                    out.append((start, i + 1, js[start + 1:i]))
            elif c == "$" and i + 1 < n and js[i + 1] == "{":
                stack.append("${"); i += 1
        else:                                          # inside ${ … }
            if c == "}":
                stack.pop()
            elif c == "{":
                stack.append("{")
            elif c == "`":
                stack.append("`")
            elif c in "'\"":
                q = c; i += 1
                while i < n and js[i] != q:
                    i += 2 if js[i] == "\\" else 1
        i += 1
    return out


def prose_like(t: str) -> bool:
    """Is this literal something a reader sees, rather than a selector or a transform?"""
    outside = SUBST.sub("", t)
    if CODEY.match(outside):
        return False
    text = re.sub(r"&[a-z]+;", " ", re.sub(r"<[^>]*>", " ", outside))
    return bool(WORDY.search(text))
JS_SKIP_CLASSY = re.compile(r"^[a-z][a-z0-9-]*( [a-z][a-z0-9-]*)+$")   # 'kcard eq' — class lists


def _js_spans(html: str, page: str):
    out = []
    # real JavaScript only — a typed script holds data, not code (the mines basemap is text/plain)
    for m in re.finditer(r"""<script(?![^>]*\btype=(?!["'](?:text/javascript|module)))[^>]*>(.*?)</script>""",
                         html, re.S):
        base, body = m.start(1), m.group(1)
        seen = set()
        for rx in JS_CONTEXT_RE:
            for lm in rx.finditer(body):
                s, e, txt = base + lm.start(2), base + lm.end(2), lm.group(2)
                if (s, e) in seen:
                    continue
                if not HAS_LETTERS.search(re.sub(r"\$\{[^}]*\}", "", txt)):
                    continue
                if JS_SKIP_CLASSY.match(txt) and len(txt) < 24:
                    continue
                seen.add((s, e))
                out.append((s, e, txt, lm.group(1)))
        for a, b, t in template_literals(body):
            s, e = base + a + 1, base + b - 1
            if (s, e) in seen or not prose_like(t):
                continue
            seen.add((s, e)); out.append((s, e, t, "`"))
        # Quoted literals that carry HTML: those are innerHTML strings — a sentence with tags
        # in it. Quoted literals WITHOUT tags are left alone on purpose: most of them are
        # lookup keys ('Atomic Physics' indexes the colour map, 'aria-pressed' names an
        # attribute), and translating a key silently breaks the thing it keys.
        masked = list(body)
        for a, b, _ in template_literals(body):
            masked[a:b] = " " * (b - a)
        for lm in QUOTED.finditer("".join(masked)):
            t = lm.group(2)
            if "<" not in t or ">" not in t or not prose_like(t):
                continue
            s, e = base + lm.start(2), base + lm.end(2)
            if (s, e) in seen:
                continue
            seen.add((s, e)); out.append((s, e, t, lm.group(1)))
        for extra in PAGE_JS_EXTRA.get(page, []):
            for lm in re.finditer(extra, body, re.S | re.M):
                s, e, txt = base + lm.start(1), base + lm.end(1), lm.group(1)
                if (s, e) in seen or not HAS_LETTERS.search(txt):
                    continue
                # the hand-listed patterns capture the text only; the delimiter is the char before it
                seen.add((s, e)); out.append((s, e, txt, body[lm.start(1) - 1] if lm.start(1) else "'"))
    return out


# per-template literal spots the generic contexts cannot see: group 1 is the text
PAGE_JS_EXTRA = {
    "home.html": [r"""^\s+(?:[a-z]+|'[a-z ]+'):\s*\['([^']+)',\s*'var\(--"""],          # KINDS labels
    "equations.html": [r"""\b(?:object|spectral|instrument|theory):\s*'([^']+)'""",   # KIND_LABEL
                       r"""const SORTS = \{ year: '([^']+)'""", r"""\bdepth: '([^']+)' \}""",
                       r"""lv\.textContent = d === 0 \? '([^']+)'""",
                       r"""eqRow\([^,]+,\s*'([^']+)'\)""",
                       r"""\{ name: '([^']+)', color:""",            # the six domain names
                       r"""bits\.push\('([^']+)'\)"""],              # "a foundation — requires nothing"
    "billiards.html": [r"""\['([A-Za-z][^'`]+)',\s*`""", r"""\['([a-z][a-z ,\-]+)',\s*(?:S\.|`|\$)""",   # dl labels, presets
                       r"""\['([^']+)',\s*\{ cut:"""],
    # Both pages build their card labels through a local para(cls, label, text) helper,
    # so the label is a function argument and no generic context sees it. Two of them
    # are also all-lowercase and short — "what reduces it", "cannot run without" —
    # which is exactly the shape JS_SKIP_CLASSY exists to skip, since that is what a
    # class list looks like. The heuristic is right to be cautious and wrong here, and
    # naming the spots is what this table is for.
    "impacts.html": [r"""para\('[a-z]*', '([^']+)'""", r"""l\.textContent = '([^']+)'"""],
    "life.html": [r"""para\('[a-z]*', '([^']+)'""", r"""l\.textContent = '([^']+)'"""],
    "universe.html": [r"""mk\('([^']+)'""",                        # the view buttons
                      r"""_LABEL = '([^']+)'""",                   # here / the Sun, at the centre
                      r"""^\s*\['([^']+)',\s*(?:null|[\d.]+e?[-+]?\d*)\]"""],   # the zoom stops
    # the KL map on /glossary: the plural label under each "appears in" group. Its keys are
    # the kinds the data uses and must not move; only the values are read out.
    "glossary.html": [r"""(?<=: ')((?:equation|theor|machine|skill|timeline|element|mine|observator|discover|mission|constant|researcher|force|instrument|rock)[a-z ]*)(?=',|' \})"""],
}

# ---- JSON rules: which keys are prose, which are names (with an EN shadow when a template
# computes anchors from them), and predicates that decide by siblings.
PROSE_KEYS = {
    "Significance", "Symbols", "Definition", "Summary", "The Science", "Tools", "Steps", "Safety", "How It Fails",
    "Done When", "Mechanism", "Mitigation", "Case", "Notes", "Known For", "Description", "Characteristics",
    "How It Works", "Materials", "Used In", "Covers", "Note", "Relative Strength", "Range", "Quantity",
    "significance", "summary", "caption", "note", "definition", "mechanism", "mitigation", "case", "notes", "known",
    "what", "objective", "desc", "char", "covers", "how", "materials", "used", "eff", "pd", "procs", "text",
    "extraction", "science", "steps", "fails", "safety", "tools", "done", "pop", "rule_text", "comment", "when",
    "aliases", "structure", "columns", "rows",
    # /life. The page names its prose "Function" and "Numbers" and neither word was
    # here, so the French mirror shipped translated chrome around English cards —
    # the failure is silent by construction, because a key this set does not know
    # is simply left alone rather than reported.
    "Function", "Numbers", "function", "numbers",
}
NAME_RULES = {
    "equations.html": {"Name": "NameEN"},
    "constants.html": {"Name": "NameEN", "name": None},
    "billiards.html": {"name": None},
    "impacts.html": {"name": None, "term": None},
    # Without this the machine names and the glossary chips stay English while the
    # prose around them is French, and the same term reads "Catalyseur" on /fr/glossary
    # and "Catalyst" here — one thing with two names in one language. None means "this
    # key is a name, translate it"; no EN shadow is needed because the template anchors
    # on the separate slug field, which is never translated.
    "life.html": {"name": None, "term": None},
    "glossary.html": {"term": None},
    "explainers.html": {"term": None},
    "theories.html": {"Name": "NameEN"},
    "timeline.html": {"event": "eventEN"},
    "universe.html": {"name": "nameEN"},
    "scales.html": {"name": "nameEN", "within": None},
    "index.html": {"name": None},
    "forces.html": {"Force Name": None},
}
NAME_KINDS = {"equation", "theory", "machine", "skill", "event", "force", "impact", "constant", "unit",
              "structure", "element", "term", "section", "page", "object class", "spectral type"}

# ---- the fixed vocabulary: values the page scripts filter, group and colour by. These are
# NOT translated in the data — every comparison would break — but they are translated for
# display, through the vocab() helper build.py puts on every page and the __VOCAB__ map
# apply() writes into the French ones. Collected from the same data blocks.
VOCAB_KEYS = {"Field", "field", "fields", "kind", "Kind", "kinds", "cat", "cats", "Category", "category",
              "categories", "Status", "status", "level", "difficulty", "domain", "Domain", "domains",
              "type", "Type", "era", "eras", "morph", "timescale", "timescales", "media", "Medium"}
# values that only ever key something internal, or read the same in French, or are not words
VOCAB_SKIP = re.compile(r"^(?:#|\d+:|f-block)|^(?:Other|Local|Star|Type [IV]+|SI |Accepted with SI)")
NEVER_KEYS = {"slug", "id", "href", "url", "kind", "field", "type", "status", "category", "cat", "level",
              "domain", "era", "sub", "formula", "Symbol", "Unit", "Equation", "Named After", "pageUrl", "pageId",
              "lastEdited", "within_slug", "withinSlug"}


def _name_ok(page: str, key: str, obj: dict):
    """Shadow key ('' for none) if obj[key] is a name to translate on this page, else None."""
    if key in NEVER_KEYS:
        return None
    if key == "name" and any(k in obj for k in ("known", "life", "country", "agency", "behind", "lat", "lon")):
        return None                                         # a person, a mine, a mission, an explainer
    rules = NAME_RULES.get(page, {})
    if key in rules:
        return rules[key] or ""
    if "kind" in obj and key == "name":
        return "" if obj.get("kind") in NAME_KINDS else None
    if key == "name":
        if "slug" in obj and "field" in obj:
            return ""                                       # an equation lookup, on any page
        if page == "machines.html" and "how" in obj:
            return ""
        if page == "skills.html" and "science" in obj:
            return ""
        if page == "machines.html" and "slug" in obj and ("cat" in obj or "level" in obj):
            return ""                                       # skill lookups on the machines page
    return None


def _json_walk(page: str, obj, fn):
    """fn(container, key_or_index, value, shadow_key) for every string to translate."""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str):
                if k in PROSE_KEYS and HAS_LETTERS.search(v):
                    fn(obj, k, v, None)
                else:
                    sh = _name_ok(page, k, obj)
                    if sh is not None and HAS_LETTERS.search(v):
                        fn(obj, k, v, sh or None)
            elif isinstance(v, list):
                if k in PROSE_KEYS:
                    _json_list(page, v, fn)
                else:
                    for x in v:
                        if isinstance(x, (dict, list)):
                            _json_walk(page, x, fn)
            elif isinstance(v, dict):
                _json_walk(page, v, fn)
    elif isinstance(obj, list):
        for x in obj:
            _json_walk(page, x, fn)


def _json_list(page, lst, fn):
    for i, x in enumerate(lst):
        if isinstance(x, str):
            if HAS_LETTERS.search(x):
                fn(lst, i, x, None)
        elif isinstance(x, list):
            _json_list(page, x, fn)
        elif isinstance(x, dict):
            _json_walk(page, x, fn)


JSON_BLOCK = re.compile(r"(<script id=\"[a-z]+\" type=\"application/json\">)(.*?)(</script>)", re.S)


def vocab_values(html: str) -> set:
    """Every distinct enum value in a page's data blocks — the words its filters are made of."""
    out = set()

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in VOCAB_KEYS:
                    for x in (v if isinstance(v, list) else [v]):
                        if isinstance(x, str) and HAS_LETTERS.search(x) and not VOCAB_SKIP.match(x):
                            out.add(x)
                if isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    for m in JSON_BLOCK.finditer(html):
        try:
            walk(json.loads(m.group(2)))
        except json.JSONDecodeError:
            continue
    return out


def extract(html: str, page: str):
    """(spans, json_strings): spans are (start, end, text) over the HTML; json_strings the set of
    strings inside the data blocks that the rules select."""
    spans = _html_spans(html) + _attr_spans(html) + _js_spans(html, page)
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    if m and HAS_LETTERS.search(m.group(1)):
        spans.append((m.start(1), m.end(1), m.group(1), None))
    strings = vocab_values(html)          # the filter vocabulary is translated for display only
    for jm in JSON_BLOCK.finditer(html):
        try:
            data = json.loads(jm.group(2))
        except json.JSONDecodeError:
            continue
        _json_walk(page, data, lambda c, k, v, sh: strings.add(v))
    spans.sort()
    out, last_end = [], -1
    for s, e, t, ctx in spans:     # drop a span nested in another (an attr inside an inline run)
        if s < last_end:
            continue
        out.append((s, e, t, ctx)); last_end = e
    return out, strings


# ---------------------------------------------------------------- application
LINK_RE = re.compile(r"""(['"`])/(?:(""" + "|".join(ROUTES) + r""")(?=[#?/'"`])|(?=['"`]))""")
SWITCH_CSS = """
  .klang { position: fixed; top: 9px; right: 12px; z-index: 60; display: flex; gap: 0; border: 1px solid var(--hairline); border-radius: 99px; background: color-mix(in oklab, var(--panel) 88%, transparent); backdrop-filter: blur(4px); overflow: hidden; font: 10.5px ui-monospace, "SF Mono", "Cascadia Code", Consolas, Menlo, monospace; letter-spacing: 0.08em; }
  .klang a { color: var(--muted); text-decoration: none; padding: 4px 9px; }
  .klang a.on { color: var(--page); background: var(--ink); }
  .klang a:hover:not(.on) { color: var(--ink); }
  @media print { .klang { display: none; } }
"""


def switch_html(page: str, lang: str) -> str:
    route = PAGE_FILES.get(page, "/")
    en = route
    fr = "/fr" + ("" if route == "/" else route)
    on = ' class="on"'
    return (f'<div class="klang" aria-label="Language · Langue">'
            f'<a href="{en}" hreflang="en" lang="en"{on if lang == "en" else ""}>EN</a>'
            f'<a href="{fr}" hreflang="fr" lang="fr"{on if lang == "fr" else ""}>FR</a></div>')


def add_switch(html: str, page: str, lang: str) -> str:
    """The EN · FR switch on every page, both languages; CSS goes into the first <style>."""
    if 'class="klang"' in html:
        return html
    html = html.replace("</style>", SWITCH_CSS + "</style>", 1)
    i = html.find("</style>")
    i = i + len("</style>") if i >= 0 else 0
    return html[:i] + "\n" + switch_html(page, lang) + html[i:]


def apply(html: str, page: str, tr: Translator) -> str:
    """The French page from the English one, using the cache only."""
    spans, _ = extract(html, page)
    out = html
    for s, e, t, ctx in reversed(spans):
        out = out[:s] + escape_for(keep_placeholders(t, tr.lookup(t)), ctx) + out[e:]

    def fix_json(m):
        try:
            data = json.loads(m.group(2))
        except json.JSONDecodeError:
            return m.group(0)

        def repl(c, k, v, sh):
            fr = tr.lookup(v)
            if sh:
                c[sh] = v
            c[k] = fr
        _json_walk(page, data, repl)
        return m.group(1) + json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + m.group(3)
    out = JSON_BLOCK.sub(fix_json, out)
    out = LINK_RE.sub(lambda m: m.group(1) + "/fr/" + (m.group(2) or ""), out)
    # the filter vocabulary, for display only: the data keeps its English values so every
    # comparison, colour lookup and grouping in the page's own script still works
    # sorted: vocab_values returns a set, and iterating it unsorted made every build
    # emit __VOCAB__ in a different order — 20 French pages rewritten on every deploy,
    # burying the one page that actually changed in twenty that had not
    vocab = {s: tr.lookup(s) for s in sorted(vocab_values(html))}
    vocab = {k: v for k, v in vocab.items() if v != k}
    if vocab:
        out = out.replace("</style>", "</style>\n<script>window.__VOCAB__ = "
                          + json.dumps(vocab, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
                          + ";</script>", 1)
    out = add_switch(out, page, "fr")
    return '<!doctype html><html lang="fr"><meta charset="utf-8">\n' + out


# ---------------------------------------------------------------- the API
SYSTEM = """You translate a science website from English into French. The site is a personal atlas of the
physical world — elements, minerals, the cosmos, equations, engines, hands-on skills, the physics of billiards
— written in a precise, plain, slightly literary register. Translate into French of the same register: exact,
unhurried, no padding, no marketing tone. Use French typographic conventions where natural (« » for quotes;
a plain space before ; : ? ! is fine). Keep numbers, units and symbols exactly as given. Keep proper names,
formulas, chemical notation, HTML tags, HTML entities, JavaScript template placeholders like ${...}, and
anything that looks like code or markup EXACTLY as they are. Keep capitalisation style: sentence case stays
sentence case, a lowercase label stays lowercase. Use the standard French scientific term (Second Law of
Thermodynamics → Deuxième principe de la thermodynamique; Work → Travail; Torque → Couple; cue ball → bille
blanche; object ball → bille visée; English / side spin → effet latéral; follow → coulé; draw → rétro; stun →
bille arrêtée; throw → déviation par frottement). Do not translate people's names, telescope and mission
names, mineral names, or trademarks. Translate ONLY; never explain, never add. Reply with a JSON array of
strings, same length and order as the input, nothing else."""


def _api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        for p in (ROOT / ".env", Path("/opt/kosmos/.env"), Path("/srv/kosmos/.env")):
            if p.exists():
                for line in p.read_text().splitlines():
                    if line.startswith("ANTHROPIC_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip("\"'")
    if not key:
        sys.exit("ANTHROPIC_API_KEY not set (env, .env, /opt/kosmos/.env)")
    return key


VOCAB_BRIEF = """These are the site's FILTER LABELS — the fixed vocabulary its chips, tags and headings are
made of, one or two words each, with no sentence around them. They name: fields of science (Thermodynamics,
Fluid Dynamics, Vectors & Geometry), classes of celestial object (Nebulae, Pulsars and Magnetars, Void,
Filament, Group as in a galaxy group), kinds of machine (Heat engine, Turbine, Reactor, Rocket, Power source),
kinds of explainer (Person, Channel, Organisation, Podcast, Book, Blog, Course, Lectures), mine kinds and
states (Open pit, Underground, Placer, Quarry, Brine, Active, Closed, Development), mission states (Completed,
Failed, On-going), the standing of a theory (Accepted, Superseded, Disproved, Speculative), skill categories
and levels (Metalwork, Joining, Rigging, Cue sports, Beginner, Intermediate, Advanced), glossary domains,
mining-impact categories (Water, Air, Land, Health, Ground, Energy) and timescales (During operation, After
closure, Both), and epochs of the universe (Radiation Era, Dark Ages, Structure Formation, Present as in the
present epoch, Far Future). Translate each as the term a French scientific site would put on that chip — short,
no article, no explanation. Where a word has an everyday sense and a technical one, the technical one is meant.
"""


def _call_api(texts: list[str], model: str, key: str, tries: int = 4, kind: str = "prose") -> list[str]:
    brief = VOCAB_BRIEF if kind == "vocab" else ""
    body = {
        "model": model,
        "max_tokens": 16000,
        "system": SYSTEM,
        "output_config": {"effort": "medium"},
        "messages": [{"role": "user", "content": brief + "Translate each string of this JSON array into French. "
                                                  "Return a JSON array of the same length.\n\n"
                                                  + json.dumps(texts, ensure_ascii=False)}],
    }
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"}, method="POST")
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                d = json.load(r)
            if d.get("stop_reason") == "refusal":
                raise RuntimeError("refusal")
            text = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text").strip()
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
            arr = json.loads(text)
            if isinstance(arr, list) and len(arr) == len(texts) and all(isinstance(x, str) for x in arr):
                return arr
            raise ValueError(f"shape mismatch: {len(arr) if isinstance(arr, list) else type(arr)} for {len(texts)}")
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            if e.code == 400 and "credit balance" in detail:
                raise OutOfCredit(detail)          # no point retrying anything: stop the whole run
            if attempt == tries - 1 or (e.code < 500 and e.code != 429):
                raise RuntimeError(f"HTTP {e.code}: {detail}")
            time.sleep(2 ** attempt * 2)
        except (urllib.error.URLError, ValueError, RuntimeError, json.JSONDecodeError) as e:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("unreachable")


class OutOfCredit(Exception):
    """The key's credit balance is exhausted — the API answers 400 to everything."""


def translate_pending(tr: Translator, model: str = "claude-opus-5", batch: int = 30, workers: int = 6,
                      progress=print) -> int:
    key = _api_key()
    # vocabulary and prose are batched apart: the filter labels are single words whose
    # everyday sense is usually the wrong one, and they get a prompt that says so
    items = sorted(tr.pending.items(), key=lambda kv: (tr.kinds.get(kv[0], "prose"), len(kv[1])))
    batches, cur, cur_len = [], [], 0
    for k, s in items:
        kind = tr.kinds.get(k, "prose")
        if cur and (len(cur) >= batch or cur_len + len(s) > 9000 or tr.kinds.get(cur[0][0], "prose") != kind):
            batches.append(cur); cur, cur_len = [], 0
        cur.append((k, s)); cur_len += len(s)
    if cur:
        batches.append(cur)
    progress(f"  translating {len(items)} strings in {len(batches)} batches with {model}")
    done = 0

    stop = {"out": None}

    def run(b):
        texts = [s for _, s in b]
        kind = tr.kinds.get(b[0][0], "prose")
        if stop["out"]:
            return b, [None] * len(b)
        try:
            fr = _call_api(texts, model, key, kind=kind)
        except OutOfCredit as e:
            stop["out"] = str(e); return b, [None] * len(b)
        except Exception as e:          # one batch failing must not lose the rest
            progress(f"  batch of {len(b)} failed ({e}); retrying one by one")
            fr = []
            for t in texts:
                if stop["out"]:
                    fr.append(None); continue
                try:
                    fr.append(_call_api([t], model, key, kind=kind)[0])
                except OutOfCredit as e2:
                    stop["out"] = str(e2); fr.append(None)
                except Exception as e2:
                    progress(f"    string failed: {t[:60]!r}: {e2}"); fr.append(None)
        return b, fr
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for b, fr in ex.map(run, batches):
            for (k, s), f in zip(b, fr):
                if f is not None:
                    tr.cache[k] = f; tr.source[k] = s; done += 1
            tr.pending = {k: v for k, v in tr.pending.items() if k not in tr.cache}
            progress(f"  {done}/{len(items)}")
            tr.save()
    if stop["out"]:
        progress(f"  STOPPED: {stop['out']}\n  {done} translated this run; {len(tr.pending)} still pending — "
                 "add credits and run again; only the missing strings are sent")
    return done
