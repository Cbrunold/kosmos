"""The chrome every page shares: the <head> a crawler and a phone need, the header with
the section nav, the search box and the language switch, and sitemap.xml / robots.txt.

build.py's emit() injects it into every English page; i18n.apply() regenerates it for
the French mirror from the same functions, so the two languages cannot drift. The two
blocks are fenced — <!--khead-->…<!--/khead--> and <!--kchrome-->…<!--/kchrome--> —
so the French build can replace them wholesale after its own link rewriting has run.

Labels are written the way they appear in the templates ("Minerals &amp; Gemstones"),
because that is the string the translation cache is keyed by.
"""
import re
from pathlib import Path

from i18n import PAGE_FILES

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
SITE = "https://kosmos.yeahborhood.com"
BANNER = "/assets/kosmos-banner-v2.webp"

# The four groups of the home launcher, in its order. The label is what the header's
# breadcrumb and the sections panel show; the home tiles carry their own longer prose.
GROUPS = [
    ("Matter &amp; Earth", [
        ("/elements", "Periodic Table"),
        ("/minerals", "Minerals &amp; Gemstones"),
        ("/mines", "Mines &amp; Extraction"),
        ("/impacts", "Mining Impacts"),
        ("/life", "Life"),
    ]),
    ("Cosmos &amp; Physics", [
        ("/cosmos", "Cosmic Exploration"),
        ("/forces", "Forces"),
        ("/theories", "Theories"),
        ("/universe", "The Universe in Three Dimensions"),
        ("/solar", "The Solar System, Running"),
        ("/scales", "The Ladder of Scale"),
        ("/timeline", "Timeline of the Universe"),
    ]),
    ("Making &amp; Doing", [
        ("/machines", "Machines"),
        ("/skills", "Skills"),
        ("/billiards", "Billiards"),
    ]),
    ("Reference", [
        ("/equations", "Equations"),
        ("/constants", "Constants &amp; Units"),
        ("/glossary", "Glossary"),
        ("/explainers", "Explainers"),
    ]),
]
LABELS = {route: label for _, links in GROUPS for route, label in links}
CURRENT = ' aria-current="page"'

# One sentence per page, for the description meta and the link preview. Written as
# HTML text (&amp;), since that is how the translation cache keys attribute text too.
DESCRIPTIONS = {
    "/": "A personal atlas of the physical world — elements, minerals, mines, the cosmos, the forces, "
         "the equations and the machines, authored in Notion and rendered as one site.",
    "/elements": "An interactive periodic table: all 118 elements with colour lenses for every property, "
                 "a temperature slider, a discovery time machine and a photo analyzer.",
    "/minerals": "3,100+ minerals with formula, elemental makeup, hardness and density, filterable by element — "
                 "plus the gemstone shelf, crystal systems and rock families.",
    "/mines": "A world map of the flagship mines and, for each raw material, its ore minerals, typical grade, "
              "concentration factor and ore-to-product process.",
    "/impacts": "What extraction costs, by mechanism — acid drainage, tailings, dust — how each harm arises, "
                "what reduces it, and where it has been documented.",
    "/life": "The molecular machinery of life asked the questions an engine is asked: how it works, what it is "
             "made of, what it costs, and the elements it cannot run without.",
    "/cosmos": "The Local Group mapped by true distance, the classes of celestial object, the stellar spectral "
               "sequence, observatories, discoveries, missions and instruments.",
    "/forces": "The four fundamental interactions — what each does, how far it reaches, and how they compare "
               "in strength.",
    "/theories": "A theory shelf from Ptolemy to the holographic principle — status, proponents, and the "
                 "equations each rests on.",
    "/universe": "Every catalogued object placed by direction and distance on one log-radial map you can turn "
                 "over, from the heliopause to the horizon.",
    "/solar": "The solar system as a running model: Keplerian elements and Kepler's equation solved in the "
              "browser, at any date from 1800 to 2050.",
    "/scales": "The ladder of scale from the heliopause to the edge of the observable universe, on one log "
               "axis of light-years.",
    "/timeline": "The history of the universe on a log axis of seconds — Planck epoch to heat death — "
                 "cross-linked to the equations and theories.",
    "/machines": "The canonical engines and machines — how each works, its cycle drawn as a p–V loop, "
                 "efficiency, materials and inventors.",
    "/skills": "Hands-on techniques with the science behind them — tools, steps, safety, how each fails and "
               "how you know it worked.",
    "/billiards": "The physics of the pool table: a live shot lab, a cushion lab, and the equations and "
                  "constants the game runs on.",
    "/equations": "Equations, laws and definitions with every symbol decoded, what each requires and what "
                  "requires it, from the foundations up.",
    "/constants": "CODATA constants with uncertainties, the seven SI defining constants, units and prefixes.",
    "/glossary": "The terms the site uses, each defined once and traced at build time to every page whose "
                 "text uses it.",
    "/explainers": "The people, channels and organisations that explain this material well — with the "
                   "glossary terms each one covers.",
}

