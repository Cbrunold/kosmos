"""Seed Machines [DB] and Skills [DB], plus the equations and inventors they link to.

The portal's other half: not how the world is, but how to make it do things.
Four tables in one script because they only make sense together —

  EQUATIONS   — the cycle efficiencies (Carnot, Otto, Diesel, Brayton), thermal
                efficiency and COP, the Lorentz force, the transformer equation,
                the Betz limit and the adiabatic relation: the mathematics the
                machines rest on, added to the Equations DB where missing.
  INVENTORS   — Newcomen, Watt, Stirling, Carnot, Otto, Diesel, Wankel, Parsons,
                Whittle, Tesla, Volta, Fermi… added to the Researchers DB where
                missing, so a machine's Inventors relation has someone to point at.
  MACHINES    — ~30 canonical machines: what it does, its cycle, typical efficiency
                and power density, what it is made of and why, where it is used,
                and links to inventors, elements and equations.
  SKILLS      — ~25 hands-on techniques: what it is, the science that makes it
                work, tools, steps, safety, how it fails, how you know it worked,
                and links to elements, equations and machines.

Cycle diagrams are not stored here — build.py draws them from the cycle name.

Efficiencies and years are textbook-typical and the prose says so. Idempotent:
backfills empty fields, unions relations, never overwrites.
Run on the VPS:  ./deploy.sh seed_engineering
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, query_all, sync_rows, title_of  # noqa: E402

MACHINES_DS = "f6c4e3cc-bfe0-4fb8-b807-3693cbcf4e88"
SKILLS_DS = "804e17aa-435b-4306-acbb-2ec926b87b10"
EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"
RESEARCHER_DS = "4cc8d7c4-9008-4017-a09b-7087720aebd3"
ELEMENTS_DS = "f01d2f3f-9698-4757-85f0-7cb7b2869dab"

# ------------------------------------------------------------------ equations
# name, equation, field, named after, symbols, significance, year
EQUATIONS = [
    ("Carnot Efficiency", "η_max = 1 − T_c/T_h", "Thermodynamics", "Sadi Carnot",
     "η_max the greatest possible efficiency of any heat engine · T_h temperature of the hot reservoir · T_c of the cold, both in kelvin",
     "The ceiling on every engine ever built, set in 1824 before anyone knew what heat was. Only the two temperatures matter — not the fluid, not the design. A car engine at 2,000 K exhausting to 300 K could at best reach 85 %; the second law, and metallurgy, keep it near a third of that.", 1824),
    ("Thermal Efficiency", "η = W_net/Q_in = 1 − Q_out/Q_in", "Thermodynamics", None,
     "η thermal efficiency · W_net net work out per cycle · Q_in heat taken from the hot source · Q_out heat rejected to the cold sink",
     "What you get for what you burn. Every real cycle's efficiency is this ratio; the Carnot value is what it would be if nothing were wasted. Rankine steam plants manage 33–45 %, combined-cycle gas plants over 60 %, and the difference between them is worth a great deal of fuel.", 1824),
    ("Otto Cycle Efficiency", "η = 1 − r^(1−γ)", "Thermodynamics", "Nikolaus Otto",
     "r compression ratio V_max/V_min · γ ratio of specific heats, about 1.4 for air",
     "The ideal efficiency of a spark-ignition engine depends on the compression ratio alone: r = 9 gives 58 % in theory. Real engines get about half that after friction, heat loss and incomplete combustion. Raise r and the fuel knocks — which is why octane rating exists, and why diesel, immune to knock, can go higher.", 1876),
    ("Diesel Cycle Efficiency", "η = 1 − (1/r^(γ−1)) · (α^γ − 1)/(γ(α − 1))", "Thermodynamics", "Rudolf Diesel",
     "r compression ratio · α cut-off ratio, the volume expansion during fuel injection · γ ratio of specific heats",
     "Heat is added at constant pressure while fuel sprays in, not at constant volume; for the same compression ratio that costs efficiency, but compression ignition allows r of 15–22 where petrol knocks at 10, so the diesel wins in the end — which is why lorries, ships and generators use it.", 1893),
    ("Brayton Cycle Efficiency", "η = 1 − (p_1/p_2)^((γ−1)/γ)", "Thermodynamics", "George Brayton",
     "p_2/p_1 the pressure ratio across the compressor · γ ratio of specific heats",
     "The gas-turbine cycle: efficiency rises with pressure ratio, so jet engines have gone from 5:1 to over 50:1 in eighty years. The catch is that a higher ratio means a hotter turbine inlet, and the whole history of the jet engine is the history of alloys and cooling that survive that temperature.", 1872),
    ("Coefficient of Performance", "COP_heating = Q_h/W ≤ T_h/(T_h − T_c)", "Thermodynamics", None,
     "COP heat delivered per unit of work · Q_h heat moved to the warm side · W work in · T_h, T_c the two temperatures in kelvin",
     "A heat pump is a heat engine run backwards, and its figure of merit can exceed 1 without breaking anything: a COP of 4 means four joules of heat moved for one joule of electricity. The Carnot limit shows why it works best when the two temperatures are close — and why heat pumps struggle in the deep cold.", 1834),
    ("Zener–Hollomon Parameter", "Z = ε̇·exp(Q/RT)", "Materials Science", "Clarence Zener and John Hollomon",
     "Z the temperature-compensated strain rate · ε̇ the strain rate · Q the activation energy for hot deformation, about 300 kJ/mol in austenite · R the gas constant · T absolute temperature",
     "Hot metal does not respond to temperature and speed separately, only to this combination of them: deforming ten times faster is worth about 130 °C of cooling. It sets the flow stress in every forging, rolling mill and extrusion press, decides whether the grains recrystallise while they are being deformed or only afterwards, and is why a slow press reaches the centre of a billet where a fast hammer moves only its skin.", 1944),
    ("Hall–Petch Relationship", "σ_y = σ_0 + k_y·d^(−1/2)", "Materials Science", "E. O. Hall and N. J. Petch",
     "σ_y the yield stress · σ_0 the friction stress a dislocation feels in the lattice alone · k_y a constant of the material · d the mean grain diameter",
     "Grain boundaries stop dislocations, so finer grain is stronger — by the inverse square root, so halving the grain size raises the boundary's share of the yield stress by 40 %. It is the one strengthening mechanism that raises toughness alongside strength instead of trading one for the other, which is why steel is normalised after forging, why niobium and vanadium earn their price in structural plate, and why an overheated part is a weak one. It reverses below about 20 nm, where the boundaries begin to slide instead of blocking.", 1951),
    ("Adiabatic Relation", "p V^γ = constant", "Thermodynamics", "Siméon Denis Poisson",
     "p pressure · V volume · γ = c_p/c_v ratio of specific heats, 1.4 for diatomic gases",
     "How a gas behaves when compressed or expanded too fast to exchange heat — the compression and power strokes of every piston engine, and the compressor and turbine of every jet. It is the curve the cycle diagrams on this site are drawn with, and the reason a bicycle pump gets hot.", 1823),
    ("Lorentz Force", "F = q(E + v × B)", "Electromagnetism", "Hendrik Lorentz",
     "F force on the charge · q charge · E electric field · v velocity · B magnetic field",
     "The force that turns every electric motor: current in a wire is moving charge, a magnetic field pushes it sideways, and a loop of it in a field turns. Run in reverse — move the wire — and the same force pushes charge along it, which is the generator. One equation, both directions.", 1895),
    ("Transformer Equation", "V_s/V_p = N_s/N_p", "Electromagnetism", None,
     "V_p, V_s primary and secondary voltage · N_p, N_s turns on each winding",
     "Two coils on one iron core, and the voltage steps by the ratio of their turns — with almost nothing lost, which is why alternating current won: step up to hundreds of kilovolts, send it across a country with small losses, step down at the other end. Faraday's law made practical.", 1885),
    ("Betz Limit", "C_p,max = 16/27 ≈ 0.593", "Fluid Dynamics", "Albert Betz",
     "C_p power coefficient: the fraction of the wind's kinetic energy a turbine extracts",
     "No turbine can take more than 59.3 % of the energy in the wind passing through it, because air that has given up all its energy would stop and block the rotor. Good modern turbines reach 45–50 %, close to the ceiling — the improvements now are in size and reliability, not the physics.", 1919),
]

# ------------------------------------------------------------------ inventors
# name, lifespan, nationality, field, known for
INVENTORS = [
    ("Thomas Newcomen", "1664–1729", "English", "Engineering",
     "The atmospheric engine of 1712, the first practical machine to turn heat into work — used to pump water out of mines for sixty years before Watt improved it."),
    ("James Watt", "1736–1819", "Scottish", "Engineering",
     "The separate condenser, which made the steam engine efficient enough to run a factory rather than just a pump; the unit of power is his."),
    ("Robert Stirling", "1790–1878", "Scottish", "Engineering",
     "A minister who patented the closed-cycle hot-air engine with a regenerator in 1816 — the most thermodynamically elegant engine ever devised, and one of the least used."),
    ("Sadi Carnot", "1796–1832", "French", "Thermodynamics",
     "Worked out the maximum efficiency of any heat engine in 1824, from the two temperatures alone, before the nature of heat was understood; died of cholera at 36."),
    ("Nikolaus Otto", "1832–1891", "German", "Engineering",
     "The four-stroke internal combustion engine of 1876 — intake, compression, power, exhaust — which is still the cycle in most of the cars on the road."),
    ("Rudolf Diesel", "1858–1913", "German", "Engineering",
     "The compression-ignition engine, designed from Carnot's theory rather than by trial; disappeared from a Channel steamer in 1913."),
    ("Felix Wankel", "1902–1988", "German", "Engineering",
     "The rotary engine with a triangular rotor: no reciprocating parts, very smooth, and a lifelong fight with its seals."),
    ("George Brayton", "1830–1892", "American", "Engineering",
     "The constant-pressure combustion cycle of 1872, built as a piston engine and now the cycle of every jet and gas turbine."),
    ("Charles Parsons", "1854–1931", "British", "Engineering",
     "The multi-stage reaction steam turbine of 1884, which powers most of the world's electricity generation and, after his Turbinia gate-crashed a naval review in 1897, most of its ships."),
    ("Frank Whittle", "1907–1996", "British", "Engineering",
     "Patented the turbojet in 1930 as an RAF cadet, was told it was impractical, and ran one in 1937."),
    ("Hans von Ohain", "1911–1998", "German", "Engineering",
     "Built the jet engine that flew first, in the Heinkel He 178 in August 1939 — independently of Whittle and unaware of him."),
    ("Nikola Tesla", "1856–1943", "Serbian-American", "Electrical Engineering",
     "The polyphase induction motor and the AC system that carries it — the machine most of the world's electricity is used by."),
    ("Galileo Ferraris", "1847–1897", "Italian", "Electrical Engineering",
     "Discovered the rotating magnetic field independently of Tesla in 1885 and published first; refused to patent it."),
    ("Zénobe Gramme", "1826–1901", "Belgian", "Electrical Engineering",
     "The first dynamo that produced smooth direct current at useful power, in 1871 — and, discovered by accident at a Vienna exhibition, ran as a motor when fed current."),
    ("Werner von Siemens", "1816–1892", "German", "Electrical Engineering",
     "The self-excited dynamo of 1866, which removed the permanent magnet and made large generators possible; the company still carries his name."),
    ("William Stanley", "1858–1916", "American", "Electrical Engineering",
     "Built the first practical transformer and demonstrated AC distribution to a town in 1886, on Westinghouse's money."),
    ("Alessandro Volta", "1745–1827", "Italian", "Physics",
     "The voltaic pile of 1800: zinc, copper and brine in a stack, and the first source of continuous electric current. The volt is his."),
    ("Gaston Planté", "1834–1889", "French", "Physics",
     "The lead–acid battery of 1859, the first that could be recharged; it still starts almost every car."),
    ("William Grove", "1811–1896", "Welsh", "Physics",
     "The fuel cell of 1839 — hydrogen and oxygen recombining over platinum to make electricity and water — a century and a half before anyone wanted one."),
    ("M. Stanley Whittingham", "1941–", "British-American", "Chemistry",
     "The first lithium intercalation battery, at Exxon in the 1970s; shared the 2019 Nobel with Goodenough and Yoshino."),
    ("John Goodenough", "1922–2023", "American", "Chemistry",
     "The lithium cobalt oxide cathode of 1980, which doubled the voltage and made the lithium-ion cell practical; the oldest Nobel laureate at 97."),
    ("Akira Yoshino", "1948–", "Japanese", "Chemistry",
     "The carbon anode that made lithium-ion safe enough to sell, in 1985; Sony shipped it in 1991."),
    ("Enrico Fermi", "1901–1954", "Italian-American", "Physics",
     "Chicago Pile-1, the first self-sustaining nuclear chain reaction, under a squash court on 2 December 1942."),
    ("Hyman Rickover", "1900–1986", "American", "Engineering",
     "The pressurized-water reactor, built first for the submarine Nautilus in 1954 and then at Shippingport for the grid; the design most of the world's reactors follow."),
    ("Jacob Perkins", "1766–1849", "American", "Engineering",
     "Patented the vapour-compression refrigeration cycle in 1834 — the cycle in every fridge and heat pump — and built one, though nobody bought it."),
    ("Carl von Linde", "1842–1934", "German", "Engineering",
     "Turned refrigeration into an industry in the 1870s, and in 1895 liquefied air — the start of the gases business."),
    ("Lester Pelton", "1829–1908", "American", "Engineering",
     "The split-bucket impulse wheel of 1878, from watching a misaligned water wheel run faster; still the turbine for high-head hydro."),
    ("James B. Francis", "1815–1892", "British-American", "Engineering",
     "The inward-flow reaction turbine of 1849, now the most widely used hydro turbine in the world."),
    ("Viktor Kaplan", "1876–1934", "Austrian", "Engineering",
     "The propeller turbine with adjustable blades, for low heads and big rivers, in 1913."),
    ("Albert Betz", "1885–1968", "German", "Fluid Dynamics",
     "Showed in 1919 that no wind turbine can take more than 59.3 % of the wind's energy — the ceiling every turbine is measured against."),
    ("Robert Goddard", "1882–1945", "American", "Engineering",
     "Flew the first liquid-fuelled rocket, on 16 March 1926, from his aunt's farm; the New York Times mocked him for thinking a rocket could work in vacuum, and apologised in 1969."),
    ("Wernher von Braun", "1912–1977", "German-American", "Engineering",
     "The V-2, built at Mittelwerk by concentration-camp labour under his technical direction, and then the Saturn V that took Apollo to the Moon. Both are his."),
]

# ------------------------------------------------------------------ machines
# name, kind, cycle, year, inventors, how, efficiency, power density, materials, used in, elements, equations
MACHINES = [
    ("Newcomen Atmospheric Engine", "Heat engine", "None", 1712, ["Thomas Newcomen"],
     "Steam at barely above atmospheric pressure fills a cylinder under a piston; a jet of cold water condenses it, the pressure inside collapses, and the weight of the atmosphere pushes the piston down. A rocking beam turns that into a pump stroke. The steam does no pushing at all — the air does.",
     "Under 1 %. Every stroke reheated a cylinder that had just been chilled.", "Very low: a house-sized engine for a few horsepower.",
     "A cast-iron cylinder bored by hand, a wooden beam, brass fittings, and a boiler that was really a large kettle.",
     "Pumping water out of tin and coal mines, which was the only job worth that much coal.",
     ["Fe", "Cu"], ["First Law of Thermodynamics", "Ideal Gas Law"]),
    ("Watt Steam Engine", "Heat engine", "Rankine", 1776, ["James Watt"],
     "Watt's insight was to condense the steam in a separate vessel kept cold, so the cylinder could stay hot; then he closed the top of the cylinder and used steam pressure on both sides, added a crank to make rotary motion, and a centrifugal governor to hold speed. That combination is the machine that ran the Industrial Revolution.",
     "3–5 % — three to four times Newcomen's, which is why it displaced him.", "Low, but enough to turn a mill.",
     "Cast iron, wrought iron, brass; the cylinder bored on Wilkinson's cannon-boring machine, the first machine tool accurate enough for the job.",
     "Mills, mines, breweries — anything that had turned on water or horses.",
     ["Fe", "Cu"], ["First Law of Thermodynamics", "Second Law of Thermodynamics", "Ideal Gas Law", "Thermal Efficiency"]),
    ("Stirling Engine", "Heat engine", "Stirling", 1816, ["Robert Stirling"],
     "A fixed charge of gas is shuttled between a hot end and a cold end by a displacer, expanding when hot and contracting when cold to drive a power piston. A regenerator — a wad of wire mesh — stores heat on the way to the cold side and gives it back on the return, which is what lets the ideal cycle match Carnot.",
     "Up to 40 % in modern engines; the ideal cycle equals Carnot's limit.", "Low: sealed, slow to respond, and heavy for its output.",
     "Stainless steel and Inconel hot ends, aluminium cold ends, helium or hydrogen as the working gas.",
     "Solar dishes, submarine air-independent propulsion, and, run backwards, cryocoolers.",
     ["He", "H", "Fe", "Ni"], ["Carnot Efficiency", "Ideal Gas Law", "Adiabatic Relation"]),
    ("Otto Four-Stroke Engine", "Heat engine", "Otto", 1876, ["Nikolaus Otto"],
     "Intake draws in air and fuel; compression squeezes it to a ninth of its volume; a spark ignites it and the pressure drives the piston down; exhaust pushes the burnt gas out. Two revolutions per power stroke, and a flywheel to carry the engine through the other three.",
     "25–35 % at best load; the ideal Otto cycle at r = 9 promises 58 %.", "About 50–100 kW per litre of displacement in a modern car.",
     "Cast iron or aluminium block, forged steel crankshaft, aluminium pistons, platinum and rhodium in the catalytic converter.",
     "Cars, motorcycles, generators, lawnmowers — most of the engines on Earth.",
     ["Fe", "Al", "Pt", "Rh"], ["Otto Cycle Efficiency", "Adiabatic Relation", "Ideal Gas Law", "Thermal Efficiency"]),
    ("Diesel Engine", "Heat engine", "Diesel", 1893, ["Rudolf Diesel"],
     "Air alone is compressed, hard enough — 15 to 22 times — that it reaches 700 °C. Fuel is then injected and ignites on contact, burning as it sprays rather than all at once. No spark, no throttle, and no knock, so the compression ratio can go where petrol cannot.",
     "40–45 % in trucks; the largest marine two-strokes exceed 50 %, the best of any piston engine.", "Lower revs, heavier build, more torque.",
     "Heavy cast-iron blocks, forged steel, injectors machined to micron tolerances at 2,000 bar.",
     "Lorries, ships, locomotives, tractors, standby generators.",
     ["Fe", "Al"], ["Diesel Cycle Efficiency", "Adiabatic Relation", "Thermal Efficiency"]),
    ("Wankel Rotary Engine", "Heat engine", "Otto", 1957, ["Felix Wankel"],
     "A triangular rotor orbits inside a peanut-shaped housing; the three chambers between them expand and contract as it turns, doing intake, compression, power and exhaust in sequence with no valves and no reciprocating parts.",
     "Around 20 %: the long, thin combustion chamber loses heat and burns badly.", "Very high — small, light and smooth for its power.",
     "Aluminium housings, cast-iron rotors, and apex seals that were the problem for fifty years.",
     "Mazda sports cars, drones, and range extenders.",
     ["Al", "Fe"], ["Otto Cycle Efficiency", "Adiabatic Relation"]),
    ("Steam Turbine", "Turbine", "Rankine", 1884, ["Charles Parsons"],
     "High-pressure steam expands through row after row of blades, each stage taking a little of the pressure drop and turning it into rotation, so the steam speed never gets destructively high. Boiler, turbine, condenser, pump — the Rankine cycle, at up to 3,000 rpm and hundreds of megawatts.",
     "33–45 % for the whole plant, depending on how hot and how high-pressure the steam is.", "Enormous: a single machine can exceed a gigawatt.",
     "Chromium-molybdenum steel rotors, nickel-alloy blades in the hot stages, titanium in the last, condensers of copper-nickel or titanium tube.",
     "Coal, gas, nuclear and geothermal power stations, and warships.",
     ["Fe", "Cr", "Ni", "Ti"], ["Thermal Efficiency", "Carnot Efficiency", "Bernoulli's Equation", "Second Law of Thermodynamics"]),
    ("Gas Turbine (Jet Engine)", "Turbine", "Brayton", 1937, ["Frank Whittle", "Hans von Ohain"],
     "A compressor squeezes air to thirty or fifty times atmospheric, fuel burns in it continuously, and the hot gas spins a turbine that drives the compressor before leaving as thrust — or, in a turbofan, driving a big fan that moves most of the air around the core. In a power station the exhaust boils water for a steam turbine instead.",
     "35–40 % alone; over 60 % in combined cycle with a steam turbine — the most efficient heat engine there is.", "The highest of any engine: a jet engine makes tens of megawatts from a tonne of metal.",
     "Titanium fans and compressors, single-crystal nickel superalloys with rhenium in the turbine, ceramic thermal-barrier coatings, and blades cooled from inside because the gas is hotter than their melting point.",
     "Airliners, fighters, helicopters, ships, and peaking and combined-cycle power plants.",
     ["Ni", "Ti", "Re", "Cr", "Co", "Al"], ["Brayton Cycle Efficiency", "Adiabatic Relation", "Thermal Efficiency", "Bernoulli's Equation"]),
    ("Pelton Wheel", "Turbine", "None", 1878, ["Lester Pelton"],
     "A high-pressure jet of water hits a ring of double buckets, splits, and leaves sideways at almost no speed — which means almost all its kinetic energy went into the wheel. An impulse turbine: the pressure is converted to velocity in the nozzle, and the wheel runs at atmospheric pressure.",
     "Over 90 %.", "High for hydro; small wheels for very high heads.",
     "Cast or forged stainless steel buckets, resistant to the sand in mountain water.",
     "Alpine and Andean hydro with heads of hundreds of metres.",
     ["Fe", "Cr"], ["Bernoulli's Equation", "Newton's Second Law"]),
    ("Francis Turbine", "Turbine", "None", 1849, ["James B. Francis"],
     "Water enters a spiral casing, is turned inward by guide vanes and flows through the runner radially in and axially out, dropping in pressure as it goes. A reaction turbine, running full of water under pressure — the opposite of a Pelton wheel.",
     "90–95 %.", "The bulk of the world's hydro capacity.",
     "Stainless-steel runners, often over 8 m across; concrete spiral casings.",
     "Most large dams, from Hoover to Itaipu to the Three Gorges.",
     ["Fe", "Cr"], ["Bernoulli's Equation", "Continuity Equation"]),
    ("Kaplan Turbine", "Turbine", "None", 1913, ["Viktor Kaplan"],
     "A propeller in a pipe, with blades whose pitch adjusts to the flow — so it stays efficient across a wide range of river conditions. For low heads and huge volumes.",
     "Over 90 % across a wide load range.", "Suited to big, slow rivers.",
     "Stainless steel blades on an oil-filled hub with the pitch mechanism inside.",
     "Run-of-river plants on the Danube, Rhine and Columbia.",
     ["Fe", "Cr"], ["Bernoulli's Equation", "Continuity Equation"]),
    ("Wind Turbine", "Turbine", "None", 1887, ["Albert Betz"],
     "Three blades, shaped like aircraft wings, generate lift from the wind and turn a shaft; a gearbox or a direct-drive generator turns that into electricity. The tower puts the rotor where the wind is faster and steadier, and the whole nacelle yaws to face it.",
     "45–50 % of the wind's energy — against a hard ceiling of 59.3 %.", "Low per unit of swept area, which is why they are enormous: rotors now exceed 200 m.",
     "Glass- and carbon-fibre blades, steel towers, neodymium magnets in direct-drive generators, several tonnes of copper.",
     "About a tenth of the world's electricity, and rising.",
     ["Nd", "Dy", "Cu", "Fe"], ["Betz Limit", "Bernoulli's Equation", "Faraday's Law of Induction"]),
    ("Brushed DC Motor", "Electric machine", "None", 1871, ["Zénobe Gramme", "Michael Faraday"],
     "Current through a coil in a magnetic field feels a sideways force and turns; a commutator — segments the brushes slide over — reverses the current every half turn so the push always goes the same way. Simple, cheap, and easy to control by voltage.",
     "70–85 %; brushes wear and spark.", "Moderate.",
     "Copper windings, iron laminations, ferrite or neodymium magnets, carbon brushes.",
     "Toys, power tools, car windows and wipers, anywhere cheap and small.",
     ["Cu", "Fe", "C", "Nd"], ["Lorentz Force", "Faraday's Law of Induction", "Ampère–Maxwell Law", "Ohm's Law"]),
    ("Induction Motor", "Electric machine", "None", 1887, ["Nikola Tesla", "Galileo Ferraris"],
     "Three-phase current in the stator makes a magnetic field that rotates on its own; it induces current in a cage of copper or aluminium bars on the rotor, and the two fields drag the rotor round just slower than the field. No brushes, no magnets, nothing to wear but bearings.",
     "85–96 %.", "Moderate; the workhorse rather than the racehorse.",
     "Silicon-steel laminations, copper stator windings, cast-aluminium rotor cage.",
     "Pumps, fans, compressors, conveyors, machine tools — around 45 % of all electricity generated is used by electric motors, most of them this one.",
     ["Cu", "Al", "Fe", "Si"], ["Faraday's Law of Induction", "Lorentz Force", "Ampère–Maxwell Law"]),
    ("Brushless Permanent-Magnet Motor", "Electric machine", "None", 1962, [],
     "Permanent magnets on the rotor, electromagnets in the stator, and an electronic controller that switches the coils in sequence as the rotor turns — the commutator's job done by transistors and a position sensor. Rare-earth magnets made it powerful; cheap electronics made it universal.",
     "90–97 %.", "The highest of any motor: kilowatts from something you can hold.",
     "Neodymium–iron–boron magnets with dysprosium for heat, copper windings, silicon-steel laminations.",
     "Electric cars, drones, e-bikes, hard drives, cordless tools.",
     ["Nd", "Dy", "Fe", "B", "Cu"], ["Lorentz Force", "Faraday's Law of Induction"]),
    ("Alternator", "Electric machine", "None", 1866, ["Werner von Siemens", "Michael Faraday"],
     "A magnet — or an electromagnet — spins inside coils, and the changing field induces an alternating voltage in them. Every power station on Earth ends in one, driven by a steam, gas, water or wind turbine; the one under a car's bonnet is the same machine in miniature.",
     "95–99 % for large machines.", "A single generator can exceed a gigawatt.",
     "Copper windings, silicon-steel cores, hydrogen cooling in the large ones because it carries heat away better than air.",
     "Every grid; every car.",
     ["Cu", "Fe", "Si", "H"], ["Faraday's Law of Induction", "Lorentz Force"]),
    ("Transformer", "Electric machine", "None", 1885, ["William Stanley"],
     "Two coils on a common iron core. Alternating current in one makes an alternating field in the core, which induces voltage in the other in proportion to the turns. No moving parts, and so efficient that stepping voltage up for transmission and down for use costs almost nothing — the reason the grid runs on AC.",
     "98–99.7 %.", "Not a prime mover; the largest weigh hundreds of tonnes.",
     "Grain-oriented silicon-steel laminations to cut eddy currents, copper or aluminium windings, mineral oil for cooling and insulation.",
     "Every substation, every pole, every phone charger.",
     ["Fe", "Si", "Cu", "Al"], ["Transformer Equation", "Faraday's Law of Induction"]),
    ("Voltaic Pile", "Power source", "None", 1800, ["Alessandro Volta"],
     "Discs of zinc and copper separated by brine-soaked cloth, stacked. Zinc dissolves and gives up electrons; they flow through the wire to the copper, where hydrogen forms. The first steady electric current — before it, electricity meant a spark from a jar.",
     "Poor, and it polarised within minutes.", "Tiny.",
     "Zinc, copper, cardboard, salt water.",
     "Davy used it to isolate sodium and potassium; every battery since is its descendant.",
     ["Zn", "Cu", "Na", "Cl"], ["Nernst Equation", "Ohm's Law"]),
    ("Lead–Acid Battery", "Power source", "None", 1859, ["Gaston Planté"],
     "Lead and lead dioxide plates in sulfuric acid; both turn to lead sulfate as it discharges and back again on charging. Heavy and old, but cheap, rugged, and able to deliver the hundreds of amps a starter motor wants.",
     "80–90 % round-trip.", "30–40 Wh/kg — a tenth of lithium-ion.",
     "Lead, lead dioxide, sulfuric acid, polypropylene case; the most recycled product in the world by mass.",
     "Starting cars, backup power, forklifts.",
     ["Pb", "S", "O", "H"], ["Nernst Equation", "Ohm's Law"]),
    ("Lithium-Ion Cell", "Power source", "None", 1991, ["M. Stanley Whittingham", "John Goodenough", "Akira Yoshino"],
     "Lithium ions shuttle between a graphite anode and a metal-oxide cathode through an electrolyte, slotting into the crystal lattices without breaking them — intercalation. Nothing is plated or dissolved, so it can do it thousands of times. Three volts and more per cell, and light.",
     "90–95 % round-trip.", "150–300 Wh/kg, the reason phones and electric cars exist.",
     "Graphite, lithium cobalt/nickel/manganese oxide or lithium iron phosphate, copper and aluminium foils, a polymer separator, an organic electrolyte that burns.",
     "Phones, laptops, electric vehicles, grid storage.",
     ["Li", "Co", "Ni", "Mn", "C", "Cu", "Al"], ["Nernst Equation", "Ohm's Law"]),
    ("Fuel Cell", "Power source", "None", 1839, ["William Grove"],
     "Hydrogen is split into protons and electrons at a platinum catalyst; the protons cross a membrane, the electrons go round the outside as current, and they meet oxygen on the far side to make water. Combustion with the electricity taken out before the heat.",
     "50–60 %, not bound by the Carnot limit because it is not a heat engine.", "Moderate; the hydrogen tank is the problem.",
     "Platinum on carbon, a Nafion membrane, graphite or steel bipolar plates.",
     "Apollo and the Shuttle, buses, forklifts, some cars.",
     ["H", "O", "Pt", "C"], ["Nernst Equation", "Gibbs Free Energy"]),
    ("Photovoltaic Cell", "Power source", "None", 1954, [],
     "A photon knocks an electron loose in a silicon junction; the built-in field at the junction sweeps it one way, and a current flows with no moving parts, no fuel and no noise. Bell Labs' first cell was 6 %; the sunlight is free, so the cost of the cell is everything.",
     "20–24 % for commercial modules; the single-junction limit is about 33 %.", "About 200 W per square metre in full sun.",
     "Polysilicon grown from the purest quartz on Earth, silver contacts, glass, aluminium frames.",
     "Rooftops, deserts, satellites; the fastest-growing source of electricity.",
     ["Si", "Ag", "Al"], ["Planck–Einstein Relation", "Ohm's Law"]),
    ("Radioisotope Thermoelectric Generator", "Power source", "None", 1961, [],
     "A lump of plutonium-238 gets hot from its own decay; thermocouples across the temperature difference make a small steady current for decades. No moving parts, no sunlight needed — the power supply for wherever solar panels cannot go.",
     "5–7 %.", "A few watts per kilogram, falling as the plutonium decays.",
     "Plutonium-238 oxide, silicon-germanium or lead-telluride thermocouples, an iridium cladding.",
     "Voyager, Cassini, New Horizons, the Mars rovers.",
     ["Pu", "Si", "Ge", "Te", "Ir"], ["Seebeck Effect", "Thermoelectric Figure of Merit", "Radioactive Decay Law", "Half-Life"]),
    ("Chicago Pile-1", "Reactor", "None", 1942, ["Enrico Fermi"],
     "Uranium lumps in a lattice of graphite blocks, stacked by hand under a squash court. The graphite slowed neutrons enough for uranium-235 to capture them; cadmium rods soaked up neutrons to hold the reaction; on 2 December 1942 the rods were withdrawn and the chain reaction sustained itself for 28 minutes at half a watt.",
     "It made no useful power; it proved the reaction.", "Half a watt.",
     "45 tonnes of uranium, 360 tonnes of graphite, cadmium rods, and a man with an axe to cut a rope holding a safety rod.",
     "The proof that led to every reactor since.",
     ["U", "C", "Cd"], ["Mass–energy equivalence", "Half-Life", "Radioactive Decay Law"]),
    ("Pressurized Water Reactor", "Reactor", "Rankine", 1957, ["Hyman Rickover", "Enrico Fermi"],
     "Uranium fuel rods heat water held at 155 bar so it cannot boil; that water passes through a steam generator and boils a separate loop, which drives a steam turbine. Two loops, so the radioactive water never leaves the containment. Boron in the coolant and control rods regulate the reaction.",
     "33 % thermal to electric — a steam plant, limited by the steam temperature the fuel cladding allows.", "A gigawatt from a core the size of a room.",
     "Uranium dioxide pellets in zirconium-alloy cladding, a steel pressure vessel 20 cm thick, boron carbide control rods, a concrete containment.",
     "About two thirds of the world's reactors, and every nuclear submarine.",
     ["U", "Zr", "B", "H", "O"], ["Mass–energy equivalence", "Half-Life", "Thermal Efficiency", "Radioactive Decay Law"]),
    ("Vapour-Compression Refrigerator", "Heat pump", "Vapour-compression", 1834, ["Jacob Perkins", "Carl von Linde"],
     "A refrigerant boils at low pressure, taking heat from the cold side; a compressor squeezes the vapour, which condenses at high pressure and gives that heat up on the warm side; a valve drops the liquid's pressure and it boils again. Run it to warm the warm side and it is a heat pump — the same machine.",
     "A COP of 3–5: three to five joules moved per joule of electricity.", "Moderate.",
     "Copper tube, aluminium fins, a hermetic compressor, and a refrigerant chosen for its boiling point and its climate impact.",
     "Every fridge, freezer and air conditioner; increasingly, heating.",
     ["Cu", "Al", "F", "C"], ["Coefficient of Performance", "Carnot Efficiency", "Second Law of Thermodynamics"]),
    ("Liquid-Propellant Rocket Engine", "Rocket", "None", 1926, ["Robert Goddard", "Wernher von Braun"],
     "Fuel and oxidiser — kerosene, hydrogen or methane with liquid oxygen — are pumped into a chamber, burn at 3,000 K, and the gas expands through a bell nozzle to several kilometres a second. It carries its own oxygen, so it works in vacuum; it can be throttled and restarted; and its turbopumps are the most power-dense machines ever built.",
     "Around 60 % of the chemical energy becomes jet kinetic energy; what matters is specific impulse — 300 to 450 seconds.", "The highest of anything: an F-1 engine made about 1.5 gigawatts of jet power.",
     "Copper-alloy chamber liners cooled by the fuel running through channels, nickel superalloys, niobium nozzle extensions, and welds that must not fail.",
     "Every orbital launch, and every landing.",
     ["H", "O", "Cu", "Nb", "Ni"], ["Tsiolkovsky Rocket Equation", "Specific Impulse", "Newton's Second Law", "Bernoulli's Equation"]),
    ("Solid-Propellant Rocket Motor", "Rocket", "None", 1942, [],
     "Fuel and oxidiser mixed into a rubbery grain, cast into the casing with a shaped hollow down the middle. Light it and it burns from the inside out until it is gone — no pumps, no valves, no way to stop it. Simple, storable for years, and enormous thrust.",
     "Specific impulse around 250–290 seconds, below liquids.", "Very high thrust; low efficiency.",
     "Ammonium perchlorate, aluminium powder and a polymer binder; a steel or carbon-fibre casing; a graphite or carbon-carbon nozzle throat.",
     "Shuttle and SLS boosters, missiles, ejection seats, model rockets.",
     ["Al", "N", "Cl", "O", "C"], ["Tsiolkovsky Rocket Equation", "Specific Impulse", "Newton's Second Law"]),
]

# ------------------------------------------------------------------ skills
# name, category, difficulty, summary, science, tools, steps, safety, fails, done, elements, equations, machines
SKILLS = [
    ("Soldering", "Joining", "Beginner",
     "Joining electrical parts with a low-melting tin alloy that wets copper and freezes into a conductive, mechanically weak joint.",
     "The iron heats the joint, not the solder: when copper reaches about 250 °C, molten tin dissolves a whisker of it and forms an intermetallic layer — a metallurgical bond, not glue. Flux strips the oxide off first so the tin can wet the metal; without it the solder balls up. Heat conducts through the joint by Fourier's law, which is why a big ground plane needs a hotter, bigger tip.",
     "Temperature-controlled iron (330–370 °C for lead-free), 0.5–0.8 mm rosin-core solder, flux pen, brass tip cleaner, tweezers, extractor fan.",
     "Tin the tip: melt a little solder on it and wipe.\nTouch the tip to both the pad and the lead at once — heat the joint, never the solder.\nAfter a second, feed solder into the far side of the joint; it should flow toward the heat.\nRemove the solder, then the iron; hold still until it dulls and sets.\nInspect: a shiny concave fillet climbing both surfaces.\nClip the lead above the fillet.",
     "Fumes are flux, not lead, but ventilate anyway. Lead solder: wash hands, no food at the bench. The iron is 350 °C and looks the same cold.",
     "A cold joint — grey, lumpy, a ball sitting on the pad — from heating the solder instead of the joint, or from movement while it froze. A bridge between neighbouring pads from too much solder. A lifted pad from too much heat for too long.",
     "The joint is bright, smooth and concave, wets both parts, and a gentle tug on the lead moves nothing.",
     ["Sn", "Cu", "Ag", "Pb"], ["Joule Heating", "Fourier's Law of Heat Conduction", "Ohm's Law"], ["Photovoltaic Cell"]),
    ("Brazing", "Joining", "Intermediate",
     "Joining metals with a filler that melts above 450 °C but below the parts — brass or silver alloy drawn into a tight gap by capillary action.",
     "The filler is pulled into a gap of a tenth of a millimetre by surface tension, and diffuses a little into both surfaces, giving a joint far stronger than solder — often stronger than the filler alloy itself, because the thin film is constrained. Flux dissolves oxide and keeps air off while the joint is red-hot.",
     "Oxy-acetylene, MAPP or propane torch; silver-brazing rod or brass rod; borax-based flux; wire brush; pickle (dilute acid) for cleanup.",
     "Fit the parts to a 0.05–0.15 mm gap; too tight and the filler cannot enter, too loose and capillarity fails.\nClean to bright metal and flux both surfaces.\nHeat the whole joint evenly to a dull red — heat the parts, not the rod.\nTouch the rod to the joint; if the parts are hot enough it melts and runs in on its own.\nFollow the joint round with the torch; the filler follows the heat.\nCool slowly, then pickle or scrub off the glassy flux.",
     "Eye protection against the flame and the flux glare. Ventilate — cadmium-bearing silver solder is toxic when hot; use cadmium-free. Hot metal looks cold within a minute.",
     "Filler that balls up and will not run: parts too cold or dirty. Filler that runs everywhere but the joint: overheated. A joint that cracks: gap too wide, or brass filler on steel that was quenched.",
     "A full, smooth fillet all round with filler visible on the far side of the joint — proof it went through.",
     ["Cu", "Zn", "Ag", "P"], ["Fourier's Law of Heat Conduction"], []),
    ("MIG Welding", "Joining", "Intermediate",
     "Fusing steel with an electric arc from a continuously fed wire, shielded by argon–CO₂ gas — the easiest process to start and the hardest to do well.",
     "The arc is a plasma at around 6,000 K carrying 100–200 A; it melts the wire and a puddle in the parent metal, which freeze together as one piece. Ohm's law and Joule heating in the arc column set the heat; the shielding gas keeps oxygen and nitrogen out of the molten pool, which would otherwise make it porous and brittle. Wire feed speed sets current; voltage sets arc length.",
     "MIG welder with gas, 0.8 mm ER70S-6 wire, 75/25 argon–CO₂, auto-darkening helmet, leather gloves and jacket, angle grinder, clamps.",
     "Grind the joint to bright metal and clamp it; earth clamp on clean metal.\nSet wire speed and voltage from the chart for the thickness, then fine-tune by sound — a steady sizzle like frying bacon.\nHold the gun at 10–15° push, 10 mm stick-out.\nStrike, let the puddle form, then travel at a speed that keeps the puddle a consistent oval.\nWeave slightly on thicker stock; straight on thin.\nStop, chip and brush; inspect the back for penetration.",
     "Arc eye is a UV burn — helmet down before you strike, and warn people nearby. Fumes: ventilate, never weld galvanised without extraction. Sparks travel metres; clear the area of anything flammable. The workpiece is hot for a long time.",
     "Porosity (holes) from wind, dirty metal or too little gas. Lack of fusion — a bead sitting on top — from too little heat or moving too fast. Burn-through on thin metal from too much. Spatter everywhere from voltage too high or a long stick-out.",
     "A bead of even width and ripple, no undercut at the edges, penetration visible on the back, and it survives a bend test without cracking.",
     ["Fe", "Ar", "C", "O", "Mn", "Si"], ["Joule Heating", "Ohm's Law", "Fourier's Law of Heat Conduction"], []),
    ("TIG Welding", "Joining", "Advanced",
     "The precise process: an arc from a non-consumable tungsten electrode under pure argon, filler fed by hand — for stainless, aluminium, titanium, and anything that has to look right.",
     "Tungsten survives the arc because it melts at 3,400 °C. Argon shields the pool completely, so reactive metals like titanium and aluminium can be welded at all — aluminium needs AC, because the reverse half-cycle blasts off its oxide skin, which melts 1,500 °C hotter than the metal under it. Heat input is controlled independently of filler, which is what makes it precise.",
     "TIG machine with high-frequency start and AC for aluminium, 2 % lanthanated tungsten, pure argon, filler rods, foot pedal, gas lens, helmet, thin gloves.",
     "Grind the tungsten to a point along its length, never across.\nClean the joint and the filler with acetone; aluminium with a dedicated stainless brush.\nSet amps roughly one per thousandth of an inch of thickness; use the pedal to trim.\nStrike, form a puddle, then dab filler into the leading edge — never into the arc.\nMove, dab, move, dab: consistent rhythm makes the stacked-dime bead.\nEase off the pedal at the end and keep the gas on for post-flow so the hot metal is covered.",
     "As MIG, plus: tungsten dust from grinding is best not breathed; thoriated tungsten is mildly radioactive — use lanthanated. HF start can upset pacemakers.",
     "Grey, sooty welds: gas coverage lost. A tungsten inclusion when the electrode touches the pool. Cracked aluminium from wrong filler or a rushed cool. Sugared stainless on the back from no back-purge.",
     "A uniform bead of overlapping crescents, silver or straw-coloured on stainless, with no discolouration beyond light gold — the colour is a thermometer.",
     ["W", "Ar", "Ti", "Al", "Fe", "Cr", "La"], ["Joule Heating", "Fourier's Law of Heat Conduction", "Ohm's Law"], ["Gas Turbine (Jet Engine)"]),
    ("Stick Welding", "Joining", "Intermediate",
     "Arc welding with a flux-coated rod that is consumed as it burns: no gas bottle, works outdoors and on rusty steel, and fits in a bag.",
     "The flux coating burns off into a shielding gas and a slag that floats on the pool, protecting it as it cools — which is why wind does not matter. The rod is the electrode and the filler at once. Different coatings (6013, 7018) give different arcs and different steel; the numbers are tensile strength in ksi and position.",
     "Inverter stick welder, 2.5–3.2 mm 6013 rods (7018 for structural, kept dry), chipping hammer, wire brush, helmet, gloves.",
     "Set 90–110 A for 3.2 mm rod; earth on clean metal.\nStrike like a match — drag the tip along the joint, lift to 3 mm to hold the arc.\nKeep the arc short: rod length above the work about equal to its diameter.\nAngle 15–20° in the direction of travel, and travel so the slag stays behind the puddle.\nWhen the rod is short, stop; chip and brush the slag before the next pass.\nRestart on the crater with a slight back-step.",
     "As MIG. Slag chips fly — eye protection when chipping. 7018 rods that have absorbed moisture crack the weld from hydrogen.",
     "Rod sticking to the work: current too low or arc too long. Slag inclusions from welding over slag. Undercut from too much current. Porosity from damp rods.",
     "Slag lifts off in a curl by itself; underneath, an even bead with fine ripples and fused edges.",
     ["Fe", "Ca", "Si", "Mn"], ["Joule Heating", "Ohm's Law"], []),
    ("Heat Treating Steel", "Metalwork", "Advanced",
     "Changing a steel's hardness and toughness by heating and cooling on purpose — annealing to soften, quenching to harden, tempering to take the brittleness back out.",
     "Iron's crystal structure changes above about 730 °C, and dissolves carbon into it. Quench fast enough and the carbon is trapped in a distorted lattice — martensite, glass-hard and brittle. Temper at 150–350 °C and some of that strain relaxes: the trade of hardness for toughness, tuned by temperature and time along an Arrhenius curve. Cool slowly instead and the carbon comes out as soft pearlite — annealing.",
     "A forge, kiln or torch; a magnet; quench oil or water; an oven for tempering; a file to test hardness; a rag on a wire.",
     "Heat the steel evenly past the point where a magnet stops sticking — about 770 °C, a bright cherry red — and hold a minute per 5 mm.\nQuench: plunge point-first into warm oil (water for plain low-alloy, but it cracks more) and agitate.\nTest with a file: it should skate off without biting.\nClean to bright metal so you can see the colours.\nTemper in an oven at 200 °C for an hour (a knife), or watch the oxide colours run to straw or bronze with a torch.\nCool in air.",
     "Oil quench can flash — use a lidded metal tank and dry steel. Everything is hot for longer than you think. Never quench in a closed vessel.",
     "Cracks in the quench from a sharp corner, water on a steel that wanted oil, or waiting too long to temper. Soft spots from uneven heating or a slow quench. Warp from quenching a long blade flat.",
     "The file skates before tempering and just barely bites after; a light hammer tap rings rather than thuds; the edge takes and holds a shave.",
     ["Fe", "C", "Cr", "Mn"], ["Arrhenius Equation", "Fourier's Law of Heat Conduction", "Newton's Law of Cooling"], ["Diesel Engine"]),
    ("Forging", "Metalwork", "Intermediate",
     "Moving hot steel with a hammer — drawing out, upsetting, bending, punching, spreading — inside the window where it flows freely: above the temperature at which it cracks, below the one at which it is ruined.",
     "Hot working is not about softness, it is about recrystallisation. Above roughly 0.4 of iron's melting point in kelvin, new strain-free grains nucleate as fast as the hammer distorts the old ones, so the steel never work-hardens and can be moved as far as you like; the stress needed to move it falls by an order of magnitude between cold and 1,200 °C. The floor is not the recrystallisation temperature but the A₃ line — 912 °C at zero carbon, falling to 727 °C at 0.77 % — below which ferrite appears beside austenite and the two shear apart. The ceiling is set three times over: austenite grain coarsens above about 1,050 °C; sulfur-bearing steel goes hot-short at the 988 °C Fe–FeS eutectic; and near 1,350 °C the grain boundaries oxidise and the steel is simply burnt. Temperature and speed trade against each other through the Zener–Hollomon parameter Z = ε̇·exp(Q/RT), Q ≈ 300 kJ/mol in austenite: hitting ten times faster is worth about 130 °C of cooling — which is why a slow press reaches the centre of a billet and a fast hammer only moves its skin. The metal flows perpendicular to the hammer face toward the nearest free surface, and the ratio of contact length to section thickness decides how deep that reaches: near 1 it goes through, below about 0.5 the surface moves while the axis is pulled into tension. The grain flow then follows the finished shape instead of being cut across it, which is what makes a forged part stronger than a machined one along the flow — and weakest across it.",
     "An anvil of 50 kg or more with 70–90 % rebound — drop a 25 mm ball bearing from 250 mm and measure — bedded solid at knuckle height; it wants to outweigh the hammer about fifty to one, or the blow's energy goes into moving the anvil instead of the steel. A 1–1.5 kg cross-pein or rounding hammer (velocity is squared in ½mv², so speed beats mass, and a hammer too heavy to swing fast is a slower hammer), and a 3 kg sledge if someone will strike for you. Tongs that fit the section, with a ring to close them. Hot cut, fullers, a butcher, punches and drifts with a can of water beside them, a monkey tool, a swage block. Coal or coke under a hood with a blower, or a gas forge whose burner can be tuned rich. Steel wire brush, a magnet, calipers, a bucket of vermiculite, and a slack tub for the tools, not the work.",
     "Pick the steel and its window. Mild works from 1,250 °C down to a dull red and forgives most things; high-carbon and alloy steels want 1,150 down to about 850 °C and no lower; air-hardening tool steel goes into vermiculite straight off the anvil, or it hardens overnight and cracks in the bin.\n"
     "Run the fire reducing, not oxidising — the pocket above the tuyere under a cover of coke, or a gas burner tuned slightly rich. An oxidising fire takes a percent of the stock as scale every heat, and pulls carbon out of the surface while it does it.\n"
     "Judge colour in shade, never in sunlight: the eye reads heat only against its surroundings, and a bar that looks dull outdoors is already burning. Yellow ≈ 1,150 °C, orange ≈ 1,000, cherry ≈ 800 — and a magnet letting go is 770 °C exactly, the one fixed point you can check by hand.\n"
     "Soak, do not just heat: about a minute per 5 mm of thickness once it is up to colour. A hot skin over a cold core tears when you move it.\n"
     "Work the heat, then stop. At 1,200 °C the bar radiates some 250 kW/m², and a 12 mm section sheds about 15 °C a second — the thirty seconds everyone quotes. Twice the section is twice the time; a 5 mm taper is done in under ten; and thin work left lying on a cold anvil face loses more by conduction than by air.\n"
     "Draw out over the far edge of the anvil or under a fuller, half-on and half-off, turning 90° each pass: a narrow contact drives metal along the bar instead of sideways. Planish flat afterwards with light, level blows.\n"
     "Never draw a round as a round. Take it to square, draw it there, knock the corners to an octagon, and round the octagon last — a cylinder hammered across its diameter turn after turn puts its own axis into tension and opens a hole down the middle.\n"
     "Upset with no more than two and a half diameters of hot bar standing unsupported, and straighten every few blows: friction pins the ends while the middle spreads, so it barrels first and folds second.\n"
     "Punch from both sides, not through: sink halfway, flip onto the raised mark, drive the slug out. Withdraw the punch every few seconds and cool it, and drop a pinch of coal dust in the hole so the steam pops it free. Punching bulges the bar — dress it back; drilling would cut the grain instead of parting it.\n"
     "Brush the scale off before any blow that matters. The oxide does not move like the metal under it: a blow presses it in as a pit, or folds it in as an inclusion that can never weld shut.\n"
     "Finish low — the last blows just above A₃ — so the strain you have only just put in recrystallises into fine grains instead of feeding coarse ones. Then normalise: three descending air cools, about 900, 855 and 815 °C, each soak shorter than the last.",
     "Carbon monoxide is what actually kills smiths — a gas forge in a shut shop, a coal fire with no draught. Alarm on the wall, door open. Hammer on anvil peaks at 110–120 dB and hearing does not grow back: plugs from the first day. Never heat galvanised, plated or unknown scrap — zinc buys you a night of fever, cadmium can kill, and sulfur-bearing free-machining steel crumbles at forging heat. Side-shielded glasses always; scale comes off the anvil as well as the work. Cotton, wool or leather, never synthetics, and boots you can kick a hot offcut out of. A glove on the tong hand only — the hammer hand needs to feel the blow. Hot steel and cold steel are the same colour. Check the hammer's wedge, never leave a hardy standing in the hole, and wet the fire down and sit with it a while before you lock up.",
     "Cold shut: a lap hammered closed over its own oxide. It is not a weld and never becomes one, and by Griffith's criterion the stress needed to run it as a crack falls as one over the square root of its length — so it is the flaw that fails the part years later. Central burst, or an end that opens into a fish mouth, from drawing a round as a round or from bites too shallow for the section: the skin moves and the axis is pulled apart. Hot shortness — edges crumbling like wet chalk at yellow — from sulfur, or from copper picked up out of scrap; both melt into the grain boundaries below forging heat. Cracks from working under the A₃ line, or from hammering through the 250–400 °C blue-brittle range where nitrogen pins the dislocations. Coarse grain from soaking at yellow, which normalising will undo; burnt steel, which sparks and crumbles and nothing will undo — cut it off. A decarburised skin that will not harden afterwards, from too many long oxidising heats: forge a blade oversize and grind through it.",
     "Sighted down its length it is straight, and it rocks nowhere on the anvil face; the section calipers what it was drawn to. Wire-brushed and read in raking light there is no dark seam — a suspect line opens under the corner of a chisel if it is a cold shut, and does nothing if it is only scale. The shape came from metal moving, not from grinding it away. And a coupon off the same bar, normalised and snapped, breaks to a fine silky grey: bright, coarse and faceted means it was too hot for too long, which is a verdict on the heat, not on the hammering.",
     ["Fe", "C", "Mn", "S", "Cu"],
     ["Zener–Hollomon Parameter", "Hall–Petch Relationship", "Arrhenius Equation", "Griffith Fracture Criterion",
      "Stefan–Boltzmann Law", "Newton's Law of Cooling"], []),
    ("Sand Casting", "Metalwork", "Intermediate",
     "Pouring molten metal into a cavity rammed in sand around a pattern — the way engine blocks, manhole covers and bronze bells are made.",
     "Molten aluminium at 700 °C or bronze at 1,100 °C flows under gravity into the mould; the sand, bonded with clay or resin, is porous enough to let the air and steam out. The metal shrinks a few percent as it freezes, so a riser feeds more in, and shrinks again as it cools, so the pattern is made oversize. Bernoulli governs the pouring basin and sprue; the metal must fill the mould before it freezes.",
     "Two-part flask, green sand (silica, bentonite clay, water), a pattern with draft, parting dust, a crucible and furnace, tongs, sprue and riser pins.",
     "Set the pattern on a board in the drag; dust it; ram sand in layers, firm at the edges.\nFlip, add the cope, place sprue and riser pins, ram again.\nLift the cope off; remove pattern and pins; cut a gate from sprue to cavity.\nClose the flask; weight it — molten metal floats a cope.\nMelt, skim the dross, and pour steadily into the sprue without stopping until the riser fills.\nLet it freeze; break out; cut off sprue and riser; clean up.",
     "Molten metal and any moisture — a damp tool, a wet floor — explode. Dry everything. Face shield, leather, and no synthetics. Pour over sand, not concrete.",
     "Misrun: metal froze before filling — too cold or gate too small. Porosity: gas from wet sand or a turbulent pour. Sand inclusions from a soft mould. Cracks from a hot tear where the casting could not shrink.",
     "The casting fills every corner of the pattern, rings when tapped, and machines clean without pockets.",
     ["Al", "Si", "Cu", "Sn"], ["Bernoulli's Equation", "Newton's Law of Cooling"], ["Otto Four-Stroke Engine"]),
    ("Turning on a Lathe", "Metalwork", "Intermediate",
     "Spinning a bar and moving a cutting tool along it to make round parts to a hundredth of a millimetre — shafts, bushes, threads.",
     "The tool shears a chip off the surface; the geometry — rake angle, relief, nose radius — sets how it cuts and how it finishes. Cutting speed is surface metres per minute, so a bigger bar turns slower; carbide runs three times faster than high-speed steel. Depth of cut times feed is how fast metal comes off; heat goes mostly into the chip, which is why it turns blue.",
     "Lathe, three-jaw chuck, carbide-insert or HSS tools, live centre, calipers and a micrometer, cutting oil, brush for chips.",
     "Grip the stock with as little stick-out as the job allows; face the end.\nSet the tool tip exactly on centre height — a scrap of shim under a rule against the stock tells you.\nSet speed from cutting speed ÷ (π × diameter); feed 0.1–0.2 mm per rev.\nRough down leaving 0.5 mm; measure; take a finishing cut with a lighter feed.\nSneak up on the size: cut, measure, cut.\nDeburr and chamfer.",
     "No gloves, no loose sleeves, no jewellery — the chuck will take a hand. Chips are hot and sharp; brush, never grab. Remove the chuck key every single time.",
     "Chatter — a rippled surface — from a long tool overhang or a thin part. Taper from a misaligned tailstock. A part that walks out of the chuck. A tool that rubs instead of cutting when below centre.",
     "The part measures within tolerance along its length, the surface finish is even, and the tool made chips, not dust.",
     ["Fe", "W", "C", "Co"], ["Newton's Second Law"], ["Steam Turbine"]),
    ("Tapping a Thread", "Metalwork", "Beginner",
     "Cutting an internal screw thread into a drilled hole with a tap — the skill behind almost every bolted joint.",
     "The tap drill leaves the right amount of metal for the thread: for an M6 × 1 thread the hole is 5 mm — major diameter minus pitch. The tap cuts on its flutes and the chip has to go somewhere; that is why you back off every half turn to break it. Steel is threaded to about 60–75 % engagement; more only makes tapping harder, not the joint stronger.",
     "Tap set (taper, second, plug), tap wrench, correct tap drill, centre punch, cutting fluid, a square.",
     "Centre-punch, drill the tap-drill size square to the surface; countersink the mouth slightly.\nStart the taper tap in the wrench, oil, and turn it in with light downward pressure, checking square from two sides.\nHalf a turn forward, quarter back to break the chip; feel for the click.\nIf it binds, back out and clear the chips — never force.\nFollow with the plug tap for full threads to the bottom of a blind hole.\nBlow out chips and test with the bolt.",
     "Small taps snap under side load and the stub is very hard to remove; keep it square and never lean on it. Cutting fluid on hands and floor.",
     "A snapped tap in the hole. Torn threads from no lubricant or dull tap. Threads that lean because the start was not square. A stripped hole from a drill too big.",
     "The bolt runs in by hand smoothly to the bottom with no wobble, and takes torque.",
     ["Fe"], ["Hooke's Law"], []),
    ("Sharpening an Edge", "Metalwork", "Beginner",
     "Bringing two ground faces of hardened steel to a clean intersection — the difference between a tool that cuts and one that tears.",
     "An edge is sharp when the two bevels meet in a line a fraction of a micron wide. Abrasive — aluminium oxide, silicon carbide, diamond — cuts the steel; coarse grits shape the bevel, fine grits reduce the scratch pattern until the edge is smooth enough to reflect no light. A burr forms as you reach the edge and must be removed, or it folds over on first use. Angle matters more than pressure: 15° per side for a kitchen knife, 25° for a chisel.",
     "Combination water or oil stones (1000/6000), or a diamond plate; a strop with compound; a marker pen; good light.",
     "Colour the bevel with marker; a few strokes on the coarse stone show whether you are holding the angle.\nRaise a burr along the whole edge on the coarse stone — feel for it on the far side.\nFlip and repeat until the burr moves to the first side.\nRepeat on the fine stone with light pressure, alternating sides.\nStrop away the burr on leather, edge trailing.\nTest.",
     "The edge is the hazard. Cut away from yourself when testing; keep fingers behind the edge on the stone.",
     "A rounded, dull edge from rocking the angle. A wire edge that felt sharp and folded on the first cut — the burr was not removed. Uneven bevels from more strokes on one side.",
     "It slices paper cleanly along its whole length, shaves arm hair, and shows no reflected line of light when looked at edge-on.",
     ["Fe", "Al", "O", "Si", "C"], ["Cauchy's Stress Theorem"], []),
    ("FDM 3D Printing", "Making", "Beginner",
     "Building a part layer by layer from a thread of molten plastic laid down by a moving nozzle — the machine that made rapid prototyping a household thing.",
     "A thermoplastic softens above its glass transition and flows through a 0.4 mm nozzle at 200–250 °C; each layer must fuse to the one below before it cools, so ambient temperature, layer height and speed are a heat-transfer problem. Layers are strong along the line and weak across it — a printed part is anisotropic. Warping is differential shrinkage as the lower layers cool while the upper ones are hot.",
     "FDM printer, PLA or PETG filament, slicer software, deburring tool, isopropanol for the bed, calipers.",
     "Level the bed: a sheet of paper drags lightly under the nozzle at every corner.\nSlice at 0.2 mm layers, 3 walls, 15–20 % infill; orient the part so its loads run along layers, not across.\nPrint the first layer slow and watch it — it should be squished slightly flat, not round.\nKeep drafts off; enclose for anything above PLA.\nLet it cool before removing; a warm PLA part bends.\nRemove supports and deburr.",
     "The nozzle is 200 °C and the bed 60 °C. ABS fumes need ventilation. Keep fingers clear of the moving gantry.",
     "Corners lifting from the bed — warping. Stringing between features from too much heat or too little retraction. Layers that split apart under load — printed the wrong way up. Under-extrusion from a partly blocked nozzle or damp filament.",
     "The first layer is uniform, the walls are smooth, dimensions match the model within a couple of tenths, and the part carries its intended load.",
     ["C", "H", "O"], ["Fourier's Law of Heat Conduction", "Newton's Law of Cooling"], ["Brushless Permanent-Magnet Motor"]),
    ("Mortise and Tenon Joint", "Making", "Intermediate",
     "The oldest strong wood joint: a tongue on one piece fitting a slot in the other, glued and sometimes pegged — chairs, doors, timber frames.",
     "Wood is strong along the grain and weak across it, and it moves with humidity across the grain but hardly at all along it. The joint works because the tenon's long-grain faces glue to the mortise's long-grain walls; end grain glues badly. Sizing the tenon a third of the stock thickness balances the strength of the tenon against the walls left either side of the mortise.",
     "Marking gauge, square, marking knife, mortise chisel, mallet, tenon saw, shoulder plane, PVA glue, clamps.",
     "Mark the mortise from the tenon stock: a third of its thickness, gauged from the same face on both pieces.\nChop the mortise: chisel bevel-toward-the-waste, levering out chips, working from the middle to the ends.\nSaw the tenon cheeks just outside the line, then the shoulders.\nPare the tenon to a snug hand-push fit — never a hammer fit, that splits the mortise.\nDry-fit, check square, glue the cheeks, clamp, check square again.\nPeg through if it will take load in tension.",
     "Chisels are sharp and slip: clamp the work, keep the free hand behind the edge. Mallet blows off the chisel end.",
     "A loose joint from sawing on the wrong side of the line — glue does not fill gaps. A split mortise from a fat tenon. Shoulders that do not close because the tenon bottoms out first.",
     "It goes together by hand with light friction, the shoulders close tight all round with no gap, and it stays square under clamping.",
     ["C", "H", "O"], ["Hooke's Law", "Young's Modulus"], []),
    ("Using a Multimeter", "Electronics", "Beginner",
     "Measuring voltage, current and resistance — the instrument that turns a circuit from a mystery into numbers.",
     "Voltage is measured across two points, in parallel, by a meter of very high resistance so it draws almost nothing. Current is measured in series, through a meter of very low resistance, so it drops almost nothing — put it across a supply and you have made a short circuit through the meter. Resistance is measured by pushing a small known current and reading the voltage: Ohm's law with the meter supplying the current, so it only works on a dead circuit.",
     "Digital multimeter with autorange, probes, alligator clips, a known-good battery to check it against.",
     "Voltage: black lead in COM, red in V; select DC or AC; touch the probes across the component, black to ground.\nCurrent: move the red lead to the A socket; break the circuit and put the meter in the gap; expect a fuse to blow if you forget to move it back.\nResistance: power off, part isolated; touch across it; open circuit reads OL.\nContinuity: the beeper — a quick check for broken wires and blown fuses.\nDiode test: forward reads about 0.6 V for silicon, OL reversed.\nWhen a reading makes no sense, check the meter on something you know first.",
     "Never measure resistance or continuity on a live circuit. Never put the meter across a supply while it is in current mode. Mains: one hand behind your back, probes with finger guards, and a CAT III meter.",
     "A blown internal fuse from measuring current across a battery. A reading of 0 V because you are in AC mode on a DC circuit. A resistance reading that changes as you touch it — your fingers are in parallel.",
     "The reading agrees with what Ohm's law says it should be, and a fresh AA reads 1.55–1.6 V.",
     ["Cu"], ["Ohm's Law", "Kirchhoff's Circuit Laws"], ["Lithium-Ion Cell", "Lead–Acid Battery"]),
    ("Crimping and Wire Termination", "Electronics", "Beginner",
     "Joining a wire to a terminal by cold-forming the metal around it — done right, a gas-tight joint better than solder; done wrong, the most common electrical fault there is.",
     "A proper crimp deforms both terminal and strands past their yield point into a single cold-welded mass with no air gaps — no oxide can form, so the resistance stays low for decades. Solder in a crimp is worse: it wicks up the strands, makes a hard point where the flexible wire becomes rigid, and it fatigues and breaks there. Contact resistance is what heats a bad joint: a tenth of an ohm at 30 A is 90 W in a connector.",
     "Ratcheting crimper with the correct dies for the terminal, wire strippers, terminals sized to the wire gauge, heat-shrink, heat gun.",
     "Strip exactly the length of the terminal barrel; no nicked strands.\nTwist the strands lightly and insert until they show at the far end but not into the mating area.\nCrimp in the ratchet die for that terminal until it releases; a half-crimp is no crimp.\nPull test: a firm tug should not move it.\nInspect: the barrel is uniformly formed, insulation grip holds the jacket, strands visible at the end.\nHeat-shrink over the joint.",
     "Live circuits: isolate first. Undersized wire for the current heats and starts fires — the crimp is not the weak point, the choice is.",
     "Strands pulled out because the wire was too small for the terminal. Insulation crimped instead of copper. Pliers instead of a ratchet die — a squashed barrel that loosens with heat cycling.",
     "It passes a hard pull, reads a few milliohms, and stays cool at full current.",
     ["Cu", "Sn"], ["Ohm's Law", "Joule Heating"], []),
    ("Building a Circuit on a Breadboard", "Electronics", "Beginner",
     "Wiring a working circuit — an LED, a resistor, a supply — without solder, and understanding why every part is there.",
     "The LED is a diode: it conducts one way and drops a fixed voltage, about 2 V for red, 3 V for blue, set by the semiconductor's band gap — the photon energy, by the Planck–Einstein relation. Without a resistor it would draw whatever current the supply can give and die. Ohm's law sizes the resistor: (supply − LED drop) ÷ desired current, so 5 V, 2 V, 10 mA → 300 Ω. Kirchhoff's laws say the current is the same everywhere in the loop and the voltages add to the supply.",
     "Breadboard, jumper wires, LEDs, resistors, a 5 V supply or battery pack, a multimeter to check.",
     "Learn the board: the long rails run the length; the short rows of five are joined across.\nWire the supply to the rails; check with the meter before adding anything.\nLED long leg (anode) toward positive, resistor in series on either side.\nCalculate the resistor and use the nearest standard value above.\nPower on: it lights. Measure the LED drop and the resistor drop; they add to the supply.\nMeasure the current in series and compare with what you calculated.",
     "Low voltage; the only real risk is a shorted battery pack getting hot. Never breadboard mains.",
     "Nothing lights: LED backwards, or a part in a row that is not connected to what you think. LED flashes and dies: no resistor. Dim: resistor far too large.",
     "The LED lights, the measured current is within 10 % of the calculation, and you can explain every part.",
     ["Ga", "N", "In", "Cu", "C"], ["Ohm's Law", "Kirchhoff's Circuit Laws", "Planck–Einstein Relation"], ["Voltaic Pile"]),
    ("Mixing and Placing Concrete", "Building", "Beginner",
     "Making the world's most-used material — cement, sand, gravel and water — and putting it where it will set into stone.",
     "Cement does not dry, it hydrates: calcium silicates react with water to grow interlocking crystals, and keep doing so for weeks. Too much water leaves pores when it evaporates — every extra bucket costs strength; too little and it will not compact. Concrete is strong in compression and weak in tension, which is why it is reinforced with steel bar, and why it cracks if it dries out fast before it has cured.",
     "Cement, sharp sand, 20 mm gravel, clean water; a mixer or a board and shovel; buckets for gauging; a trowel, float, and something to tamp with; polythene to cover it.",
     "Gauge by volume: 1 cement, 2 sand, 3 gravel for general work.\nMix the dry ingredients until one colour, then add water a little at a time to a stiff, workable mix that holds a shape.\nDampen the formwork or hole; place the concrete within an hour of mixing.\nTamp or rod it to drive the air out, especially at edges and around bar.\nStrike off level, then float once the surface sheen has gone.\nCover and keep damp for a week; do not load for a month.",
     "Wet cement is caustic and burns skin over hours without you noticing; gloves, and wash off splashes. Dust: mask when handling dry cement.",
     "Weak, dusty concrete from too much water or from drying out uncovered in sun. Honeycombing — voids at the surface — from poor compaction. Cracks from a slab with no joints, or curing too fast.",
     "It sets hard overnight, rings rather than thuds after a week, and shows no surface dusting or fine cracks.",
     ["Ca", "Si", "Al", "Fe", "O", "H"], ["Hooke's Law", "Young's Modulus"], ["Wind Turbine", "Pressurized Water Reactor"]),
    ("Anchoring into Masonry", "Building", "Beginner",
     "Fixing something heavy to a brick or concrete wall so it stays — the right drill, the right hole, the right anchor.",
     "A wall plug or expansion anchor works by friction: it swells against the sides of the hole as the screw drives in, and the pull-out strength comes from that friction times the contact area. That needs a hole of exactly the right diameter and depth in sound material — a loose hole or crumbling brick and the anchor spins. Hammer drilling pulverises masonry with a percussive carbide tip; the drill's rotation only clears the dust.",
     "Hammer drill or SDS drill, masonry bits sized to the anchor, wall plugs or sleeve anchors, a detector for pipes and cables, tape and pencil, spirit level.",
     "Scan for cables and pipes; then mark the holes off the level fixture, not the wall.\nDrill in brick, not mortar joints; drill to the depth of plug plus 10 mm, hammer on.\nBlow or vacuum the dust out of the hole — dust halves the holding power.\nPush the plug in flush; drive the screw until firm, not until it spins.\nFor heavy loads use sleeve or chemical anchors and drill the specified size.\nLoad-test by pulling before you trust it.",
     "Cables and water pipes are behind walls; scan, and drill shallow first. Dust in eyes and lungs. A drill that catches will twist your wrist — hold it with both hands.",
     "The plug spins in the hole — hole too big or brick soft. The screw pulls out under load. Cracked brick from drilling in the edge or the mortar.",
     "The screw drives to a firm stop, the fixture does not shift under a hard pull, and nothing crumbled.",
     ["Si", "Ca", "Fe", "W"], ["Newton's Second Law"], []),
    ("Essential Knots", "Rigging", "Beginner",
     "The half-dozen knots that cover most of what rope is asked to do: a loop that will not slip, a bend that joins two ropes, a hitch that holds to a post and comes off again.",
     "A knot holds by friction, and each turn of rope over rope multiplies the grip — the capstan effect: tension falls exponentially with wrap angle. A good knot is one that grips harder as it is loaded and can still be untied afterwards. Every knot weakens the rope, typically to 50–75 % of its strength, because it bends the fibres over a small radius; the bowline and figure-eight are among the kinder ones.",
     "A few metres of 8–10 mm rope; a post or rail to practise on.",
     "Bowline: fixed loop — the rabbit comes out of the hole, round the tree, back down the hole; dress it tight.\nFigure-eight on a bight: a stronger fixed loop, easy to check by eye.\nClove hitch: two turns to a post, quick on and off, not for a load that shifts.\nRound turn and two half hitches: a secure hitch that can be tied and untied under load.\nSheet bend: joins two ropes of different sizes; doubled for slippery rope.\nTrucker's hitch: a 3:1 purchase for tensioning a line.",
     "A loaded rope stores energy; stand out of line of a rope under tension. Never put a finger inside a loop that could tighten.",
     "A bowline tied backwards that capsizes under load. A clove hitch that walks off the end of a smooth pole. A knot that jams solid because it was loaded before it was dressed.",
     "It holds under a hard pull, looks like the picture, and unties by hand afterwards.",
     [], [], []),
    ("Rigging a Load with Pulleys", "Rigging", "Intermediate",
     "Lifting or pulling more than you can by hand by trading distance for force with blocks and rope.",
     "A pulley changes the direction of a force; several of them, reeved so the load hangs from n rope segments, divide the force by n and multiply the distance by n — mechanical advantage, at the price of friction in every sheave (a few percent each). Newton's second law and the tension in the rope do the accounting: the load is shared equally by every segment supporting it. The anchor sees the load plus the pull.",
     "Two or three pulley blocks rated above the load, rope, slings and shackles, a rated anchor point, gloves.",
     "Rate everything: rope, blocks, shackles, anchor — the weakest is the limit, and it takes the load plus your pull.\nReeve a 3:1: anchor a block, run the rope from the load's block up and back; count the segments holding the load.\nHaul; the load moves a third as far as your hand.\nAdd a redirect at the anchor to pull downward if that is easier — it changes direction, not advantage.\nProgress-capture with a prusik or a locking block before you let go.\nLower under control; never let the rope run.",
     "Anything under load can fail explosively; stand clear of the line of pull. Rated hardware only, no home-made anchors. Rope burns are serious.",
     "An anchor that pulls out because it was sized for the load, not the load plus haul. Rope jumping a sheave. Losing the load when someone lets go without capture.",
     "The load rises smoothly at the calculated fraction of the pull, holds when you stop, and everything is within its rating.",
     [], ["Newton's Second Law"], []),
    ("Reading Calipers and a Micrometer", "Measuring", "Beginner",
     "Measuring to a hundredth of a millimetre — the difference between a part that fits and one that almost fits.",
     "A caliper reads directly to 0.02 mm; a micrometer to 0.01 mm or better, by a screw of known pitch: one turn of the thimble is 0.5 mm, and the fifty divisions on it read hundredths. Steel expands about 12 µm per metre per degree — a warm part in a cold hand measures big. The measuring pressure matters, which is why a micrometer has a ratchet: it applies the same force every time.",
     "Digital or vernier calipers, 0–25 mm micrometer with a standard, a clean rag, a stable temperature.",
     "Zero the instrument closed; wipe the jaws.\nCalipers: close on the part square, no rocking; read; check with the depth rod and inside jaws where needed.\nMicrometer: open past the size, close on the part with the ratchet until it clicks twice; read the sleeve for millimetres and halves, the thimble for hundredths.\nTake three readings around the part; they should agree.\nCheck the micrometer against its standard now and then.\nRecord to the instrument's resolution and no further.",
     "None to speak of, beyond dropping the micrometer — which ruins it.",
     "Reading a vernier one line off. Squeezing a caliper until it flexes. Measuring hot metal straight off the lathe. Trusting the fourth decimal on a calipers display.",
     "Repeat readings agree within the instrument's resolution, and a known gauge block reads its stated size.",
     ["Fe", "Cr"], [], []),
    ("Squaring with the 3-4-5 Rule", "Measuring", "Beginner",
     "Laying out a right angle over any distance with nothing but a tape — a shed base, a wall, a fence line.",
     "A triangle with sides 3, 4 and 5 has a right angle opposite the 5, by Pythagoras: 3² + 4² = 5². Any multiple works, and a bigger triangle is more accurate because a millimetre of tape error matters less over five metres than over fifty centimetres. The same theorem checks a rectangle: if both diagonals are equal, its corners are square.",
     "A tape, string line, pegs, a pencil; two people make it easier.",
     "Set the first line with string and pegs.\nMark 3 units (say 3 m) along it from the corner.\nSwing a 4-unit arc from the corner and a 5-unit arc from the 3 m mark; where they cross is the second line's direction.\nRun the second line through that point.\nFor a rectangle, measure both diagonals; adjust until they are equal.\nUse the biggest multiple the site allows.",
     "Trip hazards from string lines; nothing else.",
     "Measuring from the wrong mark. A tape with a bent hook that adds a few millimetres. Diagonals checked to the pegs rather than the string.",
     "The two diagonals of the finished rectangle agree to within a few millimetres over several metres.",
     [], ["Pythagorean Theorem"], []),
]


def main():
    print("equations")
    eq_schema = ensure_props(EQ_DS, {}, "equations")
    ensure_select_options(EQ_DS, "Field", sorted({e[2] for e in EQUATIONS}), "equations")
    sync_rows(EQ_DS, eq_schema,
              [{"Name": n, "Equation": eq, "Field": f, "Named After": na, "Symbols": sy, "Significance": sig, "Year": y}
               for n, eq, f, na, sy, sig, y in EQUATIONS], "equations")

    print("\ninventors")
    r_schema = ensure_props(RESEARCHER_DS, {}, "researchers")
    sync_rows(RESEARCHER_DS, r_schema,
              [{"Name": n, "Lifespan": ls, "Nationality": nat, "Field": f, "Known For": k}
               for n, ls, nat, f, k in INVENTORS], "researchers")

    print("\nmachines")
    m_schema = ensure_props(MACHINES_DS, {}, "machines")
    sync_rows(MACHINES_DS, m_schema,
              [{"Name": n, "Kind": k, "Cycle": c, "Year": y, "How It Works": how, "Efficiency": eff,
                "Power Density": pd, "Materials": mat, "Used In": use}
               for n, k, c, y, _, how, eff, pd, mat, use, _, _ in MACHINES], "machines")

    print("\nskills")
    s_schema = ensure_props(SKILLS_DS, {}, "skills")
    sync_rows(SKILLS_DS, s_schema,
              [{"Name": n, "Category": cat, "Difficulty": d, "Summary": su, "The Science": sci, "Tools": t,
                "Steps": st, "Safety": sa, "How It Fails": fa, "Done When": dn}
               for n, cat, d, su, sci, t, st, sa, fa, dn, _, _, _ in SKILLS], "skills")

    # ---- relations
    print("\nrelations")
    eqs = {title_of(p, "Name"): p["id"] for p in query_all(EQ_DS) if title_of(p, "Name")}
    people = {title_of(p, "Name"): p["id"] for p in query_all(RESEARCHER_DS) if title_of(p, "Name")}
    els = {}
    for p in query_all(ELEMENTS_DS):
        sym = "".join(x["plain_text"] for x in p["properties"].get("Notation", {}).get("rich_text", [])).strip()
        if sym:
            els[sym] = p["id"]
    machines = {title_of(p, "Name"): p for p in query_all(MACHINES_DS) if title_of(p, "Name")}
    skills = {title_of(p, "Name"): p for p in query_all(SKILLS_DS) if title_of(p, "Name")}
    missing = set()

    def link(page, prop, names, lookup):
        ids = set()
        for n in names:
            if n in lookup:
                ids.add(lookup[n])
            else:
                missing.add(f"{prop}:{n}")
        cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
        new = cur | ids
        return ({prop: {"relation": [{"id": x} for x in sorted(new)]}} if new != cur else {}), len(new)

    changed = edges = 0
    for n, _, _, _, inv, _, _, _, _, _, syms, eqn in MACHINES:
        page = machines.get(n)
        if not page:
            continue
        payload = {}
        for prop, names, lookup in (("Inventors", inv, people), ("Elements", syms, els), ("Equations", eqn, eqs)):
            p, k = link(page, prop, names, lookup)
            payload.update(p); edges += k
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
    print(f"  machines: updated {changed} · {edges} links")

    changed = edges = 0
    mids = {k: v["id"] for k, v in machines.items()}
    for n, _, _, _, _, _, _, _, _, _, syms, eqn, mach in SKILLS:
        page = skills.get(n)
        if not page:
            continue
        payload = {}
        for prop, names, lookup in (("Elements", syms, els), ("Equations", eqn, eqs), ("Machines", mach, mids)):
            p, k = link(page, prop, names, lookup)
            payload.update(p); edges += k
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
    print(f"  skills: updated {changed} · {edges} links")
    if missing:
        print("  unresolved names ignored:", sorted(missing))
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
