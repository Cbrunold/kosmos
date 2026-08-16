"""Seed extraction data onto the Elements DB and flagship mines into Mines [DB].

Two tables. EXTRACTION, keyed by element symbol, fills four properties on
"All Periodical Elements": Mined As (Primary / By-product / Not mined), Ore
Grade (ppm) — a *typical mined grade* by mass, deliberately mid-range rather
than the richest deposit on Earth — Ore Minerals, and Extraction, the ore-to-
product chain in plain words. MINES fills Mines [DB] with ~85 sites, each with
coordinates for the map and a Commodities relation onto the elements it
produces.

The number the site derives from all this is the concentration factor: ore
grade over crustal abundance, i.e. how much geology has to enrich an element
before mining it pays. Iron comes out under 10, copper near 100, gold and
uranium in the hundreds, helium and antimony past 100,000. It is computed at
build time, never stored, so it cannot drift from its inputs.

Grades and process descriptions are textbook-typical (USGS commodity
summaries, Ullmann's, the standard extractive-metallurgy references), and the
prose says "typical" because it is. Coordinates are to about 0.05°, which is
a few kilometres — right for a world map, not for finding the gate.

Idempotent: backfills only empty fields, unions relations, never overwrites.
Run on the VPS:  ./deploy.sh seed_mining
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, query_all, sync_rows, title_of  # noqa: E402

ELEMENTS_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"
MINES_DS = "dd711986-067e-43f9-9a74-dd471ac4bcc6"

# ------------------------------------------------------------------ extraction
# symbol: (mined as, ore grade ppm by mass or None, ore minerals, extraction)
EXTRACTION = {
    # ---- the big metals
    "Fe": ("Primary", 500000, "hematite, magnetite, goethite (banded iron formations)",
           "Banded iron formations laid down two billion years ago are blasted, crushed and — for magnetite — "
           "magnetically separated; high-grade hematite ships as-is. Fines are sintered or pelletised, then "
           "reduced in a blast furnace with coke and limestone to pig iron and blown to steel in a basic oxygen "
           "furnace. Direct reduction with gas and an electric arc furnace is the lower-carbon route."),
    "Al": ("Primary", 250000, "bauxite (gibbsite, boehmite, diaspore)",
           "Bauxite is strip-mined from tropical laterites, then digested in hot caustic soda (the Bayer "
           "process) to dissolve the aluminium and leave the red mud behind; alumina precipitates and is "
           "calcined. Hall–Héroult cells then electrolyse it dissolved in molten cryolite at about 960 °C — "
           "roughly 14 MWh per tonne, which is why smelters chase cheap electricity."),
    "Cu": ("Primary", 5000, "chalcopyrite, bornite, chalcocite; oxides malachite, azurite, chrysocolla",
           "Porphyry ore at half a percent copper is crushed, ground and floated to a 25–30 % concentrate, "
           "flash-smelted to matte, converted to blister and electrorefined to 99.99 %; gold, silver, selenium "
           "and tellurium come out of the anode slimes. Oxide ore skips all that: heap-leached with sulfuric "
           "acid, then solvent extraction and electrowinning (SX-EW) straight to cathode."),
    "Au": ("Primary", 2, "native gold in quartz veins; refractory gold locked in pyrite and arsenopyrite; placer",
           "A gram or two per tonne is a good mine. Ore is ground and leached with dilute cyanide, the gold "
           "adsorbed onto activated carbon (CIL/CIP), stripped and electrowon into doré. Refractory ore is "
           "roasted, pressure-oxidised or bio-oxidised first to break the sulfides open. Placer gold is simply "
           "washed out by density, as it has been for five thousand years."),
    "Ag": ("Primary", 300, "argentite/acanthite, native silver; mostly within lead-zinc-copper ores",
           "Only about a quarter comes from silver mines; the rest is a by-product, floated with lead and zinc "
           "sulfides, collected from lead bullion by the Parkes process, or recovered from copper anode "
           "slimes. Primary ores are cyanide-leached like gold."),
    "Zn": ("Primary", 50000, "sphalerite",
           "Sphalerite is floated to a concentrate, roasted to zinc oxide, leached in sulfuric acid, purified by "
           "cementation with zinc dust to strip out copper, cobalt and cadmium, and electrowon onto aluminium "
           "cathodes. Cadmium, germanium and indium are by-products of the purification stage."),
    "Pb": ("Primary", 40000, "galena",
           "Galena is floated, sintered to the oxide and reduced in a blast furnace to lead bullion, which is "
           "drossed and refined — the Parkes process pulls out the silver. About half of the world's lead now "
           "comes from recycled batteries rather than mines."),
    "Ni": ("Primary", 12000, "pentlandite (sulfides); garnierite and nickel limonite (laterites)",
           "Two ore types, two industries. Sulfides are floated, flash-smelted to matte and refined — Sherritt "
           "pressure leaching or the Mond carbonyl process. Laterites, now the larger source, are either "
           "smelted in rotary kilns and electric furnaces to ferronickel and nickel pig iron, or pressure-acid-"
           "leached (HPAL) to a mixed hydroxide for batteries."),
    "Co": ("By-product", 3000, "heterogenite, carrollite (Congolese copper belt); in nickel sulfides and laterites",
           "Almost never mined on its own. Most comes from the Central African Copperbelt as a co-product of "
           "copper — leached, solvent-extracted and shipped as cobalt hydroxide, largely to China for refining. "
           "The rest is a by-product of nickel, from both sulfide smelting and laterite HPAL."),
    "Li": ("Primary", 5000, "spodumene (hard rock); lithium chloride in salar brines; petalite, lepidolite",
           "Hard rock: spodumene is concentrated by dense-media separation and flotation, calcined to flip its "
           "crystal structure, roasted with sulfuric acid, leached and precipitated as lithium carbonate or "
           "hydroxide. Brine: pumped from beneath a salt flat into evaporation ponds for a year to eighteen "
           "months, then precipitated. Direct lithium extraction from brine is the emerging third route."),
    "Sn": ("Primary", 7000, "cassiterite",
           "Cassiterite is dense and chemically stubborn, so it survives weathering into placers — most Asian tin "
           "is dredged from river beds and shallow seas and concentrated by gravity. Hard-rock ore is ground and "
           "gravity-separated the same way. The concentrate is smelted with carbon in a reverberatory or electric "
           "furnace and refined."),
    "W": ("Primary", 4000, "wolframite, scheelite",
          "The concentrate is pressure-leached in alkali, purified by solvent extraction and crystallised as "
          "ammonium paratungstate (APT), the traded intermediate. APT is calcined to the oxide and reduced with "
          "hydrogen to tungsten powder — the metal melts too high to cast — which is pressed and sintered, or "
          "carburised into tungsten carbide for tools."),
    "Mo": ("Primary", 1000, "molybdenite; mostly as a by-product of porphyry copper",
           "Molybdenite floats away from copper sulfides in a second flotation stage, or is the main product at "
           "a few porphyry-molybdenum mines. The concentrate is roasted to molybdenum trioxide, most of which "
           "goes straight into ferromolybdenum for steel; rhenium is scrubbed from the roaster flue gas."),
    "U": ("Primary", 2000, "uraninite (pitchblende), coffinite, carnotite; sandstone-hosted roll fronts",
          "About half now comes from in-situ leaching: oxygenated, mildly acid or alkaline solution is pumped "
          "through a sandstone orebody via wellfields and the uranium stripped out on ion-exchange resin, no "
          "mine required. Conventional ore is milled, acid-leached, solvent-extracted and precipitated as "
          "yellowcake (U₃O₈), then converted to UF₆, enriched in centrifuges, and made into fuel."),
    "Ti": ("Primary", 20000, "ilmenite, rutile, leucoxene (mineral sands); hard-rock ilmenite",
           "Heavy-mineral sands are dredged and the ilmenite and rutile pulled out by gravity, magnetic and "
           "electrostatic separation. Over 90 % becomes titanium dioxide pigment; the rest is chlorinated to "
           "TiCl₄ and reduced with magnesium in the Kroll process to a porous sponge, which is vacuum-arc-melted "
           "into ingot. Kroll is slow and batchwise, which is why titanium stays expensive."),
    "Cr": ("Primary", 270000, "chromite",
           "Chromite from layered intrusions — the Bushveld above all — is crushed and gravity-concentrated, then "
           "smelted with coke in a submerged-arc furnace to ferrochrome, of which almost all goes into stainless "
           "steel. Chromite is also refractory and the source of chromium chemicals."),
    "Mn": ("Primary", 350000, "pyrolusite, braunite, rhodochrosite; manganese nodules on the seabed",
           "High-grade oxide ore is mined open-pit, beneficiated by washing and gravity, and smelted to "
           "ferromanganese and silicomanganese for steelmaking, which takes about nine tenths of it. Battery-"
           "grade manganese sulfate and electrolytic manganese are made by acid leaching and electrolysis."),
    "Pt": ("Primary", 3, "in the Merensky and UG2 reefs of the Bushveld; sperrylite, cooperite; with nickel-copper sulfides",
           "Reefs a metre thick are followed underground for kilometres. Ore is floated to a concentrate, smelted "
           "to matte, and the base metals leached away in a base-metal refinery; the precious-metal concentrate "
           "then goes through a long chain of dissolution, solvent extraction and precipitation that separates "
           "platinum from palladium, rhodium, ruthenium, iridium and osmium — months, end to end."),
    "Pd": ("Primary", 3, "in nickel-copper sulfides at Norilsk and Sudbury; the J-M reef; with platinum",
           "Recovered alongside platinum from the same matte, and as a by-product of nickel smelting in the Arctic. "
           "Norilsk alone supplies about 40 % of the world's palladium; the separation chemistry is the "
           "platinum-group refinery's."),
    "Rh": ("By-product", 0.3, "in Bushveld UG2 chromitite, with platinum",
           "Comes out of the platinum-group refinery in tiny amounts — about a tenth of the platinum — from the "
           "same South African reefs. There is no rhodium mine, which is why its price swings so violently."),
    "Ir": ("By-product", 0.05, "with platinum, and in osmiridium placers", "A trace in platinum-group concentrates, separated at the tail end of the refinery."),
    "Ru": ("By-product", 0.5, "with platinum", "Separated from platinum-group concentrates by distillation of its volatile tetroxide."),
    "Os": ("By-product", 0.05, "with platinum; osmiridium", "The rarest stable element in commerce, recovered from platinum-group refining as the volatile tetroxide."),

    # ---- rare earths
    "Ce": ("Primary", 30000, "bastnäsite, monazite; ion-adsorption clays",
           "Bastnäsite is floated, then cracked open by roasting with sulfuric acid or caustic soda and leached. "
           "The mixed rare-earth solution goes through hundreds of counter-current solvent-extraction stages to "
           "separate elements whose chemistry differs by almost nothing. Cerium, the most abundant, drops out "
           "early by oxidation. Ionic clays in southern China are leached in place with ammonium sulfate."),
    "La": ("Primary", 15000, "bastnäsite, monazite", "Separated from the mixed rare-earth solution by solvent extraction after cerium is removed; the light-rare-earth end of the chain."),
    "Nd": ("Primary", 10000, "bastnäsite, monazite; ion-adsorption clays",
           "The magnet metal. Follows the same crack-and-leach route as cerium, then solvent extraction to "
           "neodymium oxide, which is reduced electrolytically in a molten fluoride bath to metal for NdFeB "
           "magnets. Praseodymium travels with it and is usually sold as a didymium mix."),
    "Pr": ("By-product", 3000, "with neodymium in bastnäsite and monazite", "Co-product of the same rare-earth ores as neodymium, and often left mixed with it as didymium for magnets."),
    "Dy": ("By-product", 300, "ion-adsorption clays, xenotime",
           "A heavy rare earth, so almost entirely from the ion-adsorption clays of southern China, leached in "
           "situ with ammonium sulfate. Added to neodymium magnets so they keep working hot."),
    "Tb": ("By-product", 50, "ion-adsorption clays, xenotime", "The scarcest of the commercially important rare earths; from the same southern-Chinese clays as dysprosium."),
    "Y": ("By-product", 2000, "xenotime, ion-adsorption clays", "Chemically a heavy rare earth and mined with them, from clays and xenotime, by the same in-situ leach and solvent-extraction route."),
    "Sc": ("By-product", None, "in nickel laterites, titanium waste streams, uranium tailings", "No scandium mine exists; it is scavenged from the acid leach liquors of nickel laterite and titanium pigment plants."),

    # ---- the rest of the mined table
    "Si": ("Primary", 460000, "quartz, quartzite",
           "Quarried quartz is reduced with coal, charcoal and wood chips in a submerged-arc furnace to "
           "metallurgical-grade silicon at 98–99 %. For chips and solar cells that is converted to trichlorosilane, "
           "distilled and redeposited in the Siemens process to nine-nines polysilicon, then pulled into single "
           "crystals by the Czochralski method — a crucible made from the purest quartz on Earth holding the melt."),
    "Mg": ("Primary", 130000, "dolomite, magnesite; seawater and brines",
           "Most of the world's magnesium metal comes from China by the Pidgeon process: calcined dolomite and "
           "ferrosilicon heated under vacuum at 1200 °C, the magnesium distilling off and condensing. The "
           "alternative is electrolysis of magnesium chloride from brine or seawater — the Dead Sea route."),
    "P": ("Primary", 130000, "apatite (francolite) in sedimentary phosphorite",
          "Phosphate rock is strip-mined, washed and floated, then attacked with sulfuric acid to make phosphoric "
          "acid for fertiliser — the wet process — leaving mountains of phosphogypsum. Elemental phosphorus is "
          "made the hard way, by reducing rock with coke and silica in an electric furnace."),
    "K": ("Primary", 170000, "sylvite, carnallite; potash brines",
          "Sylvite is mined a kilometre down with continuous miners in Saskatchewan and beneath Belarus and the "
          "Urals, or dissolved in place and pumped up as brine. Either way it is separated from the halite by "
          "flotation or hot-leach crystallisation and sold as potassium chloride, nearly all of it for fertiliser."),
    "S": ("By-product", None, "recovered from sour gas and oil; pyrite; native sulfur (historic Frasch)",
          "Hardly mined any more. Almost all sulfur is recovered from hydrogen sulfide stripped out of natural gas "
          "and oil, converted to elemental sulfur in the Claus process. The Frasch mines that melted native "
          "sulfur out of salt domes with superheated water are gone."),
    "C": ("Primary", 100000, "graphite (flake and vein); diamond in kimberlite; coal",
          "Three different industries. Flake graphite is floated, and for battery anodes spheroidised and "
          "purified. Diamonds are freed by crushing kimberlite, concentrated by density and picked out by X-ray "
          "fluorescence. Coal is stripped or longwall-mined by the billion tonnes, for energy rather than for "
          "carbon."),
    "He": ("By-product", 1300, "in natural gas from a few reservoirs, up to several percent",
           "Helium leaks from decaying uranium and thorium and collects in gas traps under a good seal. It is "
           "separated cryogenically from natural gas — the methane liquefies, the helium does not — and purified "
           "by pressure-swing adsorption. A few fields in Texas, Qatar, Algeria and Russia supply the world."),
    "Na": ("Primary", 390000, "halite (rock salt); seawater and brines",
           "Rock salt is mined underground with continuous miners; brine is pumped from solution wells and boiled "
           "down in vacuum pans; seawater is evaporated in solar ponds. Sodium metal is made by electrolysing "
           "molten sodium chloride in a Downs cell."),
    "Cl": ("Primary", 600000, "halite; brines",
           "From the same salt as sodium. Chlorine gas is made by the chlor-alkali process — electrolysing brine "
           "in membrane cells — with caustic soda and hydrogen as co-products, one of the largest chemical "
           "industries in the world."),
    "Ca": ("Primary", 400000, "limestone, dolomite, gypsum",
           "Quarried limestone is burned in a kiln to quicklime, or ground with clay and fired to cement clinker. "
           "Calcium metal itself is a small business, made by reducing lime with aluminium under vacuum."),
    "F": ("Primary", 170000, "fluorite (fluorspar)",
          "Fluorite is floated to acid-grade concentrate and reacted with sulfuric acid to make hydrofluoric acid, "
          "the root of every fluorochemical from refrigerants to Teflon; lower grades go into steelmaking as flux."),
    "B": ("Primary", 80000, "borax, kernite, colemanite, ulexite",
          "Turkey and California hold nearly all of it. Ore is mined open-pit, dissolved in hot water, filtered "
          "and recrystallised into refined borates; boric acid comes from acidifying the solution."),
    "Zr": ("By-product", 5000, "zircon in mineral sands, with ilmenite and rutile",
           "Zircon is a co-product of titanium sands, separated electrostatically. Most goes into ceramics and "
           "refractories as-is; nuclear-grade metal comes via chlorination and the Kroll process, with the "
           "hafnium — chemically almost identical — stripped out first by solvent extraction."),
    "Hf": ("By-product", 100, "in zircon, at 1–2 % of the zirconium", "Separated from zirconium during nuclear-fuel-cladding production, where it must be removed because it absorbs neutrons zirconium lets through."),
    "V": ("Primary", 7000, "vanadiferous titanomagnetite; vanadium in oil residues and steel slag",
          "Titanomagnetite is roasted with salt, leached and precipitated as vanadium pentoxide, then reduced to "
          "ferrovanadium for high-strength steel; a growing share is recovered from steel slag and refinery "
          "residues. Redox-flow batteries are the new demand."),
    "Nb": ("Primary", 17000, "pyrochlore",
           "One deposit at Araxá in Brazil supplies most of the world. Pyrochlore is floated to concentrate and "
           "reduced aluminothermically to ferroniobium, a fraction of a percent of which makes steel stronger "
           "and lighter."),
    "Ta": ("Primary", 300, "tantalite-columbite (coltan); in tin slags",
           "Coltan is gravity-concentrated, often by hand in Central Africa, or recovered from tin smelter slag. "
           "The concentrate is dissolved in hydrofluoric acid, tantalum separated from niobium by solvent "
           "extraction, and reduced with sodium to a powder for capacitors."),
    "Sb": ("Primary", 30000, "stibnite",
           "Stibnite ore, mostly Chinese, is hand-sorted or floated and either roasted to the trioxide — the flame-"
           "retardant product — or smelted with iron or carbon to metal for lead alloys."),
    "Hg": ("Primary", 5000, "cinnabar",
           "Cinnabar is roasted in air and the mercury vapour condensed — the oldest metallurgy there is. Almost "
           "all primary mining has stopped under the Minamata Convention; supply is recycled and by-product "
           "mercury from gold and gas processing."),
    "Be": ("Primary", 2500, "bertrandite, beryl",
           "One deposit in Utah supplies most of it. Bertrandite ore is leached in sulfuric acid, the beryllium "
           "extracted by solvent extraction and precipitated as hydroxide, then converted to metal, oxide or "
           "copper-beryllium master alloy."),
    "I": ("Primary", 400, "iodate in Chilean caliche; iodide in oilfield brines",
          "Chile leaches iodate out of nitrate caliche in heaps and reduces it with sulfur dioxide; Japan strips "
          "iodide from natural-gas brines by blowing it out with air. Between them, most of the world."),
    "Br": ("Primary", 5000, "in Dead Sea and Arkansas brines",
           "Concentrated brine is oxidised with chlorine and the bromine blown out with steam or air. Two sources — "
           "the Dead Sea and the Smackover formation under Arkansas — supply almost all of it."),
    "Sr": ("Primary", 280000, "celestine", "Celestine is hand-sorted or floated and converted to strontium carbonate; a small industry, mostly for pyrotechnics and magnets since television tubes disappeared."),
    "Ba": ("Primary", 400000, "barite (barytes)", "Barite is mined, ground and used almost as-is — nine tenths of it as the weighting agent in oil-well drilling mud."),

    # ---- by-products with no mine of their own
    "Ga": ("By-product", 50, "in bauxite, at tens of ppm", "Extracted from the caustic Bayer liquor of alumina refineries by ion exchange or electrolysis; no gallium mine has ever existed."),
    "Ge": ("By-product", 300, "in sphalerite; in coal fly ash", "Recovered from zinc-refinery residues and from the fly ash of germanium-rich coals, then chlorinated, distilled and hydrolysed to the oxide."),
    "In": ("By-product", 100, "in sphalerite", "Leached from zinc-refinery residues; the touchscreen metal, wholly dependent on how much zinc the world smelts."),
    "Cd": ("By-product", 300, "in sphalerite (greenockite)", "Cemented out of zinc electrolyte during purification, then distilled or electrowon."),
    "Re": ("By-product", 0.5, "in molybdenite, at hundreds of ppm", "Scrubbed from the flue gas of molybdenite roasters as perrhenic acid and precipitated as ammonium perrhenate — the source of nearly all rhenium, for jet-engine superalloys."),
    "Se": ("By-product", None, "in copper sulfides", "From the anode slimes of copper electrorefining, roasted and leached."),
    "Te": ("By-product", None, "in copper sulfides", "From copper anode slimes alongside selenium; the solar-cell (CdTe) tellurium supply is a by-product of how much copper is refined."),
    "Bi": ("By-product", None, "with lead, tungsten and copper", "Recovered from lead refining (the Betterton–Kroll process) and from tungsten and copper circuits; almost no primary bismuth mining."),
    "As": ("By-product", None, "arsenopyrite, in copper and gold ores", "Recovered as the trioxide from smelter flue dusts, mostly in China; more often it is a contaminant to be disposed of than a product to be sold."),
    "Tl": ("By-product", None, "in zinc and lead sulfides", "A trace in zinc- and lead-smelter flue dust; production is tiny and mostly a matter of keeping it out of the environment."),

    # ---- taken from air or water, not from the ground
    "N": ("Not mined", None, "the atmosphere (78 %); historic Chilean nitrate caliche", "Separated from air cryogenically, and fixed as ammonia by Haber–Bosch — the process that feeds half the world."),
    "O": ("Not mined", None, "the atmosphere (21 %)", "Cryogenic air separation, or pressure-swing adsorption for smaller volumes."),
    "H": ("Not mined", None, "water; natural gas", "Almost all from steam reforming of methane; electrolysis of water is the growing low-carbon route."),
    "Ar": ("Not mined", None, "the atmosphere (0.93 %)", "A by-product of cryogenic air separation, sitting between oxygen and nitrogen in the column."),
    "Ne": ("Not mined", None, "the atmosphere (18 ppm)", "Air separation; a by-product of very large oxygen plants, which is why Ukrainian steelworks once supplied most of it."),
    "Kr": ("Not mined", None, "the atmosphere (1 ppm)", "Air separation, at the bottom of the oxygen column."),
    "Xe": ("Not mined", None, "the atmosphere (0.09 ppm)", "Air separation; the rarest thing routinely extracted from air, and priced accordingly."),
}

# ------------------------------------------------------------------ mines
# name, country, region, lat, lon, type, status, commodities (symbols), opened, notes
MINES = [
    # copper
    ("Escondida", "Chile", "Antofagasta Region", -24.27, -69.07, "Open pit", "Active", ["Cu", "Au", "Ag", "Mo"], 1990,
     "The largest copper mine on Earth — over a million tonnes a year, roughly 5 % of world supply — in the Atacama at 3,100 m, running on desalinated seawater pumped up from the coast."),
    ("Chuquicamata", "Chile", "Antofagasta Region", -22.30, -68.90, "Open pit + underground", "Active", ["Cu", "Mo"], 1915,
     "The largest open pit by excavated volume, 4.3 km long and nearly a kilometre deep; converted to a block-cave underground mine in 2019 because the pit walls could go no further."),
    ("Grasberg", "Indonesia", "Papua", -4.06, 137.11, "Open pit + underground", "Active", ["Cu", "Au", "Ag"], 1973,
     "The world's largest gold mine and second-largest copper mine, at 4,100 m in the Sudirman Range; the pit is exhausted and production now comes from one of the largest block caves ever built."),
    ("Bingham Canyon", "United States", "Utah", 40.52, -112.15, "Open pit", "Active", ["Cu", "Mo", "Au", "Ag"], 1906,
     "The deepest open pit in the world, 1.2 km deep and 4 km across, mined continuously for over a century; a 2013 landslide inside it was one of the largest non-volcanic slides in North America."),
    ("El Teniente", "Chile", "O'Higgins Region", -34.09, -70.35, "Underground", "Active", ["Cu", "Mo"], 1905,
     "The largest underground copper mine, with more than 3,000 km of tunnels beneath the Andes; Codelco's flagship."),
    ("Collahuasi", "Chile", "Tarapacá Region", -20.98, -68.68, "Open pit", "Active", ["Cu", "Mo"], 1999,
     "Among the three largest copper mines by output, at 4,400 m — high enough that the workforce rotates down to the coast to sleep."),
    ("Cerro Verde", "Peru", "Arequipa", -16.53, -71.60, "Open pit", "Active", ["Cu", "Mo"], 1976,
     "One of the largest concentrators anywhere, processing over 400,000 tonnes of ore a day; the pit overlooks Arequipa."),
    ("Morenci", "United States", "Arizona", 33.08, -109.36, "Open pit", "Active", ["Cu", "Mo"], 1872,
     "The largest copper mine in North America and the place where heap leaching and SX-EW were proven at scale in the 1980s."),
    ("Oyu Tolgoi", "Mongolia", "Ömnögovi", 43.01, 106.86, "Open pit + underground", "Active", ["Cu", "Au"], 2013,
     "A copper-gold porphyry in the South Gobi whose underground block cave, started in 2023, is one of the largest ever undertaken; a third of Mongolia's economy rides on it."),
    ("Kamoa-Kakula", "DR Congo", "Lualaba", -10.77, 25.29, "Underground", "Active", ["Cu"], 2021,
     "The highest-grade major copper mine in the world, around 5 % copper against a global average of 0.5 %, and the fastest-growing."),
    ("Kansanshi", "Zambia", "North-Western Province", -12.10, 26.42, "Open pit", "Active", ["Cu", "Au"], 2005,
     "The largest copper mine in Africa, on the Zambian side of the Copperbelt."),
    ("Olympic Dam", "Australia", "South Australia", -30.44, 136.89, "Underground", "Active", ["Cu", "U", "Au", "Ag"], 1988,
     "An iron-oxide copper-gold deposit that also holds the largest known uranium resource on Earth; found in 1975 by drilling on a geological hunch under 300 m of barren cover."),
    ("Norilsk–Talnakh", "Russia", "Krasnoyarsk Krai", 69.35, 88.20, "Underground", "Active", ["Ni", "Cu", "Pd", "Pt", "Co"], 1935,
     "Above the Arctic Circle: the largest palladium producer in the world and one of the largest of nickel, from magmatic sulfides; built by Gulag labour and long one of the most polluted places on the planet."),
    # iron
    ("Mount Whaleback", "Australia", "Pilbara, Western Australia", -23.37, 119.67, "Open pit", "Active", ["Fe"], 1968,
     "The largest single-pit iron mine, 5.5 km long, at Newman; the Pilbara as a whole ships over 800 million tonnes a year, most of it to China."),
    ("Carajás", "Brazil", "Pará", -6.06, -50.16, "Open pit", "Active", ["Fe"], 1985,
     "The richest large iron ore on Earth at around 65 % iron, in the Amazon; the S11D expansion runs without trucks, on conveyors, to keep the forest footprint down."),
    ("Kiruna", "Sweden", "Norrbotten", 67.85, 20.20, "Underground", "Active", ["Fe"], 1898,
     "The largest underground iron mine, a magnetite slab 4 km long dipping under the town — which is now being moved 3 km east because the ground above the workings is subsiding."),
    ("Sishen", "South Africa", "Northern Cape", -27.78, 22.99, "Open pit", "Active", ["Fe"], 1953,
     "One of the largest open-pit iron mines, feeding an 861 km railway to the port of Saldanha."),
    ("Hull–Rust–Mahoning", "United States", "Minnesota", 47.43, -92.94, "Open pit", "Active", ["Fe"], 1895,
     "The Mesabi Range pit that fed American steelmaking for a century; now taconite pellets from low-grade magnetite after the rich ore ran out in the 1950s."),
    # aluminium
    ("Weipa", "Australia", "Queensland", -12.63, 141.87, "Open pit", "Active", ["Al"], 1963,
     "Bauxite a few metres below the surface of Cape York, strip-mined at over 35 million tonnes a year and shipped to the Gladstone refineries."),
    ("Sangarédi (CBG)", "Guinea", "Boké Region", 11.12, -13.80, "Open pit", "Active", ["Al"], 1973,
     "Guinea holds the largest and best bauxite reserves in the world and has become the biggest exporter, almost all of it to China; Sangarédi is the oldest of the big operations."),
    ("Huntly", "Australia", "Western Australia", -32.60, 116.10, "Open pit", "Active", ["Al"], 1976,
     "The world's largest bauxite mine by output, worked in strips through jarrah forest south of Perth and rehabilitated behind."),
    # gold
    ("Muruntau", "Uzbekistan", "Navoiy Region", 41.50, 64.57, "Open pit", "Active", ["Au"], 1967,
     "The largest open-pit gold mine, in the Kyzylkum desert, and one of the largest gold producers of any kind at over two million ounces a year."),
    ("Carlin Trend", "United States", "Nevada", 40.97, -116.38, "Open pit + underground", "Active", ["Au"], 1965,
     "Gold too fine to see, dispersed through limestone — the 'invisible gold' that made Nevada one of the world's great gold provinces once cyanide heap leaching could recover it."),
    ("Mponeng", "South Africa", "Gauteng", -26.42, 27.42, "Underground", "Active", ["Au", "U"], 1986,
     "The deepest mine on Earth, approaching 4 km, on the Witwatersrand basin that has produced around 40 % of all the gold ever mined; rock at the face is 60 °C and has to be cooled with ice."),
    ("Boddington", "Australia", "Western Australia", -32.75, 116.37, "Open pit", "Active", ["Au", "Cu"], 1987,
     "Australia's largest gold mine, a low-grade, high-tonnage operation south-east of Perth."),
    ("Kalgoorlie Super Pit", "Australia", "Western Australia", -30.78, 121.50, "Open pit", "Active", ["Au"], 1893,
     "The Golden Mile of the 1890s rush, consolidated into one pit 3.5 km long that swallowed the old underground workings and part of the town."),
    ("Pueblo Viejo", "Dominican Republic", "Sánchez Ramírez", 18.93, -70.18, "Open pit", "Active", ["Au", "Ag"], 2012,
     "Worked by the Spanish in the 1500s; today one of the largest gold mines in the Americas, with refractory ore treated by pressure oxidation."),
    ("Yanacocha", "Peru", "Cajamarca", -6.98, -78.52, "Open pit", "Active", ["Au"], 1993,
     "For years the largest gold mine in Latin America, a heap-leach operation at 4,000 m whose water use set off a decade of conflict with the farms below."),
    # silver
    ("Fresnillo", "Mexico", "Zacatecas", 23.17, -102.87, "Underground", "Active", ["Ag", "Au", "Pb", "Zn"], 1554,
     "The world's largest primary silver mine, in production almost continuously since the sixteenth century."),
    ("Cannington", "Australia", "Queensland", -21.87, 140.92, "Underground", "Active", ["Ag", "Pb", "Zn"], 1997,
     "One of the largest silver producers anywhere, from a single silver-lead-zinc orebody in outback Queensland."),
    ("Cerro Rico de Potosí", "Bolivia", "Potosí", -19.62, -65.75, "Underground", "Active", ["Ag", "Sn", "Zn"], 1545,
     "The mountain that bankrolled the Spanish empire, still worked by cooperatives; so riddled with galleries that the summit is sinking."),
    # zinc & lead
    ("Red Dog", "United States", "Alaska", 68.07, -162.87, "Open pit", "Active", ["Zn", "Pb", "Ag"], 1989,
     "The largest zinc mine in the world, above the Arctic Circle on Iñupiat land; concentrate is trucked to a port that ships only in the ice-free hundred days of summer."),
    ("Rampura Agucha", "India", "Rajasthan", 25.83, 74.73, "Open pit + underground", "Active", ["Zn", "Pb", "Ag"], 1991,
     "One of the largest and highest-grade zinc mines, around 13 % zinc, and the core of India's zinc industry."),
    ("Mount Isa", "Australia", "Queensland", -20.72, 139.48, "Underground", "Active", ["Cu", "Zn", "Pb", "Ag"], 1931,
     "A copper and lead-zinc-silver district under one town, mined for ninety years; the copper side is closing."),
    ("Broken Hill", "Australia", "New South Wales", -31.96, 141.47, "Underground", "Active", ["Zn", "Pb", "Ag"], 1885,
     "The lead-zinc-silver lode that founded BHP — the 'Broken Hill Proprietary' — and shaped Australian mining law and unionism."),
    # nickel & cobalt
    ("Sudbury Basin", "Canada", "Ontario", 46.47, -81.20, "Underground", "Active", ["Ni", "Cu", "Pd", "Pt", "Co"], 1883,
     "Nickel-copper sulfides around the rim of a 1.85-billion-year-old meteorite impact crater; the Creighton mine reaches 2.4 km and hosts a neutrino observatory in a disused level."),
    ("Sorowako", "Indonesia", "South Sulawesi", -2.53, 121.36, "Open pit", "Active", ["Ni"], 1978,
     "Laterite nickel smelted to matte on site; Indonesia's laterites now supply about half the world's nickel, and Sorowako was where the industry started."),
    ("Mutanda", "DR Congo", "Lualaba", -10.78, 25.83, "Open pit", "Active", ["Cu", "Co"], 2010,
     "The largest cobalt mine in the world; the Congolese Copperbelt supplies around 70 % of global cobalt as a co-product of copper."),
    ("Tenke Fungurume", "DR Congo", "Lualaba", -10.62, 26.13, "Open pit", "Active", ["Cu", "Co"], 2009,
     "One of the largest copper-cobalt operations on the Copperbelt, now Chinese-owned like most of the belt's cobalt output."),
    ("Voisey's Bay", "Canada", "Newfoundland and Labrador", 56.33, -62.10, "Open pit + underground", "Active", ["Ni", "Cu", "Co"], 2005,
     "A nickel-copper-cobalt sulfide found in 1993 by two prospectors looking for diamonds, on the Labrador coast."),
    # lithium
    ("Greenbushes", "Australia", "Western Australia", -33.87, 116.06, "Open pit", "Active", ["Li", "Ta", "Sn"], 1888,
     "The largest hard-rock lithium mine in the world, and the highest grade at around 2 % Li₂O; a tin mine for its first century."),
    ("Salar de Atacama", "Chile", "Antofagasta Region", -23.50, -68.30, "Brine", "Active", ["Li", "K"], 1984,
     "The richest lithium brine known, pumped from beneath the salt flat into evaporation ponds that cover 40 km²; the water it removes from the driest desert on Earth is the centre of the argument about it."),
    ("Salar del Hombre Muerto", "Argentina", "Catamarca", -25.40, -67.05, "Brine", "Active", ["Li"], 1997,
     "Argentina's first lithium brine operation, at 4,000 m on the Puna."),
    ("Salar de Uyuni", "Bolivia", "Potosí", -20.30, -67.50, "Brine", "Development", ["Li"], 2023,
     "The largest lithium resource in the world under the largest salt flat, and one of the hardest to work: high magnesium, a rainy season, and a state monopoly that has produced little so far."),
    ("Pilgangoora", "Australia", "Western Australia", -21.03, 118.90, "Open pit", "Active", ["Li", "Ta"], 2018,
     "One of the large Pilbara spodumene mines that turned Western Australia into the world's main source of hard-rock lithium within a decade."),
    # uranium
    ("Cigar Lake", "Canada", "Saskatchewan", 58.07, -104.53, "Underground", "Active", ["U"], 2014,
     "The highest-grade uranium orebody ever mined, around 15 % U₃O₈ — a hundred times a typical mine — so rich it is cut by remote jet-boring beneath frozen ground and never touched by hand."),
    ("McArthur River", "Canada", "Saskatchewan", 57.76, -105.05, "Underground", "Active", ["U"], 1999,
     "The largest high-grade uranium mine in the world, in the Athabasca Basin, mined by raise-boring through artificially frozen rock."),
    ("Inkai", "Kazakhstan", "Turkistan Region", 45.00, 67.70, "In-situ leach", "Active", ["U"], 2009,
     "Uranium dissolved out of a sandstone aquifer through wellfields with no mine at all; Kazakhstan produces about 40 % of the world's uranium this way."),
    ("Rössing", "Namibia", "Erongo Region", -22.48, 15.03, "Open pit", "Active", ["U"], 1976,
     "The longest-running open-pit uranium mine, on very low-grade ore around 0.03 % — economic only at enormous scale."),
    ("Ranger", "Australia", "Northern Territory", -12.68, 132.92, "Open pit", "Closed", ["U"], 1980,
     "Surrounded by, and excised from, Kakadu National Park on Mirarr land; closed in 2021 with a rehabilitation bill of over a billion dollars."),
    # titanium, zircon
    ("Richards Bay Minerals", "South Africa", "KwaZulu-Natal", -28.70, 32.15, "Placer", "Active", ["Ti", "Zr", "Fe"], 1977,
     "Coastal dunes dredged in a moving pond, the heavy minerals spiralled out, and the dunes rebuilt and replanted behind; ilmenite is smelted on site to titania slag."),
    ("Tellnes", "Norway", "Rogaland", 58.33, 6.42, "Open pit", "Active", ["Ti"], 1960,
     "The largest hard-rock ilmenite deposit in the world, and Europe's main titanium source."),
    # platinum group, chromium
    ("Impala Rustenburg", "South Africa", "North West", -25.62, 27.20, "Underground", "Active", ["Pt", "Pd", "Rh", "Cr"], 1969,
     "Narrow reefs of the Bushveld Complex followed for kilometres underground; the Bushveld holds around three quarters of the world's platinum-group metals."),
    ("Mogalakwena", "South Africa", "Limpopo", -23.98, 28.92, "Open pit", "Active", ["Pt", "Pd", "Rh", "Ni", "Cu"], 1993,
     "The largest open-pit platinum mine, on the Platreef, where the ore is thick enough to be dug from surface rather than followed underground."),
    ("Stillwater", "United States", "Montana", 45.39, -109.88, "Underground", "Active", ["Pd", "Pt"], 1986,
     "The only primary platinum-group mine in the United States, on the palladium-rich J-M reef."),
    ("Kemi", "Finland", "Lapland", 65.78, 24.53, "Open pit + underground", "Active", ["Cr"], 1968,
     "The only chromium mine in the European Union, feeding the Tornio stainless-steel works next door."),
    # manganese
    ("Kalahari Manganese Field", "South Africa", "Northern Cape", -27.15, 22.95, "Open pit + underground", "Active", ["Mn"], 1964,
     "Around 80 % of the world's known land-based manganese lies in this one field near Hotazel."),
    ("Groote Eylandt", "Australia", "Northern Territory", -13.97, 136.45, "Open pit", "Active", ["Mn"], 1966,
     "The largest manganese ore mine in the world, on Anindilyakwa land in the Gulf of Carpentaria."),
    # rare earths
    ("Bayan Obo", "China", "Inner Mongolia", 41.77, 109.97, "Open pit", "Active", ["Ce", "La", "Nd", "Fe", "Nb"], 1957,
     "The largest rare-earth deposit on Earth, supplying about half of the world's rare earths — opened as an iron mine, with the rare earths as an afterthought; the tailings lake at Baotou is one of the most contaminated places in China."),
    ("Mountain Pass", "United States", "California", 35.48, -115.53, "Open pit", "Active", ["Ce", "La", "Nd"], 1952,
     "Dominated world rare-earth supply from the 1960s to the 1990s, closed in 2002 after a spill and Chinese competition, and reopened in 2017 as the only rare-earth mine in the Americas."),
    ("Mount Weld", "Australia", "Western Australia", -28.86, 122.55, "Open pit", "Active", ["Nd", "Ce", "La"], 2007,
     "A rare-earth laterite over an ancient carbonatite; the largest rare-earth producer outside China, with processing in Malaysia."),
    ("Ganzhou ionic clays", "China", "Jiangxi", 24.90, 114.80, "In-situ leach", "Active", ["Dy", "Tb", "Y"], 1970,
     "Heavy rare earths adsorbed on ordinary clay, leached in place with ammonium sulfate — nearly all the world's dysprosium and terbium, at severe cost to the hillsides."),
    # tin, tungsten, molybdenum, niobium, others
    ("Bangka Island", "Indonesia", "Bangka Belitung", -2.13, 106.11, "Placer", "Active", ["Sn"], 1711,
     "Tin dredged from rivers, beaches and the seabed for three centuries; Indonesia is the largest exporter, much of it from small and unlicensed pits."),
    ("San Rafael", "Peru", "Puno", -14.24, -70.30, "Underground", "Active", ["Sn"], 1969,
     "The largest tin mine in the Americas, at 4,500 m in the Andes."),
    ("Shizhuyuan", "China", "Hunan", 25.72, 113.10, "Underground", "Active", ["W", "Sn", "Mo", "Bi"], 1980,
     "A polymetallic skarn in the Nanling range — the tungsten province that gives China around 80 % of world supply."),
    ("Climax", "United States", "Colorado", 39.37, -106.19, "Open pit", "Active", ["Mo"], 1918,
     "Once supplied most of the world's molybdenum from a single mountain at 3,400 m; closed in the 1990s and reopened in 2012."),
    ("Araxá (CBMM)", "Brazil", "Minas Gerais", -19.65, -46.94, "Open pit", "Active", ["Nb"], 1961,
     "One deposit, one company, around 80 % of the world's niobium — the largest single-source dominance of any metal."),
    ("Spor Mountain", "United States", "Utah", 39.72, -113.20, "Open pit", "Active", ["Be"], 1969,
     "The source of roughly two thirds of the world's beryllium, from bertrandite in volcanic tuff."),
    ("Xikuangshan", "China", "Hunan", 27.75, 111.48, "Underground", "Active", ["Sb"], 1897,
     "The 'world antimony capital': for much of the twentieth century a quarter of all antimony came from this one district."),
    ("Almadén", "Spain", "Ciudad Real", 38.78, -4.83, "Underground", "Closed", ["Hg"], None,
     "Mercury mined since Roman times — a third of all the mercury humanity has ever produced — closed in 2002 and now a World Heritage site."),
    ("Panzhihua", "China", "Sichuan", 26.58, 101.72, "Open pit", "Active", ["V", "Ti", "Fe"], 1970,
     "Vanadium-bearing titanomagnetite that makes China the largest vanadium producer, with the iron and titanium as co-products."),
    # industrial minerals, salts, energy
    ("Goderich", "Canada", "Ontario", 43.74, -81.72, "Underground", "Active", ["Na", "Cl"], 1959,
     "The largest underground salt mine in the world, in a 100 m thick bed 500 m beneath Lake Huron; road salt for the whole Great Lakes region."),
    ("Dead Sea Works", "Israel", "Southern District", 31.03, 35.37, "Brine", "Active", ["K", "Br", "Mg"], 1934,
     "Solar evaporation of the saltiest large water body on Earth for potash, the largest bromine output anywhere, and magnesium metal — while the sea itself drops a metre a year."),
    ("Esterhazy", "Canada", "Saskatchewan", 50.65, -102.08, "Underground", "Active", ["K"], 1962,
     "The largest potash mine in the world, a kilometre down in a Devonian salt bed; Saskatchewan alone supplies about a third of world potash."),
    ("Khouribga", "Morocco", "Béni Mellal-Khénifra", 32.88, -6.90, "Open pit", "Active", ["P"], 1921,
     "The largest phosphate mine on Earth; Morocco and Western Sahara hold around 70 % of the world's phosphate rock, and the ore travels 187 km to the coast as slurry in a pipeline."),
    ("Boron", "United States", "California", 35.03, -117.68, "Open pit", "Active", ["B"], 1927,
     "The largest borate mine, supplying about 30 % of the world's refined borates from a Mojave desert pit; the twenty-mule teams hauled from near here."),
    ("Kırka", "Turkey", "Eskişehir", 39.28, 30.53, "Open pit", "Active", ["B"], 1970,
     "Turkey holds around 70 % of the world's boron reserves, and the state producer Eti Maden works them from Kırka and its neighbours."),
    ("Las Cuevas", "Mexico", "San Luis Potosí", 22.00, -100.60, "Underground", "Active", ["F"], 1958,
     "The largest fluorspar mine in the world; Mexico and China supply most of the fluorine that becomes hydrofluoric acid."),
    ("Balama", "Mozambique", "Cabo Delgado", -13.30, 38.66, "Open pit", "Active", ["C"], 2017,
     "The largest graphite mine outside China, built for the battery-anode market."),
    ("Jwaneng", "Botswana", "Southern District", -24.52, 24.70, "Open pit", "Active", ["C"], 1982,
     "The richest diamond mine in the world by value; three kimberlite pipes under the Kalahari sand, and the reason Botswana is not poor."),
    ("Mir", "Russia", "Sakha (Yakutia)", 62.53, 113.99, "Open pit + underground", "Closed", ["C"], 1957,
     "A 525 m deep, 1.2 km wide hole in the permafrost, so large the airspace above it was closed to helicopters; the underground mine that succeeded it flooded in 2017."),
    ("North Antelope Rochelle", "United States", "Wyoming", 43.60, -105.30, "Open pit", "Active", ["C"], 1983,
     "The largest coal mine in the world by output, stripping a seam 20 m thick in the Powder River Basin."),
    ("Cerrejón", "Colombia", "La Guajira", 11.08, -72.65, "Open pit", "Active", ["C"], 1985,
     "The largest open-pit coal mine in Latin America, on Wayuu land, with its own railway and Caribbean port."),
    ("Bush Dome / Cliffside", "United States", "Texas", 35.35, -101.98, "Gas field", "Active", ["He"], 1929,
     "The Federal Helium Reserve near Amarillo: helium from Hugoton–Panhandle gas, stockpiled underground since the airship era and sold down over the last decade."),
    ("Ras Laffan", "Qatar", "Al Khor", 25.90, 51.55, "Gas field", "Active", ["He"], 2005,
     "Helium stripped from the North Field's gas as it is liquefied for export — a by-product that makes Qatar the second-largest helium producer."),
    ("Spruce Pine", "United States", "North Carolina", 35.92, -82.06, "Quarry", "Active", ["Si"], 1900,
     "The purest quartz on Earth, and the source of nearly every crucible in which semiconductor silicon is grown; when Hurricane Helene flooded the town in 2024 the chip industry noticed."),
    ("Fugu", "China", "Shaanxi", 39.03, 111.07, "Quarry", "Active", ["Mg"], 1995,
     "Dolomite for the Pidgeon-process magnesium plants of the Shaanxi–Shanxi border, which make most of the world's magnesium metal on cheap coal."),
    ("Nueva Victoria", "Chile", "Tarapacá Region", -20.72, -69.63, "Open pit", "Active", ["I"], 1990,
     "Iodine leached from the nitrate caliche of the Atacama — the same ore that made Chile rich before Haber–Bosch — supplying about half the world's iodine."),
]


def main():
    print("elements")
    schema = ensure_props(ELEMENTS_DS, {}, "elements")
    pages = query_all(ELEMENTS_DS)
    by_sym = {}
    for p in pages:
        sym = "".join(x["plain_text"] for x in p["properties"].get("Notation", {}).get("rich_text", [])).strip()
        if sym:
            by_sym[sym] = p
    filled, skipped, unknown = 0, 0, []
    for sym, (mined_as, grade, minerals, text) in EXTRACTION.items():
        page = by_sym.get(sym)
        if not page:
            unknown.append(sym)
            continue
        payload = {}
        want = {"Mined As": ("select", mined_as), "Ore Grade (ppm)": ("number", grade),
                "Ore Minerals": ("rich_text", minerals), "Extraction": ("rich_text", text)}
        for prop, (kind, val) in want.items():
            if val is None or prop not in schema:
                continue
            cur = page["properties"].get(prop, {})
            curval = cur.get(cur.get("type", ""), None)
            if curval not in (None, [], ""):
                continue                              # a human already answered
            if kind == "select":
                payload[prop] = {"select": {"name": val}}
            elif kind == "number":
                payload[prop] = {"number": val}
            else:
                payload[prop] = {"rich_text": [{"text": {"content": val}}]}
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
            filled += 1
        else:
            skipped += 1
    if unknown:
        print("  symbols not found in the Elements DB:", unknown)
    print(f"  extraction: {filled} elements filled, {skipped} already complete, {len(EXTRACTION)} defined")

    print("\nmines")
    m_schema = ensure_props(MINES_DS, {}, "mines")
    sync_rows(MINES_DS, m_schema,
              [{"Name": n, "Country": c, "Region": r, "Latitude": lat, "Longitude": lon,
                "Type": t, "Status": st, "Opened": op, "Notes": notes}
               for n, c, r, lat, lon, t, st, _, op, notes in MINES],
              "mines")

    mines = {title_of(p, "Name"): p for p in query_all(MINES_DS) if title_of(p, "Name")}
    changed, edges, missing = 0, 0, set()
    for n, *_rest in MINES:
        syms = _rest[6]
        page = mines.get(n)
        if not page:
            continue
        ids = set()
        for s in syms:
            if s in by_sym:
                ids.add(by_sym[s]["id"])
            else:
                missing.add(s)
        cur = {x["id"] for x in (page["properties"].get("Commodities", {}).get("relation") or [])}
        new = cur | ids
        edges += len(new)
        if new != cur:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
                 {"properties": {"Commodities": {"relation": [{"id": x} for x in sorted(new)]}}})
            changed += 1
    if missing:
        print("  unresolved element symbols ignored:", sorted(missing))
    print(f"  commodities: updated {changed} mines · {edges} mine→element links")
    print("\nnow run: python3 scripts/fetch_elements.py && python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