CSS = (WEB / "chrome.css").read_text()
JS = (WEB / "chrome.js").read_text()

TITLE = re.compile(r"<title>(.*?)</title>", re.S)
KHEAD = re.compile(r"<!--khead-->.*?<!--/khead-->", re.S)
KCHROME = re.compile(r"<!--kchrome-->.*?<!--/kchrome-->", re.S)
# What the header replaces: the per-template breadcrumb, and the periodic table's eyebrow
KNAV = re.compile(r'[ \t]*<nav class="knav">.*?</nav>\n?', re.S)
EYEBROW = re.compile(r'[ \t]*<div class="eyebrow">.*?</div>\n?', re.S)


def identity(s: str) -> str:
    return s


def route_of(page_file: str) -> str:
    return PAGE_FILES.get(page_file, "/")


def _urls(route: str):
    tail = "" if route == "/" else route
    return SITE + tail, SITE + "/fr" + tail


def head_html(page_file: str, lang: str, title: str, lookup=identity) -> str:
    """Everything between the doctype and the template's own <title>."""
    route = route_of(page_file)
    en, fr = _urls(route)
    url = fr if lang == "fr" else en
    desc = lookup(DESCRIPTIONS.get(route, DESCRIPTIONS["/"]))
    return (
        f'<!--khead--><html lang="{lang}"><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="description" content="{desc}">\n'
        '<meta name="theme-color" content="#f2f4f5" media="(prefers-color-scheme: light)">\n'
        '<meta name="theme-color" content="#0e1116" media="(prefers-color-scheme: dark)">\n'
        f'<link rel="canonical" href="{url}">\n'
        f'<link rel="alternate" hreflang="en" href="{en}">\n'
        f'<link rel="alternate" hreflang="fr" href="{fr}">\n'
        f'<link rel="alternate" hreflang="x-default" href="{en}">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="Kosmos">\n'
        f'<meta property="og:locale" content="{"fr_FR" if lang == "fr" else "en_US"}">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:url" content="{url}">\n'
        f'<meta property="og:image" content="{SITE}{BANNER}">\n'
        '<meta property="og:image:width" content="1800">\n'
        '<meta property="og:image:height" content="514">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<!--/khead-->\n'
    )


