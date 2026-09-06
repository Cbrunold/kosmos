"""Sanity-check the built French pages before they ship.

The failure this exists for: a French apostrophe (l'énergie) landed inside a
single-quoted JS literal and took a whole page's script down with a SyntaxError —
the page still returned 200 and still looked almost right, so nothing else caught it.

Checks, per page in public/fr:
  1. every non-JSON <script> parses (node --check, if node is on the path)
  2. every JSON data block parses, and carries the same number of records as the
     English page it came from
  3. the language switch is present, and internal links point into /fr/
  4. no French text leaked into an href, id or class

Exit code 1 if anything fails, so ./deploy.sh stops before shipping.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import i18n  # noqa: E402

# Real JavaScript only: a script with any type= other than text/javascript or module is
# data, not code — the mines page carries its basemap as <script type="text/plain">.
SCRIPT = re.compile(r"""<script(?![^>]*\btype=(?!["'](?:text/javascript|module)))[^>]*>(.*?)</script>""", re.S)


def _reject(tok):
    raise ValueError(f"{tok} is not JSON a browser will parse")


def node_bin():
    n = shutil.which("node")
    if n:
        return n
    for p in Path.home().glob(".nvm/versions/node/*/bin/node"):
        return str(p)
    return None


def main():
    pub = ROOT / "public"
    node = node_bin()
    if not node:
        print("  note: node not found — skipping the JavaScript syntax check")
    fails = []
    for page in i18n.PAGE_FILES:
        fr, en = pub / "fr" / page, pub / page
        if not fr.exists():
            fails.append(f"{page}: missing from public/fr"); continue
        html, ehtml = fr.read_text(), en.read_text()
        if node:
            for i, m in enumerate(SCRIPT.finditer(html)):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as t:
                    t.write(m.group(1)); tmp = t.name
                r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
                os.unlink(tmp)
                if r.returncode:
                    err = (r.stderr.strip().splitlines() or ["?"])[-3:]
                    fails.append(f"{page}: script #{i} does not parse — {' / '.join(x.strip() for x in err)}")
        fb = list(i18n.JSON_BLOCK.finditer(html))
        eb = list(i18n.JSON_BLOCK.finditer(ehtml))
        if len(fb) != len(eb):
            fails.append(f"{page}: {len(fb)} data blocks, English has {len(eb)}")
        for a, b in zip(fb, eb):
            try:
                # parse like a browser: Python would accept Infinity and NaN, JSON.parse
                # throws on them, and the page's script dies with it
                fd, ed = json.loads(a.group(2), parse_constant=_reject), json.loads(b.group(2), parse_constant=_reject)
            except (json.JSONDecodeError, ValueError) as e:
                fails.append(f"{page}: a data block does not parse in a browser — {e}"); continue
            if isinstance(fd, list) and isinstance(ed, list) and len(fd) != len(ed):
                fails.append(f"{page}: data block has {len(fd)} records, English has {len(ed)}")
        if 'class="klang"' not in html:
            fails.append(f"{page}: no language switch")
        # the switch's EN half is meant to leave the mirror — it is the way back
        body = re.sub(r'<div class="klang".*?</div>', "", html, flags=re.S)
        for bad in re.findall(r'href="/(?!fr/|fr"|/|#)[a-z]+"', body):
            fails.append(f"{page}: link out of the mirror — {bad}")
        for attr in re.findall(r'\b(?:id|class)="([^"]*[À-ÿ][^"]*)"', html):
            fails.append(f"{page}: accented text in an id/class — {attr!r}")
    n = len(i18n.PAGE_FILES)
    if fails:
        print(f"FRENCH CHECK FAILED — {len(fails)} problem(s) across {n} pages:")
        for f in fails[:40]:
            print("   ", f)
        sys.exit(1)
    print(f"french pages ok — {n} pages: scripts parse, data blocks match, links stay in /fr")


if __name__ == "__main__":
    main()
