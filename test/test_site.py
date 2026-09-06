"""The invariants that have already broken once, pinned.

    python3 -m pytest -q

Runs against the committed build (public/, data/) and needs no token and no network;
node is used where it is on the path (slug parity, French scripts parsing) and those
tests are skipped where it is not. Each test names the incident it exists for.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402
import check_fr  # noqa: E402
import chrome  # noqa: E402
import i18n  # noqa: E402

PUB = ROOT / "public"
EN_PAGES = sorted(PUB.glob("*.html"))
FR_PAGES = sorted((PUB / "fr").glob("*.html"))
ALL_PAGES = EN_PAGES + FR_PAGES
SERVER = (ROOT / "server.js").read_text()
ROUTES = dict(re.findall(r"^\s+'(/[\w./-]*)': '([\w./-]+)',", SERVER, re.M))   # route -> file in public/
SCRIPT = re.compile(r"<script(?![^>]*\btype=(?![\"'](?:text/javascript|module)))[^>]*>(.*?)</script>", re.S)
NODE = check_fr.node_bin()


def page_html(path: Path) -> str:
    return path.read_text()


def all_names():
    """Every entity name the site slugs, from the data the pages are built from."""
    names = set()
    for rows in build.notion.values():
        for r in rows:
            for k in ("Name", "Term", "Event", "Force Name", "Object ID"):
                if isinstance(r.get(k), str):
                    names.add(r[k])
    names |= {e["name"] for e in build.elements}
    return sorted(names)


# ---------------------------------------------------------------- slugs
@pytest.mark.skipif(NODE is None, reason="node not found")
@pytest.mark.parametrize("template", sorted(p.name for p in (ROOT / "web").glob("*.template.html")
                                            if "const slug = " in p.read_text()))
def test_python_slugify_matches_every_page_js_slug(template):
    """The 2026-08 incident: build.py's slugify deleted a character JS treated as a
    separator, and 96 search deep-links landed on the right page and scrolled nowhere.
    Every template with its own slug() must agree with Python on every name."""
    src = (ROOT / "web" / template).read_text()
    m = re.search(r"const slug = \(s\) =>.*?;", src, re.S)
    assert m, f"{template}: slug() not found"
    js = m.group(0) + "\nconst names = JSON.parse(require('fs').readFileSync(0, 'utf8'));\n" \
                      "process.stdout.write(JSON.stringify(names.map(slug)));"
    names = all_names()
    out = subprocess.run([NODE, "-e", js], input=json.dumps(names), capture_output=True, text=True, check=True)
    got = json.loads(out.stdout)
    bad = [(n, build.slugify(n), g) for n, g in zip(names, got) if build.slugify(n) != g]
    assert not bad, f"{template}: {len(bad)} names slug differently, e.g. {bad[:3]}"


# ---------------------------------------------------------------- data blocks
@pytest.mark.parametrize("page", ALL_PAGES, ids=lambda p: str(p.relative_to(PUB)))
def test_data_blocks_parse_like_a_browser(page):
    """/cosmos was dead from 2026-08-20 to 09-06: Python wrote Infinity into a data block,
    read it back happily, and the browser threw on the page's first JSON.parse."""
    html = page_html(page)
    for b in i18n.JSON_BLOCK.finditer(html):   # the home page has none: its numbers are placeholders
        json.loads(b.group(2), parse_constant=check_fr._reject)


# ---------------------------------------------------------------- what a page calls
@pytest.mark.parametrize("page", ALL_PAGES, ids=lambda p: str(p.relative_to(PUB)))
def test_page_defines_what_its_scripts_call(page):
    """The periodic table called vocab() from 2026-08-23 on a page that never defined it,
    because it was written by a path that skipped the injection. Every helper a page's
    scripts use must be defined on that page."""
    html = page_html(page)
    scripts = "\n".join(m.group(1) for m in SCRIPT.finditer(html))
    if re.search(r"\bvocab\(", scripts):
        assert "const vocab = " in html, f"{page.name}: calls vocab() but never defines it"
    if "KosmosSearch." in scripts:
        assert "window.KosmosSearch = " in html, f"{page.name}: uses KosmosSearch but never defines it"


# ---------------------------------------------------------------- search index
PLAIN = {"equation", "theory", "researcher", "event", "mine", "machine", "skill", "term", "explainer",
         "life", "impact", "structure"}
