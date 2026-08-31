"""Add Swordsmithing to Skills [DB] — the blade as a carbon problem.

/skills already has Forging (moving hot steel) and Heat Treating Steel
(hardening it afterwards). Neither says the thing a sword is actually about:
that every property a blade has is set by how much carbon is dissolved in its
iron, that no single carbon content gives both an edge and a spine, and that
the answer is to put two different steels in one bar and then harden only part
of it.

So the card is built on the carbon axis and the old French shop classification
that names its bands — fer under 0.1 %, then doux, mi-doux, dur, extra-dur —
with the two points that matter to a smith marked on it: the 0.2 % core and the
0.7 % skin of a Japanese blade, and the ~1.7 % ceiling past which the alloy is
not steel at all. There the melting point has fallen from 1,538 °C toward the
1,147 °C eutectic and the first liquid appears around 1,250 °C, so the welding
fire a low-carbon billet sits happily in melts this one and it runs out of the
hearth instead of forging — which is the sense in which over-carburised iron
goes to lead in the fire. What survives is brittle: the carbon it could not
dissolve sits as cementite on the grain boundaries.

Everything else hangs off equations the shelf already carries: Zener–Hollomon
for the forging window, Arrhenius and the Heat Equation for the carbon
diffusion that folding and decarburisation both are, Hall–Petch for what the
folds and the low finish buy, Newton's cooling and Fourier for the clay coat
that lets the edge quench to martensite while the spine cools to pearlite, and
Griffith for the cold shut at a weld that fails a year later.

The numbers are the traditional ones and the prose says which are conventions:
the classification boundaries move by a tenth of a percent between sources, and
1.7 % against the 2.11 % phase line is the same disagreement.

Idempotent like the other seeds — sync_rows inserts if missing and backfills
only empty fields, relations are unioned, nothing a human edited is overwritten.
Run on the VPS:  ./deploy.sh seed_swordsmithing
Then, for the French mirror:  ./deploy.sh translate
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, query_all, sync_rows, title_of  # noqa: E402
from seed_engineering import ELEMENTS_DS, EQ_DS, SKILLS_DS  # noqa: E402

# name, category, difficulty, summary, science, tools, steps, safety, fails, done, elements, equations, machines
SKILLS = [
    ("Swordsmithing", "Metalwork", "Advanced",
     "Building a blade out of two steels of different carbon content — a hard skin that will hold an edge wrapped round a soft core that will not snap — and then quenching it under a coat of clay so that only the edge hardens.",

     "A blade is a carbon problem before it is anything else. Carbon dissolved in iron is what a quench has to work with, and the traditional French shop classification names the bands by what they do under a hammer and a file: below about 0.1 % it is not steel at all but fer — soft, tough, unhardenable, it bends before it breaks and will never hold an edge; 0.1–0.3 % is acier doux; 0.3–0.6 % mi-doux; 0.6–0.7 % dur, which quenches hard and is where an edge lives; and above roughly 0.7 % extra-dur, harder and more wear-resistant still, and increasingly willing to crack rather than bend. The boundaries move by a tenth of a percent between sources — they are conventions laid over a continuum, not phase lines — but the ordering never moves, and neither does the ceiling. Past about 1.7 % the alloy has left steel behind: it is cast iron, its melting point has fallen from 1,538 °C for pure iron toward the 1,147 °C eutectic, and the first liquid now appears around 1,250 °C, inside the range of the welding fire a low-carbon billet sits happily in. It does not forge, it slumps and runs; and what survives is brittle, because the carbon it could not dissolve stands as cementite along the grain boundaries where the hammer finds it.\n"
     "A sword needs two of those bands at once — an edge hard enough to cut, a body tough enough to be hit — and no single carbon content gives both. Hence two steels in one bar: for the Japanese blade, kawagane, the skin, brought to about 0.7 %, forged into a U and welded round shingane, a core near 0.2 % that cannot harden and is there precisely because it cannot. The smith does not buy those numbers, he makes them. Tamahagane out of the tatara is inhomogeneous — carbon runs from under 0.1 % to over 1.5 % within one bloom — so the cakes are broken and sorted on the fracture face, bright and faceted for the high-carbon skin, grey and fibrous for the core, and adjusted from there by where in the fire a piece is held: near the tuyere, in the oxygen, carbon burns out of it.\n"
     "Folding does three things, and layer count is the least of them. Each weld at about 1,300 °C halves the thickness of every slag stringer and every carbon-rich or carbon-poor patch and doubles their number, so fifteen folds is 2¹⁵ = 32,768 layers and, far more usefully, a homogeneity fifteen halvings finer than the bloom's. Each fold also loses carbon from the surface it has just opened, which is how a 1.5 % piece is brought down to 0.7 % — and why a bar folded too many times finishes soft. Diffusion does the smoothing and it is slow: with D ≈ 1×10⁻¹⁰ m²/s for carbon in austenite at 1,200 °C, √(Dt) is about a third of a millimetre in ten minutes, so a hundred heats blur a layer boundary and never erase the difference between skin and core. The same arithmetic run at the surface of an oxidising fire is decarburisation, which is why a blade is forged oversize and ground back through its own soft skin.\n"
     "The hammering itself lives inside the ordinary hot-working window — above the A₃ line the steel recrystallises as fast as it is deformed and so never work-hardens, and temperature trades against strain rate through the Zener–Hollomon parameter — but the sword's version is unforgiving at both ends: high-carbon skin steel wants 1,150 °C down to about 850 °C and nothing below it. The last blows are struck low on purpose, so the strain just put in recrystallises into fine grain instead of feeding coarse. That is worth real strength by Hall–Petch, σ_y ∝ d^(−1/2), and it is the one gain that raises toughness alongside it.\n"
     "Then the quench, which is the point of the whole exercise and the moment most blades are lost. Clay — clay, charcoal powder and stone dust, mixed thin — is painted over the finished blade: a film along the edge, several millimetres over the spine. Heated in a darkened shop to just above the transformation, around 780–800 °C (a magnet lets go at 770 °C, the one fixed point a hand can check), and quenched edge-first into water at 30–40 °C, the bare edge sheds heat fast enough to miss the nose of the transformation curve and freezes as martensite: carbon trapped in a distorted lattice, glass-hard, brittle, and the least dense structure iron takes. Under the clay the spine cannot — Fourier's law through a few millimetres of insulator is enough to slow it below the critical rate — so it cools to soft pearlite. The blade bends the wrong way first as the thin edge contracts, then comes back as the martensite forms and expands, and takes its curvature in about a second; the visible boundary between the two structures, the hamon, is a phase map that follows the clay line, not a decoration. Tempering at 150–200 °C afterwards trades a little of that hardness back for the toughness to survive being used.",

     "A charcoal hearth with a blower or box bellows, deep enough to hold a reducing pocket, and pine charcoal cut to size — the fuel is a variable here, not a detail. A small hard anvil bedded solid, a 1–1.5 kg hand hammer and a 3–5 kg sledge if someone will strike for you, tongs that fit a flat bar. Wet washi paper, a clay-and-straw-ash slurry for the stacking weld, and a spatula-handled plate to build the stack on. A hardy, a hot cut and a chisel for the fold notches; a sen scraper and coarse files for the cold finish. Clay, charcoal powder and stone dust for the hardening coat, and a brush. A quench tank long enough to take the whole blade at once, with a thermometer in it. A magnet, calipers, a straightedge, a bucket of vermiculite. And a polisher's stones, or the polisher — the finished geometry and the visibility of the hamon are their work, not the smith's.",

     "Sort the steel before anything else. Break the tamahagane cakes and read the fractures: bright and faceted is high carbon, grey and fibrous is low. Set aside two piles — the skin near 0.7 %, the core near 0.2 % — and reckon on about ten kilograms of raw material for one long blade, most of which leaves as scale and offcuts.\n"
     "Adjust what the piles are not. Held near the tuyere in the oxygen, carbon burns out of a piece; held back in the reducing pocket under a cover of charcoal, it does not. Cakes are heated and water-quenched flat so that they break cleanly and can be re-sorted.\n"
     "Stack and weld. Two to three kilograms of sorted flakes are built onto a handle plate, bound in wet washi, coated in clay slurry and straw ash to keep the air off, and brought to about 1,300 °C — a colour with no name in daylight, which is one reason the shop is dark. Consolidate with light, fast blows; heavy ones only spray the stack.\n"
     "Fold twelve to sixteen times, alternating lengthwise and crosswise so the grain runs both ways. Notch, fold over the edge of the anvil, flux, weld the whole face in one heat, draw back out. Brush the scale off before every weld: oxide does not move like the metal under it, and a blow presses it in as an inclusion that will never close.\n"
     "Build the composite. Draw the skin steel to a long plate, forge it into a U, insert the soft core, weld the assembly closed along its length, and check that the core has not been squeezed out of the point.\n"
     "Sunobe: draw the billet to the blade's length and section. Then hizukuri at about 1,100 °C — establish the edge, the shinogi ridge and the mune, and shape the kissaki — working down to a dull red and stopping there. Below about 850 °C the high-carbon skin is being damaged, not shaped.\n"
     "Normalise, then finish cold. Two or three descending air cools to refine the grain, then a sen scraper and files to true the geometry, because after hardening it can only be ground.\n"
     "Coat: a thin film of clay along the edge, several millimetres over the spine and the shinogi, feathered wherever the hamon is meant to move. Let it dry completely — clay that flakes in the tank takes the hamon with it.\n"
     "Yaki-ire, in the dark: heat the whole blade evenly to just above the magnet, spine leading so the thin edge does not overshoot, and quench edge-first into water at 30–40 °C in one movement. It will hiss, bend, and come back.\n"
     "Temper at 150–200 °C for an hour. Then check: sight down it, measure the curvature against what was planned, and correct the straightness by tapping the spine or by local warming — gently, knowing a hardened blade has very little give left.\n"
     "Finish the tang: shape the nakago, cut the yasurime file marks, drill the mekugi-ana, and cut the signature and the date last, once the blade has proved it survived. Then it goes to the polisher.",

     "Charcoal in a closed shop makes carbon monoxide, which is what actually kills smiths: an alarm on the wall and the door open. The quench tank flashes steam off a blade's whole surface at once — face and arms covered, no synthetics, and never a lidded vessel. Hammer on anvil runs 110–120 dB and hearing does not grow back. Hot steel and cold steel are the same colour, and a blade is long enough to burn someone standing behind you. Scale comes off the work and the anvil both: side-shielded glasses always. Never heat galvanised or unknown scrap — zinc buys a night of fever, cadmium can kill. A blade that cracks in the quench can throw a piece. And the object at the end is a weapon: what may be made, kept or carried is a matter of local law, and worth reading before the fire is lit.",

     "The quench crack — a ping in the tank and a line running up from the edge — from water too cold or steel too hot, an over-thick clay edge, a sharp internal corner, or a flaw that was already there. It is the failure everyone plans around, and it ends the blade. A hamon that never appears, or appears in patches: under temperature, water too warm, or clay that lifted. Delamination at the skin-core weld months later, from a cold shut hammered closed over its own oxide — never a weld, and by Griffith's criterion the stress needed to run it as a crack falls as one over the square root of its length. Curvature wrong or reversed, from heating unevenly along the length. A skin that will not harden at all: decarburised in too many long oxidising heats, or folded until the carbon that should sit at 0.7 % is down near 0.3 %. Hot shortness — edges crumbling like wet chalk at yellow — from sulfur, which is exactly what a charcoal smelt keeps out of tamahagane and scrap does not. Coarse grain from soaking at yellow, which normalising undoes; burnt steel, which sparks and crumbles and nothing undoes.",

     "Out of the polish, the hamon runs unbroken from the tang to the point and follows the line the clay was painted on; the hada shows the folding, with no dark seam that opens under the corner of a chisel. The blade is straight in both planes and its curvature is where it was planned to be. A file skates on the edge and bites on the spine — the two steels doing two different jobs, which is the whole design. It rings rather than thuds when tapped. And it cuts a rolled mat without chipping the edge or taking a set, then sights straight afterwards.",

     ["Fe", "C", "Si", "P", "S", "Ti"],
     ["Zener–Hollomon Parameter", "Hall–Petch Relationship", "Arrhenius Equation", "Heat Equation",
      "Griffith Fracture Criterion", "Newton's Law of Cooling", "Fourier's Law of Heat Conduction"],
     []),
]


def union_relation(page, prop, ids):
    cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
    new = cur | set(ids)
    return {prop: {"relation": [{"id": x} for x in sorted(new)]}} if new != cur else {}


def main():
    print("skills")
    schema = ensure_props(SKILLS_DS, {}, "skills")
    ensure_select_options(SKILLS_DS, "Category", sorted({s[1] for s in SKILLS}), "skills")
    sync_rows(SKILLS_DS, schema,
              [{"Name": n, "Category": cat, "Difficulty": d, "Summary": su, "The Science": sci, "Tools": t,
                "Steps": st, "Safety": sa, "How It Fails": fa, "Done When": dn}
               for n, cat, d, su, sci, t, st, sa, fa, dn, _, _, _ in SKILLS], "skills")

    print("\nrelations")
    skills = {title_of(p, "Name"): p for p in query_all(SKILLS_DS) if title_of(p, "Name")}
    eqs = {title_of(p, "Name"): p["id"] for p in query_all(EQ_DS) if title_of(p, "Name")}
    els = {}
    for p in query_all(ELEMENTS_DS):
        sym = "".join(x["plain_text"] for x in p["properties"].get("Notation", {}).get("rich_text", [])).strip()
        if sym:
            els[sym] = p["id"]

    missing, changed, edges = set(), 0, 0
    for n, *_, syms, eqn, _mach in SKILLS:
        page = skills.get(n)
        if not page:
            missing.add(f"skill:{n}")
            continue
        payload = {}
        for prop, names, lookup in (("Elements", syms, els), ("Equations", eqn, eqs)):
            ids = [lookup[x] for x in names if x in lookup]
            missing.update(f"{n} -> {prop}:{x}" for x in names if x not in lookup)
            payload.update(union_relation(page, prop, ids))
            edges += len(ids)
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
            changed += 1
    print(f"  skills: updated {changed} · {edges} links")

    if missing:
        print("\nunresolved names ignored:")
        for m in sorted(missing):
            print("  ", m)
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
