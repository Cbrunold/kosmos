"""Seed fluids and waves — the two shelves the Equations DB was thinnest on
where the rest of the site needs them most.

  FLUIDS (12)  — hydrostatic pressure, Pascal, Archimedes, Newtonian viscosity,
                 Reynolds number, Poiseuille, Stokes' law, Darcy's law, drag,
                 Torricelli, hydraulic power, capillary rise (Jurin). The DB had
                 Bernoulli, continuity, Navier–Stokes and Betz — flow, with no
                 statics beneath it and no viscosity, so Navier–Stokes required
                 nothing on the shelf and tailings, groundwater, settling ponds
                 and hydro turbines had no equation to point at.
  WAVES (7)    — wave speed v = fλ, standing waves, refractive index, thin lens,
                 inverse-square intensity, the Rayleigh criterion, the decibel.
                 Doppler, the speed of sound and the wave equation were already
                 there; they now rest on v = fλ, and cosmological redshift rests
                 on Doppler.

Field values reuse the existing "Fluid Dynamics", "Waves & Optics" and
"Acoustics" rather than adding a "Fluid Statics" — one more field is one more
button, and the domain grouping on the page already puts them together.

Hooks, all through relations that exist: Machines (Pelton ← Torricelli, the
hydro turbines ← hydraulic power, wind turbine ← drag and Reynolds), Skills
(soldering and brazing ← capillary rise; sand casting ← hydrostatic pressure
and Torricelli), Instruments (every telescope ← the Rayleigh criterion). And one
relation that did not exist: Mining Impacts [DB] gets an "Equations" relation
(dual: "Impacts" on the equations side), so acid drainage and drawdown point at
Darcy, tailings and dust at Stokes, dam failure at hydrostatic pressure. build.py
and both templates render it.

Same rules as seed_foundations: years are when the statement was written in
about its present form; Named After only for a person's name; idempotent —
insert missing, backfill empty, union relations, never overwrite; unresolved
names reported, not guessed.

Run on the VPS:  ./deploy.sh seed_fluids_waves seed_glossary
"""
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, query_all, sync_rows, title_of  # noqa: E402
from seed_glossary import find_ds  # noqa: E402

EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"
EQ_DB = "300fc8ac-ca04-429d-a732-406181d9f4b9"
MACHINES_DS = "f6c4e3cc-bfe0-4fb8-b807-3693cbcf4e88"
SKILLS_DS = "804e17aa-435b-4306-acbb-2ec926b87b10"
INSTRUMENTS_DS = "e72fed70-784c-42d2-be1a-3c833ac7fc63"
IMPACTS_TITLE = "Mining Impacts [DB]"    # created by seed_impacts; resolved by title, like fetch_all does

FL = "Fluid Dynamics"
WO = "Waves & Optics"
AC = "Acoustics"

