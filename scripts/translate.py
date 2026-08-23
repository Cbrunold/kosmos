"""Fill data/i18n/fr.json — the English → French cache the French pages are built from.

    python3 scripts/translate.py            # build, extract, translate what is new, rebuild
    python3 scripts/translate.py --dry      # build, extract, report what would be sent; no API call
    ./deploy.sh translate                   # the same on the VPS, then fetch, build, ship, commit, push

What it does: builds the English pages (extraction works on built HTML, so the
templates, the Notion data and build.py's own text are all covered), walks every
page with scripts/i18n.extract, sends the strings the cache does not have to
claude-opus-5 in batches, saves after every batch (a crash loses nothing), drops
cached strings no page uses any more, and rebuilds so public/fr/ reflects it.

Cost is proportional to what changed: a first run is the whole site (~370k
characters); after that, the sentences edited in Notion since last time. The
cache is committed, so a build anywhere — without a key — produces the same
French pages.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import i18n  # noqa: E402


def build():
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], check=True, stdout=subprocess.DEVNULL)


def main(argv):
    dry = "--dry" in argv
    print("building the English pages")
    build()
    tr = i18n.Translator()
    live = set()
    per_page = []
    for page in i18n.PAGE_FILES:
        f = ROOT / "public" / page
        if not f.exists():
            continue
        spans, strs = i18n.extract(f.read_text(), page)
        texts = {t for _, _, t in spans} | strs
        new = 0
        for t in texts:
            k = i18n.key_of(t)
            live.add(k)
            if k not in tr.cache:
                tr.want(t); new += 1
        per_page.append((page, len(texts), new))
    pruned = tr.prune(live)
    for page, n, new in per_page:
        print(f"  {page:16} {n:5} strings · {new:5} new")
    chars = sum(len(s) for s in tr.pending.values())
    print(f"{len(tr.cache)} cached · {len(tr.pending)} to translate ({chars:,} chars) · {pruned} stale dropped")
    if dry:
        for s in sorted(tr.pending.values(), key=len)[:40]:
            print("   ", repr(s[:100]))
        tr.save()
        return
    if tr.pending:
        i18n.translate_pending(tr)
    tr.save()
    print("rebuilding with the new cache")
    build()
    print("done —", len(tr.cache), "strings in", tr.path.relative_to(ROOT))


if __name__ == "__main__":
    main(sys.argv[1:])