def header_html(page_file: str, lang: str, lookup=identity) -> str:
    """The bar on every page: breadcrumb, search, the sections panel, EN · FR.
    Every reader-facing label sits alone inside a block element, so i18n.extract
    sees it as its own string — the same string the home tiles use."""
    route = route_of(page_file)
    en_route, fr_route = route, "/fr" + ("" if route == "/" else route)
    prefix = "/fr" if lang == "fr" else ""

    def href(r: str) -> str:
        return (prefix + r) if r != "/" else (prefix or "/")

    crumb = f'<a class="kh-brand" href="{href("/")}"><div>KOSMOS</div></a>'
    if route in LABELS:
        crumb += f'<span class="kh-sep" aria-hidden="true">/</span><div class="kh-cur">{lookup(LABELS[route])}</div>'

    # the home page has the big search in its hero; everywhere else it lives up here
    search = "" if route == "/" else (
        '<div class="kh-search">'
        f'<input class="kh-q" id="kh-q" type="search" autocomplete="off" spellcheck="false" '
        f'placeholder="{lookup("search Kosmos…")}" aria-label="{lookup("Search Kosmos")}" '
        'aria-controls="kh-results" aria-expanded="false">'
        '<div class="kh-results" id="kh-results" role="listbox" hidden></div>'
        '</div>')

    groups = []
    for glabel, links in GROUPS:
        items = "".join(
            f'<li><a href="{href(r)}"{CURRENT if r == route else ""}><div>{lookup(label)}</div></a></li>'
            for r, label in links)
        groups.append(f'<div class="kh-group"><div class="kh-ghead">{lookup(glabel)}</div><ul class="kh-list">{items}</ul></div>')

    on = ' class="on"'
    switch = (f'<div class="klang" aria-label="{lookup("Language · Langue")}">'
              f'<a href="{en_route}" hreflang="en" lang="en"{on if lang == "en" else ""}><div>EN</div></a>'
              f'<a href="{fr_route}" hreflang="fr" lang="fr"{on if lang == "fr" else ""}><div>FR</div></a></div>')

    return (
        f'<!--kchrome--><header class="khdr" data-page="{route.strip("/") or "home"}">\n'
        '<div class="kh-row">\n'
        f'<nav class="kh-crumb" aria-label="Kosmos">{crumb}</nav>\n'
        f'<div class="kh-tools">{search}'
        f'<button class="kh-menu" type="button" aria-expanded="false" aria-controls="kh-panel">{lookup("Sections")}</button>'
        f'{switch}</div>\n'
        '</div>\n'
        f'<nav class="kh-panel" id="kh-panel" aria-label="Sections" hidden>{"".join(groups)}</nav>\n'
        '</header><!--/kchrome-->'
    )


def inject(html: str, page_file: str, lang: str = "en", lookup=identity) -> str:
    """A built page, with the head and the header on. The CSS goes into the page's first
    <style>; the header and its script go right after it, before any page script, so a
    template may call KosmosSearch synchronously."""
    html = KNAV.sub("", html, count=1)
    html = EYEBROW.sub("", html, count=1)
    m = TITLE.search(html)
    title = lookup(m.group(1)) if m else "Kosmos"
    i = html.find("</style>")
    assert i >= 0, f"{page_file}: no <style> to hang the chrome on"
    html = html[:i] + "\n" + CSS + html[i:]
    j = html.find("</style>") + len("</style>")
    html = (html[:j] + "\n" + header_html(page_file, lang, lookup)
            + "\n<script>" + JS + "</script>" + html[j:])
    return "<!doctype html>" + head_html(page_file, lang, title, lookup) + html


def replace_blocks(html: str, page_file: str, lang: str, title: str, lookup=identity) -> str:
    """Swap both fenced blocks for their versions in another language — what the French
    build does after it has translated and rewritten everything else."""
    html = KHEAD.sub(lambda _: head_html(page_file, lang, title, lookup).rstrip("\n"), html, count=1)
    html = KCHROME.sub(lambda _: header_html(page_file, lang, lookup), html, count=1)
    return html


def sitemap_xml(lastmod: str) -> str:
    routes = sorted({r for r in PAGE_FILES.values()}, key=lambda r: (r != "/", r))
    rows = []
    for route in routes:
        en, fr = _urls(route)
        alt = (f'<xhtml:link rel="alternate" hreflang="en" href="{en}"/>'
               f'<xhtml:link rel="alternate" hreflang="fr" href="{fr}"/>')
        for loc in (en, fr):
            rows.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod>{alt}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n")


ROBOTS = f"User-agent: *\nAllow: /\nDisallow: /api/\nSitemap: {SITE}/sitemap.xml\n"


def write_sitemap(pub: Path, lastmod: str) -> None:
    (pub / "sitemap.xml").write_text(sitemap_xml(lastmod))
    (pub / "robots.txt").write_text(ROBOTS)
    print(f"wrote public/sitemap.xml ({2 * len(PAGE_FILES)} urls) and public/robots.txt")