# ------------------------------------------------------------------ equations
# name, equation, field, named after, symbols, significance, year
EQUATIONS = [
    # ---- fluids
    ("Hydrostatic Pressure", "p = p₀ + ρ g h", FL, None,
     "p pressure at depth h · p₀ pressure at the surface · ρ fluid density · g gravitational acceleration · h depth below the surface",
     "Pressure in a still fluid rises with depth by the weight of the column above — about one atmosphere per ten metres of water. Stevin had it in 1586, Pascal made it precise in 1653. It is the load on a tailings dam's face, the pressure a diver feels, the metallostatic head that fills a sand mould, and the p in every fluid equation that follows.", 1653),
    ("Pascal's Principle", "Δp is the same everywhere in a confined fluid  ⇒  F₂/F₁ = A₂/A₁", FL, "Blaise Pascal",
     "Δp a change in pressure applied to an enclosed fluid · F₁, F₂ the forces on two pistons · A₁, A₂ their areas",
     "Push on a confined fluid anywhere and the pressure rises everywhere by the same amount — so a small force on a small piston becomes a large force on a large one. Every hydraulic jack, brake and excavator arm is this. It trades force for distance like a lever, and the work is the same at both ends.", 1653),
    ("Archimedes' Principle", "F_b = ρ_fluid V g", FL, "Archimedes",
     "F_b the buoyant force, upward · ρ_fluid density of the fluid displaced · V volume of fluid displaced · g gravitational acceleration",
     "A body in a fluid is pushed up by the weight of the fluid it displaces — the pressure below it is higher than the pressure above, by exactly that much. It floats if it weighs less than the fluid it would displace, sinks if more. It is why a mineral's specific gravity can be measured by weighing it in air and in water, why ships of steel float, and why hot air rises.", -250),
    ("Newtonian Viscosity", "τ = μ (du/dy)", FL, "Isaac Newton",
     "τ shear stress in the fluid · μ dynamic viscosity, in pascal-seconds · du/dy the velocity gradient across the flow",
     "Newton's hypothesis of 1687: the drag between layers of a fluid sliding past one another is proportional to how fast the velocity changes across them, and the constant is the viscosity. Water's is a millipascal-second, honey's a few thousand times more, air's fifty times less. Fluids that obey it are Newtonian; paint, blood and mud are not, and their viscosity depends on how hard they are pushed.", 1687),
    ("Reynolds Number", "Re = ρ v L / μ", FL, "Osborne Reynolds",
     "Re a dimensionless ratio of inertial to viscous forces · ρ density · v flow speed · L a characteristic length — pipe diameter, blade chord · μ dynamic viscosity",
     "One number decides whether a flow is smooth or turbulent: below about 2,000 in a pipe it is laminar and predictable, above about 4,000 it breaks into eddies. Reynolds watched a thread of dye in a glass tube in 1883 and saw where it happened. It is why a model in a wind tunnel tells you about the full-size aircraft only if Re matches, and why bacteria swim in a world that feels like treacle.", 1883),
    ("Poiseuille's Law", "Q = π r⁴ Δp / (8 μ L)", FL, "Jean Léonard Marie Poiseuille",
     "Q volume flow rate · r pipe radius · Δp pressure drop along the pipe · μ dynamic viscosity · L pipe length",
     "Laminar flow through a pipe goes as the fourth power of the radius: halve the bore and the same pressure moves one-sixteenth the fluid. Poiseuille was a physician measuring blood in glass capillaries in 1840; the law explains why a small narrowing of an artery matters so much, why a hydraulic line is sized as it is, and why a syringe with a fine needle takes so much force.", 1840),
    ("Stokes' Law", "F_d = 6π μ r v;  terminal v = 2 (ρ_p − ρ_f) g r² / (9 μ)", FL, "George Gabriel Stokes",
     "F_d drag on a small sphere moving slowly through a fluid · μ dynamic viscosity · r sphere radius · v its speed · ρ_p, ρ_f particle and fluid density",
     "For a small particle in slow flow, drag is proportional to speed, and a settling particle reaches a terminal velocity that goes as the square of its radius. That is why fine tailings take days to clear a pond and clays may never settle, why dust hangs in air, why sediment sorts itself by grain size, and how a flotation cell and a settling tank are sized. Valid while the Reynolds number stays below about one.", 1851),
    ("Darcy's Law", "Q = −K A (Δh / L)", FL, "Henry Darcy",
     "Q volume flow through a porous medium · K hydraulic conductivity, a property of the rock or soil and the fluid · A cross-section · Δh/L the drop in hydraulic head over the distance L",
     "Groundwater moves down the head gradient at a rate set by how open the rock is. Darcy found it in 1856 sizing sand filters for the fountains of Dijon. It is the equation of a mine's dewatering cone, of how far and how fast acid drainage travels from a waste dump, of the seepage through a tailings dam, and — with a leak coefficient — of every aquifer model.", 1856),
    ("Drag Equation", "F_d = ½ ρ v² C_d A", FL, None,
     "F_d drag force · ρ fluid density · v speed relative to the fluid · C_d drag coefficient, found by experiment · A frontal area",
     "At the speeds of cars, birds and turbine blades drag goes with the square of the speed — twice as fast, four times the force, eight times the power. The drag coefficient sweeps up everything shape and Reynolds number do: about 0.3 for a modern car, 1.0 for a cyclist upright, 0.04 for an aerofoil. Rayleigh gave it this form in 1876; the v² was Newton's.", 1876),
    ("Torricelli's Law", "v = √(2 g h)", FL, "Evangelista Torricelli",
     "v the speed of a jet leaving an opening · g gravitational acceleration · h the height of fluid surface above the opening",
     "Fluid escapes a hole at the speed a stone would reach falling the same height — Torricelli's 1643 result, a century before Bernoulli explained it as energy conservation. It sets the jet speed of a Pelton wheel from its head, the pour rate through a casting sprue, and how long a tank takes to drain.", 1643),
    ("Hydraulic Power", "P = ρ g Q h", FL, None,
     "P power available · ρ water density · g gravitational acceleration · Q volume flow rate · h head: the height the water falls",
     "Head times flow times the weight of water — the power a hydro site can give before turbine and generator losses take their share. A hundred metres of head and a cubic metre a second is about a megawatt. It is potential energy per second, and every dam, mill race and micro-hydro scheme is designed on it.", None),
    ("Capillary Rise", "h = 2 γ cos θ / (ρ g r)", FL, "James Jurin",
     "h height the liquid climbs in a narrow tube · γ surface tension · θ contact angle between liquid and wall · ρ liquid density · g gravitational acceleration · r tube radius",
     "Liquid climbs a narrow gap when it wets the walls, and higher the narrower the gap — Jurin's law of 1718. It draws molten solder and brazing alloy into a joint that fits closely and refuses one that does not, lifts water through soil and up a plant, and wicks ink into paper. When the liquid does not wet, θ passes 90° and it is pushed out instead: mercury in glass.", 1718),

    # ---- waves
    ("Wave Speed", "v = f λ", WO, None,
     "v speed of the wave · f frequency, cycles per second · λ wavelength, the distance between repeats",
     "A wave advances one wavelength every cycle. Fix the speed — sound in air, light in vacuum — and frequency and wavelength are one quantity written two ways: 440 Hz is 78 cm of air, green light is 5.5 × 10¹⁴ Hz. Mersenne measured it for strings in 1636. Doppler, refraction, standing waves and every spectrum on the cosmos page start here.", 1636),
    ("Standing Waves", "f_n = n v / (2L)  (n = 1, 2, 3…)", WO, None,
     "f_n the nth resonant frequency · v wave speed on the string or in the pipe · L its length · n the harmonic number",
     "Confine a wave and only those wavelengths that fit — a whole number of half-waves — survive; the rest cancel. That is why a string, a pipe and a laser cavity have a fundamental and overtones, why a bridge has modes, and why an electron in an atom has discrete energies. Sauveur named the harmonics in 1701.", 1701),
    ("Refractive Index", "n = c / v", WO, None,
     "n refractive index of a medium · c speed of light in vacuum · v speed of light in the medium",
     "Light slows in matter — by a third in glass, a quarter in water, a factor of 2.4 in diamond — and the ratio is the refractive index. Snell's law is the consequence: the wavefront bends where its speed changes. It is why a lens focuses, a prism disperses, a fibre guides, and a diamond sparkles; Huygens explained it with wavefronts in 1678.", 1678),
    ("Thin Lens Equation", "1/f = 1/d_o + 1/d_i", WO, None,
     "f focal length · d_o distance from lens to object · d_i distance from lens to image",
     "Where a lens puts the image of an object, given how strongly it bends light. Halley wrote it in 1693, though the ray tracing goes back to Kepler. It sizes a camera, a telescope's eyepiece, a pair of spectacles and the analyzer's photograph; the same form serves a curved mirror.", 1693),
    ("Inverse-Square Law of Intensity", "I = P / (4π r²)", WO, None,
     "I intensity: power per unit area at distance r · P the source's total power · 4πr² the area of the sphere the power has spread over",
     "Light, sound and gravity spread out over a sphere whose surface grows as the square of the distance, so what reaches you falls as one over that square. Kepler stated it for light in 1604. It is why a star's apparent brightness gives its distance once its luminosity is known — the whole cosmic distance ladder — and why doubling the distance from a lamp quarters the light.", 1604),
    ("Rayleigh Criterion", "θ ≈ 1.22 λ / D", WO, "Lord Rayleigh",
     "θ the smallest angle two points can be apart and still be told apart · λ wavelength · D aperture diameter",
     "The finest detail any telescope, microscope or eye can resolve is set by wavelength over aperture — diffraction, not workmanship, is the floor. It is why telescopes are big, why radio dishes are enormous and get combined into interferometers, why JWST sees sharper in the infrared than Hubble does only because it is larger, and why a microscope cannot show an atom in visible light.", 1879),
    ("Decibel Scale", "L = 10 log₁₀ (I / I₀)", AC, None,
     "L level in decibels · I the intensity being described · I₀ a reference intensity — for sound in air, 10⁻¹² W/m², about the threshold of hearing",
     "Ten times the intensity is ten decibels more; a hundred times, twenty. The scale is logarithmic because hearing is: a hundred-fold range in power sounds like a moderate step. Named for Bell and standardised in 1924, it serves any ratio — a filter's rolloff, an antenna's gain, a signal above its noise.", 1924),
]

