"""Add crustal abundance to the "All Periodical Elements" database in Notion.

Rarity is the one thing the periodic table could not show: Notion has
"Nat. Occurrence" (primordial / from decay / synthetic), which is where an
element came from, not how much of it there is. This adds a "Crustal Abundance"
number property in parts per million by mass and fills all 118 rows.

Values are continental-crust averages, chiefly Rudnick & Gao (2003) as carried
by the CRC Handbook. They span twenty-four orders of magnitude — oxygen at 46%
by mass down to astatine, of which the entire crust holds a few grams at any
moment — so anything reading these should use a log scale.

Elements 95 and up are left empty rather than set to zero: americium onward do
not occur naturally at all, and a zero would render as a real measurement.
Technetium, promethium, and the heavy decay-chain members do occur, in traces
so small the figures are order-of-magnitude estimates rather than measurements.

Idempotent, and never overwrites a value already set.
Run on the VPS:  python3 scripts/seed_abundance.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path
from notion import token, headers, call, query_all  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
ELEMENTS_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"   # All Periodical Elements
PROP = "Crustal Abundance"

# symbol -> parts per million by mass in the continental crust.
# None = does not occur naturally.
ABUNDANCE = {
    "H": 1400, "He": 0.008, "Li": 20, "Be": 2.8, "B": 10,
    "C": 200, "N": 19, "O": 461000, "F": 585, "Ne": 0.005,
    "Na": 23600, "Mg": 23300, "Al": 82300, "Si": 282000, "P": 1050,
    "S": 350, "Cl": 145, "Ar": 3.5, "K": 20900, "Ca": 41500,
    "Sc": 22, "Ti": 5650, "V": 120, "Cr": 102, "Mn": 950,
    "Fe": 56300, "Co": 25, "Ni": 84, "Cu": 60, "Zn": 70,
    "Ga": 19, "Ge": 1.5, "As": 1.8, "Se": 0.05, "Br": 2.4,
    "Kr": 1e-4, "Rb": 90, "Sr": 370, "Y": 33, "Zr": 165,
    "Nb": 20, "Mo": 1.2, "Tc": 1e-13, "Ru": 0.001, "Rh": 0.001,
    "Pd": 0.015, "Ag": 0.075, "Cd": 0.15, "In": 0.25, "Sn": 2.3,
    "Sb": 0.2, "Te": 0.001, "I": 0.45, "Xe": 3e-5, "Cs": 3,
    "Ba": 425, "La": 39, "Ce": 66.5, "Pr": 9.2, "Nd": 41.5,
    "Pm": 2e-19, "Sm": 7.05, "Eu": 2, "Gd": 6.2, "Tb": 1.2,
    "Dy": 5.2, "Ho": 1.3, "Er": 3.5, "Tm": 0.52, "Yb": 3.2,
    "Lu": 0.8, "Hf": 3, "Ta": 2, "W": 1.25, "Re": 7e-4,
    "Os": 0.0015, "Ir": 0.001, "Pt": 0.005, "Au": 0.004, "Hg": 0.085,
    "Tl": 0.85, "Pb": 14, "Bi": 0.0085, "Po": 2e-10, "At": 3e-20,
    "Rn": 4e-13, "Fr": 1e-18, "Ra": 9e-7, "Ac": 5.5e-10, "Th": 9.6,
    "Pa": 1.4e-6, "U": 2.7, "Np": 3e-12, "Pu": 3e-11,
    # 95–118: synthetic only, no natural crustal abundance
    "Am": None, "Cm": None, "Bk": None, "Cf": None, "Es": None,
    "Fm": None, "Md": None, "No": None, "Lr": None, "Rf": None,
    "Db": None, "Sg": None, "Bh": None, "Hs": None, "Mt": None,
    "Ds": None, "Rg": None, "Cn": None, "Nh": None, "Fl": None,
    "Mc": None, "Lv": None, "Ts": None, "Og": None,
}


def main():
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{ELEMENTS_DS}")
    if PROP not in ds["properties"]:
        call("PATCH", f"https://api.notion.com/v1/data_sources/{ELEMENTS_DS}",
             {"properties": {PROP: {"number": {"format": "number"}}}})
        print(f"created property {PROP!r}")
    else:
        print(f"property {PROP!r} already exists")

    rows = query_all(ELEMENTS_DS)
    print(f"{len(rows)} element rows in Notion")

    set_, skipped, unknown, natural_none = 0, 0, [], 0
    for r in rows:
        p = r["properties"]
        sym = "".join(x["plain_text"] for x in p.get("Notation", {}).get("rich_text", [])).strip()
        name = "".join(x["plain_text"] for x in p.get("Element", {}).get("title", [])).strip()
        if sym not in ABUNDANCE:
            unknown.append(f"{name} ({sym or 'no notation'})")
            continue
        val = ABUNDANCE[sym]
        if val is None:
            natural_none += 1
            continue                       # synthetic: leave empty, not zero
        if p.get(PROP, {}).get("number") is not None:
            skipped += 1
            continue                       # already answered
        call("PATCH", f"https://api.notion.com/v1/pages/{r['id']}",
             {"properties": {PROP: {"number": val}}})
        set_ += 1

    if unknown:
        print("  no abundance defined for:", ", ".join(unknown))
    print(f"abundance: {set_} set, {skipped} already had a value, "
          f"{natural_none} left empty as synthetic")
    print("\nnow run: python3 scripts/fetch_elements.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
