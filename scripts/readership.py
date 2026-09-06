"""Who reads the site — from nginx's own access log, with nothing added to the pages.

    python3 scripts/readership.py              # the last 7 days
    python3 scripts/readership.py --days 30
    python3 scripts/readership.py --log path   # a log other than /var/log/nginx/kosmos.access.log

deploy/nginx-kosmos.conf writes the site's requests to /var/log/nginx/kosmos.access.log
(combined format); logrotate keeps the .1 and .N.gz behind it, and this reads them all.

What it counts: page views by people — bots, uptime monitors, curl and the deploy's own
health checks are dropped by user agent and by path — and visitors, which is a hash of
address + agent + day that exists only inside this run. The raw address is never
printed, and nothing here is stored. Then: the pages read, English vs French, phone vs
desktop, and where readers came from. Run it on the VPS; the log is not in the repo.
"""
import argparse
import glob
import gzip
import hashlib
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

LOG = "/var/log/nginx/kosmos.access.log"
LINE = re.compile(r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>\S+) (?P<path>\S+) [^"]*" '
                  r'(?P<status>\d{3}) (?P<bytes>\d+|-) "(?P<ref>[^"]*)" "(?P<ua>[^"]*)"')
BOT = re.compile(r"bot|crawl|spider|slurp|fetch|scan|monitor|curl|wget|python|httpx|go-http|java/|"
                 r"headless|lighthouse|pingdom|uptime|facebookexternalhit|preview|validator|feed", re.I)
PHONE = re.compile(r"Mobile|Android|iPhone|iPad|iPod", re.I)
SKIP = re.compile(r"^/(health|api/|assets/|search\.json|sitemap\.xml|robots\.txt|favicon)")
SALT = hashlib.sha1(str(datetime.now(timezone.utc).timestamp()).encode()).hexdigest()  # per run: hashes cannot be joined across runs


def lines(path: str):
    for f in sorted(glob.glob(path + "*"), key=lambda p: (p.endswith(".gz"), p)):
        opener = gzip.open if f.endswith(".gz") else open
        try:
            with opener(f, "rt", errors="replace") as fh:
                yield from fh
        except OSError as e:
            print(f"  (could not read {f}: {e})", file=sys.stderr)


def route_of(path: str):
    """('/elements', 'en') from anything the server answers 200 for; None if not a page."""
    p = urlsplit(path).path.rstrip("/") or "/"
    if SKIP.match(p):
        return None
    lang = "en"
    if p == "/fr" or p.startswith("/fr/"):
        lang, p = "fr", (p[3:] or "/")
    if p == "/index.html":
        p = "/elements"
    return p, lang


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--log", default=LOG)
    a = ap.parse_args(argv)
    if not glob.glob(a.log + "*"):
        sys.exit(f"no log at {a.log} — the site's own access_log is set in deploy/nginx-kosmos.conf; "
                 "once that is live on the VPS, readers start being counted from then on")
    since = datetime.now(timezone.utc) - timedelta(days=a.days)

    views = Counter(); by_day = defaultdict(Counter); visitors = defaultdict(set)
    langs = Counter(); phone = Counter(); refs = Counter(); status = Counter()
    dropped = Counter(); n_lines = 0
    for raw in lines(a.log):
        m = LINE.match(raw)
        if not m:
            dropped["unparsed"] += 1; continue
        n_lines += 1
        try:
            t = datetime.strptime(m["time"], "%d/%b/%Y:%H:%M:%S %z")
        except ValueError:
            dropped["bad time"] += 1; continue
        if t < since:
            continue
        if m["method"] != "GET":
            dropped["not GET"] += 1; continue
        status[m["status"]] += 1
        if m["status"] not in ("200", "304"):
            continue
        if BOT.search(m["ua"]) or not m["ua"] or m["ua"] == "-":
            dropped["bots & monitors"] += 1; continue
        r = route_of(m["path"])
        if r is None:
            dropped["not a page"] += 1; continue
        route, lang = r
        day = t.strftime("%Y-%m-%d")
        who = hashlib.sha1(f"{SALT}|{day}|{m['ip']}|{m['ua']}".encode()).hexdigest()
        views[route] += 1
        by_day[day]["views"] += 1
        visitors[day].add(who)
        visitors[route].add(who)
        langs[lang] += 1
        screen = "phone" if PHONE.search(m["ua"]) else "desktop"
        phone[screen] += 1
        if screen == "phone":
            by_day[day]["phone"] += 1
        host = urlsplit(m["ref"]).netloc.lower() if m["ref"] not in ("-", "") else "(direct)"
        if "kosmos.yeahborhood.com" not in host:
            refs[host or "(direct)"] += 1

    total = sum(views.values())
    print(f"kosmos readership — last {a.days} days · {n_lines:,} log lines read · {total:,} page views by people")
    if not total:
        print("  nothing yet.")
        for k, v in dropped.most_common():
            print(f"  dropped {v:,} {k}")
        return
    print()
    print("  day          views  visitors  phone")
    for day in sorted(by_day):
        d = by_day[day]
        print(f"  {day}  {d['views']:6,}  {len(visitors[day]):8,}  {100 * d['phone'] / d['views']:4.0f}%")
    print()
    print("  page                    views  visitors")
    for route, n in views.most_common():
        print(f"  {route:22} {n:6,}  {len(visitors[route]):8,}")
    print()
    share = lambda c, k: f"{100 * c[k] / max(1, sum(c.values())):.0f}%"   # noqa: E731
    print(f"  language   en {share(langs, 'en')} · fr {share(langs, 'fr')}")
    print(f"  screen     desktop {share(phone, 'desktop')} · phone {share(phone, 'phone')}")
    print()
    print("  came from")
    for host, n in refs.most_common(12):
        print(f"  {host:34} {n:6,}")
    print()
    print("  dropped: " + " · ".join(f"{v:,} {k}" for k, v in dropped.most_common()) if dropped else "")
    print("  status:  " + " · ".join(f"{k} ×{v:,}" for k, v in sorted(status.items())))


if __name__ == "__main__":
    main(sys.argv[1:])
