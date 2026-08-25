"""Add the biologists. There were none.

188 researchers on file and not one of them worked on life — no Darwin, no
Mendel, no Pasteur. The two apparent hits when the databases were searched for
biology were Goodenough and Grove, matching the word "cell" in a battery.

The gap was worse than an omission, because the site already carries their work.
Michaelis-Menten is on the equations shelf and neither author was here. So is
Goldman-Hodgkin-Katz, and so is the Nernst equation that sits underneath it —
three equations, five missing people. Those come first in this list; the rest
are here because a science portal without Darwin is a strange object.

Fields are new to the Researchers DB (Biochemistry, Neurophysiology, Molecular
Biology, X-ray Crystallography and so on), and are added to the select if it is
one. Nobel entries follow the format already in the column — "Chemistry 2019" —
so medicine is written "Medicine" rather than the prize's full "Physiology or
Medicine", which would not fit the tag the card draws.

Dates were checked rather than recalled: Goldman 1910-1998 and the constant-field
equation derived for his 1943 doctorate, Woese 1928-2012, Hazen born 1948.

Idempotent: adds missing rows, backfills empty fields, overwrites nothing.
Run on the VPS:  ./deploy.sh seed_biologists
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, query_all, sync_rows, title_of  # noqa: E402

RESEARCHER_DS = "4cc8d7c4-9008-4017-a09b-7087720aebd3"

# name, lifespan, nationality, field, known for, Nobel ("" if none)
PEOPLE = [
    # ---- the people behind equations the site already shows
    ("Walther Nernst", "1864–1941", "German", "Physical Chemistry",
     "The Nernst equation — the voltage a concentration gradient can drive — which is the foundation under every membrane potential, and the third law of thermodynamics.", "Chemistry 1920"),
    ("Leonor Michaelis", "1875–1949", "German", "Biochemistry",
     "With Menten, the equation for how fast an enzyme works and how that changes with substrate. Still the first thing anyone is taught about enzyme kinetics.", ""),
    ("Maud Menten", "1879–1960", "Canadian", "Biochemistry",
     "Co-author of the Michaelis–Menten equation, and one of the first Canadian women to earn a medical doctorate — she had to leave the country to be allowed to do research.", ""),
    ("David E. Goldman", "1910–1998", "American", "Biophysics",
     "The constant-field equation, derived for his doctorate at Columbia in 1943, which became the G in Goldman–Hodgkin–Katz.", ""),
    ("Alan Hodgkin", "1914–1998", "British", "Neurophysiology",
     "With Huxley, measured the action potential in a squid's giant axon and modelled it well enough to predict it — the first quantitative account of how a nerve fires.", "Medicine 1963"),
    ("Andrew Huxley", "1917–2012", "British", "Neurophysiology",
     "Half of Hodgkin–Huxley, and later the sliding-filament theory of how a muscle actually shortens.", "Medicine 1963"),
    # ---- the rest
    ("Antonie van Leeuwenhoek", "1632–1723", "Dutch", "Microbiology",
     "A draper with no training who ground his own lenses past 270× and was the first to see bacteria, protists and spermatozoa — then reported them to the Royal Society for fifty years.", ""),
    ("Charles Darwin", "1809–1882", "British", "Evolutionary Biology",
     "Natural selection: worked out in the 1830s, sat on for twenty years, and published in 1859 only because Wallace had arrived at the same idea.", ""),
    ("Gregor Mendel", "1822–1884", "Moravian", "Genetics",
     "Inheritance as discrete units, from some 28,000 pea plants. Published in 1866 into complete silence and rediscovered in 1900, sixteen years after he died.", ""),
    ("Louis Pasteur", "1822–1895", "French", "Microbiology",
     "Germ theory, and the swan-neck flask that ended spontaneous generation. He also discovered molecular chirality by sorting two mirror-image tartrate crystals under a lens with tweezers.", ""),
    ("Rosalind Franklin", "1920–1958", "British", "X-ray Crystallography",
     "Photograph 51, and the measurements that fixed DNA's dimensions. It was shown to Watson without her knowledge; she died at 37, four years before the prize.", ""),
    ("Francis Crick", "1916–2004", "British", "Molecular Biology",
     "With Watson, the double helix in 1953 — and afterwards the central dogma and the shape of the coding problem.", "Medicine 1962"),
    ("James Watson", "1928–", "American", "Molecular Biology",
     "With Crick, the structure of DNA, built on Franklin's diffraction data and Chargaff's base ratios.", "Medicine 1962"),
    ("Dorothy Hodgkin", "1910–1994", "British", "X-ray Crystallography",
     "Solved penicillin, vitamin B₁₂ and insulin by X-ray diffraction. B₁₂ took eight years and showed the cobalt sitting at its centre.", "Chemistry 1964"),
    ("Frederick Sanger", "1918–2013", "British", "Biochemistry",
     "Sequenced insulin, proving a protein has a definite sequence, then invented the method for sequencing DNA. The only person with two Nobel prizes in chemistry.", "Chemistry 1958 & 1980"),
    ("Barbara McClintock", "1902–1992", "American", "Genetics",
     "Transposable elements in maize: genes that move. Reported in 1950, disbelieved for decades, and given the prize at 81.", "Medicine 1983"),
    ("Lynn Margulis", "1938–2011", "American", "Evolutionary Biology",
     "Endosymbiosis — mitochondria and chloroplasts were free-living bacteria taken inside another cell and never digested. Rejected by fifteen journals, now textbook.", ""),
    ("Carl Woese", "1928–2012", "American", "Microbiology",
     "Read ribosomal RNA to build a tree of life from sequence rather than shape, and found a third domain nobody had suspected: the archaea.", ""),
    ("Robert Hazen", "1948–", "American", "Mineralogy",
     "Mineral evolution: most of Earth's five thousand mineral species exist because life changed the atmosphere, and up to two-thirds of them date from the rise of oxygen.", ""),
]


def main():
    schema = ensure_props(RESEARCHER_DS, {"Nobel": {"rich_text": {}}}, "researchers")
    if schema.get("Field") == "select":
        ensure_select_options(RESEARCHER_DS, "Field", sorted({p[3] for p in PEOPLE}), "researchers")
    sync_rows(RESEARCHER_DS, schema,
              [{"Name": n, "Lifespan": ls, "Nationality": nat, "Field": f, "Known For": k}
               for n, ls, nat, f, k, _ in PEOPLE],
              "researchers", key="Name")
    # Nobel is its own pass: sync_rows fills it only if the column is in the row map,
    # and most of these have no prize, so an empty string would write a blank rather
    # than leave the field alone
    pages = {title_of(p, "Name"): p for p in query_all(RESEARCHER_DS) if title_of(p, "Name")}
    n = 0
    for name, _, _, _, _, nobel in PEOPLE:
        if not nobel:
            continue
        page = pages.get(name)
        if not page:
            print(f"  ! no row for {name!r}")
            continue
        if "".join(x.get("plain_text", "") for x in (page["properties"].get("Nobel") or {}).get("rich_text", [])).strip():
            continue
        call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
             {"properties": {"Nobel": {"rich_text": [{"type": "text", "text": {"content": nobel}}]}}})
        n += 1
    print(f"nobel: {n} filled")


if __name__ == "__main__":
    main()