# ------------------------------------------------------------------ requires
REQUIRES = {
    # fluids
    "Hydrostatic Pressure": ["Newton's Second Law"],
    "Pascal's Principle": ["Hydrostatic Pressure", "Mechanical Advantage"],
    "Archimedes' Principle": ["Hydrostatic Pressure"],
    "Newtonian Viscosity": ["Derivative"],
    "Reynolds Number": ["Newtonian Viscosity"],
    "Poiseuille's Law": ["Newtonian Viscosity", "Circle: Circumference and Area"],
    "Stokes' Law": ["Newtonian Viscosity", "Archimedes' Principle", "Sphere: Surface and Volume", "Reynolds Number"],
    "Darcy's Law": ["Hydrostatic Pressure", "Gradient"],
    "Drag Equation": ["Kinetic Energy", "Reynolds Number"],
    "Torricelli's Law": ["Bernoulli's Equation", "Kinematic Equations"],
    "Hydraulic Power": ["Power", "Gravitational Potential Energy", "Continuity Equation"],
    "Capillary Rise": ["Hydrostatic Pressure", "Trigonometric Ratios"],
    # existing fluid rows, back onto the new statics and viscosity
    "Bernoulli's Equation": ["Hydrostatic Pressure"],
    "Navier–Stokes Equations": ["Newtonian Viscosity", "Newton's Second Law", "Continuity Equation"],
    "Betz Limit": ["Drag Equation"],
    # waves
    "Standing Waves": ["Wave Speed"],
    "Refractive Index": ["Wave Speed"],
    "Thin Lens Equation": ["Refractive Index", "Small-Angle Approximation"],
    "Inverse-Square Law of Intensity": ["Sphere: Surface and Volume", "Power"],
    "Rayleigh Criterion": ["Small-Angle Approximation", "Diffraction Grating Equation"],
    "Decibel Scale": ["Inverse-Square Law of Intensity"],
    # existing wave rows, back onto v = fλ
    "Doppler Effect": ["Wave Speed"],
    "Wave Equation": ["Wave Speed"],
    "Newton–Laplace Speed of Sound": ["Wave Speed", "Adiabatic Relation"],
    "Snell's Law": ["Refractive Index"],
    "Bragg's Law": ["Wave Speed"],
    "Diffraction Grating Equation": ["Wave Speed"],
    "Gaussian Beam Divergence": ["Small-Angle Approximation", "Wave Speed"],
    "Cosmological Redshift": ["Doppler Effect"],
    "Elastic Wave Equation": ["Wave Equation"],
    "Seismic Wave Speeds": ["Elastic Wave Equation", "Young's Modulus"],
    "De Broglie Wavelength": ["Wave Speed", "Momentum and Impulse"],
    "Planck–Einstein Relation": ["Wave Speed"],
}

