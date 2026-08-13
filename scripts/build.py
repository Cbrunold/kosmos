"""Assemble public/index.html from the web/ sources and the synced element data.

    python3 scripts/build.py

Inputs:  web/periodic-table.template.html  (the periodic table page, __DATA__ placeholder)
         web/analyzer.{css,html,js}        (photo -> elemental breakdown feature)
         data/chemistry/elements.json      (synced from Notion via scripts/fetch_elements.py)
Output:  public/index.html                 (the single file server.js serves)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"

tpl = (WEB / "periodic-table.template.html").read_text()
css = (WEB / "analyzer.css").read_text()
html = (WEB / "analyzer.html").read_text()
js = (WEB / "analyzer.js").read_text()

# late-bind paint() so the analyzer's wrapper applies on search/theme repaints
for old, new in [
    ("q.addEventListener('input', paint);", "q.addEventListener('input', () => paint());"),
    ("matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paint);",
     "matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => paint());"),
]:
    assert old in tpl, f"template drifted, marker missing: {old}"
    tpl = tpl.replace(old, new)

tpl = tpl.replace("</style>", css + "</style>", 1)
tpl = tpl.replace('<div class="layout">', html + '\n<div class="layout">', 1)
head, sep, _ = tpl.rpartition("</script>")
tpl = head + js + sep + "\n"

data = json.dumps(json.load(open(ROOT / "data" / "chemistry" / "elements.json")),
                  separators=(",", ":")).replace("</", "<\\/")
tpl = tpl.replace("__DATA__", data)

dest = ROOT / "public" / "index.html"
dest.write_text(tpl)
print(f"wrote {len(tpl)} bytes -> {dest.relative_to(ROOT)}")