PREFIXED = {"galaxy": "lg-", "observatory": "obs-", "discovery": "disc-", "mission": "mission-", "instrument": "instr-"}
STATIC = {"catalogue", "spectral", "instruments", "prefixes", "units"}


def test_search_index_targets_exist():
    """Every search result must land somewhere: a route the server answers, and an anchor
    the target page will have — either in its HTML or as slug(name) of a name that page's
    data carries, so its script will create it."""
    idx = json.loads((PUB / "search.json").read_text())
    symbols = {e["notation"] for e in build.elements}
    pages = {}
    bad = []
    assert all(href.startswith("/people#") for kind, _, _, _, href in idx["items"] if kind == "researcher"), \
        "every researcher lands on /people — 114 used to point at a /cosmos anchor that page never rendered"
    for kind, name, sub, text, href in idx["items"]:
        route, _, anchor = href.partition("#")
        if route not in ROUTES or not ROUTES[route].endswith(".html"):
            bad.append((kind, name, href, "no such route")); continue
        html = pages.setdefault(route, (PUB / ROUTES[route]).read_text())
        if kind in PLAIN or kind in PREFIXED:
            want = PREFIXED.get(kind, "") + build.slugify(name)
            if anchor != want:
                bad.append((kind, name, href, f"anchor should be {want}")); continue
            if json.dumps(name, ensure_ascii=False)[1:-1] not in html and name not in html:
                bad.append((kind, name, href, "name absent from the page's data"))
        elif kind == "element":
            if anchor not in symbols:
                bad.append((kind, name, href, "anchor is not an element symbol"))
        elif kind in ("mineral", "gemstone"):
            if anchor != name.lower():
                bad.append((kind, name, href, "anchor should be the lower-cased name"))
        elif anchor in STATIC or kind in ("spectral type", "object class"):
            if anchor in STATIC and f'id="{anchor}"' not in html:
                bad.append((kind, name, href, "static anchor missing from the page"))
        elif anchor and not re.fullmatch(r"[a-z0-9-]+", anchor):
            bad.append((kind, name, href, "anchor is not slug-shaped"))
    assert not bad, f"{len(bad)} search targets would miss, e.g. {bad[:5]}"


# ---------------------------------------------------------------- the chrome
@pytest.mark.parametrize("page", ALL_PAGES, ids=lambda p: str(p.relative_to(PUB)))
def test_every_page_has_the_chrome(page):
    """Until 2026-09-06 no page had a viewport meta, a description, or a nav past the
    breadcrumb; the English pages had no doctype at all. All of it comes from one place."""
    html = page_html(page)
    lang = "fr" if page.parent.name == "fr" else "en"
    assert html.startswith("<!doctype html>")
    assert f'<html lang="{lang}">' in html
    for needle in ('<meta name="viewport"', '<meta name="description" content="', '<link rel="canonical" href="',
                   '<meta property="og:title"', 'class="khdr"', 'class="kh-panel"', 'class="klang"'):
        assert needle in html, f"{page.relative_to(PUB)}: missing {needle}"
    if lang == "fr":
        assert 'href="https://kosmos.yeahborhood.com/fr' in html


def test_sitemap_and_robots_cover_every_route():
    sitemap = (PUB / "sitemap.xml").read_text()
    for route, file in ROUTES.items():
        if not file.endswith(".html") or route == "/index.html":
            continue
        en = chrome.SITE + ("" if route == "/" else route)
        assert f"<loc>{en}</loc>" in sitemap, f"{route} missing from sitemap"
        assert f"<loc>{chrome.SITE}/fr{'' if route == '/' else route}</loc>" in sitemap, f"/fr{route} missing from sitemap"
    assert "Sitemap: " + chrome.SITE + "/sitemap.xml" in (PUB / "robots.txt").read_text()


# ---------------------------------------------------------------- the checks that gate a deploy
@pytest.mark.parametrize("script", ["check_content.py", "check_fr.py"])
def test_deploy_checks_pass(script):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


# ---------------------------------------------------------------- the scripts' shape
def test_only_notion_py_talks_to_notion():
    """Thirteen scripts once carried their own token() and pagination loop; a second copy
    is where the next divergence starts."""
    offenders = []
    for p in ROOT.glob("scripts/**/*.py"):
        if p.name == "notion.py":
            continue
        s = p.read_text()
        for fn in ("def token(", "def query_all(", "def find_ds("):
            if fn in s:
                offenders.append(f"{p.relative_to(ROOT)}: {fn}")
    assert not offenders, offenders


