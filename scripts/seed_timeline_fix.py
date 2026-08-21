"""Correct five temperatures and one time on Cosmic Timeline [DB].

Found by the two checks now running in build.py:build_timeline_page.

CHECK 1, T = T0(1 + z), the cleanest relation in cosmology. Nine of eleven
rows carrying both already agreed to better than 15%; the three below did
not, and in every case the redshift is the trustworthy half:

  Cosmic Noon              T 9 -> 8.2 K    z = 2 gives 8.18
  The First Stars          T 50 -> 57 K    z = 20 gives 57.2
  Dark Energy Takes Over   T 3.6 -> 3.8 K  z = 0.4 gives 3.82

CHECK 2, the radiation era, where t = 2.42 g*^-1/2 (1 MeV / T)^2 s. The
well-known anchors were already right to within 40% -- nucleosynthesis at
180 s and 10^9 K, neutrino decoupling at 1 s and 10^10 K -- but two rows
earlier than that were not:

  Electroweak Symmetry     t 1e-12 -> 1e-11 s. The temperature (10^15 K,
  Breaking                 about 100 GeV) is the standard figure and implies
                           3e-11 s. The time was low by a factor of 30.

  Quark Epoch              T 1e13 -> 2e14 K. It carried exactly the same
                           temperature as Quark Confinement, which cannot be:
                           confinement is what ENDS the quark epoch, so it
                           must be the cooler of the two. At the epoch's
                           stated 10^-9 s the temperature is about 2 x 10^14 K.

Not touched, and worth saying why: Baryogenesis and Electroweak Symmetry
Breaking still sit at the same temperature. That is not an error -- in
electroweak baryogenesis they are the same event -- but the database gives
them separate times, which is a claim it cannot support. Left for a human.

Unlike sync_rows this OVERWRITES. Idempotent.
Run on the VPS:  ./deploy.sh seed_timeline_fix
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, query_all  # noqa: E402

DS = "3c1ab928-8ffa-48e7-b0bc-b90e16480a46"      # Cosmic Timeline [DB]
KEY = "Event"

FIXES = {
    "Cosmic Noon": {"Temperature (K)": 8.2},
    "The First Stars": {"Temperature (K)": 57},
    "Dark Energy Takes Over": {"Temperature (K)": 3.8},
    "Electroweak Symmetry Breaking": {"Seconds After Big Bang": 1e-11},
    "Quark Epoch": {"Temperature (K)": 2e14},
}


def title_of(page, prop=KEY):
    p = page["properties"].get(prop, {})
    return "".join(x["plain_text"] for x in p.get("title", [])) or None


def current(page, prop):
    p = page["properties"].get(prop, {})
    return p.get("number") if p.get("type") == "number" else None


if __name__ == "__main__":
    pages = {title_of(p): p for p in query_all(DS) if title_of(p)}
    missing = [n for n in FIXES if n not in pages]
    if missing:
        sys.exit(f"rows not in the database: {missing}")

    fixed = skipped = 0
    for name, props in FIXES.items():
        page = pages[name]
        changed = {k: v for k, v in props.items() if current(page, k) != v}
        if not changed:
            skipped += 1
            print(f"  ok       {name}")
            continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {k: {"number": v} for k, v in changed.items()}})
        fixed += 1
        for k, v in changed.items():
            print(f"  FIXED    {name} · {k}: {current(page, k):g} -> {v:g}")
    print(f"timeline fix: {fixed} rows corrected, {skipped} already correct")