# ------------------------------------------------------------------ hooks
MACHINE_EQUATIONS = {
    "Pelton Wheel": ["Torricelli's Law", "Hydraulic Power"],
    "Francis Turbine": ["Hydraulic Power", "Hydrostatic Pressure"],
    "Kaplan Turbine": ["Hydraulic Power", "Hydrostatic Pressure"],
    "Wind Turbine": ["Drag Equation", "Reynolds Number"],
    "Gas Turbine (Jet Engine)": ["Reynolds Number"],
    "Steam Turbine": ["Reynolds Number"],
}
SKILL_EQUATIONS = {
    "Soldering": ["Capillary Rise"],
    "Brazing": ["Capillary Rise"],
    "Sand Casting": ["Hydrostatic Pressure", "Torricelli's Law"],
    "Mixing and Placing Concrete": ["Capillary Rise"],
}
INSTRUMENT_EQUATIONS = {   # every telescope resolves at λ/D; the survey and the CMB mapper too
    "Hubble Space Telescope (HST)": ["Rayleigh Criterion", "Thin Lens Equation"],
    "James Webb Space Telescope (JWST)": ["Rayleigh Criterion"],
    "Very Large Telescope (VLT)": ["Rayleigh Criterion"],
    "Keck Observatory": ["Rayleigh Criterion"],
    "Atacama Large Millimeter/submillimeter Array (ALMA)": ["Rayleigh Criterion", "Wave Speed"],
    "Large Synoptic Survey Telescope (LSST)": ["Rayleigh Criterion", "Inverse-Square Law of Intensity"],
    "Chandra X-ray Observatory": ["Rayleigh Criterion"],
}
IMPACT_EQUATIONS = {
    "Acid mine drainage": ["Darcy's Law"],
    "Water table drawdown": ["Darcy's Law"],
    "Pit lakes and perpetual treatment": ["Darcy's Law", "Hydrostatic Pressure"],
    "Arsenic mobilisation": ["Darcy's Law"],
    "Cyanide release": ["Darcy's Law"],
    "Tailings dam failure": ["Hydrostatic Pressure", "Darcy's Law", "Stokes' Law"],
    "Riverine tailings disposal": ["Stokes' Law"],
    "Dust and particulates": ["Stokes' Law", "Drag Equation"],
    "Silicosis": ["Stokes' Law"],
    "Subsidence": ["Hydrostatic Pressure"],
}


