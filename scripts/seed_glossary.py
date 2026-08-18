"""Create and seed Glossary [DB]: the terms the rest of the site uses.

Each term has a domain, a one- or two-sentence definition, and optional
aliases. What it does NOT store is where the term appears — build.py traces
every term through the text of every entity on the site that carries prose
(equations, theories, machines, skills, timeline events, mines, observatories,
discoveries, missions, constants, researchers, forces, instruments, rock types
and the extraction stories on the elements) and computes the "appears in" links at
build time. Maintained by hand those links would rot the day a new page was
added; computed, a term added here traces itself, and a page added elsewhere
shows up under every term it uses.

Idempotent: creates the database if missing, backfills empty fields, never
overwrites a definition someone has edited.
Run on the VPS:  ./deploy.sh seed_glossary
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, sync_rows  # noqa: E402


def find_ds(title):
    """Data-source id by exact title, or None. (seed_constants has one too, but that
    module authenticates at import, which breaks offline validation of this one.)"""
    d = call("POST", "https://api.notion.com/v1/search",
             {"query": title, "filter": {"property": "object", "value": "data_source"}, "page_size": 50})
    for r in d.get("results", []):
        if "".join(x.get("plain_text", "") for x in r.get("title", [])).strip() == title:
            return r["id"]
    return None

PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"   # Physical Sciences
TITLE = "Glossary [DB]"

DOMAINS = ["Mechanics", "Thermodynamics", "Electromagnetism", "Quantum", "Relativity", "Cosmology", "Astronomy",
           "Nuclear & Particle", "Chemistry", "Mineralogy", "Mining & Metallurgy", "Machines",
           "Workshop", "Mathematics", "Measurement", "Waves & Fluids", "Cue sports"]

# term, domain, definition, aliases (comma-separated, for tracing)
TERMS = [
    # ---- thermodynamics
    ("Entropy", "Thermodynamics", "A measure of how many microscopic arrangements a system could be in and still look the same from outside — equivalently, of energy that can no longer do work. It never decreases in a closed system, which is the second law.", "entropies"),
    ("Enthalpy", "Thermodynamics", "Internal energy plus pressure times volume: the heat content of a system at constant pressure, and the quantity that changes when something burns, boils or reacts in the open.", ""),
    ("Adiabatic", "Thermodynamics", "A process with no heat exchanged with the surroundings — because it is insulated, or because it happens too fast for heat to move. Compression and expansion strokes in engines are close to it.", "adiabat, adiabatically, isentropic"),
    ("Isothermal", "Thermodynamics", "A process at constant temperature, which means heat flows in or out exactly as fast as work is done. The slow, ideal limit that real engines cannot reach.", "isotherm"),
    ("Isobaric", "Thermodynamics", "At constant pressure. Boiling in an open boiler and combustion in a gas turbine are both isobaric.", "isobar, constant pressure"),
    ("Isochoric", "Thermodynamics", "At constant volume, so no work is done — the ideal picture of the spark firing in a petrol engine, all the heat arriving before the piston moves.", "isochore, constant volume"),
    ("Heat engine", "Thermodynamics", "Any device that takes heat from a hot source, turns some of it into work, and rejects the rest to a cold sink. The fraction it converts is bounded by the two temperatures alone.", "heat engines"),
    ("Thermal efficiency", "Thermodynamics", "Work out divided by heat in — what you get for what you burn. Real engines run from a few percent to about 60 %.", "efficiency"),
    ("Carnot limit", "Thermodynamics", "The greatest efficiency any heat engine can have between two temperatures: 1 − T_cold/T_hot, in kelvin. Set in 1824, never beaten.", "Carnot efficiency, Carnot"),
    ("Coefficient of performance", "Thermodynamics", "For a heat pump or refrigerator, the heat moved per unit of work put in. Unlike an efficiency it can exceed 1 — a good heat pump moves four joules of heat for one of electricity.", "COP"),
    ("Regenerator", "Thermodynamics", "A heat store — usually a matrix of wire or ceramic — that takes heat from a gas on one pass and gives it back on the return, so it is not thrown away. The trick that lets a Stirling engine approach the Carnot limit.", "regenerative"),
    ("Working fluid", "Thermodynamics", "The gas or liquid that carries heat through an engine's cycle: air in an Otto engine, steam in a Rankine plant, refrigerant in a heat pump.", "working gas"),
    ("Latent heat", "Thermodynamics", "Heat that changes a substance's phase without changing its temperature — melting, boiling. Why steam scalds worse than water at the same temperature, and why boilers and condensers dominate a steam plant.", ""),
    ("Black body", "Thermodynamics", "An idealised object that absorbs all radiation falling on it and emits a spectrum that depends only on its temperature. Stars, and the microwave background, come remarkably close.", "blackbody, black-body"),
    ("Absolute zero", "Thermodynamics", "0 K, −273.15 °C: the temperature at which a system holds the least energy it possibly can. Unreachable in a finite number of steps, by the third law.", "kelvin"),
    # ---- electromagnetism
    ("Electromotive force", "Electromagnetism", "The voltage a source can drive round a circuit — from a battery's chemistry or a changing magnetic field. Not a force, despite the name.", "EMF, back-EMF"),
    ("Induction", "Electromagnetism", "A changing magnetic field through a loop of wire drives a voltage in it. The principle of every generator, transformer and induction motor.", "induced, induces, inductive"),
    ("Commutator", "Electromagnetism", "The segmented copper ring on a DC motor's shaft that reverses the coil current every half turn, so the push always goes the same way. Brushes rub on it, and wear.", "commutation, brushes"),
    ("Rotating magnetic field", "Electromagnetism", "What three-phase current makes in a ring of stator coils: a magnetic field that spins on its own, with nothing moving. The rotor of an induction motor chases it.", "rotating field, field that rotates"),
    ("Eddy current", "Electromagnetism", "A current induced in a lump of conductor by a changing field, circulating uselessly and heating it. Why transformer cores are stacked from thin insulated sheets instead of cast solid.", "eddy currents, laminations"),
    ("Permittivity", "Electromagnetism", "How much a material resists forming an electric field inside it. The vacuum's own value, ε₀, sets the strength of the electric force.", ""),
    ("Permeability", "Electromagnetism", "The magnetic counterpart of permittivity: how readily a material carries a magnetic field. Iron's is thousands of times the vacuum's, which is why motors have iron in them.", ""),
    ("Superconductivity", "Electromagnetism", "The complete loss of electrical resistance below a critical temperature, when electrons pair up and move as one quantum state. Explained by BCS theory in 1957.", "superconductor, superconducting"),
    # ---- quantum
    ("Quantum", "Quantum", "The smallest possible unit of something — energy, charge, angular momentum. Planck's 1900 proposal that energy comes in packets of hf, made to fit a graph, started everything.", "quantised, quantized, quanta"),
    ("Wavefunction", "Quantum", "The mathematical object that describes a quantum system; its square gives the probability of finding it in each state. Whether it is a thing or a description is still argued.", "wave function"),
    ("Uncertainty principle", "Quantum", "Position and momentum — or energy and time — cannot both be sharply defined at once; the product of their spreads has a floor of about ℏ/2. Not a limit on measurement but on what exists to measure.", "uncertainty"),
    ("Band gap", "Quantum", "The energy gap between the electrons a solid holds tightly and the ones free to move. Zero in a metal, small in a semiconductor, large in an insulator; it sets an LED's colour and a solar cell's voltage.", "bandgap, band structure"),
    ("Intercalation", "Quantum", "Ions slipping into the layers of a crystal — lithium into graphite — without breaking it apart. What lets a lithium-ion cell charge and discharge thousands of times.", "intercalate, intercalates"),
    ("Entanglement", "Quantum", "Two particles sharing one quantum state, so that measuring one fixes the other's outcome however far apart they are. Bell's inequality turned the philosophy into an experiment, and the experiments agreed with quantum mechanics.", "entangled"),
    ("Qubit", "Quantum", "A two-state quantum system used as a bit — one that can be in a superposition of 0 and 1 and entangled with others. Copying one is forbidden.", "qubits"),
    # ---- relativity
    ("Spacetime", "Relativity", "Space and time as one four-dimensional thing, whose curvature is gravity. Matter tells it how to bend; it tells matter how to move.", "space-time"),
    ("Geodesic", "Relativity", "The straightest possible path through curved spacetime — the path a freely falling body follows. Orbits are geodesics; the apple falls along one.", "geodesics"),
    ("Event horizon", "Relativity", "The surface around a black hole inside which nothing, light included, can get out. Its area is the black hole's entropy, which is where thermodynamics and gravity meet.", "horizon"),
    ("Schwarzschild radius", "Relativity", "The radius a mass must be squeezed inside to become a black hole — 3 km for the Sun, 9 mm for the Earth.", ""),
    ("Time dilation", "Relativity", "Clocks run slower when moving fast or sitting deep in a gravitational field. GPS satellites correct for both, in opposite directions.", "dilation"),
    # ---- cosmology
    ("Redshift", "Cosmology", "The stretching of light to longer wavelengths as the universe expands during its journey. Written z; the CMB is at z ≈ 1100, and it doubles as a clock and a distance.", "redshifted, redshifts"),
    ("Recombination", "Cosmology", "The moment, 380,000 years in, when the universe cooled enough for electrons to bind to protons and become neutral hydrogen — after which light could travel freely.", ""),
    ("Cosmic microwave background", "Cosmology", "The light released at recombination, arriving now stretched a thousandfold into microwaves at 2.725 K from every direction. The oldest light there is.", "CMB, microwave background"),
    ("Inflation", "Cosmology", "A proposed burst of exponential expansion in the first fraction of a second, which would explain why the universe is so flat and uniform and where the seeds of galaxies came from.", "inflaton, inflationary"),
    ("Dark matter", "Cosmology", "Matter that gravitates but neither emits nor absorbs light, inferred from how galaxies and clusters move; about five times as much of it as ordinary matter, and its identity is unknown.", ""),
    ("Dark energy", "Cosmology", "Whatever is making the expansion of the universe accelerate — about seven tenths of its energy budget, consistent so far with a cosmological constant.", "cosmological constant"),
    ("Scale factor", "Cosmology", "The size of the universe relative to now, written a; distances between galaxies grow in proportion to it. Redshift is 1/a − 1.", ""),
    ("Hubble constant", "Cosmology", "The present rate of expansion — how fast recession speed grows with distance, about 70 km/s per megaparsec. Two careful methods disagree on it by 5σ, which is the Hubble tension.", "Hubble parameter, Hubble tension"),
    ("Big Bang nucleosynthesis", "Cosmology", "The first few minutes, when the universe was hot enough to fuse protons and neutrons into helium and traces of lithium; the predicted 24 % helium by mass is what we see.", "nucleosynthesis, primordial"),
    ("Reionization", "Cosmology", "The stripping of electrons back off intergalactic hydrogen by the first stars and quasars, between about 150 million and a billion years — the universe's second, and final, phase change.", "reionized, reionize"),
    ("Population III", "Cosmology", "The first generation of stars, made of hydrogen and helium alone, huge and short-lived; none has yet been observed.", "first stars"),
    ("Heat death", "Cosmology", "The far future in which the universe reaches maximum entropy — no gradients, no structure, no work possible.", ""),
    # ---- astronomy
    ("Spectral type", "Astronomy", "A star's classification by the absorption lines in its light, which is really by temperature: O B A F G K M, hottest to coolest. The Sun is a G2.", "spectral class, spectral sequence"),
    ("Parallax", "Astronomy", "The apparent shift of a nearby star against distant ones as the Earth moves round the Sun. The only direct measure of stellar distance, and the origin of the parsec.", "parsec"),
    ("Cepheid", "Astronomy", "A pulsating star whose period is set by its true brightness, so measuring the period gives the distance. The rung of the distance ladder everything above stands on.", "Cepheids"),
    ("Quasar", "Astronomy", "The core of a distant galaxy outshining the whole galaxy, powered by matter falling onto a supermassive black hole. The first was recognised in 1963 by its redshift.", "quasars, active galactic nucleus, AGN"),
    ("Pulsar", "Astronomy", "A spinning neutron star sweeping a radio beam past us like a lighthouse, with a regularity that rivals atomic clocks. Found in 1967 and briefly labelled LGM-1.", "pulsars, neutron star"),
    ("Chandrasekhar limit", "Astronomy", "About 1.4 solar masses: the most a white dwarf can weigh before electron degeneracy pressure fails and it collapses.", ""),
    ("Interferometer", "Astronomy", "An instrument that combines waves from two paths and reads their difference — kilometre-long arms for gravitational waves, or telescopes a continent apart to resolve a black hole's shadow.", "interferometry, interferometers, interferometric"),
    # ---- nuclear & particle
    ("Fission", "Nuclear & Particle", "A heavy nucleus splitting into two lighter ones and releasing energy and neutrons; if each fission causes at least one more, the reaction is self-sustaining.", "chain reaction, fissile"),
    ("Fusion", "Nuclear & Particle", "Light nuclei joining into a heavier one and releasing energy — the power source of stars, and the hard way to make helium on Earth.", "fuse, fusing"),
    ("Half-life", "Nuclear & Particle", "The time for half of a sample of a radioactive isotope to decay. Fixed for each isotope, from microseconds to longer than the age of the universe.", "half-lives"),
    ("Isotope", "Nuclear & Particle", "Atoms of one element with different numbers of neutrons — same chemistry, different mass and sometimes different stability. Uranium-235 fissions; uranium-238 mostly does not.", "isotopes"),
    ("Moderator", "Nuclear & Particle", "A material — water, graphite — that slows fast neutrons down so uranium-235 can capture them. Every thermal reactor has one.", "moderated, moderating, slowed neutrons"),
    ("Enrichment", "Nuclear & Particle", "Raising the share of uranium-235 above its natural 0.7 %, by spinning uranium hexafluoride in centrifuges. Reactor fuel is 3–5 %; a weapon needs about 90 %.", "enriched"),
    ("Baryon", "Nuclear & Particle", "A particle made of three quarks — protons and neutrons, essentially. Ordinary matter is baryonic; the excess of baryons over antibaryons is the unsolved problem of baryogenesis.", "baryons, baryonic, baryogenesis"),
    ("Standard Model", "Nuclear & Particle", "The theory of everything except gravity: twelve matter particles, four force carriers, the Higgs, and about nineteen numbers nobody can derive. Fifty years unbroken.", ""),
    ("Gauge symmetry", "Nuclear & Particle", "A symmetry of the equations under local transformations that turns out to require the existence of a force. Electromagnetism, the weak and strong forces are all gauge forces.", "gauge theory, gauge"),
    ("Symmetry breaking", "Nuclear & Particle", "A state that has less symmetry than the laws that produced it, like a pencil falling over. The Higgs field's doing it is what gives the W and Z their mass.", "spontaneous symmetry breaking"),
    ("Neutrino", "Nuclear & Particle", "A near-massless neutral particle that barely interacts with anything; trillions pass through you each second. The cosmic neutrino background at 1.95 K is still undetected.", "neutrinos"),
    # ---- chemistry
    ("Oxidation", "Chemistry", "Loss of electrons — historically, combining with oxygen. Rust, fire and a battery discharging are all oxidation on one side and reduction on the other.", "oxidise, oxidize, oxidised, redox"),
    ("Reduction", "Chemistry", "Gain of electrons; in metallurgy, pulling a metal out of its ore by stripping the oxygen or sulfur off it — with carbon, hydrogen, or electricity.", "reduced, reducing"),
    ("Electrolysis", "Chemistry", "Driving a chemical reaction with electric current — splitting water, or dissolving aluminium out of alumina in a Hall–Héroult cell. The reverse of a battery.", "electrolyse, electrolytic, electrowinning, electrorefining"),
    ("Catalyst", "Chemistry", "A substance that speeds a reaction without being consumed, by offering an easier path. Platinum in a fuel cell and a catalytic converter; iron in Haber–Bosch.", "catalytic, catalysis"),
    ("Activation energy", "Chemistry", "The energy barrier a reaction must climb before it runs, and the reason rates rise so steeply with temperature — the Arrhenius law.", "Arrhenius"),
    ("Flux", "Chemistry", "In joining and smelting, a substance that dissolves oxide and keeps air off hot metal so it can wet and bond — rosin in solder, borax in brazing, limestone in a blast furnace.", "fluxes"),
    ("Alloy", "Chemistry", "A metal mixed with other elements to change its properties: steel is iron with carbon, bronze copper with tin, superalloys nickel with a dozen things.", "alloys, alloyed"),
    ("Mole", "Chemistry", "The chemist's counting unit: 6.022 × 10²³ entities, chosen so that a mole of carbon-12 weighs twelve grams.", "molar"),
    # ---- mineralogy
    ("Mineral", "Mineralogy", "A naturally occurring solid with a definite chemical composition and crystal structure. About 6,000 are known; a rock is a mixture of them.", "minerals"),
    ("Mohs hardness", "Mineralogy", "A 1–10 scratch scale: each mineral scratches the ones below it. Talc 1, gypsum 2, calcite 3, quartz 7, corundum 9, diamond 10. Ordinal, not linear.", "Mohs, hardness"),
    ("Specific gravity", "Mineralogy", "A mineral's density relative to water. Quartz 2.65, hematite 5.3, gold 19.3 — one of the quickest ways to tell minerals apart in the hand.", "S.G."),
    ("Silicate", "Mineralogy", "A mineral built from silicon–oxygen tetrahedra, linked into chains, sheets or frameworks. Over 90 % of the crust: feldspar, quartz, mica, olivine, pyroxene.", "silicates"),
    ("Kimberlite", "Mineralogy", "A volcanic rock from very deep in the mantle that carries diamonds up in pipes. Almost every diamond mine is a kimberlite pipe.", ""),
    ("Placer", "Mineralogy", "A deposit of dense, resistant minerals — gold, cassiterite, ilmenite — concentrated by rivers or waves after weathering out of rock. Panned, dredged, or sluiced.", "placers, alluvial"),
    ("Pegmatite", "Mineralogy", "A very coarse-grained igneous rock, the last liquid of a cooling granite, where rare elements — lithium, tantalum, beryllium — concentrate in big crystals.", "pegmatites"),
    ("Laterite", "Mineralogy", "The deep, iron- and aluminium-rich soil left when tropical rain leaches everything else out of rock. Bauxite is an aluminium laterite; nickel laterites are half the world's nickel.", "laterites, lateritic"),
    ("Porphyry deposit", "Mineralogy", "A huge, low-grade body of copper (often with molybdenum and gold) disseminated through a granitic intrusion. Most of the world's copper, mined open-pit at half a percent.", "porphyry"),
    # ---- mining & metallurgy
    ("Ore", "Mining & Metallurgy", "Rock that holds enough of something valuable to be worth mining. What counts as enough depends on price and technology, and changes.", "ores, orebody, ore body"),
    ("Ore grade", "Mining & Metallurgy", "The concentration of the wanted element in the ore — 50 % for iron, 0.5 % for copper, a few grams per tonne for gold. Divided by crustal abundance it gives the concentration factor.", "grade, cut-off grade"),
    ("Concentration factor", "Mining & Metallurgy", "How much geology has enriched an element above its average in the crust before it is worth mining: about 3 for aluminium, 80 for copper, 500 for gold, over 100,000 for antimony.", "clarke of concentration"),
    ("Flotation", "Mining & Metallurgy", "Grinding ore to powder, mixing it with water and chemicals that make the wanted mineral water-repellent, and blowing bubbles through it — the mineral floats off in the froth. The workhorse of base-metal mining.", "froth flotation, floated"),
    ("Smelting", "Mining & Metallurgy", "Melting an ore or concentrate with a reducing agent and a flux so the metal separates from the slag. Blast furnaces, flash smelters, submerged-arc furnaces.", "smelt, smelted, smelter, matte, slag"),
    ("Leaching", "Mining & Metallurgy", "Dissolving the wanted metal out of ore with a chemical — cyanide for gold, sulfuric acid for copper oxides and uranium — and recovering it from the solution. Heaps, tanks, or in the ground.", "leach, leached, heap leach, in-situ leach, cyanidation"),
    ("Solvent extraction", "Mining & Metallurgy", "Separating metals in solution by shaking with an organic liquid that prefers one of them, over and over. Copper, uranium, and every one of the rare earths.", "SX, SX-EW"),
    ("Tailings", "Mining & Metallurgy", "What is left after the valuable mineral is taken out — most of the rock, ground fine and wet, stored behind dams. The largest structures the industry builds, and the ones that fail worst.", ""),
    ("Open pit", "Mining & Metallurgy", "Mining from the surface down in benches, moving the overburden aside. Cheap per tonne, so it wins for low-grade ore; the deepest is over a kilometre.", "open-pit, opencast, strip mining"),
    ("Underground mining", "Mining & Metallurgy", "Following the ore down shafts and tunnels when it is too deep or too narrow for a pit. Room-and-pillar, longwall, block caving; the deepest reach 4 km.", "underground, block cave, longwall"),
    ("Brine", "Mining & Metallurgy", "Salt-saturated water, pumped from beneath salt flats or the sea, from which lithium, potash, bromine and magnesium are taken by evaporation or chemistry.", "brines, salar"),
    ("Bayer process", "Mining & Metallurgy", "Dissolving bauxite in hot caustic soda to get pure alumina, leaving red mud behind. Step one of aluminium; Hall–Héroult is step two.", "Bayer"),
    ("Hall–Héroult process", "Mining & Metallurgy", "Electrolysing alumina dissolved in molten cryolite at about 960 °C to make aluminium metal — the reason aluminium smelters sit next to cheap electricity.", "Hall–Héroult, Hall-Héroult, Hall–Heroult, Hall-Heroult"),
    ("Kroll process", "Mining & Metallurgy", "Reducing titanium or zirconium chloride with magnesium metal in a sealed vessel to a porous sponge. Slow and batchwise, and why titanium is expensive.", "Kroll"),
    ("Blast furnace", "Mining & Metallurgy", "A tall shaft in which iron ore, coke and limestone are charged at the top and hot air blown in at the bottom; molten iron and slag are tapped from the hearth. Iron's route to steel for seven centuries.", "pig iron"),
    ("Rare earths", "Mining & Metallurgy", "The fifteen lanthanides plus scandium and yttrium — not rare, but so alike chemically that separating them takes hundreds of solvent-extraction stages. Neodymium magnets are the reason anyone cares.", "rare earth, rare-earth, lanthanide, lanthanides, REE"),
    # ---- machines
    ("Cycle", "Machines", "A sequence of processes that brings a working fluid back to its starting state, done over and over. On a p–V diagram it is a closed loop, and the area inside is the work per cycle.", "cycles"),
    ("Compression ratio", "Machines", "The cylinder's largest volume over its smallest. Higher means more efficient — until the fuel knocks, which is what limits petrol engines to about 10 and frees diesels to reach 20.", ""),
    ("Four-stroke", "Machines", "Intake, compression, power, exhaust — one power stroke every two revolutions. Otto's 1876 cycle, and most engines on the road.", "four stroke, two-stroke"),
    ("Turbine", "Machines", "A rotor of blades that a moving fluid — steam, gas, water, wind — spins as it passes. Reaction turbines run full of fluid under pressure; impulse turbines take a jet.", "turbines"),
    ("Superalloy", "Machines", "A nickel- or cobalt-based alloy that keeps its strength close to its melting point, grown as a single crystal for turbine blades. The reason jet engines can run hotter than their own metal would allow.", "superalloys, single-crystal"),
    ("Stator", "Machines", "The part of an electric machine that does not move — the outer ring of coils or magnets. The rotor turns inside it.", "rotor"),
    ("Specific impulse", "Machines", "How much thrust a rocket gets per unit of propellant per second, in seconds: 250–300 for solids, up to 450 for hydrogen–oxygen. The rocket equivalent of fuel economy.", "Isp"),
    ("Power density", "Machines", "Power per unit of mass or volume. A jet engine's is enormous, a wind turbine's tiny — which is why one is small and the other is not.", ""),
    ("Fuel cell", "Machines", "A device that combines a fuel and oxygen electrochemically to make electricity and water directly, without burning — so it is not bound by the Carnot limit.", "fuel cells"),
    ("Thermocouple", "Machines", "Two different metals joined at a hot end and a cold end make a small voltage — the Seebeck effect. Used to measure temperature, and in bulk to power spacecraft from a lump of plutonium.", "thermoelectric, Seebeck"),
    # ---- workshop
    ("Annealing", "Workshop", "Heating a metal and cooling it slowly to soften it and relieve stress. The opposite of quenching.", "anneal, annealed"),
    ("Quenching", "Workshop", "Cooling hot steel fast — in oil or water — to trap carbon in a hard, brittle structure called martensite. Tempering afterwards trades some hardness back for toughness.", "quench, quenched, martensite, tempering, temper"),
    ("Work hardening", "Workshop", "A metal getting harder and more brittle as it is bent or hammered cold, as its crystals tangle. Why a paperclip snaps after a few bends, and why forged parts are annealed between heats.", "work-hardening, work-harden, work-hardens, work-hardened, cold working"),
    ("Wetting", "Workshop", "A liquid metal spreading over and bonding to a solid one, as solder must to copper. Needs a clean surface and flux; if it balls up instead, the joint has failed before it froze.", "wet, wets"),
    ("Capillary action", "Workshop", "Liquid pulled into a narrow gap by surface tension. What draws brazing filler through a joint, and why the gap has to be tight.", "capillarity"),
    ("Arc", "Workshop", "Electric current jumping through ionised gas — a plasma at thousands of degrees. The heat source of arc welding and of the arc furnace.", "arc welding, arcs"),
    ("Shielding gas", "Workshop", "Argon or a mix blown over a weld pool to keep oxygen and nitrogen out, which would otherwise make it porous and brittle. Stick welding makes its own from the flux coating.", "shielding, argon"),
    ("Burr", "Workshop", "The thin ragged edge of metal left where a cut or grind ends. On a blade it must be removed or it folds on first use; on machined parts it is deburred.", "burrs, deburr, deburring"),
    ("Tolerance", "Workshop", "The permitted variation in a dimension — how far from nominal a part may be and still fit. Tighter costs more; a lathe holds a hundredth of a millimetre.", "tolerances"),
    ("Mechanical advantage", "Workshop", "The factor by which a machine multiplies force at the cost of distance — a lever's arm ratio, the number of rope segments in a pulley system.", "purchase"),
    ("Cure", "Workshop", "The chemical hardening of concrete, epoxy or resin over time — a reaction, not drying. Concrete kept damp for a week is far stronger than concrete left to dry out.", "curing, cured, hydration"),
    # ---- mathematics & measurement
    ("Logarithmic scale", "Mathematics", "An axis on which each step multiplies rather than adds, so quantities spanning many orders of magnitude fit on one picture. The timeline, the abundance lenses and the p–V diagram of a steam engine all use one.", "log scale, log axis, orders of magnitude"),
    ("Order of magnitude", "Mathematics", "A factor of ten. Two things an order of magnitude apart differ tenfold; the timeline covers 161 of them.", "orders of magnitude"),
    ("Dimensionless", "Mathematics", "A quantity with no units — a ratio, like the fine-structure constant or a compression ratio — and so the same for anyone who measures it.", ""),
    ("Parts per million", "Measurement", "One part in a million by mass, unless stated otherwise: 1 ppm is 1 gram per tonne. Crustal abundances and ore grades on this site are quoted in it.", "ppm"),
    ("Kelvin", "Measurement", "The SI unit of temperature, counted from absolute zero in steps the size of a Celsius degree. Every thermodynamic formula wants kelvin.", "K"),
    ("Electronvolt", "Measurement", "The energy an electron gains crossing one volt — 1.6 × 10⁻¹⁹ J. The natural unit of atoms (eV), nuclei (MeV) and particle physics (GeV, TeV).", "eV, MeV, GeV, TeV"),
    ("Sigma", "Measurement", "One standard deviation; a result's distance from the null in those units. Particle physics claims a discovery at 5σ; the Hubble tension has reached it.", "standard deviation, 5σ"),
    ("Density", "Measurement", "Mass per unit volume — and, by extension, any quantity per unit volume: energy density, charge density, number density. The critical density is the one that decides whether the universe expands forever.", "densities"),
    # ---- filling the gaps /explainers surfaced (2026-08-17). Adding the explainers
    # showed which words the site uses constantly but had never defined: no black
    # hole, no galaxy, no orbit, no electron, and no home at all for mechanics.
    # Chosen on measured use in the site's own prose, not on what sounded missing.
    ("Momentum", "Mechanics", "Mass times velocity — the quantity a collision conserves whatever else it destroys. Newton stated his second law as its rate of change, which is the form that survives when the mass is changing too.", ""),
    ("Friction", "Mechanics", "The force resisting sliding between surfaces, roughly proportional to how hard they are pressed together and nearly independent of contact area. It wears tools out, and it is also the only reason brakes, bolts and knots hold.", "frictional"),
    ("Resonance", "Mechanics", "Driving a system at its own natural frequency, so small repeated pushes accumulate into a large amplitude. It tunes a radio, shatters a glass, and is the thing bridges are designed to avoid.", "resonant, resonate"),
    ("Stress", "Mechanics", "Force per unit area inside a material — the quantity a part actually fails on, not the load you applied. Paired with strain, the deformation it causes, it gives both stiffness and breaking point.", ""),
    ("Combustion", "Thermodynamics", "Rapid oxidation that releases heat and light: fuel plus oxygen to carbon dioxide and water, when it goes cleanly. The heat source for most engines on this site, and the reason nearly all of them breathe air.", "combustible"),
    ("Magnetic field", "Electromagnetism", "The field produced by moving charge and by intrinsic spin, exerting force only on charge that is itself moving. It has no sources — no magnetic monopole has ever been found — so its field lines close on themselves.", ""),
    ("Electric field", "Electromagnetism", "Force per unit charge at a point in space. Unlike the magnetic field it begins and ends on charge, and a changing one is half of what light is made of.", ""),
    ("Lens", "Electromagnetism", "A shaped piece of transparent material that brings light to a focus by refraction, its power set by curvature and refractive index. Its errors — chromatic and spherical — are why a good one is several elements deep.", ""),
    ("Photon", "Quantum", "The quantum of the electromagnetic field: massless, always moving at c, carrying energy hf. Light behaves as a wave right up until you count the arrivals one at a time.", ""),
    ("Electron", "Nuclear & Particle", "The light, negatively charged, apparently pointlike particle whose arrangement around a nucleus fixes every chemical property an element has. Found in 1897; no one has yet measured a size for it.", ""),
    ("Gravitational wave", "Relativity", "A ripple in spacetime radiated when masses accelerate asymmetrically — merging black holes and neutron stars. Predicted in 1916 and detected in 2015, at a strain smaller than a proton's width across a four-kilometre arm.", ""),
    ("Black hole", "Astronomy", "A region where gravity has closed spacetime around itself, bounded by an event horizon that nothing crosses outward. Stellar ones start above about three solar masses; supermassive ones of millions to billions sit in galactic centres.", ""),
    ("Galaxy", "Astronomy", "A gravitationally bound system of stars, gas, dust and dark matter — from dwarfs of a few million stars to giants of a trillion. The Milky Way is a barred spiral roughly 100,000 light-years across.", "galaxies, galactic"),
    ("Orbit", "Astronomy", "The path one body follows around another under gravity alone: an ellipse with the primary at a focus, as Kepler found. Changing one costs velocity, which is why spaceflight is bookkeeping in delta-v.", ""),
    ("Exoplanet", "Astronomy", "A planet around a star other than the Sun. The first around a main-sequence star was confirmed in 1995; thousands are known now, most of them found by transit or by radial velocity.", "extrasolar planet"),
    ("Transit", "Astronomy", "A planet crossing the disc of its star as seen from here, dimming it by a fraction of a percent for a few hours. The depth gives the planet's radius and the repeat gives its year.", ""),
    ("Telescope", "Astronomy", "An instrument that gathers light over an area vastly larger than a pupil and brings it to a focus. Aperture sets both the faintest thing visible and the finest detail resolvable, which is why they only ever get bigger.", ""),
    ("Neutron star", "Astronomy", "What is left when a massive star's iron core gives way — one or two solar masses inside about 20 km, held up by neutron degeneracy pressure. The ones that spin and beam are pulsars.", ""),
    ("Periodic table", "Chemistry", "The elements ordered by atomic number so that each column shares an outer-electron structure, and therefore its chemistry. Mendeleev left gaps in 1869 and the missing elements arrived where he had put them.", ""),
    ("Vacuum", "Machines", "Space with the gas pumped out, rated by how much pressure is left — from a rough 10⁻³ mbar down to ultra-high vacuum below 10⁻⁹. Electron microscopes, thin-film coating and particle beams all need one to work at all.", ""),
    ("Soil mechanics", "Machines", "How soil behaves as a structural material: its shear strength, how water moves through it, how much it settles under load. Foundations, dams, tunnels and slopes stand or fail on it.", ""),
    ("Concrete", "Workshop", "Cement, water and aggregate, which hardens by hydration rather than by drying and goes on gaining strength for years. Strong in compression and weak in tension, which is why it is cast around steel.", ""),
    ("Thin film", "Workshop", "A layer from a few atoms to a few microns thick, laid down by evaporation, sputtering or chemical vapour. Mirrors, anti-reflection coatings, semiconductors and hard tool coatings are all made this way.", ""),
    ("Plate tectonics", "Mineralogy", "The Earth's outer shell is broken into plates that move over the mantle, and nearly everything geological — earthquakes, volcanoes, mountain belts, most ore deposits — happens where they meet.", "tectonic, tectonics"),
    ("Derivative", "Mathematics", "The instantaneous rate of change of one quantity with respect to another — the slope of a curve at a point. Almost every law of physics on this site is written as one.", ""),
    ("Integral", "Mathematics", "The accumulation of a quantity across an interval: the area under the curve, and the inverse of the derivative. Work, charge and total mass are each an integral of something simpler.", ""),
    ("Probability", "Mathematics", "How often an outcome occurs in the long run, on a scale of 0 to 1. Quantum mechanics makes it fundamental rather than an admission of ignorance, which is the part that still bothers people.", "probabilities, probabilistic"),
    ("Fourier transform", "Mathematics", "The decomposition of any signal into the sines and cosines that sum to it, trading time for frequency. Spectroscopy, crystallography and every kind of signal processing run on it.", "Fourier"),
    ("Prime number", "Mathematics", "A whole number above 1 divisible only by itself and 1. There are infinitely many, they thin out logarithmically, and no one can tell you the next one without looking.", "primes"),
    ("Light-year", "Measurement", "The distance light covers in a year — 9.46 × 10¹² km. A length despite the name, and the unit that makes galactic distances legible.", "light year"),
    # ---- the shop-floor and control vocabulary the explainers use and the site had
    # skipped. Weaker warrant than the batch above: /skills teaches turning on a
    # lathe without ever writing "machining", so several of these earn their first
    # appearance from an explainer rather than from the site's own prose.
    ("Machining", "Workshop", "Cutting metal to size by removing chips — turning, milling, drilling, grinding. How a part gets from roughly the right shape to within a hundredth of a millimetre, and why a forged part is stronger than a machined one.", "machined, machinist"),
    ("Lathe", "Workshop", "A machine that spins the work while a fixed tool travels along it, cutting anything round: shafts, bushes, threads. The first machine tool able to reproduce its own parts, and still the one a shop buys first.", ""),
    ("Screw thread", "Workshop", "The helical ridge that turns rotation into clamping force. Pitch sets how far one turn advances it and the flank angle sets how much load it carries, which is why threads are standardised and why the standards do not interchange.", ""),
    ("Milling", "Workshop", "Cutting with a rotating multi-toothed tool while the work moves past it — the operation that makes flat faces, slots and pockets, as turning makes round ones.", ""),
    ("Shock wave", "Mechanics", "A pressure front travelling faster than the medium's own speed of sound, across which pressure, density and temperature jump almost discontinuously. Supersonic flight, explosions and supernova remnants all drive one.", "shockwave"),
    ("Control system", "Machines", "A loop that measures what a machine is actually doing, compares it with what was asked, and corrects the difference. Feedback is what makes it hold steady — or, badly tuned, what makes it hunt and oscillate.", "feedback loop"),
    # ---- the vocabulary seed_foundations introduced: vectors, calculus and the
    # mechanics of work, energy and rotation. Every one already appears in the
    # equations, machines or skills prose and traced to nothing. Two names are
    # qualified on purpose — "Mechanical work" and "Mechanical power" — because
    # bare "work" and "power" would trace "how it works" and "rocket-powered"
    # (117 and 63 hits, mostly noise); the aliases carry the physics senses.
    ("Vector", "Mathematics", "A quantity with a direction as well as a size — velocity, force, a field — written as components along axes. Add them tip to tail; multiply them two ways, dot and cross. A scalar is what it is not.", ""),
    ("Scalar", "Mathematics", "A quantity that is just a number, with no direction: mass, temperature, energy, pressure. A scalar field gives one at every point in space; its gradient is a vector.", ""),
    ("Dot product", "Mathematics", "The product of two vectors that gives a number: their lengths times the cosine of the angle between them — how much of one lies along the other. Zero for perpendicular vectors. Work is force dot displacement.", "scalar product"),
    ("Cross product", "Mathematics", "The product of two vectors that gives a third, at right angles to both, with the parallelogram's area as its length. Torque, angular momentum and the magnetic force are all cross products.", "vector product"),
    ("Radian", "Mathematics", "The natural measure of angle: arc length divided by radius, so a full turn is 2π and a straight angle π. Not a unit but a ratio, which is why sin θ ≈ θ needs no conversion factor.", ""),
    ("Solid angle", "Mathematics", "How much of the view something fills, as the area it cuts from a sphere over the radius squared, in steradians; the whole sky is 4π. Every inverse-square law is a statement about solid angle.", "steradian"),
    ("Gradient", "Mathematics", "Of a scalar field, the vector that points where it rises fastest, with the slope as its length. Heat flows down the temperature gradient; a conservative force is minus the gradient of its potential.", ""),
    ("Divergence", "Mathematics", "Of a vector field, the net outflow per unit volume at a point — a source if positive, a sink if negative. Integrated over a volume it equals the flux through the boundary, which is Gauss's theorem and Gauss's law.", ""),
    ("Curl", "Mathematics", "Of a vector field, how much it circulates about a point, as a vector along the axis of rotation. Its flux through a surface equals the circulation round the edge — Stokes' theorem — which is how a changing magnetic field drives a current round a loop.", ""),
    ("Curvature", "Mathematics", "How sharply a curve or surface bends: one over the radius of the circle that best fits it there. Straight lines have none. In general relativity it is what gravity is — matter tells spacetime how to curve.", "curved, curve"),
    ("Tensor", "Mathematics", "A vector's bigger relative: an array that turns one vector into another by a single multiplication and keeps its meaning under any rotation of the axes. Stress is one; so is the metric of spacetime.", ""),
    ("Mechanical work", "Mechanics", "Force times the distance moved along it, in joules — only the component of force along the motion counts, so carrying a load on the level does none. It is what a heat engine delivers and what a pulley system conserves.", "work done, work–energy"),
    ("Kinetic energy", "Mechanics", "The energy of motion, ½mv² — quadratic in speed, so doubling the speed quadruples it. What the wind hands a turbine, what a crumple zone must absorb, what a bullet carries.", ""),
    ("Potential energy", "Mechanics", "Energy stored by position or configuration and recoverable as motion: a raised weight, a stretched spring, water behind a dam, a satellite in a high orbit. Kinetic and potential trade back and forth; without friction their sum is fixed.", ""),
    ("Mechanical power", "Mechanics", "The rate of doing work, in watts — force times velocity, or torque times angular speed. An engine's power, not its force, sets how fast it can climb a hill; a turbine is sold by this number.", "power output, watts, kilowatts, megawatts, gigawatts, horsepower"),
    ("Torque", "Mechanics", "The turning effect of a force: force times lever arm, at right angles — a longer wrench or a push square to the handle gives more. What a motor delivers to its shaft and a nut is tightened to.", "torques"),
    ("Angular momentum", "Mechanics", "What a spinning or orbiting body keeps unless a torque acts on it: moment of inertia times angular velocity, or r × p. Why a gyroscope holds, a skater spins up, and a planet sweeps equal areas in equal times.", ""),
    ("Moment of inertia", "Mechanics", "The rotational counterpart of mass — how hard a body is to spin up — set by how far from the axis its mass sits, squared. A flywheel puts its mass at the rim for exactly this reason.", ""),
    ("Centripetal acceleration", "Mechanics", "The inward acceleration of anything moving on a curve, v²/r, needed just to keep turning at constant speed. Supplied by gravity for an orbit, by the road for a car, by the tension in a string. \"Centrifugal\" is the same thing seen from the turning frame.", "centripetal, centrifugal"),
    ("Simple harmonic motion", "Mechanics", "The sinusoidal motion of anything pulled back toward equilibrium in proportion to how far it has strayed — a mass on a spring, a pendulum at small angles, an atom in a lattice. Its period does not depend on the amplitude, which is what makes clocks possible.", "SHM, harmonic oscillator, simple harmonic"),
    ("Flywheel", "Machines", "A heavy wheel on a shaft that stores rotational energy and smooths a jerky drive: a piston engine fires in pulses and the flywheel carries it between them. Mass at the rim, where the moment of inertia counts most.", "flywheels"),
    # ---- fluids and waves, with seed_fluids_waves. A new domain: these are neither
    # the mechanics of particles nor electromagnetism, and the wave words serve
    # sound, light and water alike.
    ("Buoyancy", "Waves & Fluids", "The upward push a fluid gives anything in it, equal to the weight of fluid displaced. Why a mineral weighs less in water than in air — and by exactly its own volume of water, which is how specific gravity is measured.", "buoyant"),
    ("Viscosity", "Waves & Fluids", "A fluid's resistance to flowing — the drag between its own layers sliding past each other. Water's is low, honey's high, and it is what makes fine particles settle slowly and pipes lose pressure.", "viscous"),
    ("Turbulence", "Waves & Fluids", "Flow that has broken into eddies and no longer moves in orderly layers; the alternative is laminar. The Reynolds number says which you get, and turbulence is what mixes, drags and roars.", "turbulent, laminar"),
    ("Hydraulic head", "Waves & Fluids", "The height of a column of water that would produce a given pressure — the energy of water per unit weight, in metres. Groundwater flows down the head gradient; a dam's power is head times flow.", "head gradient, metres of head"),
    ("Terminal velocity", "Waves & Fluids", "The steady speed a falling body reaches when drag equals its weight. For a fine particle in water it goes as the radius squared, which is why silt settles in hours and clay in months.", ""),
    ("Wavelength", "Waves & Fluids", "The distance between one crest of a wave and the next. Times the frequency it gives the wave speed; for light it is what colour means, for sound, pitch.", ""),
    ("Frequency", "Waves & Fluids", "How many cycles pass a point per second, in hertz. Middle A is 440; visible light is around 5 × 10¹⁴; the energy of a photon is this times Planck's constant.", "hertz, Hz"),
    ("Standing wave", "Waves & Fluids", "A wave trapped between two boundaries so that only whole numbers of half-wavelengths fit — the fundamental and its harmonics. Strings, pipes, laser cavities and, in a sense, electrons in atoms.", "harmonics, harmonic, resonant frequency"),
    ("Refraction", "Waves & Fluids", "The bending of a wave where its speed changes — light entering glass, sound crossing warm air, a sea swell reaching the shallows. Snell's law gives the angle; the refractive index gives the speed.", "refract, refracts, refractive index"),
    # ---- the pool table, with seed_billiards. Its own domain: the words are the
    # game's, not physics'. "English" left out as an alias — it is a nationality on
    # every researcher card; "follow" and "draw" left out as terms — ordinary
    # words on this site — so Topspin and Backspin carry them as aliases.
    ("Tangent line", "Cue sports", "The line at right angles to the line of centres at contact — where the cue ball goes immediately after hitting the object ball, before any spin acts. The ninety-degree rule, drawn on the cloth.", ""),
    ("Ghost ball", "Cue sports", "The imaginary cue ball frozen where the real one must be at contact: touching the object ball on the far side from the pocket, its centre one ball's width away along the pocket line. Aim at its centre.", ""),
    ("Cut angle", "Cue sports", "The angle between the cue ball's path and the line of centres at contact — zero for a straight-in shot, 30° for a half-ball hit. It sets how the speed and energy divide between the two balls.", "cut"),
    ("Throw", "Cue sports", "The object ball's departure a degree or few off the line of centres, from friction between the balls during contact — forward on a cut, sideways with side spin. Slow shots throw more.", "cut-induced throw, spin-induced throw"),
    ("Side spin", "Cue sports", "Spin about a vertical axis, from a tip left or right of centre. It throws the object ball, alters the rebound off a cushion, and on the way there produces squirt and swerve — four effects for one stroke.", "sidespin, running side, reverse side"),
    ("Squirt", "Cue sports", "The cue ball's small deflection off the cue's line when struck with side spin, away from the side the tip was on. A property of the cue's front-end mass, not of the table; low-deflection shafts move that mass back.", "cue-ball deflection"),
    ("Swerve", "Cue sports", "The curve of a cue ball hit with side spin and an elevated cue, from friction with the cloth. Small on a level cue, large in a massé; it partly cancels squirt at some speed, and only that speed.", "massé"),
    ("Stun", "Cue sports", "A cue ball arriving with no spin — hit slightly below centre so it is still sliding at contact. It stops dead on a straight shot and holds the tangent line on a cut.", "stun shot, stunned"),
    ("Topspin", "Cue sports", "Forward spin from a tip above centre. It survives the collision and bends the cue ball forward off the tangent line as it takes up roll — the follow shot, and the thirty-degree rule.", "follow shot"),
    ("Backspin", "Cue sports", "Reverse spin from a tip below centre. After the collision the cloth's friction turns it into a return: the cue ball comes back. Twice the speed pulls back four times as far.", "draw shot"),
    ("Miscue", "Cue sports", "The tip sliding off the ball instead of gripping it — beyond about half a radius of offset, or with no chalk. The ball goes almost nowhere and sometimes off the table.", "miscues"),
    ("Cushion", "Cue sports", "The rubber rail the ball rebounds from. It returns about three-quarters of the energy and drags on what runs along it, so the ball leaves shorter than it arrived — more so at speed, and side spin changes it either way.", "cushions"),
]


def main():
    ds = find_ds(TITLE)
    if not ds:
        db = call("POST", "https://api.notion.com/v1/databases", {
            "parent": {"type": "page_id", "page_id": PARENT_PAGE},
            "title": [{"type": "text", "text": {"content": TITLE}}],
            "initial_data_source": {"properties": {
                "Term": {"title": {}},
                "Domain": {"select": {"options": [{"name": d} for d in DOMAINS]}},
                "Definition": {"rich_text": {}},
                "Aliases": {"rich_text": {}},
            }},
        })
        ds = db["data_sources"][0]["id"]
        print("created", TITLE, ds)
    else:
        print(TITLE, "exists:", ds)
    schema = ensure_props(ds, {"Aliases": {"rich_text": {}}}, "glossary")
    ensure_select_options(ds, "Domain", DOMAINS, "glossary")
    sync_rows(ds, schema,
              [{"Term": t, "Domain": dom, "Definition": defn, "Aliases": al or None} for t, dom, defn, al in TERMS],
              "glossary", key="Term")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
