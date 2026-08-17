"""Create and seed Mining Impacts [DB]: what extraction costs, mechanism by mechanism.

The site's mining half describes how each metal is won and almost nothing about
what winning it does. Measured across all 88 mine notes and 118 element
extraction stories: "tailings" appears once, and acid mine drainage, waste,
closure, subsidence and emissions appear zero times. The glossary defines
Tailings — "stored behind dams" — and no record anywhere carries a fact about
one. This fills that side, prompted by SystExt (systext.org), whose whole
subject it is.

Mechanisms, not sites. A per-mine impact table would need field data for 88
mines on five continents; a mechanism generalises, and Where links it to the
mine types the Mines DB already records, so build.py can count how many mines
on the site each impact attaches to without anyone maintaining a list.

Written to stay descriptive. A tailings dam failure has a mechanism and a death
toll; both are facts. Every figure quoted here was checked against a published
source before it went in, and where no figure is quoted, none was known.

Idempotent: creates the database if missing, backfills empty fields, never
overwrites an edit made in Notion.
Run on the VPS:  ./deploy.sh seed_impacts
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_glossary import find_ds  # noqa: E402
from seed_theories import call, ensure_props, ensure_select_options, sync_rows  # noqa: E402

PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"   # Physical Sciences
TITLE = "Mining Impacts [DB]"

CATEGORIES = ["Water", "Air", "Land", "Health", "Ground", "Energy"]
TIMESCALES = ["During operation", "After closure", "Both"]
# these match the Type values already on Mines [DB], so build.py can join on them
WHERE = ["Open pit", "Underground", "Open pit + underground", "Quarry", "Brine",
         "Placer", "In-situ leach", "Tailings storage", "Heap leach", "Smelter", "Artisanal"]

# name, category, timescale, where, mechanism, mitigation, case
IMPACTS = [
    ("Acid mine drainage", "Water", "Both", ["Open pit", "Underground", "Tailings storage"],
     "Sulfide minerals — pyrite above all — oxidise on contact with air and water to sulfuric acid, and the acid then dissolves metals out of the surrounding rock. Bacteria accelerate the reaction by orders of magnitude. Once it starts it sustains itself for as long as sulfide and oxygen last, which is centuries.",
     "Flooding old workings to exclude oxygen, capping and lining waste rock, adding limestone to neutralise; where the load is too large, treating the water indefinitely.",
     "The Richmond mine at Iron Mountain, California has produced the most acidic water ever measured — pH as low as −3.6, with dissolved metals up to 200 g/L (Nordstrom & Alpers, 2000)."),
    ("Tailings dam failure", "Ground", "Both", ["Tailings storage"],
     "Tailings are stored wet behind embankments often built from the tailings themselves. Saturated fine material can liquefy — losing its strength and flowing like a liquid — under a rise in the water table, an earthquake, or simply the slow creep of an over-steep upstream-raised wall.",
     "Downstream or centreline construction instead of upstream raises, dewatered or thickened tailings, piezometer monitoring, and independent review of the design.",
     "Brumadinho, Brazil, 25 January 2019: a Vale iron ore dam failed without warning and killed about 270 people. Fundão at Mariana, 5 November 2015, killed 19 and carried tailings down 668 km of watercourse."),
    ("Cyanide release", "Water", "During operation", ["Heap leach", "Open pit"],
     "Gold is dissolved out of ore as a cyanide complex, so a working plant holds large volumes of cyanide-bearing solution in ponds and circuits. A wall failure, an overflow after heavy rain, or a pipeline break puts it into surface water, where it is acutely toxic to fish at very low concentrations.",
     "Lined ponds with freeboard for storm events, cyanide destruction circuits before discharge, and the industry's voluntary International Cyanide Management Code.",
     "Baia Mare, Romania, 30 January 2000: a dam at the Aurul plant released about 100,000 m³ of water carrying roughly 100 tonnes of cyanide into the Someș, then the Tisza and the Danube."),
    ("Mercury in artisanal gold", "Health", "Both", ["Artisanal", "Placer"],
     "Small-scale miners mix mercury with crushed ore to amalgamate the gold, then burn the amalgam off with a torch, releasing mercury vapour directly to air and to whoever is holding it. What reaches water is methylated by bacteria into methylmercury, which accumulates up the food chain.",
     "Retorts that condense and recover the vapour, gravity concentration before amalgamation, and mercury-free processing; the Minamata Convention obliges signatory states to reduce and where feasible eliminate its use.",
     "UNEP attributes close to 40 % of all anthropogenic mercury entering the atmosphere to artisanal and small-scale gold mining — the single largest source."),
    ("Arsenic mobilisation", "Water", "After closure", ["Underground", "Open pit", "Smelter"],
     "Arsenic rides with gold and copper in arsenopyrite and enargite. Roasting the ore to free the gold drives off arsenic as a trioxide dust that is water-soluble, where the mineral it came from was not — turning a locked-up element into one that travels.",
     "Capture and stable disposal of roaster dust, arsenic fixation as scorodite, and containment of what has already been produced.",
     "Giant Mine, Yellowknife holds 237,000 tonnes of arsenic trioxide dust in underground chambers. Canada's remediation freezes the surrounding rock with passive thermosyphons, and is planned to hold for at least a century."),
    ("Water table drawdown", "Water", "During operation", ["Open pit", "Underground", "In-situ leach"],
     "A pit or shaft below the water table only stays dry if it is pumped, and pumping lowers the water table across a radius far wider than the hole. Wells, springs and wetlands that depended on that level fall with it, and in arid districts the mine competes directly with everything else drawing on the aquifer.",
     "Recharge of pumped water back to the aquifer, grout curtains around the workings, and allocation limits set from a monitored regional model rather than the mine's own balance.",
     ""),
    ("Riverine tailings disposal", "Water", "During operation", ["Open pit", "Underground"],
     "Where terrain or seismicity makes a dam impractical, some operations have discharged tailings straight into a river system. The load buries the bed, raises it until the river breaks its banks, and spreads fine sediment and metals over the floodplain far downstream.",
     "Now rejected by most regulators and lenders in favour of engineered storage; where it has happened, remediation means dredging and long-term floodplain monitoring.",
     "The Ok Tedi mine in Papua New Guinea discharged to the Fly River system for decades, with sediment aggrading the bed and killing floodplain forest well over 100 km downstream."),
    ("Subsidence", "Ground", "Both", ["Underground", "In-situ leach", "Brine"],
     "Taking rock out leaves a void, and the ground above it eventually comes down — gently as a trough over longwall panels, abruptly as a sinkhole where a solution cavity or an old shaft collapses. Solution mining of salt and potash dissolves the cavity in the first place, so the ground keeps moving long after work stops.",
     "Backfilling with paste or waste rock, leaving support pillars, and mapping old workings so that what is above them can be planned around.",
     ""),
    ("Silicosis", "Health", "During operation", ["Underground", "Open pit", "Quarry"],
     "Drilling and blasting rock high in quartz makes respirable crystalline silica fine enough to reach the deep lung, where it scars tissue irreversibly. The disease develops over years, is incurable, and greatly raises the risk of tuberculosis — which is why it spreads fastest where the two meet.",
     "Wet drilling, ventilation, dust suppression on haul roads, respiratory protection, and screening programmes that catch it early enough to remove the worker from exposure.",
     "South Africa's gold mines produced silicosis on a scale that led to a class action settled in 2019 covering tens of thousands of current and former miners."),
    ("Dust and particulates", "Air", "During operation", ["Open pit", "Quarry", "Heap leach"],
     "Blasting, haulage on unsealed roads, crushing and dry tailings surfaces all put particulate into the air. Beyond the respiratory load it carries whatever the ore carries — lead, arsenic, cadmium — onto soil, roofs and gardens downwind.",
     "Watering and sealing haul roads, enclosing crushers and conveyors, wind fences, and revegetating or wetting exposed tailings beaches.",
     ""),
    ("Radioactive legacy", "Health", "After closure", ["Underground", "Open pit", "In-situ leach"],
     "Uranium ore holds the whole decay chain, so its tailings retain most of the original radioactivity as thorium-230 and radium-226 long after the uranium is gone. Radium decays to radon, a gas that escapes the pile continuously, and radium-226's 1,600-year half-life sets the timescale for containment.",
     "Thick engineered covers to cut radon exhalation, relocation of tailings away from watercourses, and institutional control that has to outlast any company.",
     "The Wismut operations in East Germany left one of the largest uranium legacies anywhere; the German rehabilitation programme has run since 1991 and is measured in decades and billions of euros."),
    ("Lead exposure", "Health", "Both", ["Smelter", "Open pit", "Underground"],
     "Lead reaches people as smelter emissions, as dust from ore stockpiles and tailings, and as contaminated soil that children then put their hands in. It is a developmental neurotoxin with no threshold known to be safe, and the exposure that matters most happens before school age.",
     "Emission controls and stack monitoring, soil replacement in affected neighbourhoods, buffer zones, and blood-lead screening of local children rather than of workers alone.",
     "Kabwe in Zambia, smelting lead from 1902 to 1994, left soil and dust contamination that continues to produce some of the highest childhood blood-lead levels recorded anywhere."),
    ("Sulfur dioxide emissions", "Air", "During operation", ["Smelter"],
     "Roasting and smelting sulfide ores drives off sulfur as sulfur dioxide. Released untreated it acidifies rain downwind, strips foliage and acidifies soils and lakes across an area far larger than the plant.",
     "Capture as sulfuric acid — now standard and usually sold — plus scrubbing and continuous stack monitoring.",
     "Smelting at Sudbury, Ontario denuded a landscape large enough to be visible from orbit; capture, a 381 m stack and a regreening programme running since 1978 have reversed much of it."),
    ("Waste rock and strip ratio", "Land", "During operation", ["Open pit", "Quarry"],
     "Reaching ore in a pit means removing everything above and around it. The strip ratio — tonnes of waste per tonne of ore — is commonly several to one, so the waste dumps are the largest structures on most sites and outlast the pit itself.",
     "Backfilling worked-out pit sections, using waste as construction material where it is not acid-generating, and shaping and revegetating dumps as they are built rather than at the end.",
     ""),
    ("Falling ore grade", "Energy", "Both", ["Open pit", "Underground"],
     "The richest deposits are mined first, so average grades fall over time — copper mined today is a fraction of a percent where it was several percent a century ago. Every tonne of metal then needs more rock moved, more rock ground, more water and more energy, and produces more tailings, with no change in practice required for the impact to grow.",
     "Recovery improvements, recycling of metal already above ground, and selective mining that leaves low-grade material in place rather than processing it.",
     ""),
    ("Smelting energy demand", "Energy", "During operation", ["Smelter"],
     "Pulling a metal out of its compound takes at least the energy that bound it, and often much more. Aluminium is the extreme case: Hall–Héroult electrolysis uses roughly 13–15 kWh of electricity per kilogram of metal, which is why smelters are built where power is cheap rather than where the ore is.",
     "Siting on low-carbon grids, inert anodes and process improvements, and recycling — remelting aluminium takes a small fraction of the energy of making it from ore.",
     ""),
    ("Land clearance and deforestation", "Land", "During operation", ["Open pit", "Placer", "Artisanal", "Quarry"],
     "The mine footprint is only part of it: access roads, power lines, camps and the settlement that follows open ground that was previously hard to reach, and in forest the clearance that follows the road usually exceeds the clearance for the mine.",
     "Routing and access control, offsets and set-asides agreed before the road is built, and progressive rehabilitation of worked-out ground.",
     ""),
    ("Pit lakes and perpetual treatment", "Water", "After closure", ["Open pit", "Underground"],
     "When pumping stops, groundwater returns and fills the void. If the walls are sulfide-bearing, the lake that forms is acidic and metal-rich, and it will keep forming for as long as water flows — which means the treatment plant becomes a permanent installation and the liability outlives the company that created it.",
     "Financial assurance sized to perpetual care, passive treatment wetlands where the load allows, and backfilling or flooding designed to limit oxidation from the start.",
     "The Berkeley Pit at Butte, Montana has been filling since pumping stopped in 1982; its water is acidic and metal-laden, and treatment is expected to continue indefinitely."),
]


def main():
    ds = find_ds(TITLE)
    if not ds:
        db = call("POST", "https://api.notion.com/v1/databases", {
            "parent": {"type": "page_id", "page_id": PARENT_PAGE},
            "title": [{"type": "text", "text": {"content": TITLE}}],
            "initial_data_source": {"properties": {
                "Name": {"title": {}},
                "Category": {"select": {"options": [{"name": c} for c in CATEGORIES]}},
                "Timescale": {"select": {"options": [{"name": t} for t in TIMESCALES]}},
                "Where": {"multi_select": {"options": [{"name": w} for w in WHERE]}},
                "Mechanism": {"rich_text": {}},
                "Mitigation": {"rich_text": {}},
                "Case": {"rich_text": {}},
            }},
        })
        ds = db["data_sources"][0]["id"]
        print("created", TITLE, ds)
    else:
        print(TITLE, "exists:", ds)
    schema = ensure_props(ds, {
        "Category": {"select": {"options": [{"name": c} for c in CATEGORIES]}},
        "Timescale": {"select": {"options": [{"name": t} for t in TIMESCALES]}},
        "Where": {"multi_select": {"options": [{"name": w} for w in WHERE]}},
        "Mechanism": {"rich_text": {}},
        "Mitigation": {"rich_text": {}},
        "Case": {"rich_text": {}},
    }, "impacts")
    ensure_select_options(ds, "Category", CATEGORIES, "impacts")
    ensure_select_options(ds, "Timescale", TIMESCALES, "impacts")
    sync_rows(ds, schema,
              [{"Name": n, "Category": c, "Timescale": t, "Where": w or None,
                "Mechanism": mech, "Mitigation": mit or None, "Case": case or None}
               for n, c, t, w, mech, mit, case in IMPACTS],
              "impacts", key="Name")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