def ensure_impacts_relation(impacts_ds):
    """Impacts.Equations <-> Equations.Impacts, dual. Idempotent."""
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{impacts_ds}")
    if "Equations" in ds["properties"]:
        print("  impacts: Equations relation already exists")
        return
    body = {"properties": {"Equations": {"relation": {"data_source_id": EQ_DS, "type": "dual_property",
                                                       "dual_property": {"synced_property_name": "Impacts"}}}}}
    try:
        call("PATCH", f"https://api.notion.com/v1/data_sources/{impacts_ds}", body)
        print("  impacts: created Equations / Impacts relation")
    except urllib.error.HTTPError as e:
        sys.exit(f"could not create the impacts relation: {e.code} {e.read().decode()[:200]}")


def union_relation(page, prop, ids):
    cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
    new = cur | set(ids)
    return {prop: {"relation": [{"id": x} for x in sorted(new)]}} if new != cur else {}


def link_table(label, ds, table, prop, eq_ids, missing):
    rows = {title_of(p, "Name"): p for p in query_all(ds) if title_of(p, "Name")}
    changed = edges = 0
    for name, eqn in table.items():
        page = rows.get(name)
        if not page:
            missing.add(f"{label}:{name}")
            continue
        ids = [eq_ids[q] for q in eqn if q in eq_ids]
        missing.update(f"{label}:{name} -> {q}" for q in eqn if q not in eq_ids)
        payload = union_relation(page, prop, ids)
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
        edges += len(ids)
    print(f"  {label}: updated {changed} · {edges} links")


def main():
    print("equations")
    schema = ensure_props(EQ_DS, {}, "equations")
    ensure_select_options(EQ_DS, "Field", sorted({e[2] for e in EQUATIONS}), "equations")
    sync_rows(EQ_DS, schema,
              [{"Name": n, "Equation": eq, "Field": f, "Named After": na, "Symbols": sy, "Significance": sig, "Year": y}
               for n, eq, f, na, sy, sig, y in EQUATIONS], "equations")

    print("\nrequires")
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
    if "Requires" not in schema and "Requires" not in ensure_props(EQ_DS, {}, "equations"):
        sys.exit("no Requires relation on the Equations DB — run seed_foundations first")
    missing = set()
    changed = edges = 0
    for name, prereqs in REQUIRES.items():
        page = pages.get(name)
        if not page:
            missing.add(f"Requires:{name}")
            continue
        ids = [pages[q]["id"] for q in prereqs if q in pages]
        missing.update(f"Requires:{name} -> {q}" for q in prereqs if q not in pages)
        payload = union_relation(page, "Requires", ids)
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
        edges += len(ids)
    print(f"  equations: updated {changed} · {edges} requires-edges")

    print("\nhooks")
    eq_ids = {n: p["id"] for n, p in pages.items()}
    link_table("machines", MACHINES_DS, MACHINE_EQUATIONS, "Equations", eq_ids, missing)
    link_table("skills", SKILLS_DS, SKILL_EQUATIONS, "Equations", eq_ids, missing)
    link_table("instruments", INSTRUMENTS_DS, INSTRUMENT_EQUATIONS, "Equations", eq_ids, missing)
    impacts_ds = find_ds(IMPACTS_TITLE)
    if impacts_ds:
        ensure_impacts_relation(impacts_ds)
        link_table("impacts", impacts_ds, IMPACT_EQUATIONS, "Equations", eq_ids, missing)
    else:
        print("  impacts: Mining Impacts [DB] not found — skipped")

    if missing:
        print("\nunresolved names ignored:")
        for m in sorted(missing):
            print("  ", m)
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