def test_one_shot_scripts_live_in_migrations():
    stray = sorted(p.name for p in ROOT.glob("scripts/fix_*.py")) + sorted(p.name for p in ROOT.glob("scripts/*_fix.py"))
    assert not stray, f"one-shot scripts belong in scripts/migrations/: {stray}"


@pytest.mark.parametrize("script", sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("scripts/**/*.py")))
def test_every_script_compiles(script):
    subprocess.run([sys.executable, "-m", "py_compile", str(ROOT / script)], check=True)


# ---------------------------------------------------------------- billiards
def test_billiards_constants_have_one_source():
    """/billiards used to hardcode every constant its lab ran on while its numbers tab restated
    them as prose, and nothing read anything. data/billiards/constants.json is now both: the
    lab reads every key, the table is rendered from the list, and no constant is typed twice."""
    cj = json.loads((ROOT / "data/billiards/constants.json").read_text())["constants"]
    tpl = (ROOT / "web/billiards.template.html").read_text()
    physics = (ROOT / "web/billiards/physics.js").read_text()
    for c in cj:
        assert f"C.{c['key']}" in physics, f"{c['key']} is in the table but the physics never reads it"
    typed = re.findall(r"const (?:R|M|G|E_BB|MU_S|MU_R|MU_SP|MU_C|TABLE_L|TABLE_W|RP|SHELF_C|SHELF_S|SW_K) = [0-9]", tpl + physics)
    typed += re.findall(r"E_C = Math\.sqrt\([0-9]", tpl + physics)
    assert not typed, f"constants typed into the lab again: {typed}"
    for fn in ("function step(", "function collide(", "function shoot(", "function bounce(", "function cushion("):
        assert fn not in tpl, f"{fn} belongs in web/billiards/physics.js, not the template"
    page = (PUB / "billiards.html").read_text()
    data = json.loads(next(b.group(2) for b in i18n.JSON_BLOCK.finditer(page)))
    assert data["constants"] == {c["key"]: c["value"] for c in cj}
    assert [r[0] for r in data["table"]["rows"]] == [c["name"] for c in cj]


# ---------------------------------------------------------------- entity URLs (server.js)
@pytest.fixture(scope="module")
def server():
    """server.js on a spare port, serving the committed build."""
    if NODE is None:
        pytest.skip("node not found")
    import os, socket, time, urllib.request
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0)); port = sock.getsockname()[1]
    proc = subprocess.Popen([NODE, str(ROOT / "server.js")], env={**os.environ, "PORT": str(port)},
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1); break
            except Exception:
                time.sleep(0.1)
        else:
            proc.kill(); pytest.fail("server.js did not come up: " + proc.stderr.read()[-500:])
        yield f"http://127.0.0.1:{port}"
    finally:
        proc.kill()


def _get(url, **headers):
    import urllib.request, urllib.error
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=5)
        return r.status, r.read().decode(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), dict(e.headers)


def test_entity_url_serves_the_section_page_as_that_entity(server):
    """/equations/pythagorean-theorem unfurls as the theorem, not as the shelf, and lands on
    its card; every search result's href has such a URL."""
    status, html, h = _get(server + "/equations/pythagorean-theorem")
    assert status == 200
    assert "<title>Pythagorean Theorem · Kosmos</title>" in html
    assert '<link rel="canonical" href="https://kosmos.yeahborhood.com/equations/pythagorean-theorem">' in html
    assert '<meta property="og:title" content="Pythagorean Theorem · Kosmos">' in html
    assert "history.replaceState(null, '', \"/equations#pythagorean-theorem\")" in html
    assert _get(server + "/equations/pythagorean-theorem", **{"If-None-Match": h["ETag"]})[0] == 304
    status, html, _ = _get(server + "/fr/people/albert-einstein")
    assert status == 200 and '<html lang="fr">' in html and "/fr/people#albert-einstein" in html
    assert _get(server + "/equations/no-such-thing")[0] == 404
    assert _get(server + "/nope/pythagorean-theorem")[0] == 404


@pytest.mark.skipif(NODE is None, reason="node not found")
def test_billiards_physics_under_node():
    """The physics core lives in web/billiards/physics.js so node can run it against closed
    forms: the ninety-degree rule at e = 1, momentum kept, energy never made, the slide
    distance the integrator finds against the formula, throw peaking near half-ball, the
    cushion running long and reverse short, a straight shot that drops."""
    r = subprocess.run([NODE, "--test", str(ROOT / "test/billiards/physics.test.cjs")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
