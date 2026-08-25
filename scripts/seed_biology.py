"""Give the elements and the minerals their biological dimension.

The site had biology in it already and never said so: six biophysics equations
(Michaelis-Menten, Goldman-Hodgkin-Katz, Poiseuille, Reynolds), five of the
eighteen mining impacts are biological mechanisms, and every major biomineral
was sitting unlabelled in a 3,142-row Minerals DB. What was missing was the
label, not the content.

Two fields, no new databases:

  Elements gets "Biological Role" (prose) and "Biological Class" (Bulk / Trace /
  Ultratrace / Not essential). Eleven elements are 99.9 % of a body by mass;
  eight more are established trace requirements; a dozen are essential to some
  organisms and not others. That is a lens on the periodic table, and it pairs
  with Crustal Abundance into the comparison the site could not make before:
  what the crust is made of against what life is made of.

  Minerals gets "Biological Role" on the eighteen rows that have one — bone,
  shell, nacre, kidney stones, the magnetite in magnetotactic bacteria and in
  chiton teeth, the goethite in limpet teeth.

Deliberately not filled: a role for every element. Most have none, and writing
"no known role" 88 times would be noise; the class field carries that. Where an
element is a notable poison rather than a nutrient the note says so, because
that is what connects it to /impacts.

Idempotent: adds the properties if missing, fills only empty fields.
Run on the VPS:  ./deploy.sh seed_biology
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, query_all, title_of  # noqa: E402

ELEMENTS_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"   # All Periodical Elements
MINERALS_DS = "a2db78db-efb7-4952-b8bc-e4ab98d42264"   # Minerals
ROLE = "Biological Role"
KLASS = "Biological Class"
CLASSES = ["Bulk", "Trace", "Ultratrace", "Not essential"]

# symbol -> (class, role).  Role omitted where there is nothing to say.
ELEMENTS = {
    # ---- the bulk eleven: 99.9 % of a body by mass
    "O":  ("Bulk", "The largest share of body mass, about 65 %, most of it water. Also the terminal electron acceptor that makes aerobic respiration roughly sixteen times more productive than fermentation."),
    "C":  ("Bulk", "The backbone of every organic molecule: four bonds, catenation, and a chemistry rich enough to build everything alive. About 18 % of body mass."),
    "H":  ("Bulk", "Half the atoms in a body. Water, every organic molecule, and the proton gradients across membranes that ATP synthase turns into ATP."),
    "N":  ("Bulk", "In every amino acid and every nucleotide base. The atmosphere is 78 % N₂ and almost inert, so life depends on nitrogen fixation to reach it."),
    "Ca": ("Bulk", "Bone and shell as phosphate and carbonate, and the intracellular signal that triggers muscle contraction and neurotransmitter release."),
    "P":  ("Bulk", "The backbone of DNA and RNA, the P in ATP, and as hydroxylapatite most of the mineral in bone."),
    "K":  ("Bulk", "The dominant cation inside cells. The gradient it holds against sodium is the resting membrane potential."),
    "S":  ("Bulk", "In cysteine and methionine; the disulfide bridges between cysteines hold protein shapes together."),
    "Na": ("Bulk", "The dominant cation outside cells, and the other half of the gradient every nerve impulse spends."),
    "Cl": ("Bulk", "The counter-ion to sodium and potassium, and the acid in stomach hydrochloric acid."),
    "Mg": ("Bulk", "At the centre of chlorophyll, and the cofactor for essentially every enzyme that handles ATP."),
    # ---- established trace requirements
    "Fe": ("Trace", "Haemoglobin and myoglobin carry oxygen on it; cytochromes pass electrons along it. Its deficiency is the commonest nutritional disorder in the world."),
    "Zn": ("Trace", "Structural or catalytic in thousands of enzymes, and in the zinc-finger proteins that read DNA."),
    "Cu": ("Trace", "In cytochrome c oxidase at the end of the respiratory chain, and in the haemocyanin that carries oxygen in molluscs and arthropods — which is why their blood is blue."),
    "Mn": ("Trace", "In the oxygen-evolving complex of photosystem II: the four-manganese cluster that splits water, and so the source of every oxygen atom in the air."),
    "I":  ("Trace", "Thyroid hormones, and nothing else. Its deficiency is the commonest preventable cause of intellectual disability."),
    "Se": ("Trace", "In selenocysteine, the twenty-first amino acid, at the active site of the glutathione peroxidases that clear peroxides."),
    "Mo": ("Trace", "At the active site of nitrogenase, and of the enzymes that reduce nitrate and sulfite."),
    "Co": ("Trace", "The atom at the centre of vitamin B₁₂ — the only known biological use of cobalt, and the only vitamin with a metal in it."),
    # ---- essential to some organisms, or beneficial and still argued
    "F":  ("Ultratrace", "Substitutes into tooth apatite as fluorapatite, which needs a lower pH to dissolve. Beneficial rather than established as essential."),
    "Cr": ("Ultratrace", "Long listed as essential for glucose tolerance; the evidence weakened and it is now usually classed as beneficial at most."),
    "Ni": ("Ultratrace", "The active-site metal of urease — the first enzyme ever crystallised — and of the hydrogenases of many bacteria."),
    "V":  ("Ultratrace", "In vanadium nitrogenase and in the bromoperoxidases of algae, and concentrated a millionfold by sea squirts for reasons still unsettled."),
    "B":  ("Ultratrace", "Essential to plants, where it cross-links pectin in the cell wall. The case in animals is unresolved."),
    "Si": ("Ultratrace", "As amorphous silica it builds diatom frustules, radiolarian skeletons, sponge spicules and the phytoliths that stiffen grasses."),
    "Br": ("Ultratrace", "Required to cross-link collagen IV in basement membranes — shown in 2014, which makes it the most recently established essential element."),
    "W":  ("Ultratrace", "The heaviest element with a known biological role: tungsten enzymes in some archaea and anaerobic bacteria, filling the seat molybdenum takes elsewhere."),
    "Cd": ("Ultratrace", "A marine diatom runs a cadmium carbonic anhydrase where zinc is scarce — the only known essential use of an element that is otherwise purely toxic."),
    "Sr": ("Ultratrace", "Follows calcium into bone and shell, and acantharean radiolarians build their whole skeleton from celestine, strontium sulfate."),
    "As": ("Ultratrace", "Some marine algae make arsenosugars and one bacterium respires arsenate. Otherwise a poison, and it works by impersonating phosphate."),
    # ---- no role, but worth saying why they matter
    "Pb": ("Not essential", "No biological role. It mimics calcium and zinc closely enough to enter bone and jam enzymes, with no threshold known to be safe."),
    "Hg": ("Not essential", "No biological role. Bacteria methylate it into methylmercury, which crosses membranes and accumulates up the food chain."),
    "Al": ("Not essential", "No known role, despite being the commonest metal in the crust — largely because it is locked in silicates and nearly insoluble at the pH life runs at."),
    "U":  ("Not essential", "No biological role. Chemically it is a heavy-metal kidney poison first and a radiological hazard second."),
}

# mineral name -> role
MINERALS = {
    "Calcite": "Shells of foraminifera and coccolithophores, sea-urchin spines, and the calcite lenses in brittlestar arms that work as an eye.",
    "Aragonite": "Nacre and coral skeletons. Molluscs choose it over calcite even though it is the less stable polymorph.",
    "Vaterite": "The least stable calcium carbonate: fish otoliths where they have gone wrong, gastropod shell repair, and some sponge spicules.",
    "Monohydrocalcite": "In the otoliths of some fish and in guano-derived deposits — one of the few places this hydrate forms at all.",
    "Hydroxylapatite": "The mineral of bone and dentine. Enamel is the same compound grown as much larger crystals, which is why it is harder and cannot be repaired.",
    "Fluorapatite": "Shark tooth enameloid, and what tooth apatite partly becomes with fluoride: harder to dissolve because it needs a lower pH.",
    "Whitlockite": "The second most abundant mineral in bone, and a common component of dental calculus.",
    "Weddellite": "Calcium oxalate dihydrate: kidney stones, and the raphide crystals plants grow as a defence against being eaten.",
    "Whewellite": "The oxalate monohydrate — the commoner kidney stone, and the crust many lichens deposit on rock.",
    "Struvite": "Magnesium ammonium phosphate. Infection stones, formed when urease-positive bacteria raise urine pH past where it precipitates.",
    "Magnetite": "Magnetotactic bacteria grow chains of it to follow field lines; chitons cap their radular teeth with it, the hardest biomineral known; and it appears in the navigation of birds and salmon.",
    "Goethite": "Limpet teeth are goethite fibres in a chitin matrix — among the strongest biological materials ever measured.",
    "Pyrite": "Framboidal pyrite forms where microbes reduce sulfate in anoxic sediment, which is why its texture is read as a fossil of bacterial activity.",
    "Celestine": "Acantharean radiolarians build their entire skeleton from strontium sulfate — the only organisms known to do so, and the reason their skeletons dissolve after death.",
    "Barite": "Barium sulfate statocysts, used as gravity sensors by some algae and by Loxodes ciliates.",
    "Gypsum": "Statoliths in some jellyfish, and a product of sulfur-oxidising bacteria in caves.",
    "Dolomite": "Microbially mediated in modern lagoons — part of the answer to why dolomite is abundant in old rock and hard to make in a laboratory.",
    "Siderite": "Forms in anoxic, iron-rich pore water where microbes reduce iron, which makes it a marker for those conditions.",
}


def rt(s):
    return {"rich_text": [{"type": "text", "text": {"content": s}}]}


def fill(ds, label, want, key_prop, props, get_key):
    ensure_props(ds, props, label)
    if KLASS in props:
        ensure_select_options(ds, KLASS, CLASSES, label)
    rows = query_all(ds)
    filled = missing = 0
    seen = set()
    for r in rows:
        k = get_key(r)
        if k not in want:
            continue
        seen.add(k)
        p, patch = r["properties"], {}
        val = want[k]
        klass, role = val if isinstance(val, tuple) else (None, val)
        if role and not (p.get(ROLE) or {}).get("rich_text"):
            patch[ROLE] = rt(role)
        if klass and not (p.get(KLASS) or {}).get("select"):
            patch[KLASS] = {"select": {"name": klass}}
        if patch:
            call("PATCH", f"https://api.notion.com/v1/pages/{r['id']}", patch)
            filled += 1
    missing = [k for k in want if k not in seen]
    print(f"{label}: {filled} filled, {len(want)} defined"
          + (f", NOT MATCHED: {missing}" if missing else ""))


def main():
    fill(ELEMENTS_DS, "elements", ELEMENTS, "Notation",
         {ROLE: {"rich_text": {}}, KLASS: {"select": {"options": [{"name": c} for c in CLASSES]}}},
         lambda r: "".join(x["plain_text"] for x in
                           (r["properties"].get("Notation") or {}).get("rich_text", [])).strip())
    fill(MINERALS_DS, "minerals", MINERALS, "Name", {ROLE: {"rich_text": {}}},
         lambda r: title_of(r, "Name"))
    print("\nnow run: python3 scripts/fetch_elements.py && python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
