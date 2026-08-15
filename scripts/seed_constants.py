"""Create and seed the Constants [DB] and Units [DB] in Notion.

Values are CODATA 2022 where applicable, IAU 2015 nominal for solar/planetary
quantities, and Planck 2018 / SH0ES 2022 for cosmological parameters (both
sides of the Hubble tension are listed deliberately).

Idempotent: skips databases and rows that already exist.
Run on the VPS:  python3 scripts/seed_constants.py
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"   # Physical Sciences


def token() -> str:
    if os.environ.get("NOTION_TOKEN"):
        return os.environ["NOTION_TOKEN"]
    for p in (ROOT / ".env", Path("/srv/kosmos/.env")):
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("NOTION_TOKEN="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    sys.exit("NOTION_TOKEN not set")


H = {"Authorization": f"Bearer {token()}", "Notion-Version": "2025-09-03", "Content-Type": "application/json"}


def call(method, url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=H, method=method)
    return json.load(urllib.request.urlopen(req))


def find_ds(title):
    d = call("POST", "https://api.notion.com/v1/search",
             {"query": title, "filter": {"property": "object", "value": "data_source"}, "page_size": 50})
    for r in d.get("results", []):
        if "".join(x.get("plain_text", "") for x in r.get("title", [])).strip() == title:
            return r["id"]
    return None


def create_db(title, properties):
    db = call("POST", "https://api.notion.com/v1/databases", {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE},
        "title": [{"type": "text", "text": {"content": title}}],
        "initial_data_source": {"properties": properties},
    })
    return db["data_sources"][0]["id"]


def existing_titles(ds, prop="Name"):
    out, cursor = set(), None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        d = call("POST", f"https://api.notion.com/v1/data_sources/{ds}/query", body)
        for r in d["results"]:
            out.add("".join(x["plain_text"] for x in r["properties"][prop]["title"]).strip())
        if not d.get("has_more"):
            break
        cursor = d["next_cursor"]
    return out


# ---------------------------------------------------------------- constants
CAT = ["Defining (SI)", "Universal", "Electromagnetic", "Atomic & nuclear",
       "Thermodynamic", "Astronomical", "Cosmological", "Mathematical"]

# name, symbol, value (display), numeric, unit, uncertainty, exact, category, note
CONSTANTS = [
    ("Speed of light in vacuum", "c", "299 792 458", 299792458.0, "m s⁻¹", "exact", True, "Defining (SI)",
     "Fixes the metre. The universal speed limit and the conversion factor between space and time."),
    ("Planck constant", "h", "6.626 070 15 × 10⁻³⁴", 6.62607015e-34, "J s", "exact", True, "Defining (SI)",
     "Fixes the kilogram since 2019. The quantum of action — the size of the graininess in nature."),
    ("Elementary charge", "e", "1.602 176 634 × 10⁻¹⁹", 1.602176634e-19, "C", "exact", True, "Defining (SI)",
     "Fixes the ampere. The charge of a proton; quarks carry thirds of it."),
    ("Boltzmann constant", "k_B", "1.380 649 × 10⁻²³", 1.380649e-23, "J K⁻¹", "exact", True, "Defining (SI)",
     "Fixes the kelvin. The exchange rate between temperature and energy per degree of freedom."),
    ("Avogadro constant", "N_A", "6.022 140 76 × 10²³", 6.02214076e23, "mol⁻¹", "exact", True, "Defining (SI)",
     "Fixes the mole. How many entities are in a mole — now a defined count, not a measurement."),
    ("Caesium hyperfine frequency", "Δν_Cs", "9 192 631 770", 9192631770.0, "Hz", "exact", True, "Defining (SI)",
     "Fixes the second: the tick of the caesium atomic clock every other unit is built on."),
    ("Luminous efficacy", "K_cd", "683", 683.0, "lm W⁻¹", "exact", True, "Defining (SI)",
     "Fixes the candela — the one SI base unit defined with human eyes in mind (555 nm green)."),

    ("Reduced Planck constant", "ℏ", "1.054 571 817… × 10⁻³⁴", 1.054571817e-34, "J s", "exact (h/2π)", True, "Universal",
     "Planck's constant per radian. The natural unit of angular momentum and the ℏ in every quantum equation."),
    ("Newtonian constant of gravitation", "G", "6.674 30(15) × 10⁻¹¹", 6.6743e-11, "m³ kg⁻¹ s⁻²",
     "±0.000 15 × 10⁻¹¹ (2.2 × 10⁻⁵ relative)", False, "Universal",
     "The worst-measured fundamental constant by far — gravity is too weak to pin down precisely."),
    ("Planck length", "l_P", "1.616 255(18) × 10⁻³⁵", 1.616255e-35, "m", "±1.1 × 10⁻⁵ relative", False, "Universal",
     "Where quantum mechanics and gravity must merge; ~10²⁰ times smaller than a proton."),
    ("Planck time", "t_P", "5.391 247(60) × 10⁻⁴⁴", 5.391247e-44, "s", "±1.1 × 10⁻⁵ relative", False, "Universal",
     "Light crossing a Planck length. No theory describes the universe before one of these."),
    ("Planck mass", "m_P", "2.176 434(24) × 10⁻⁸", 2.176434e-8, "kg", "±1.1 × 10⁻⁵ relative", False, "Universal",
     "Surprisingly macroscopic — about the mass of a flea's egg, or 10¹⁹ protons."),
    ("Planck temperature", "T_P", "1.416 784(16) × 10³²", 1.416784e32, "K", "±1.1 × 10⁻⁵ relative", False, "Universal",
     "The hottest meaningful temperature; reached, if ever, at the first instant of the Big Bang."),
    ("Standard gravity", "g₀", "9.806 65", 9.80665, "m s⁻²", "exact (defined)", True, "Universal",
     "The conventional surface gravity of Earth — a definition, not a measurement; real values vary by ~0.5%."),

    ("Vacuum electric permittivity", "ε₀", "8.854 187 8188(14) × 10⁻¹²", 8.8541878188e-12, "F m⁻¹",
     "±1.6 × 10⁻¹⁰ relative", False, "Electromagnetic",
     "How strongly the vacuum resists an electric field. Exact before 2019; now measured, via α."),
    ("Vacuum magnetic permeability", "μ₀", "1.256 637 061 27(20) × 10⁻⁶", 1.25663706127e-6, "N A⁻²",
     "±1.6 × 10⁻¹⁰ relative", False, "Electromagnetic",
     "The magnetic counterpart of ε₀; together they give c = 1/√(ε₀μ₀), Maxwell's great discovery."),
    ("Characteristic impedance of vacuum", "Z₀", "376.730 313 412(59)", 376.730313412, "Ω",
     "±1.6 × 10⁻¹⁰ relative", False, "Electromagnetic",
     "The vacuum's resistance to electromagnetic waves — why antennas are matched to ~377 Ω."),
    ("Fine-structure constant", "α", "7.297 352 5643(11) × 10⁻³  (1/137.035 999 177)", 7.2973525643e-3, "—",
     "±1.6 × 10⁻¹⁰ relative", False, "Electromagnetic",
     "Dimensionless, so every civilization measures the same number. Nobody knows why it is 1/137."),

    ("Electron mass", "m_e", "9.109 383 7139(28) × 10⁻³¹", 9.1093837139e-31, "kg", "±3.1 × 10⁻¹⁰ relative", False,
     "Atomic & nuclear", "1/1836 of the proton — light enough to be quantum-mechanically smeared across an atom."),
    ("Proton mass", "m_p", "1.672 621 925 95(52) × 10⁻²⁷", 1.67262192595e-27, "kg", "±3.1 × 10⁻¹⁰ relative", False,
     "Atomic & nuclear", "Only ~1% of it is the quark masses; the rest is the binding energy of the strong force."),
    ("Neutron mass", "m_n", "1.674 927 500 56(85) × 10⁻²⁷", 1.67492750056e-27, "kg", "±5.1 × 10⁻¹⁰ relative", False,
     "Atomic & nuclear", "Heavier than the proton by 0.14% — which is why free neutrons decay in ~15 minutes."),
    ("Atomic mass constant", "u", "1.660 539 068 92(52) × 10⁻²⁷", 1.66053906892e-27, "kg",
     "±3.1 × 10⁻¹⁰ relative", False, "Atomic & nuclear",
     "One twelfth of a carbon-12 atom — the unit every atomic mass on the periodic table is quoted in."),
    ("Rydberg constant", "R_∞", "1.097 373 156 8157(12) × 10⁷", 1.0973731568157e7, "m⁻¹",
     "±1.1 × 10⁻¹² relative", False, "Atomic & nuclear",
     "The most precisely measured constant of all, to twelve digits — hydrogen's spectrum is that sharp."),
    ("Bohr radius", "a₀", "5.291 772 105 44(82) × 10⁻¹¹", 5.29177210544e-11, "m", "±1.6 × 10⁻¹⁰ relative", False,
     "Atomic & nuclear", "The size of a hydrogen atom in its ground state — the natural ruler of chemistry."),
    ("Bohr magneton", "μ_B", "9.274 010 0657(29) × 10⁻²⁴", 9.2740100657e-24, "J T⁻¹", "±3.1 × 10⁻¹⁰ relative", False,
     "Atomic & nuclear", "The magnetic moment of one electron spin — the quantum of magnetism in matter."),
    ("Compton wavelength", "λ_C", "2.426 310 235 38(76) × 10⁻¹²", 2.42631023538e-12, "m",
     "±3.1 × 10⁻¹⁰ relative", False, "Atomic & nuclear",
     "Confine an electron tighter than this and pair production begins — the edge of single-particle quantum mechanics."),

    ("Molar gas constant", "R", "8.314 462 618…", 8.314462618, "J mol⁻¹ K⁻¹", "exact (N_A·k_B)", True, "Thermodynamic",
     "Boltzmann's constant per mole. The R in pV = nRT, Arrhenius, van 't Hoff, and Nernst."),
    ("Faraday constant", "F", "96 485.332 12…", 96485.33212, "C mol⁻¹", "exact (N_A·e)", True, "Thermodynamic",
     "Charge per mole of electrons — the bridge between chemistry's moles and electricity's coulombs."),
    ("Stefan–Boltzmann constant", "σ", "5.670 374 419… × 10⁻⁸", 5.670374419e-8, "W m⁻² K⁻⁴",
     "exact (from h, c, k_B)", True, "Thermodynamic",
     "How brightly a hot body glows. Exact since 2019 because its ingredients are."),
    ("Wien displacement constant", "b", "2.897 771 955… × 10⁻³", 2.897771955e-3, "m K", "exact (from h, c, k_B)",
     True, "Thermodynamic", "Peak wavelength × temperature. Divide by a star's temperature to get its colour."),
    ("Molar volume of an ideal gas", "V_m", "22.413 969 54… × 10⁻³", 22.41396954e-3, "m³ mol⁻¹",
     "exact (at 273.15 K, 101.325 kPa)", True, "Thermodynamic",
     "22.4 litres per mole at STP — the number every chemistry student memorises."),

    ("Astronomical unit", "au", "1.495 978 707 × 10¹¹", 1.495978707e11, "m", "exact (defined)", True, "Astronomical",
     "The Earth–Sun distance, fixed by definition since 2012 rather than measured."),
    ("Parsec", "pc", "3.085 677 581 49 × 10¹⁶", 3.0856775814913673e16, "m", "exact (648000/π au)", True,
     "Astronomical", "The distance at which 1 au subtends one arcsecond — parallax made into a unit. 3.26 light-years."),
    ("Light-year", "ly", "9.460 730 472 5808 × 10¹⁵", 9.4607304725808e15, "m", "exact (365.25 d × c)", True,
     "Astronomical", "How far light travels in a Julian year — a unit of distance, despite the name."),
    ("Solar mass", "M_☉", "1.988 41 × 10³⁰", 1.98841e30, "kg", "±6 × 10⁻⁵ relative (via G)", False, "Astronomical",
     "The Sun's mass is known far less precisely than GM_☉, because G is the weak link."),
    ("Solar mass parameter", "GM_☉", "1.327 124 400 18 × 10²⁰", 1.32712440018e20, "m³ s⁻²",
     "adopted (IAU nominal)", True, "Astronomical",
     "Known to ten digits from orbits — which is why celestial mechanics uses GM, never G and M separately."),
    ("Solar radius", "R_☉", "6.957 × 10⁸", 6.957e8, "m", "adopted (IAU nominal)", True, "Astronomical",
     "The photosphere's radius; the Sun has no solid surface, so this is a convention."),
    ("Solar luminosity", "L_☉", "3.828 × 10²⁶", 3.828e26, "W", "adopted (IAU nominal)", True, "Astronomical",
     "The Sun's total power output — the yardstick every other star is measured against."),
    ("Earth mass", "M_⊕", "5.972 2(6) × 10²⁴", 5.9722e24, "kg", "±1.0 × 10⁻⁴ relative", False, "Astronomical",
     "Also limited by G: Cavendish weighed the Earth in 1798 and we have only refined it since."),
    ("Earth equatorial radius", "R_⊕", "6.378 137 × 10⁶", 6378137.0, "m", "exact (WGS 84)", True, "Astronomical",
     "The reference ellipsoid GPS uses; the poles are 21 km closer to the centre."),

    ("Hubble constant (Planck 2018, CMB)", "H₀", "67.4 ± 0.5", 67.4, "km s⁻¹ Mpc⁻¹", "±0.5 (early-universe route)",
     False, "Cosmological",
     "Inferred from the microwave background assuming ΛCDM. Disagrees with the distance-ladder value below by ~5σ — the Hubble tension."),
    ("Hubble constant (SH0ES 2022, distance ladder)", "H₀", "73.04 ± 1.04", 73.04, "km s⁻¹ Mpc⁻¹",
     "±1.04 (late-universe route)", False, "Cosmological",
     "Measured directly from Cepheids and Type Ia supernovae. Both measurements are careful; something is missing."),
    ("CMB temperature", "T₀", "2.725 48 ± 0.000 57", 2.72548, "K", "±0.000 57", False, "Cosmological",
     "The most perfect black body ever measured, and the coldest thing in nature outside a laboratory."),
    ("Matter density parameter", "Ω_m", "0.315 ± 0.007", 0.315, "—", "±0.007 (Planck 2018)", False, "Cosmological",
     "All matter, of which only about one sixth is the ordinary kind."),
    ("Dark energy density parameter", "Ω_Λ", "0.685 ± 0.007", 0.685, "—", "±0.007 (Planck 2018)", False,
     "Cosmological", "Two thirds of the universe's energy budget, and nobody knows what it is."),
    ("Baryon density", "Ω_b h²", "0.022 37 ± 0.000 15", 0.02237, "—", "±0.000 15 (Planck 2018)", False,
     "Cosmological", "Ordinary matter — atoms — comes to under 5% of the total."),
    ("Critical density", "ρ_c", "8.5 × 10⁻²⁷", 8.5e-27, "kg m⁻³", "±3% (tracks H₀)", False, "Cosmological",
     "The density that makes space flat: about five hydrogen atoms per cubic metre."),
    ("Age of the universe", "t₀", "13.797 ± 0.023", 13.797, "Gyr", "±0.023 (Planck 2018)", False, "Cosmological",
     "Derived from the Friedmann equations given the densities above — not observed directly."),

    ("Pi", "π", "3.141 592 653 589 793…", 3.141592653589793, "—", "exact (irrational)", True, "Mathematical",
     "Circumference over diameter. Appears in half the equations on this site, most of them not about circles."),
    ("Euler's number", "e", "2.718 281 828 459 045…", 2.718281828459045, "—", "exact (irrational)", True,
     "Mathematical", "The base of natural growth and decay — and of every exponential on the shelf."),
]

CONST_EQUATIONS = {
    "c": ["Mass–energy equivalence", "Lorentz Factor", "Lorentz Transformations", "Einstein Field Equations",
          "Planck's Law", "Schwarzschild Radius", "Klein–Gordon Equation", "Fine-Structure Constant",
          "Ampère–Maxwell Law", "Gravitational Time Dilation", "Chandrasekhar Limit", "FLRW Metric"],
    "h": ["Planck–Einstein Relation", "Planck's Law", "De Broglie Wavelength", "Eyring Equation",
          "Einstein A and B Coefficients", "Wien's Displacement Law"],
    "ℏ": ["Schrödinger Equation", "Heisenberg Uncertainty Principle", "Dirac Equation", "Klein–Gordon Equation",
          "Feynman Path Integral", "Chandrasekhar Limit", "Fine-Structure Constant"],
    "k_B": ["Boltzmann Distribution", "Boltzmann Entropy", "Partition Function", "Equipartition Theorem",
            "Planck's Law", "Eyring Equation", "Debye Length", "Fermi–Dirac Distribution", "BCS Energy Gap"],
    "G": ["Law of Universal Gravitation", "Einstein Field Equations", "First Friedmann Equation",
          "Second Friedmann Equation", "Schwarzschild Radius", "Escape Velocity", "Vis-Viva Equation",
          "Kepler's Third Law", "Chandrasekhar Limit", "Einstein–Hilbert Action", "Gravitational Time Dilation",
          "Critical Density"],
    "e": ["Coulomb's Law", "Fine-Structure Constant", "Drude Conductivity", "Plasma Frequency", "Debye Length",
          "Josephson Effect", "London Equations"],
    "ε₀": ["Coulomb's Law", "Gauss's Law", "Poisson's Equation", "Fine-Structure Constant", "Plasma Frequency",
           "Debye Length", "Rutherford Scattering"],
    "μ₀": ["Ampère–Maxwell Law", "Alfvén Velocity", "London Equations"],
    "N_A": ["Avogadro's Law", "Ideal Gas Law"],
    "R": ["Ideal Gas Law", "Arrhenius Equation", "Van 't Hoff Equation", "Reaction Isotherm", "Nernst Equation",
          "Goldman–Hodgkin–Katz Equation", "Eyring Equation"],
    "σ": ["Stefan–Boltzmann Law"],
    "b": ["Wien's Displacement Law"],
    "m_e": ["Drude Conductivity", "Plasma Frequency", "Bohr Model Energy Levels", "London Equations",
            "De Broglie Wavelength", "Saha Ionization Equation"],
    "m_p": ["Chandrasekhar Limit"],
    "a₀": ["Bohr Model Energy Levels"],
    "α": ["Fine-Structure Constant", "Standard Model Lagrangian"],
    "M_☉": ["Chandrasekhar Limit", "Kepler's Third Law", "Escape Velocity", "Schwarzschild Radius"],
    "pc": ["Hubble's Law"],
    "H₀": ["Hubble's Law", "First Friedmann Equation", "Second Friedmann Equation", "Critical Density"],
    "T₀": ["Planck's Law", "Wien's Displacement Law", "Cosmological Redshift", "Saha Ionization Equation"],
    "R_∞": ["Rydberg Formula", "Bohr Model Energy Levels", "Saha Ionization Equation"],
    "ρ_c": ["First Friedmann Equation", "Critical Density"],
    "Ω_m": ["Critical Density", "Second Friedmann Equation", "Cosmological Equation of State"],
    "Ω_Λ": ["Critical Density", "Second Friedmann Equation", "Cosmological Equation of State"],
    "t₀": ["First Friedmann Equation", "Hubble's Law"],
    "g₀": ["Specific Impulse"],
    "π": ["Euler's Identity", "Normal Distribution", "Fourier Transform", "Gaussian Beam Divergence",
          "Coulomb's Law", "Einstein Field Equations"],
    "F": ["Nernst Equation", "Goldman–Hodgkin–Katz Equation"],
}

# ---------------------------------------------------------------- units
# name, symbol, kind, quantity, definition
UNITS = [
    ("metre", "m", "SI base", "length", "Fixed by c = 299 792 458 m s⁻¹ — the distance light travels in 1/299 792 458 s."),
    ("kilogram", "kg", "SI base", "mass", "Fixed by h = 6.626 070 15 × 10⁻³⁴ J s. Since 2019 no physical artefact defines it."),
    ("second", "s", "SI base", "time", "9 192 631 770 periods of the caesium-133 hyperfine transition."),
    ("ampere", "A", "SI base", "electric current", "Fixed by e = 1.602 176 634 × 10⁻¹⁹ C — a flow of 1/e elementary charges per second."),
    ("kelvin", "K", "SI base", "thermodynamic temperature", "Fixed by k_B = 1.380 649 × 10⁻²³ J K⁻¹."),
    ("mole", "mol", "SI base", "amount of substance", "Exactly 6.022 140 76 × 10²³ elementary entities."),
    ("candela", "cd", "SI base", "luminous intensity", "Fixed by K_cd = 683 lm W⁻¹ at 540 THz — the only unit tied to human vision."),

    ("hertz", "Hz", "SI derived", "frequency", "s⁻¹"),
    ("newton", "N", "SI derived", "force", "kg m s⁻²"),
    ("pascal", "Pa", "SI derived", "pressure, stress", "N m⁻² = kg m⁻¹ s⁻²"),
    ("joule", "J", "SI derived", "energy, work, heat", "N m = kg m² s⁻²"),
    ("watt", "W", "SI derived", "power", "J s⁻¹ = kg m² s⁻³"),
    ("coulomb", "C", "SI derived", "electric charge", "A s"),
    ("volt", "V", "SI derived", "electric potential", "W A⁻¹ = kg m² s⁻³ A⁻¹"),
    ("farad", "F", "SI derived", "capacitance", "C V⁻¹"),
    ("ohm", "Ω", "SI derived", "electrical resistance", "V A⁻¹"),
    ("siemens", "S", "SI derived", "electrical conductance", "A V⁻¹ = Ω⁻¹"),
    ("weber", "Wb", "SI derived", "magnetic flux", "V s"),
    ("tesla", "T", "SI derived", "magnetic flux density", "Wb m⁻² = kg s⁻² A⁻¹"),
    ("henry", "H", "SI derived", "inductance", "Wb A⁻¹"),
    ("degree Celsius", "°C", "SI derived", "temperature relative to 273.15 K", "K − 273.15"),
    ("becquerel", "Bq", "SI derived", "radioactivity", "s⁻¹ (one decay per second)"),
    ("gray", "Gy", "SI derived", "absorbed radiation dose", "J kg⁻¹"),
    ("sievert", "Sv", "SI derived", "equivalent radiation dose", "J kg⁻¹, weighted by biological effect"),
    ("radian", "rad", "SI derived", "plane angle", "m/m — dimensionless; 2π in a full turn"),
    ("steradian", "sr", "SI derived", "solid angle", "m²/m² — 4π over a whole sphere"),

    ("minute", "min", "Accepted with SI", "time", "60 s"),
    ("hour", "h", "Accepted with SI", "time", "3600 s"),
    ("day", "d", "Accepted with SI", "time", "86 400 s"),
    ("degree", "°", "Accepted with SI", "plane angle", "π/180 rad"),
    ("litre", "L", "Accepted with SI", "volume", "10⁻³ m³"),
    ("tonne", "t", "Accepted with SI", "mass", "10³ kg"),
    ("electronvolt", "eV", "Accepted with SI", "energy", "1.602 176 634 × 10⁻¹⁹ J (exact) — the currency of particle physics"),
    ("dalton", "Da", "Accepted with SI", "mass", "1.660 539 068 92 × 10⁻²⁷ kg — one twelfth of carbon-12"),

    ("astronomical unit", "au", "Astronomy", "length", "1.495 978 707 × 10¹¹ m (exact) — the Earth–Sun distance"),
    ("parsec", "pc", "Astronomy", "length", "3.085 677 581 × 10¹⁶ m ≈ 3.26 ly"),
    ("light-year", "ly", "Astronomy", "length", "9.460 730 473 × 10¹⁵ m"),
    ("solar mass", "M_☉", "Astronomy", "mass", "1.988 41 × 10³⁰ kg — the standard stellar yardstick"),
    ("jansky", "Jy", "Astronomy", "spectral flux density", "10⁻²⁶ W m⁻² Hz⁻¹ — radio astronomy's unit"),

    ("ångström", "Å", "Other", "length", "10⁻¹⁰ m — roughly one atom across; the unit of crystallography"),
    ("barn", "b", "Other", "cross section", "10⁻²⁸ m² — nuclear cross sections, named for 'big as a barn'"),
    ("bar", "bar", "Other", "pressure", "10⁵ Pa ≈ one atmosphere"),
    ("standard atmosphere", "atm", "Other", "pressure", "101 325 Pa (exact)"),

    ("quetta", "Q", "SI prefix", "10³⁰", "10³⁰"),
    ("ronna", "R", "SI prefix", "10²⁷", "10²⁷"),
    ("yotta", "Y", "SI prefix", "10²⁴", "10²⁴"),
    ("zetta", "Z", "SI prefix", "10²¹", "10²¹"),
    ("exa", "E", "SI prefix", "10¹⁸", "10¹⁸"),
    ("peta", "P", "SI prefix", "10¹⁵", "10¹⁵"),
    ("tera", "T", "SI prefix", "10¹²", "10¹²"),
    ("giga", "G", "SI prefix", "10⁹", "10⁹"),
    ("mega", "M", "SI prefix", "10⁶", "10⁶"),
    ("kilo", "k", "SI prefix", "10³", "10³"),
    ("hecto", "h", "SI prefix", "10²", "10²"),
    ("deca", "da", "SI prefix", "10¹", "10¹"),
    ("deci", "d", "SI prefix", "10⁻¹", "10⁻¹"),
    ("centi", "c", "SI prefix", "10⁻²", "10⁻²"),
    ("milli", "m", "SI prefix", "10⁻³", "10⁻³"),
    ("micro", "µ", "SI prefix", "10⁻⁶", "10⁻⁶"),
    ("nano", "n", "SI prefix", "10⁻⁹", "10⁻⁹"),
    ("pico", "p", "SI prefix", "10⁻¹²", "10⁻¹²"),
    ("femto", "f", "SI prefix", "10⁻¹⁵", "10⁻¹⁵"),
    ("atto", "a", "SI prefix", "10⁻¹⁸", "10⁻¹⁸"),
    ("zepto", "z", "SI prefix", "10⁻²¹", "10⁻²¹"),
    ("yocto", "y", "SI prefix", "10⁻²⁴", "10⁻²⁴"),
    ("ronto", "r", "SI prefix", "10⁻²⁷", "10⁻²⁷"),
    ("quecto", "q", "SI prefix", "10⁻³⁰", "10⁻³⁰"),
]


def main():
    # ---- Constants DB
    c_ds = find_ds("Constants [DB]")
    if not c_ds:
        c_ds = create_db("Constants [DB]", {
            "Name": {"title": {}},
            "Symbol": {"rich_text": {}},
            "Value": {"rich_text": {}},
            "Numeric": {"number": {"format": "number"}},
            "Unit": {"rich_text": {}},
            "Uncertainty": {"rich_text": {}},
            "Exact": {"checkbox": {}},
            "Category": {"select": {"options": [{"name": c} for c in CAT]}},
            "Note": {"rich_text": {}},
        })
        print("created Constants [DB]:", c_ds)
    else:
        print("Constants [DB] exists:", c_ds)

    have = existing_titles(c_ds)
    added = 0
    for name, sym, val, num, unit, unc, exact, cat, note in CONSTANTS:
        if name in have:
            continue
        call("POST", "https://api.notion.com/v1/pages", {
            "parent": {"type": "data_source_id", "data_source_id": c_ds},
            "properties": {
                "Name": {"title": [{"text": {"content": name}}]},
                "Symbol": {"rich_text": [{"text": {"content": sym}}]},
                "Value": {"rich_text": [{"text": {"content": val}}]},
                "Numeric": {"number": num},
                "Unit": {"rich_text": [{"text": {"content": unit}}]},
                "Uncertainty": {"rich_text": [{"text": {"content": unc}}]},
                "Exact": {"checkbox": exact},
                "Category": {"select": {"name": cat}},
                "Note": {"rich_text": [{"text": {"content": note}}]},
            },
        })
        added += 1
    print(f"constants: {added} added, {len(CONSTANTS)} total defined")

    # ---- Units DB
    u_ds = find_ds("Units [DB]")
    if not u_ds:
        kinds = sorted({k for _, _, k, _, _ in UNITS})
        u_ds = create_db("Units [DB]", {
            "Name": {"title": {}},
            "Symbol": {"rich_text": {}},
            "Kind": {"select": {"options": [{"name": k} for k in kinds]}},
            "Quantity": {"rich_text": {}},
            "Definition": {"rich_text": {}},
        })
        print("created Units [DB]:", u_ds)
    else:
        print("Units [DB] exists:", u_ds)

    have_u = existing_titles(u_ds)
    added_u = 0
    for name, sym, kind, qty, defn in UNITS:
        if name in have_u:
            continue
        call("POST", "https://api.notion.com/v1/pages", {
            "parent": {"type": "data_source_id", "data_source_id": u_ds},
            "properties": {
                "Name": {"title": [{"text": {"content": name}}]},
                "Symbol": {"rich_text": [{"text": {"content": sym}}]},
                "Kind": {"select": {"name": kind}},
                "Quantity": {"rich_text": [{"text": {"content": qty}}]},
                "Definition": {"rich_text": [{"text": {"content": defn}}]},
            },
        })
        added_u += 1
    print(f"units: {added_u} added, {len(UNITS)} total defined")
    print("\ndata source ids — add these to scripts/fetch_all.py:")
    print(f'    "constants": "{c_ds}",')
    print(f'    "units": "{u_ds}",')


if __name__ == "__main__":
    main()
