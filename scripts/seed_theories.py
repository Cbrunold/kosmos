"""Seed the Theories [DB] and Researchers [DB] in Notion.

Both databases already exist but are nearly empty (2 theories, 5 bare
researcher names as of 2026-08-15), so this script *fills* rather than
creates: it adds any missing properties to the schema, inserts missing rows,
and backfills empty fields on rows that are already there. It never
overwrites a value a human has already set.

Chronology uses a `Year` number property, mirroring the Equations [DB]
convention (negative = BCE), rather than the existing empty `Date Proposed`
date property — a year is what the sources actually support, and a date
would invent a month and a day nobody knows.

Status is a four-point scale rather than three: `Superseded` distinguishes
Newtonian mechanics (still taught, still used, simply not the last word)
from `Disproved` ideas like the aether, which were tested and found absent.

Idempotent: safe to re-run. Relations are wired separately by link_theories.py.
Run on the VPS:  python3 scripts/seed_theories.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from notion import token, headers, call, query_all, find_ds, title_of, is_empty, chunks, encode, ensure_props, ensure_select_options, sync_rows  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
THEORY_DS = "215048ed-e6a6-4b9a-858b-73e8c801629e"
RESEARCHER_DS = "4cc8d7c4-9008-4017-a09b-7087720aebd3"

STATUSES = ["Accepted", "Superseded", "Speculative", "Disproved"]


# ------------------------------------------------------------------ researchers
# name, lifespan, nationality, field, known for
RESEARCHERS = [
    ("Claudius Ptolemy", "c. 100–170", "Roman Egyptian", "Astronomy",
     "The Almagest — the geocentric model that organised the sky for fourteen centuries."),
    ("Nicolaus Copernicus", "1473–1543", "Polish", "Astronomy",
     "Put the Sun at the centre and published it the year he died, which may have been wise."),
    ("Johannes Kepler", "1571–1630", "German", "Astronomy",
     "Three laws of planetary motion, extracted from Tycho Brahe's data by sheer arithmetic stubbornness."),
    ("Galileo Galilei", "1564–1642", "Italian", "Astronomy & Mechanics",
     "Turned the telescope upward and found moons, phases, and trouble."),
    ("Christiaan Huygens", "1629–1695", "Dutch", "Optics",
     "The wave theory of light, the pendulum clock, and Saturn's rings correctly explained."),
    ("Isaac Newton", "1642–1727", "English", "Mechanics & Optics",
     "One law of gravitation for apples and planets alike — and the calculus to work it out."),
    ("Georg Ernst Stahl", "1659–1734", "German", "Chemistry",
     "Systematised phlogiston, the most productive wrong idea in the history of chemistry."),
    ("Antoine Lavoisier", "1743–1794", "French", "Chemistry",
     "Killed phlogiston with a balance, named oxygen, and was guillotined anyway."),
    ("John Dalton", "1766–1844", "English", "Chemistry",
     "Atoms with fixed weights — the idea that made chemistry quantitative."),
    ("Thomas Young", "1773–1829", "English", "Optics",
     "The double-slit experiment, and a decent stab at the Rosetta Stone in his spare time."),
    ("Augustin-Jean Fresnel", "1788–1827", "French", "Optics",
     "Made the wave theory of light quantitative, and left it needing an aether to wave in."),
    ("Michael Faraday", "1791–1867", "English", "Electromagnetism",
     "Discovered induction with almost no mathematics — the field concept was his."),
    ("Rudolf Clausius", "1822–1888", "German", "Thermodynamics",
     "Named entropy and stated the second law in the form everyone still quotes."),
    ("James Clerk Maxwell", "1831–1879", "Scottish", "Electromagnetism",
     "Four equations that turned electricity, magnetism, and light into one subject."),
    ("Josiah Willard Gibbs", "1839–1903", "American", "Thermodynamics",
     "Built statistical mechanics and chemical thermodynamics, quietly, at Yale."),
    ("Ludwig Boltzmann", "1844–1906", "Austrian", "Statistical Mechanics",
     "S = k log W, carved on his gravestone — he did not live to see atoms accepted."),
    ("Hendrik Lorentz", "1853–1928", "Dutch", "Theoretical Physics",
     "Wrote down the transformations of special relativity before anyone knew what they meant."),
    ("J. J. Thomson", "1856–1940", "English", "Atomic Physics",
     "Discovered the electron and proposed the plum pudding his student would demolish."),
    ("Max Planck", "1858–1947", "German", "Quantum Theory",
     "Quantised energy as a desperate fix for the black-body spectrum, and started everything."),
    ("Henri Poincaré", "1854–1912", "French", "Mathematics & Physics",
     "Found chaos in the three-body problem and came within a hair of special relativity."),
    ("David Hilbert", "1862–1943", "German", "Mathematics",
     "Derived the field equations of general relativity within days of Einstein, by a different route."),
    ("Ernest Rutherford", "1871–1937", "New Zealander", "Nuclear Physics",
     "Fired alpha particles at gold foil and discovered the nucleus in the ricochet."),
    ("Albert Einstein", "1879–1955", "German-American", "Theoretical Physics",
     "Special relativity, general relativity, the photoelectric effect — and a lifelong quarrel with quantum mechanics."),
    ("Max Born", "1882–1970", "German-British", "Quantum Mechanics",
     "Interpreted the wavefunction as probability, which is the part Einstein never accepted."),
    ("Niels Bohr", "1885–1962", "Danish", "Quantum Mechanics",
     "Quantised the atom, then spent thirty years arguing with Einstein about what it meant."),
    ("Erwin Schrödinger", "1887–1961", "Austrian", "Quantum Mechanics",
     "One wave equation for all of chemistry, and one very famous hypothetical cat."),
    ("Arnold Sommerfeld", "1868–1951", "German", "Atomic Physics",
     "Refined the Bohr model and introduced the fine-structure constant; taught more Nobel laureates than anyone."),
    ("Louis de Broglie", "1892–1987", "French", "Quantum Mechanics",
     "Proposed that matter has a wavelength, in a doctoral thesis, and was right."),
    ("Alfred Wegener", "1880–1930", "German", "Geophysics",
     "Saw that the continents fit together and was ridiculed for fifty years."),
    ("Fritz Zwicky", "1898–1974", "Swiss", "Astrophysics",
     "Weighed the Coma cluster in 1933, found most of it missing, and named dark matter."),
    ("Georges Lemaître", "1894–1966", "Belgian", "Cosmology",
     "A priest who derived the expanding universe from Einstein's equations two years before Hubble measured it."),
    ("Paul Dirac", "1902–1984", "English", "Quantum Field Theory",
     "Married relativity to quantum mechanics and got antimatter as an unavoidable side effect."),
    ("Werner Heisenberg", "1901–1976", "German", "Quantum Mechanics",
     "Matrix mechanics and the uncertainty principle — the end of the classical trajectory."),
    ("Hermann Bondi", "1919–2005", "Austrian-British", "Cosmology",
     "Co-authored the steady state theory, the most elegant cosmology that turned out to be wrong."),
    ("Thomas Gold", "1920–2004", "Austrian-American", "Astrophysics",
     "Steady state cosmology, and the correct identification of pulsars as neutron stars."),
    ("Fred Hoyle", "1915–2001", "English", "Astrophysics",
     "Explained where the elements come from, coined 'Big Bang' as an insult, and never believed it."),
    ("George Gamow", "1904–1968", "Russian-American", "Cosmology",
     "Predicted the microwave background, and wrote the physics books people actually finished."),
    ("Ralph Alpher", "1921–2007", "American", "Cosmology",
     "Calculated Big Bang nucleosynthesis for his PhD; the prediction of the CMB was in it."),
    ("Maria Goeppert Mayer", "1906–1972", "German-American", "Nuclear Physics",
     "The nuclear shell model and its magic numbers, worked out unpaid for most of her career."),
    ("Felix Bloch", "1905–1983", "Swiss-American", "Condensed Matter",
     "Bloch's theorem — why electrons move through a crystal lattice at all."),
    ("John Bardeen", "1908–1991", "American", "Condensed Matter",
     "The only person with two Nobel Prizes in physics: the transistor, then superconductivity."),
    ("Leon Cooper", "1930–2024", "American", "Superconductivity",
     "Cooper pairs — the bound electrons that carry a supercurrent."),
    ("Robert Schrieffer", "1931–2019", "American", "Superconductivity",
     "Wrote down the many-body wavefunction that completed BCS theory."),
    ("Claude Shannon", "1916–2001", "American", "Information Theory",
     "Invented information as a measurable quantity, and juggled while riding a unicycle."),
    ("Richard Feynman", "1918–1988", "American", "Quantum Field Theory",
     "Path integrals, diagrams, and the first serious proposal for a quantum computer."),
    ("Julian Schwinger", "1918–1994", "American", "Quantum Field Theory",
     "Built QED by a formalism so dense that Feynman's pictures won the popularity contest."),
    ("Sin-Itiro Tomonaga", "1906–1979", "Japanese", "Quantum Field Theory",
     "Developed QED independently in wartime Japan, in near-total isolation."),
    ("Freeman Dyson", "1923–2020", "British-American", "Quantum Field Theory",
     "Proved the three formulations of QED were the same theory."),
    ("William Fowler", "1911–1995", "American", "Nuclear Astrophysics",
     "Measured the nuclear reaction rates that make stellar nucleosynthesis quantitative."),
    ("Margaret Burbidge", "1919–2020", "British-American", "Astrophysics",
     "Lead author of B²FH, the paper that explained where every element heavier than helium comes from."),
    ("Geoffrey Burbidge", "1925–2010", "British-American", "Astrophysics",
     "Co-author of B²FH; remained a Big Bang sceptic to the end."),
    ("Murray Gell-Mann", "1929–2019", "American", "Particle Physics",
     "Quarks, the eightfold way, and the name 'quark' lifted from Finnegans Wake."),
    ("Sheldon Glashow", "1932–", "American", "Particle Physics",
     "The first electroweak gauge theory, and a long-running scepticism about string theory."),
    ("Abdus Salam", "1926–1996", "Pakistani", "Particle Physics",
     "Electroweak unification, and a lifetime spent building physics in the developing world."),
    ("Steven Weinberg", "1933–2021", "American", "Particle Physics",
     "'A Model of Leptons' — three pages that became the Standard Model."),
    ("Peter Higgs", "1929–2024", "British", "Particle Physics",
     "Predicted the boson in 1964 and waited forty-eight years for CERN to find it."),
    ("François Englert", "1932–", "Belgian", "Particle Physics",
     "Published the Brout–Englert mechanism weeks before Higgs, and shared the prize."),
    ("Gerard 't Hooft", "1946–", "Dutch", "Quantum Field Theory",
     "Proved electroweak theory renormalisable, making it physics rather than speculation."),
    ("David Gross", "1941–", "American", "Particle Physics",
     "Asymptotic freedom — why quarks rattle around loosely inside a proton and can never leave."),
    ("Frank Wilczek", "1951–", "American", "Particle Physics",
     "Asymptotic freedom as a graduate student; later, the axion."),
    ("Howard Georgi", "1947–", "American", "Particle Physics",
     "The first grand unified theory, whose predicted proton decay has stubbornly failed to appear."),
    ("Julius Wess", "1934–2007", "Austrian", "Particle Physics",
     "Co-founded supersymmetry, still the best-motivated idea with no experimental support."),
    ("Bruno Zumino", "1923–2014", "Italian", "Particle Physics",
     "The other half of the Wess–Zumino model."),
    ("Stephen Hawking", "1942–2018", "British", "Cosmology",
     "Showed black holes evaporate, which is still the sharpest clue we have about quantum gravity."),
    ("Jacob Bekenstein", "1947–2015", "Israeli-American", "Gravitation",
     "Argued a black hole has entropy proportional to its area, and was disbelieved until Hawking proved it."),
    ("Roger Penrose", "1931–", "British", "Mathematical Physics",
     "Proved that general relativity predicts its own breakdown: singularities are unavoidable."),
    ("Leonard Susskind", "1940–", "American", "String Theory",
     "String theory from the start, the holographic principle, and the black hole war with Hawking."),
    ("Michael Green", "1946–", "British", "String Theory",
     "The 1984 anomaly cancellation that triggered the first superstring revolution."),
    ("John Schwarz", "1941–", "American", "String Theory",
     "Kept string theory alive through the decade nobody was listening."),
    ("Edward Witten", "1951–", "American", "String Theory",
     "Unified five string theories into M-theory; the only physicist to win a Fields Medal."),
    ("Juan Maldacena", "1968–", "Argentine", "String Theory",
     "The AdS/CFT correspondence — the most-cited idea in theoretical physics this century."),
    ("Carlo Rovelli", "1956–", "Italian", "Quantum Gravity",
     "Loop quantum gravity, and the argument that time is not fundamental."),
    ("Lee Smolin", "1955–", "American", "Quantum Gravity",
     "Loop quantum gravity, and a book-length case against string theory."),
    ("Abhay Ashtekar", "1949–", "Indian-American", "Quantum Gravity",
     "The variables that made loop quantum gravity tractable."),
    ("Alan Guth", "1947–", "American", "Cosmology",
     "Inflation — a fraction of a second of exponential expansion that explains why the sky looks so uniform."),
    ("Andrei Linde", "1948–", "Russian-American", "Cosmology",
     "Chaotic and eternal inflation, in which our universe is one bubble among endlessly many."),
    ("Alexei Starobinsky", "1948–2023", "Russian", "Cosmology",
     "Proposed an inflationary model in 1980 that current CMB data still fits best."),
    ("Vera Rubin", "1928–2016", "American", "Astronomy",
     "Measured flat galaxy rotation curves and turned dark matter from a curiosity into a crisis."),
    ("James Peebles", "1935–", "Canadian-American", "Cosmology",
     "Built most of the theoretical scaffolding of modern physical cosmology."),
    ("George Smoot", "1945–", "American", "Cosmology",
     "COBE's map of the microwave background — the first picture of structure in the infant universe."),
    ("Saul Perlmutter", "1959–", "American", "Cosmology",
     "Led one of the two supernova teams that found the expansion is speeding up."),
    ("Brian Schmidt", "1967–", "American-Australian", "Cosmology",
     "Led the other one, and got the same unwelcome answer."),
    ("Adam Riess", "1969–", "American", "Cosmology",
     "Wrote up the accelerating-universe result, and now leads the distance-ladder side of the Hubble tension."),
    ("Michel Mayor", "1942–", "Swiss", "Astronomy",
     "Co-discovered 51 Pegasi b, the first planet found around a Sun-like star."),
    ("Didier Queloz", "1966–", "Swiss", "Astronomy",
     "The graduate student on the other end of that discovery."),
    ("Mordehai Milgrom", "1946–", "Israeli", "Astrophysics",
     "Proposed modifying gravity instead of adding dark matter — a minority view that refuses to die."),
    ("Harry Hess", "1906–1969", "American", "Geology",
     "Seafloor spreading — the mechanism that made continental drift respectable."),
    ("J. Tuzo Wilson", "1908–1993", "Canadian", "Geophysics",
     "Transform faults and hotspots; assembled the pieces into plate tectonics."),
    ("Edward Lorenz", "1917–2008", "American", "Meteorology",
     "Rounded a number from six digits to three, got a different forecast, and founded chaos theory."),
    ("Mitchell Feigenbaum", "1944–2019", "American", "Nonlinear Dynamics",
     "Found a universal constant hiding in the route from order to chaos."),
    ("Hugh Everett III", "1930–1982", "American", "Quantum Mechanics",
     "Proposed the many-worlds interpretation, was ignored, and left physics for defence analysis."),
    ("John Stewart Bell", "1928–1990", "Northern Irish", "Quantum Foundations",
     "Turned a philosophical argument into an inequality that experiments could — and did — violate."),
    ("David Deutsch", "1953–", "British", "Quantum Computing",
     "Defined the universal quantum computer."),
    ("Peter Shor", "1959–", "American", "Quantum Computing",
     "The factoring algorithm that made everyone take quantum computing seriously."),
]

RESEARCHER_PROPS = {
    "Lifespan": {"rich_text": {}},
    "Nationality": {"rich_text": {}},
    "Field": {"rich_text": {}},
    "Known For": {"rich_text": {}},
}

# ------------------------------------------------------------------ theories
# name, year, status, summary, proponents
THEORIES = [
    ("Geocentric Model", 150, "Disproved",
     "Earth at rest in the centre, everything else on nested spheres. It survived fourteen centuries because it "
     "worked: with enough epicycles Ptolemy's system predicted planetary positions to within a degree.",
     ["Claudius Ptolemy"]),
    ("Heliocentrism", 1543, "Accepted",
     "The Sun at the centre, the Earth a planet like any other. Copernicus's version still used circles and was "
     "no more accurate than Ptolemy's; Kepler's ellipses are what finally made it win.",
     ["Nicolaus Copernicus", "Johannes Kepler", "Galileo Galilei"]),
    ("Phlogiston Theory", 1667, "Disproved",
     "Combustible bodies were said to contain phlogiston, released as they burned. The theory died when Lavoisier "
     "weighed the products and found them heavier — the awkward fix, negative mass, was one step too far.",
     ["Georg Ernst Stahl"]),
    ("Wave Theory of Light", 1690, "Superseded",
     "Light as a wave in a medium, which explained diffraction and interference that particles could not. Correct "
     "about the wave, wrong about the medium, and eventually absorbed into quantum electrodynamics.",
     ["Christiaan Huygens", "Thomas Young", "Augustin-Jean Fresnel"]),
    ("Corpuscular Theory of Light", 1704, "Superseded",
     "Newton's competing account: light as a stream of particles. Dismissed for a century after Young's double "
     "slit, then partly vindicated by the photon — though not in any form Newton would recognise.",
     ["Isaac Newton"]),
    ("Newtonian Mechanics", 1687, "Superseded",
     "Three laws of motion and one of gravitation, covering everything from a dropped apple to the orbit of "
     "Neptune. Still how every bridge is built; simply not exact at high speed or strong gravity.",
     ["Isaac Newton"]),
    ("Caloric Theory", 1783, "Disproved",
     "Heat as a weightless, conserved fluid flowing from hot to cold. It explained thermal expansion and got the "
     "gas laws right, and it was undone by cannon boring: friction made heat without limit, so nothing was conserved.",
     ["Antoine Lavoisier"]),
    ("Atomic Theory", 1803, "Accepted",
     "Matter as discrete atoms with fixed weights, combining in whole-number ratios. Dalton made chemistry "
     "quantitative; atoms were not directly confirmed until Einstein explained Brownian motion a century later.",
     ["John Dalton"]),
    ("Luminiferous Aether", 1818, "Disproved",
     "If light is a wave, something must be waving — so space was filled with an invisible, frictionless, rigid "
     "medium. Michelson and Morley looked for the Earth's motion through it in 1887 and found precisely nothing.",
     ["Augustin-Jean Fresnel", "Hendrik Lorentz"]),
    ("Kinetic Theory of Gases", 1857, "Accepted",
     "Pressure and temperature as bookkeeping for molecules in flight. It derived the gas laws from mechanics "
     "and statistics alone, and gave the first real evidence that molecules were more than a convenient fiction.",
     ["James Clerk Maxwell", "Ludwig Boltzmann", "Rudolf Clausius"]),
    ("Classical Electromagnetism", 1865, "Accepted",
     "Four equations tying electricity, magnetism, and light into a single field theory — and predicting that "
     "light is an electromagnetic wave travelling at a speed built from two laboratory constants.",
     ["James Clerk Maxwell", "Michael Faraday"]),
    ("Statistical Mechanics", 1902, "Accepted",
     "Thermodynamics derived from counting microstates. It explains why entropy increases without any law saying "
     "it must: there are simply overwhelmingly more disordered arrangements than ordered ones.",
     ["Ludwig Boltzmann", "Josiah Willard Gibbs"]),
    ("Quantum Hypothesis", 1900, "Superseded",
     "Energy exchanged only in discrete packets, hf at a time. Planck introduced it as an act of desperation to "
     "fit the black-body curve and spent years trying to explain it away; Einstein took it literally instead.",
     ["Max Planck", "Albert Einstein"]),
    ("Plum Pudding Model", 1904, "Disproved",
     "Electrons embedded in a diffuse sphere of positive charge. Rutherford's foil experiment killed it in one "
     "afternoon: alpha particles bounced straight back, which meant the positive charge was concentrated in a point.",
     ["J. J. Thomson"]),
    ("Rutherford Model of the Atom", 1911, "Superseded",
     "A tiny dense nucleus with electrons somewhere around it — almost entirely empty space. Correct about the "
     "nucleus and fatally wrong about the orbits: classical electrons would radiate and spiral in within nanoseconds.",
     ["Ernest Rutherford"]),
    ("Special Relativity", 1905, "Accepted",
     "Drop the aether, keep the speed of light constant for everyone, and space and time have to bend to comply. "
     "Simultaneity becomes relative, and mass and energy turn out to be the same quantity.",
     ["Albert Einstein", "Hendrik Lorentz", "Henri Poincaré"]),
    ("Bohr Model of the Atom", 1913, "Superseded",
     "Electrons in fixed orbits, jumping between them and emitting a photon for the difference. It got hydrogen's "
     "spectrum exactly right and every other atom wrong, which was the clue that something deeper was needed.",
     ["Niels Bohr", "Arnold Sommerfeld"]),
    ("General Relativity", 1915, "Accepted",
     "Gravity is not a force but the curvature of spacetime, with matter telling space how to bend and space "
     "telling matter how to move. It predicted light bending, Mercury's orbit, black holes, and gravitational waves.",
     ["Albert Einstein", "David Hilbert"]),
    ("Continental Drift & Plate Tectonics", 1912, "Accepted",
     "The continents move, riding rigid plates on a convecting mantle. Wegener saw the fit of the coastlines and "
     "was dismissed for lack of a mechanism; seafloor spreading supplied one fifty years later.",
     ["Alfred Wegener", "Harry Hess", "J. Tuzo Wilson"]),
    ("Wave–Particle Duality", 1924, "Accepted",
     "Not just light — everything. De Broglie assigned a wavelength to matter, and electrons duly diffracted. "
     "The wavelength of anything larger than a molecule is far too small to notice, which is why the world looks solid.",
     ["Louis de Broglie", "Albert Einstein"]),
    ("Quantum Mechanics", 1925, "Accepted",
     "States as vectors, observables as operators, outcomes as probabilities. The most precisely tested theory "
     "ever written, and the one whose meaning is still argued about a century on.",
     ["Werner Heisenberg", "Erwin Schrödinger", "Max Born", "Paul Dirac"]),
    ("Copenhagen Interpretation", 1927, "Speculative",
     "The wavefunction is knowledge, not substance, and measurement collapses it. The default taught in textbooks, "
     "though it never says what counts as a measurement — which is exactly the objection that will not go away.",
     ["Niels Bohr", "Werner Heisenberg"]),
    ("Big Bang Cosmology", 1927, "Accepted",
     "The universe was hot and dense and has been expanding ever since. Lemaître derived it from Einstein's "
     "equations; the microwave background, the light-element abundances, and the redshifts all agree.",
     ["Georges Lemaître", "George Gamow", "James Peebles"]),
    ("Band Theory of Solids", 1928, "Accepted",
     "Electrons in a periodic lattice occupy continuous bands with gaps between them. The width of the gap is the "
     "whole difference between a copper wire, a silicon chip, and a pane of glass.",
     ["Felix Bloch", "Arnold Sommerfeld"]),
    ("Dark Matter", 1933, "Accepted",
     "Galaxies and clusters move as though they hold five times the mass we can see. Zwicky found it and was "
     "ignored; Rubin's rotation curves made it undeniable. Its identity remains completely unknown.",
     ["Fritz Zwicky", "Vera Rubin"]),
    ("Local Hidden Variables", 1935, "Disproved",
     "Einstein's position: quantum randomness reflects missing information, not genuine indeterminacy. Bell turned "
     "it into a testable inequality; every experiment since has violated it. Nature really is non-local.",
     ["Albert Einstein", "John Stewart Bell"]),
    ("Quantum Electrodynamics", 1948, "Accepted",
     "Electrons and photons as a relativistic quantum field theory. Its prediction of the electron's magnetic "
     "moment matches experiment to twelve digits — the most accurate agreement in all of science.",
     ["Richard Feynman", "Julian Schwinger", "Sin-Itiro Tomonaga", "Freeman Dyson"]),
    ("Information Theory", 1948, "Accepted",
     "Information measured in bits, with a hard limit on how fast any noisy channel can carry it. Written for "
     "telephone engineers; now underneath every disk, modem, and compression format in existence.",
     ["Claude Shannon"]),
    ("Steady State Theory", 1948, "Disproved",
     "An eternal, unchanging universe that expands while new matter appears to keep the density constant. Elegant, "
     "serious, and finished off by the microwave background in 1965 — Hoyle never conceded.",
     ["Fred Hoyle", "Hermann Bondi", "Thomas Gold"]),
    ("Big Bang Nucleosynthesis", 1948, "Accepted",
     "The first three minutes made hydrogen, helium, and a trace of lithium, in ratios fixed by the neutron-proton "
     "balance. The predicted helium fraction of about a quarter by mass is what we observe.",
     ["George Gamow", "Ralph Alpher"]),
    ("Nuclear Shell Model", 1949, "Accepted",
     "Protons and neutrons fill quantised shells much as electrons do, with closed shells at the 'magic numbers'. "
     "It explains which nuclei are unusually stable, and which are the ones that fission.",
     ["Maria Goeppert Mayer"]),
    ("BCS Theory of Superconductivity", 1957, "Accepted",
     "Electrons pair up through lattice vibrations and condense into a single quantum state that flows without "
     "resistance. It took forty-six years after the discovery of superconductivity to explain it.",
     ["John Bardeen", "Leon Cooper", "Robert Schrieffer"]),
    ("Stellar Nucleosynthesis", 1957, "Accepted",
     "Every element heavier than lithium was cooked inside a star or in the explosion that ended it. The B²FH "
     "paper worked out the whole chain — the carbon in your body was assembled in a red giant.",
     ["Fred Hoyle", "Margaret Burbidge", "Geoffrey Burbidge", "William Fowler"]),
    ("Many-Worlds Interpretation", 1957, "Speculative",
     "There is no collapse: the wavefunction just keeps evolving, and every outcome happens in its own branch. "
     "Mathematically the leanest interpretation, and the hardest to believe before breakfast.",
     ["Hugh Everett III"]),
    ("Chaos Theory", 1963, "Accepted",
     "Deterministic systems can be unpredictable, because arbitrarily small differences in the starting state grow "
     "exponentially. Lorenz found it in a truncated weather simulation; the constants turn out to be universal.",
     ["Edward Lorenz", "Mitchell Feigenbaum", "Henri Poincaré"]),
    ("Higgs Mechanism", 1964, "Accepted",
     "A field filling all of space that gives the weak force carriers their mass while leaving the photon massless. "
     "Predicted in 1964, confirmed at the LHC in 2012 — one of the longest waits in physics.",
     ["Peter Higgs", "François Englert"]),
    ("Electroweak Unification", 1967, "Accepted",
     "Electromagnetism and the weak nuclear force as two aspects of one interaction, split apart as the early "
     "universe cooled. The predicted W and Z bosons turned up at CERN in 1983, at the predicted masses.",
     ["Steven Weinberg", "Abdus Salam", "Sheldon Glashow", "Gerard 't Hooft"]),
    ("Supersymmetry", 1971, "Speculative",
     "A symmetry pairing every fermion with a boson, which would tidy up the Higgs mass and supply a dark matter "
     "candidate. The LHC has found none of the partners, and the simplest versions are now excluded.",
     ["Julius Wess", "Bruno Zumino"]),
    ("Quantum Chromodynamics", 1973, "Accepted",
     "The strong force, carried by gluons between colour-charged quarks. Its strange signature is that the force "
     "grows with distance, so a quark can never be pulled out on its own.",
     ["Murray Gell-Mann", "David Gross", "Frank Wilczek"]),
    ("Grand Unified Theories", 1974, "Speculative",
     "One gauge group at high energy, splitting into the strong, weak, and electromagnetic forces as things cool. "
     "The simplest versions predict the proton decays; forty years of watching tanks of water say it does not.",
     ["Howard Georgi", "Sheldon Glashow"]),
    ("Black Hole Thermodynamics", 1974, "Accepted",
     "Black holes have entropy proportional to their surface area and radiate at a temperature set by their mass. "
     "It ties gravity, quantum mechanics, and thermodynamics together, and nobody fully understands why.",
     ["Stephen Hawking", "Jacob Bekenstein", "Roger Penrose"]),
    ("The Standard Model", 1975, "Accepted",
     "Twelve matter particles, four force carriers, one Higgs, and about nineteen numbers nobody can derive. "
     "It has survived every experiment for fifty years while explaining neither gravity nor dark matter.",
     ["Steven Weinberg", "Sheldon Glashow", "Murray Gell-Mann"]),
    ("Cosmic Inflation", 1980, "Speculative",
     "A burst of exponential expansion in the first fraction of a second, smoothing the universe and stretching "
     "quantum fluctuations into the seeds of galaxies. It fits the data well; the mechanism is still guesswork.",
     ["Alan Guth", "Andrei Linde", "Alexei Starobinsky"]),
    ("Quantum Information Theory", 1982, "Accepted",
     "Information stored in quantum states, where it can be superposed and entangled but never copied. Shor's "
     "algorithm showed the payoff, and started the race to build a machine that can run it.",
     ["Richard Feynman", "David Deutsch", "Peter Shor"]),
    ("Modified Newtonian Dynamics", 1983, "Speculative",
     "Change the law of gravity at very low accelerations instead of adding invisible matter. It fits galaxy "
     "rotation curves remarkably well and clusters and the microwave background remarkably badly.",
     ["Mordehai Milgrom"]),
    ("String Theory", 1984, "Speculative",
     "Particles as vibrating strings in ten dimensions, with gravity falling out unavoidably rather than being "
     "inserted. Forty years of beautiful mathematics and not one testable prediction at reachable energies.",
     ["Michael Green", "John Schwarz", "Edward Witten", "Leonard Susskind"]),
    ("Loop Quantum Gravity", 1988, "Speculative",
     "Quantise spacetime itself, giving area and volume discrete spectra with no background geometry assumed. "
     "The main rival to strings; it takes general relativity more seriously and particle physics less.",
     ["Carlo Rovelli", "Lee Smolin", "Abhay Ashtekar"]),
    ("Holographic Principle", 1993, "Speculative",
     "Everything inside a region can be encoded on its boundary, one bit per four Planck areas. Suggested by "
     "black hole entropy, made concrete by AdS/CFT, and still without a formulation for our own universe.",
     ["Gerard 't Hooft", "Leonard Susskind", "Juan Maldacena"]),
    ("Dark Energy", 1998, "Accepted",
     "The expansion of the universe is accelerating, driven by something with negative pressure that makes up "
     "about seven tenths of everything. A cosmological constant fits — at a value 120 orders of magnitude off theory.",
     ["Saul Perlmutter", "Brian Schmidt", "Adam Riess"]),
]

THEORY_PROPS = {
    "Year": {"number": {"format": "number"}},
}

# theory name -> equation names in the Equations [DB] (used by link_theories.py)
THEORY_EQUATIONS = {
    "Geocentric Model": ["Kepler's First Law"],
    "Heliocentrism": ["Kepler's First Law", "Kepler's Second Law", "Kepler's Third Law"],
    "Wave Theory of Light": ["Wave Equation", "Snell's Law", "Diffraction Grating Equation", "Bragg's Law"],
    "Corpuscular Theory of Light": ["Snell's Law"],
    "Newtonian Mechanics": ["Newton's Second Law", "Law of Universal Gravitation", "Kepler's Third Law",
                            "Escape Velocity", "Vis-Viva Equation", "Principle of Least Action"],
    "Caloric Theory": ["First Law of Thermodynamics", "Newton's Law of Cooling"],
    "Atomic Theory": ["Dalton's Law of Partial Pressures", "Avogadro's Law", "Law of Mass Action"],
    "Luminiferous Aether": ["Lorentz Transformations", "Wave Equation"],
    "Kinetic Theory of Gases": ["Ideal Gas Law", "Boltzmann Distribution", "Equipartition Theorem",
                                "Graham's Law of Effusion", "Van der Waals Equation", "Boyle's Law",
                                "Charles's Law", "Gay-Lussac's Law"],
    "Classical Electromagnetism": ["Ampère–Maxwell Law", "Faraday's Law of Induction", "Gauss's Law",
                                   "Gauss's Law for Magnetism", "Coulomb's Law", "Electric Field",
                                   "Poisson's Equation", "Wave Equation"],
    "Statistical Mechanics": ["Boltzmann Entropy", "Partition Function", "Boltzmann Distribution",
                              "Equipartition Theorem", "Fermi–Dirac Distribution", "Second Law of Thermodynamics"],
    "Quantum Hypothesis": ["Planck's Law", "Planck–Einstein Relation", "Wien's Displacement Law",
                           "Kirchhoff's Law of Thermal Radiation", "Stefan–Boltzmann Law"],
    "Plum Pudding Model": ["Rutherford Scattering"],
    "Rutherford Model of the Atom": ["Rutherford Scattering", "Coulomb's Law", "Electric Field"],
    "Special Relativity": ["Lorentz Factor", "Lorentz Transformations", "Mass–Energy Equivalence"],
    "Bohr Model of the Atom": ["Bohr Model Energy Levels", "Rydberg Formula", "Planck–Einstein Relation"],
    "General Relativity": ["Einstein Field Equations", "Einstein–Hilbert Action", "Geodesic Equation",
                           "Gravitational Time Dilation", "Schwarzschild Radius", "FLRW Metric"],
    "Continental Drift & Plate Tectonics": ["Seismic Wave Speeds", "Elastic Wave Equation"],
    "Wave–Particle Duality": ["De Broglie Wavelength", "Planck–Einstein Relation"],
    "Quantum Mechanics": ["Schrödinger Equation", "Heisenberg Uncertainty Principle", "De Broglie Wavelength",
                          "Planck–Einstein Relation", "Dirac Equation"],
    "Copenhagen Interpretation": ["Schrödinger Equation", "Heisenberg Uncertainty Principle"],
    "Big Bang Cosmology": ["First Friedmann Equation", "Second Friedmann Equation", "FLRW Metric",
                           "Hubble's Law", "Cosmological Redshift", "Critical Density",
                           "Cosmological Fluid Equation", "Cosmological Equation of State",
                           "Linear Perturbation Growth", "Saha Ionization Equation"],
    "Band Theory of Solids": ["Bloch's Theorem", "Fermi–Dirac Distribution", "Drude Conductivity"],
    "Dark Matter": ["Critical Density", "Second Friedmann Equation", "Linear Perturbation Growth",
                    "Law of Universal Gravitation"],
    "Local Hidden Variables": ["Bell State", "Qubit State"],
    "Quantum Electrodynamics": ["Feynman Path Integral", "Fine-Structure Constant", "Dirac Equation",
                                "Klein–Gordon Equation"],
    "Information Theory": ["Shannon Entropy", "Shannon–Hartley Channel Capacity", "Boltzmann Entropy"],
    "Steady State Theory": ["Hubble's Law", "FLRW Metric", "First Friedmann Equation"],
    "Big Bang Nucleosynthesis": ["Saha Ionization Equation", "First Friedmann Equation", "Boltzmann Distribution"],
    "Nuclear Shell Model": ["Half-Life", "Radioactive Decay Law", "Schrödinger Equation"],
    "BCS Theory of Superconductivity": ["BCS Energy Gap", "London Equations", "Josephson Effect",
                                        "Fermi–Dirac Distribution"],
    "Stellar Nucleosynthesis": ["Saha Ionization Equation", "Chandrasekhar Limit", "Stefan–Boltzmann Law",
                                "Arrhenius Equation"],
    "Many-Worlds Interpretation": ["Schrödinger Equation", "Qubit State"],
    "Chaos Theory": ["Lorenz System", "Logistic Map", "Feigenbaum Constant"],
    "Higgs Mechanism": ["Higgs Potential", "Standard Model Lagrangian"],
    "Electroweak Unification": ["Standard Model Lagrangian", "Higgs Potential", "Fine-Structure Constant"],
    "Supersymmetry": ["Standard Model Lagrangian", "Higgs Potential"],
    "Quantum Chromodynamics": ["Standard Model Lagrangian", "Klein–Gordon Equation"],
    "Grand Unified Theories": ["Standard Model Lagrangian", "Fine-Structure Constant", "Half-Life"],
    "Black Hole Thermodynamics": ["Schwarzschild Radius", "Boltzmann Entropy", "Planck's Law",
                                  "Stefan–Boltzmann Law", "Einstein Field Equations"],
    "The Standard Model": ["Standard Model Lagrangian", "Higgs Potential", "Dirac Equation",
                           "Klein–Gordon Equation", "Fine-Structure Constant"],
    "Cosmic Inflation": ["First Friedmann Equation", "FLRW Metric", "Linear Perturbation Growth",
                         "Cosmological Equation of State"],
    "Quantum Information Theory": ["Qubit State", "Bell State", "No-Cloning Theorem", "Shannon Entropy"],
    "Modified Newtonian Dynamics": ["Newton's Second Law", "Law of Universal Gravitation"],
    "String Theory": ["Einstein–Hilbert Action", "Principle of Least Action", "Euler–Lagrange Equation",
                      "Noether's Theorem"],
    "Loop Quantum Gravity": ["Einstein Field Equations", "Einstein–Hilbert Action", "Geodesic Equation"],
    "Holographic Principle": ["Schwarzschild Radius", "Boltzmann Entropy", "Shannon Entropy"],
    "Dark Energy": ["Second Friedmann Equation", "Cosmological Equation of State", "Einstein Field Equations",
                    "Critical Density", "Hubble's Law"],
    # the two rows that were already in Notion
    "Quantum Gravity": ["Einstein Field Equations", "Einstein–Hilbert Action", "Schrödinger Equation",
                        "Schwarzschild Radius", "Geodesic Equation"],
    "Unification Theories": ["Standard Model Lagrangian", "Higgs Potential", "Fine-Structure Constant"],
}

# proponents for the two pre-existing rows, which have none set
EXISTING_PROPONENTS = {
    "Quantum Gravity": ["Carlo Rovelli", "Lee Smolin", "Roger Penrose", "Stephen Hawking"],
    "Unification Theories": ["Steven Weinberg", "Abdus Salam", "Sheldon Glashow", "Howard Georgi"],
}

# year + status for the pre-existing rows (their Summary is already written, and is kept)
EXISTING_META = {
    "Quantum Gravity": (1930, "Speculative"),
    "Unification Theories": (1974, "Speculative"),
}


def main():
    print("researchers")
    r_schema = ensure_props(RESEARCHER_DS, RESEARCHER_PROPS, "researchers")
    sync_rows(RESEARCHER_DS, r_schema,
              [{"Name": n, "Lifespan": ls, "Nationality": nat, "Field": f, "Known For": k}
               for n, ls, nat, f, k in RESEARCHERS],
              "researchers")

    print("\ntheories")
    t_schema = ensure_props(THEORY_DS, THEORY_PROPS, "theories")
    ensure_select_options(THEORY_DS, "Status", STATUSES, "theories")
    rows = [{"Name": n, "Year": y, "Status": s, "Summary": summary}
            for n, y, s, summary, _ in THEORIES]
    rows += [{"Name": n, "Year": y, "Status": s} for n, (y, s) in EXISTING_META.items()]
    sync_rows(THEORY_DS, t_schema, rows, "theories")

    print("\nnow run: python3 scripts/link_theories.py")


if __name__ == "__main__":
    main()
