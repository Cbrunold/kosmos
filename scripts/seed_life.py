"""Create and seed Life [DB]: the molecular machinery.

The site already has a page for engines — how each one works, what it is made
of, what it costs, how efficient it is. This is the same page for the machines
inside a cell, and the parallel is not a conceit: ATP synthase is a rotary motor
with a stator and a drive shaft, the bacterial flagellum is an electric motor
run on protons instead of electrons, and kinesin walks. They are described the
way /machines describes a turbine because that is what they are.

What makes them belong here rather than in a biology textbook is the Elements
column. Photosystem II needs four manganese atoms, nitrogenase a molybdenum-iron
cluster, carbonic anhydrase a zinc, haemoglobin four irons, chlorophyll a
magnesium. Those are the same elements the periodic table now carries a
biological role for, so the page chips through to them and the story closes:
the elements say what life uses them for, and this says what it built with them.

Numbers are quoted where they are well established and the organism is named
where the figure depends on it — a bacterial ribosome and a human one differ by
a factor of five and it would be sloppy to print one number for both.

Idempotent: creates the database if missing, backfills empty fields, never
overwrites an edit made in Notion.
Run on the VPS:  ./deploy.sh seed_life
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_glossary import find_ds  # noqa: E402
from seed_theories import call, ensure_props, ensure_select_options, sync_rows  # noqa: E402

PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"   # Physical Sciences
TITLE = "Life [DB]"
KINDS = ["Motor", "Enzyme", "Pump", "Carrier", "Pigment", "Structure", "Copier"]

# name, kind, elements it needs, how it works, the number that pins it down
LIFE = [
    ("ATP synthase", "Motor", ["H", "Mg"],
     "A rotary motor. Protons crossing the membrane turn a ring of subunits like water turning a wheel, and the shaft attached to it deforms three catalytic sites in turn, each squeezing ADP and phosphate together into ATP. It runs backwards just as happily, spending ATP to pump protons.",
     "Around three ATP per revolution, and hundreds of revolutions a second. A human body turns over roughly its own mass in ATP each day, almost all of it here."),
    ("Ribosome", "Copier", ["Mg", "P"],
     "Reads messenger RNA three bases at a time and builds the protein it specifies, catching each amino acid on a transfer RNA that pairs with the codon. The catalytic site is RNA, not protein, which is the strongest evidence that RNA came first.",
     "About 20 amino acids a second in a bacterium, nearer 2 to 5 in a human cell. An error roughly every 10,000 residues."),
    ("Rubisco", "Enzyme", ["Mg", "C", "O"],
     "Fixes carbon dioxide onto a five-carbon sugar, the first step of turning air into biomass. It is also slow, and it confuses oxygen for carbon dioxide often enough that plants run a whole salvage pathway to clean up after it.",
     "Three or so carbon dioxide molecules a second per site — dismal for an enzyme, and compensated for by sheer quantity. It is thought to be the most abundant protein on Earth."),
    ("Photosystem II", "Enzyme", ["Mn", "Ca", "O"],
     "Uses the energy of four photons to strip four electrons from two water molecules, releasing O₂. The work is done by a cluster of four manganese atoms and one calcium, which cycles through five oxidation states to store up the charge before letting go.",
     "Four photons per oxygen molecule. Every oxygen atom in the atmosphere has passed through a cluster like this one."),
    ("Nitrogenase", "Enzyme", ["Mo", "Fe", "S"],
     "Breaks the triple bond in atmospheric N₂ — one of the strongest in chemistry — at ambient temperature and pressure, on a cluster of molybdenum, iron and sulfur. Oxygen destroys it, so organisms that use it must keep it in an anoxic pocket.",
     "Sixteen ATP per nitrogen molecule fixed. Industry does the same job at 400 °C and 200 atmospheres."),
    ("Carbonic anhydrase", "Enzyme", ["Zn"],
     "Converts carbon dioxide and water to bicarbonate and back, with a single zinc atom holding a hydroxide ion in position to attack. Without it the reaction is far too slow to move CO₂ out of tissue at the rate breathing requires.",
     "Up to a million reactions a second — among the fastest enzymes known, and close to the limit set by how fast substrate can diffuse to it."),
    ("Haemoglobin", "Carrier", ["Fe", "O"],
     "Four subunits, each with an iron atom in a haem ring, each binding one oxygen molecule. Binding one makes the next easier, so it loads almost fully in the lungs and unloads sharply in tissue — the cooperativity is the whole trick.",
     "Four oxygen molecules per protein, and about 270 million proteins in a single red blood cell."),
    ("Chlorophyll", "Pigment", ["Mg", "N"],
     "The antenna. A magnesium atom at the centre of a flat nitrogen ring, absorbing red and blue light and passing the energy on to the reaction centre. It reflects green, which is why the world looks the way it does.",
     "Structurally the same ring as haem, with magnesium in place of iron — the two most important pigments in biology differ by one atom."),
    ("Sodium–potassium pump", "Pump", ["Na", "K", "P"],
     "Spends one ATP to push three sodium ions out and haul two potassium ions in, against both gradients. That imbalance is the battery every nerve impulse discharges, and it is the gradient the Goldman–Hodgkin–Katz equation describes.",
     "Three sodium out, two potassium in, per ATP. In a resting neuron this pump alone can take more than half the cell's energy budget."),
    ("Cytochrome c oxidase", "Enzyme", ["Cu", "Fe", "O"],
     "The last step of respiration: takes electrons that have come down the whole chain and hands them to oxygen, making water. Two copper centres and two haem irons pass the charge along, and the energy released pumps protons for ATP synthase to spend.",
     "Four electrons and four protons per oxygen molecule. This is where almost all the oxygen you breathe ends up."),
    ("DNA polymerase", "Copier", ["Mg", "P"],
     "Copies a DNA strand base by base, and — crucially — checks its own work, backing up to excise a wrong base before continuing. The proofreading is worth about a hundredfold in accuracy on its own.",
     "Around 1,000 bases a second in a bacterium, with a final error rate near one in a billion once repair has finished."),
    ("Kinesin", "Motor", ["Mg", "P"],
     "Walks. Two heads step alternately along a microtubule, each step powered by one ATP, hauling cargo from the centre of a cell towards its edge. Its opposite number, dynein, walks the other way.",
     "An 8-nanometre step per ATP, roughly 100 steps a second — about a micron of travel every ten seconds."),
    ("Myosin", "Motor", ["Mg", "Ca", "P"],
     "The motor of muscle. Heads project from a thick filament, grab the neighbouring actin filament, pull, and let go — millions in parallel and out of step, so the pull is smooth. Calcium is the signal that uncovers the binding sites and starts it.",
     "Each head cycles a few times a second; a muscle shortens because a great many heads are pulling at once, not because any one is fast."),
    ("Bacterial flagellar motor", "Motor", ["H"],
     "An electric motor built from protein: a rotor, a ring of stator units, and a drive shaft turning a helical filament like a propeller. It is driven by protons falling across the membrane, and it can reverse in under a millisecond, which is how a bacterium changes direction.",
     "Up to a few hundred revolutions a second in E. coli, and over a thousand in some species."),
    ("Collagen", "Structure", ["C", "N", "O", "Br"],
     "A rope of three chains wound together, the most abundant protein in a mammal and the tension-bearing half of bone, tendon and skin. Its network form, collagen IV, is cross-linked with bromine — the discovery that made bromine an essential element in 2014.",
     "Roughly a third of all protein in a mammal by mass. Its tensile strength approaches that of steel wire, per unit mass."),
    ("Cellulose", "Structure", ["C", "H", "O"],
     "Glucose chains laid flat and hydrogen-bonded side by side into fibres that almost nothing can digest — the reason wood and cotton exist, and the reason herbivores keep microbes to do the digesting for them.",
     "The most abundant organic polymer on the planet, produced on the order of 10¹¹ tonnes a year."),
]


def main():
    props = {
        "Kind": {"select": {"options": [{"name": k} for k in KINDS]}},
        "Elements": {"multi_select": {}},
        "Function": {"rich_text": {}},
        "Numbers": {"rich_text": {}},
    }
    ds = find_ds(TITLE)
    if not ds:
        db = call("POST", "https://api.notion.com/v1/databases", {
            "parent": {"type": "page_id", "page_id": PARENT_PAGE},
            "title": [{"type": "text", "text": {"content": TITLE}}],
            "initial_data_source": {"properties": {"Name": {"title": {}}, **props}},
        })
        ds = db["data_sources"][0]["id"]
        print("created", TITLE, ds)
    else:
        print(TITLE, "exists:", ds)
    schema = ensure_props(ds, props, "life")
    ensure_select_options(ds, "Kind", KINDS, "life")
    sync_rows(ds, schema,
              [{"Name": n, "Kind": k, "Elements": els, "Function": fn, "Numbers": num}
               for n, k, els, fn, num in LIFE],
              "life", key="Name")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
