"""Seed the mathematics the physics is written in, and the mechanics it forgot.

Three gaps in the Equations DB, found by reading it (145 rows, 39 fields):

  VECTORS & GEOMETRY   — nothing. Pythagoras was the only geometry on the shelf,
                         yet Gauss's law, Faraday's law, the continuity equation
                         and Poisson's equation are all written with ∇, the Lorentz
                         force and torque with ×, work with ·, and the geodesic
                         equation and FLRW metric with curvature. 13 rows.
  CALCULUS             — the derivative itself, the fundamental theorem, chain
                         rule, Taylor series, and the three theorems (gradient,
                         divergence, Stokes) that turn ∇ from notation into
                         physics. 8 rows.
  MECHANICS            — had two equations, F = ma and gravitation. No kinematics,
                         momentum, work, energy, power, torque, angular momentum,
                         SHM, friction or mechanical advantage — for a site whose
                         Machines and Skills pages rest on exactly those. 18 rows.

And one new relation, REQUIRES: "you need X to read Y". Different in kind from
Related (a loose web of neighbours): this is a dependency graph. It is a dual
self-relation on the Equations DB — Requires on one side, Required By synced on
the other — so F = ma lists what it leans on and the derivative lists what leans
on it. Edges run both between the new rows and from existing equations back to
their new prerequisites; a handful join two rows that were both already present
(Fourier Transform requires Euler's Identity).

Years are when the statement was first written down in something like its
present form, not when the idea was first had, and the significance text says
which when the two differ (Archimedes had torque; Gibbs wrote r × F). Named
After is filled only where the name is a person's.

Idempotent, like the other seeds: inserts missing rows, backfills only empty
fields, unions relations, never overwrites anything a human set. Reports any
name it could not resolve rather than guessing.

Run on the VPS:  ./deploy.sh seed_foundations
"""
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, query_all, sync_rows, title_of  # noqa: E402

EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"
EQ_DB = "300fc8ac-ca04-429d-a732-406181d9f4b9"   # Equations [DB] database, for the fallback endpoint (see link_elements.py)
MACHINES_DS = "f6c4e3cc-bfe0-4fb8-b807-3693cbcf4e88"
SKILLS_DS = "804e17aa-435b-4306-acbb-2ec926b87b10"

VG = "Vectors & Geometry"
CA = "Calculus"
ME = "Mechanics"

# ------------------------------------------------------------------ equations
# name, equation, field, named after, symbols, significance, year
EQUATIONS = [
    # ---- vectors & geometry
    ("Vector Magnitude", "|v| = √(v_x² + v_y² + v_z²)", VG, None,
     "v a vector · v_x, v_y, v_z its components along three perpendicular axes · |v| its length, a plain number",
     "Pythagoras applied twice, and the first thing you do with any quantity that has a direction — velocity, force, field. Everything on this site that reads r² in a denominator, from gravitation to Coulomb's law, is this: the squared length of the vector from source to point. Written in Gibbs's notation of 1881; the geometry is 2,400 years older.", 1881),
    ("Dot Product", "a · b = |a| |b| cos θ = a_x b_x + a_y b_y + a_z b_z", VG, None,
     "a, b two vectors · θ the angle between them · a · b a number, not a vector: how much of one lies along the other",
     "The overlap of two directions. Zero when they are perpendicular, largest when aligned, negative when opposed — which is why work is F · d and not F times d: a force at right angles to the motion does nothing. The component form on the right is what a computer calculates; the cosine form is what it means.", 1881),
    ("Cross Product", "|a × b| = |a| |b| sin θ, direction ⊥ to both by the right-hand rule", VG, None,
     "a, b two vectors · θ the angle between them · a × b a third vector, perpendicular to the plane of the first two, with the area of their parallelogram as its length",
     "The turning quantity. Torque is r × F, angular momentum r × p, the magnetic force qv × B — every time a physical effect points at right angles to its causes, this is the operation. Largest when the two are perpendicular and zero when parallel, which is why pushing straight along a wrench handle turns nothing. Its components are a determinant.", 1881),
    ("Vector Projection", "proj_b a = (a · b / |b|²) b,  |proj_b a| = |a| cos θ", VG, None,
     "a the vector being projected · b the direction projected onto · proj_b a the shadow a casts along b",
     "How much of a force acts along a slope, how much of a velocity is toward the observer, how much of a field crosses a surface — every 'component along' in physics is a projection, and the dot product does the work. The redshift a spectrograph measures is the projection of a galaxy's velocity onto the line of sight; the rest is invisible to it.", 1881),
    ("Trigonometric Ratios", "sin θ = opp/hyp,  cos θ = adj/hyp,  tan θ = opp/adj,  sin²θ + cos²θ = 1", VG, None,
     "θ an angle in a right triangle · opp, adj the sides opposite and adjacent to it · hyp the hypotenuse",
     "The dictionary between angles and lengths. Snell's law, Bragg's law and the diffraction grating are each one line of trigonometry; so is resolving a force on an incline or laying out a roof pitch. Hipparchus tabulated chords around 150 BCE; the sine as we write it came from India in the fifth century and reached Europe through Arabic. The identity on the right is Pythagoras again.", -150),
    ("Law of Cosines", "c² = a² + b² − 2ab cos C", VG, None,
     "a, b, c the three sides of any triangle · C the angle opposite side c",
     "Pythagoras for triangles that are not right-angled: the correction term vanishes when C = 90°. It is what a surveyor uses to close a triangle from two sides and the included angle, what a navigator uses for a course change, and what the dot product's cosine form is a restatement of. Euclid proved it geometrically in the Elements; al-Kashi wrote it with a cosine in 1427.", -300),
    ("Circle: Circumference and Area", "C = 2πr,  A = πr²", VG, None,
     "r radius · C circumference · A area · π the ratio of any circle's circumference to its diameter, 3.14159…",
     "Archimedes squeezed π between 3 10/71 and 3 1/7 by fitting 96-sided polygons inside and outside a circle, and showed the area equals that of a right triangle with the radius and circumference as its legs — the first rigorous calculation of a curved figure. On a lathe the cutting speed is π × diameter × rpm; every wheel, pulley and orbit begins here.", -250),
    ("Sphere: Surface and Volume", "A = 4πr²,  V = (4/3)πr³", VG, None,
     "r radius · A surface area · V volume",
     "The result Archimedes asked to have carved on his tomb: a sphere has two-thirds the volume and two-thirds the surface of the cylinder that just contains it. The 4πr² is why every inverse-square law is inverse-square — light, gravity and electric flux spread over a spherical shell whose area grows as r². The r³ is why a planet's mass, and its gravity, are set by its radius cubed.", -225),
    ("Arc Length and Radians", "s = rθ  (θ in radians; 2π rad = 360°)", VG, None,
     "s length along the arc · r radius · θ the angle subtended, measured as arc length over radius — a pure number",
     "An angle is a ratio, not a count of degrees: the arc it cuts from a circle divided by the radius. That is what makes sin θ ≈ θ true for small angles, ω = v/r hold without a conversion factor, and every equation with a frequency in it come out in the right units. Roger Cotes saw in 1714 that this was the natural measure; the word 'radian' arrived in 1873.", 1714),
    ("Solid Angle", "Ω = A/r²  (a full sphere subtends 4π steradians)", VG, None,
     "Ω solid angle in steradians · A the area cut from a sphere of radius r centred on the vertex",
     "The radian's three-dimensional cousin: how much of the sky something fills, as the area it covers on a sphere over the radius squared. Gauss's law is the statement that a point charge's flux through any closed surface is the same 4π worth of solid angle; a telescope's field of view, a lamp's output in candela, and the fraction of a star's light a planet intercepts are all solid angles.", 1760),
    ("Determinant", "det [a b; c d] = ad − bc;  det of 3×3 = a(ei − fh) − b(di − fg) + c(dh − eg)", VG, None,
     "a…i the entries of a square matrix · det a single number: the signed area (2×2) or volume (3×3) spanned by the rows",
     "The scale factor of a linear map — how much a transformation stretches area or volume, with a sign for whether it flips orientation. Zero means the map squashes space flat and cannot be undone. The cross product is a 3×3 determinant; the Jacobian in every change of variables is one; the volume of a crystal's unit cell is the determinant of its three lattice vectors. Seki Takakazu had it in 1683, Leibniz independently a decade later.", 1683),
    ("Euler's Polyhedron Formula", "V − E + F = 2", VG, "Leonhard Euler",
     "V, E, F the numbers of vertices, edges and faces of any convex polyhedron",
     "Count the corners, edges and faces of a cube (8, 12, 6), a tetrahedron (4, 6, 4) or a soccer ball (60, 90, 32) and the same 2 comes out every time. It does not care about lengths or angles — only how the pieces connect — which made it the first theorem of topology. It is why there are exactly five Platonic solids, and it constrains every crystal habit on the minerals page: a form's faces and edges must obey it.", 1752),
    ("Curvature", "κ = 1/R;  for a curve y(x): κ = |y″| / (1 + y′²)^(3/2)", VG, None,
     "κ curvature · R the radius of the circle that best fits the curve at that point · y′, y″ the first and second derivatives",
     "How sharply a path bends: the reciprocal of the radius of the circle that hugs it. A straight line has zero, a tight corner a lot. Huygens needed it in 1673 to make a pendulum keep exact time; a road engineer needs it to bank a bend; general relativity generalises it to spacetime, where curvature is what gravity is — the geodesic equation and the FLRW metric are curvature statements. Gauss showed a surface's curvature can be measured from within it, without leaving.", 1673),

    # ---- calculus
    ("Derivative", "f′(x) = df/dx = lim_{h→0} [f(x+h) − f(x)] / h", CA, None,
     "f a function · f′ or df/dx its rate of change · h a step that shrinks to nothing",
     "The slope of a curve at a single point, obtained by taking the slope over an ever-smaller step. Velocity is the derivative of position, acceleration of velocity, current of charge, power of work; almost every law of physics on this site is a statement about a derivative. Newton had it in 1665 as fluxions; the notation that survived is Leibniz's, from 1675.", 1675),
    ("Fundamental Theorem of Calculus", "∫_a^b f′(x) dx = f(b) − f(a)", CA, None,
     "f′ a rate of change · ∫_a^b … dx the total accumulated between a and b · f(b) − f(a) the net change",
     "Adding up a rate of change over an interval gives the total change — so integration undoes differentiation, and the area under a velocity graph is the distance travelled. Barrow had the geometric version in 1670; his student Newton and, separately, Leibniz turned it into a method. Kinematics, the rocket equation and every 'work is the integral of force' rest on it.", 1670),
    ("Chain Rule", "d/dx f(g(x)) = f′(g(x)) · g′(x)", CA, None,
     "f, g two functions, one applied to the other · f′, g′ their derivatives",
     "Rates multiply through a chain of dependence: if pressure depends on depth and depth on time, the rate of pressure change is the product of the two rates. It is what turns dv/dt into v dv/dx (the origin of ½mv²), lets the heat equation be solved by substitution, and makes every physical derivative computable rather than merely defined.", 1676),
    ("Taylor Series", "f(x) = Σ_{n=0}^∞ f⁽ⁿ⁾(a) (x − a)ⁿ / n!", CA, "Brook Taylor",
     "f a smooth function · f⁽ⁿ⁾(a) its nth derivative at the point a · n! n factorial",
     "Any smooth function, rebuilt near a point from its derivatives there: a constant, plus a slope, plus a curvature, and so on. Keep one term and you have linear approximation; keep them all and e^x, sin x and cos x become polynomials — which is how Euler's identity is proved. It is the machinery behind every 'for small x' in physics, from the pendulum to the low-speed limit of relativity.", 1715),
    ("Small-Angle Approximation", "sin θ ≈ θ,  tan θ ≈ θ,  cos θ ≈ 1 − θ²/2  (θ in radians, θ ≪ 1)", CA, None,
     "θ an angle in radians, small compared with 1",
     "The first terms of three Taylor series, and the reason the simple pendulum has a simple period, a lens has a focal length, and a diffraction pattern has evenly spaced fringes. At 10° the error in sin θ ≈ θ is half a percent; at 30° it is 5 %. Every one of those results is exact only in the limit, and the honest ones say so.", None),
    ("Gradient", "∇f = (∂f/∂x, ∂f/∂y, ∂f/∂z)", CA, None,
     "f a scalar field — a number at every point, like temperature or pressure · ∇f a vector at every point, pointing uphill, with the slope as its length",
     "Where a field rises fastest, and how fast. Heat flows down the temperature gradient (Fourier's law), water down the pressure gradient, and a conservative force is minus the gradient of its potential energy — F = −∇U — which is what makes a ball roll downhill. Hamilton introduced the ∇ symbol in 1837; the vector reading of it is Gibbs's.", 1853),
    ("Divergence Theorem", "∮_S F · dA = ∫_V (∇ · F) dV", CA, "Carl Friedrich Gauss",
     "F a vector field · S a closed surface enclosing the volume V · dA an outward-pointing patch of surface · ∇ · F the divergence: net outflow per unit volume at a point",
     "What flows out through a closed surface equals what is created inside it. That single sentence is Gauss's law for electricity (flux out equals charge within), Gauss's law for magnetism (no flux, no monopoles) and the continuity equation of fluid flow. It is the fundamental theorem of calculus in three dimensions: an integral over a boundary traded for one over the interior.", 1813),
    ("Stokes' Theorem", "∮_C F · dl = ∫_S (∇ × F) · dA", CA, "George Gabriel Stokes",
     "F a vector field · C a closed loop bounding the surface S · dl a step along the loop · ∇ × F the curl: how much the field circulates about a point",
     "The circulation around a loop equals the curl through any surface it bounds. Faraday's law of induction is this theorem applied to a changing magnetic field; the Ampère–Maxwell law is it applied to current. Kelvin set it as an exam question in a letter to Stokes in 1850, and Stokes put it on the Smith's Prize paper in 1854 — Maxwell was among those who sat it.", 1854),

    # ---- mechanics
    ("Kinematic Equations", "v = v₀ + at,  s = v₀t + ½at²,  v² = v₀² + 2as", ME, None,
     "s displacement · v₀, v initial and final velocity · a constant acceleration · t time",
     "Motion under a steady push, from a dropped stone to a car braking. Galileo got them from a ball rolling down an incline in 1638; the Merton scholars had the mean-speed rule three centuries earlier. Each is the fundamental theorem of calculus applied once or twice to a constant, and they fail the moment the acceleration is not constant — for that you need F = ma and a differential equation.", 1638),
    ("Newton's Third Law", "F_AB = −F_BA", ME, "Isaac Newton",
     "F_AB the force body A exerts on body B · F_BA the force B exerts back on A: equal in size, opposite in direction",
     "Forces come in pairs, and the pair acts on two different bodies — which is why they never cancel. A rocket goes up because it pushes exhaust down; a jet engine and a swimmer work the same way. It is the reason momentum is conserved: the two forces in a pair change the two momenta by equal and opposite amounts.", 1687),
    ("Momentum and Impulse", "p = mv,  J = F Δt = Δp", ME, None,
     "p momentum, a vector · m mass · v velocity · J impulse: a force F acting for a time Δt, equal to the change in momentum it produces",
     "Newton wrote his second law as the rate of change of this 'quantity of motion', not as F = ma — and his form is the one that survives relativity. Impulse is why a crumple zone works: the same momentum change spread over a longer time is a smaller force. Specific impulse, the rocket engineer's figure of merit, is impulse per unit of propellant.", 1687),
    ("Conservation of Momentum", "Σ p_before = Σ p_after  (no external force)", ME, None,
     "Σ p the vector sum of the momenta of everything in the system",
     "In any collision, explosion or separation, the total momentum before equals the total after — Wallis, Wren and Huygens each derived it for the Royal Society in 1668, twenty years before the Principia. It follows from the third law and is what makes a rocket work in vacuum: exhaust goes one way, the ship the other, and the sum stays what it was. Noether's theorem later showed it is the symmetry of space under translation.", 1668),
    ("Work", "W = F · d = ∫ F · ds", ME, None,
     "W work, in joules · F force · d displacement, or ds a step along the path · F · d the dot product: only the component of force along the motion counts",
     "Force times the distance moved along it. Carry a suitcase across a level floor and you do no work on it, however tired you are; lift it a metre and you do. Coriolis gave the quantity its name and its ½mv² partner in 1829. It is what a heat engine delivers, what a pulley system trades force against, and what an integral of force along a path always means.", 1829),
    ("Kinetic Energy", "K = ½mv²", ME, None,
     "K kinetic energy, in joules · m mass · v speed",
     "The energy of motion. Leibniz's vis viva of 1686 was mv²; the half arrived when Coriolis matched it to work in 1829, so that the work done accelerating a body equals exactly this. It is quadratic in speed, which is why a car at 100 km/h has four times the stopping energy of one at 50, and why the wind's power goes as the cube of its speed — this, times the mass arriving per second.", 1829),
    ("Work–Energy Theorem", "W_net = ΔK = ½mv² − ½mv₀²", ME, None,
     "W_net the net work done on a body by all forces · ΔK its change in kinetic energy",
     "Net work in equals kinetic energy out — the bookkeeping that ties force to motion without solving for the motion in between. It falls out of F = ma and the chain rule in three lines and is the fastest way to find a speed at the bottom of a hill, a projectile's launch speed, or a bullet's energy from the depth of a hole.", 1829),
    ("Gravitational Potential Energy", "U = mgh  (near a surface);  U = −GMm/r  (in general)", ME, None,
     "U potential energy · m the mass raised · g the local gravitational acceleration · h height above a chosen zero · G the gravitational constant · M the attracting mass · r distance between centres",
     "Energy stored by position in a gravitational field: what a raised weight, a reservoir behind a dam or a satellite in a high orbit can give back. The mgh form is the −GMm/r form linearised near a planet's surface. Rankine named it in 1853. Hydroelectric turbines run on the first form; escape velocity and the vis-viva equation on the second.", 1853),
    ("Conservation of Mechanical Energy", "K + U = constant  (no friction or other dissipation)", ME, None,
     "K kinetic energy · U potential energy · their sum unchanged as one turns into the other",
     "A pendulum trades height for speed and back; a roller coaster the same; a comet the same over centuries. Helmholtz stated the general principle in 1847 — that when the sum seems to fall, the difference has gone into heat — and it became the first law of thermodynamics. Bernoulli's equation is this per unit volume of a flowing fluid.", 1847),
    ("Power", "P = dW/dt = F · v", ME, None,
     "P power, in watts · W work · t time · F force · v velocity",
     "How fast work is done. Watt needed a number to sell engines against horses and settled on 550 foot-pounds per second in 1782; the SI named its unit after him. An engine's power, not its force, sets how quickly it climbs a hill; a turbine's rating is this figure; and the same equation shows why towing at speed costs more than towing slowly.", 1782),
    ("Torque", "τ = r × F,  |τ| = r F sin θ", ME, None,
     "τ torque, a vector along the axis of rotation · r the lever arm from the axis to where the force acts · F the force · θ the angle between them",
     "The turning effect of a force: bigger with a longer arm and a force at right angles to it, zero when you push along the arm. Archimedes had the law of the lever in 250 BCE; the vector form with the cross product is Gibbs's. It is what a motor delivers to its shaft, what a tap wrench applies to a thread, and what a wheel nut is torqued to.", -250),
    ("Moment of Inertia", "I = Σ m_i r_i² = ∫ r² dm", ME, None,
     "I moment of inertia · m_i a bit of mass at distance r_i from the axis · the sum or integral over the whole body",
     "The rotational counterpart of mass: how hard a body is to spin up, set not just by how much mass it has but by how far from the axis it sits — hence the square. Euler defined it in 1765. A flywheel puts its mass at the rim for exactly this reason; a figure skater pulls arms in to spin faster; a hollow shaft is nearly as stiff in torsion as a solid one for a fraction of the weight.", 1765),
    ("Angular Momentum", "L = r × p = Iω;  dL/dt = τ", ME, None,
     "L angular momentum · r position from the axis · p linear momentum · I moment of inertia · ω angular velocity · τ net torque",
     "What a spinning or orbiting body keeps unless a torque acts on it. Kepler's second law — equal areas in equal times — is its conservation for a planet, seen eighty years before Newton explained why. It is why a gyroscope holds its axis, why a collapsing star spins up into a pulsar, and why a turbine's blades are shaped to change the working fluid's angular momentum as it passes.", 1775),
    ("Centripetal Acceleration", "a = v²/r = ω²r,  directed toward the centre", ME, None,
     "a the acceleration of anything moving on a circle · v its speed · r the circle's radius · ω its angular velocity",
     "Turning is accelerating, even at constant speed, because the direction of the velocity changes — and the acceleration points inward. Huygens derived it in 1659 and Newton used it to link the Moon's orbit to a falling apple: set it equal to GM/r² and Kepler's third law follows. It is also the load on a spinning flywheel and the reason a centrifuge separates.", 1673),
    ("Simple Harmonic Motion", "d²x/dt² = −ω²x  ⇒  x = A cos(ωt + φ),  ω = √(k/m)", ME, None,
     "x displacement from equilibrium · ω angular frequency · A amplitude · φ phase · k the restoring stiffness (Hooke's law) · m mass",
     "Whenever the restoring force is proportional to the displacement, the motion is a sinusoid with a period that does not depend on how big the swing is. A mass on a spring, a pendulum at small angles, a plucked string, an atom in a crystal lattice, an LC circuit — the same equation, and near any stable equilibrium every system looks like this to first order. That universality is why the sine wave is everywhere.", 1678),
    ("Pendulum Period", "T = 2π √(L/g)  (small swings)", ME, None,
     "T the period of one full swing · L the length from pivot to centre of mass · g the local gravitational acceleration",
     "The period depends on the length and on gravity — not on the mass, and, for small swings, not on the amplitude. Galileo noticed the last in 1602; Huygens made a clock of it in 1657 and derived the formula in 1673. It is the small-angle approximation applied to SHM, and it made g measurable to four figures with a string and a stone.", 1673),
    ("Friction", "F_f ≤ μ_s N  (static),  F_f = μ_k N  (sliding)", ME, "Guillaume Amontons",
     "F_f the friction force · N the normal force pressing the surfaces together · μ_s, μ_k the coefficients of static and kinetic friction, properties of the pair of surfaces",
     "Friction is proportional to the load and independent of the contact area — Amontons's laws of 1699, which da Vinci had in his notebooks two centuries earlier and Coulomb refined in 1785. Static friction is what a knot, a masonry anchor and a clutch rely on; kinetic friction is what a brake pad and a bearing pay. The coefficients are empirical, and the honest tables give ranges.", 1699),
    ("Mechanical Advantage", "MA = F_out / F_in = d_in / d_out  (ideal)", ME, None,
     "MA mechanical advantage · F_in, F_out the force applied and the force delivered · d_in, d_out the distances each moves",
     "A lever, a pulley block, a screw or a gear train trades force for distance, and the product — the work — stays the same. A four-part tackle lifts with a quarter of the effort and hauls four times the rope. Archimedes claimed he could move the Earth with a long enough lever; the catch is how far the other end has to travel. Friction eats into the ideal figure, and rigging tables say by how much.", -250),
]

# ------------------------------------------------------------------ requires
# equation -> the equations you need to read it. New rows and existing ones alike;
# every name is resolved against the live DB and unresolved ones are reported.
REQUIRES = {
    # geometry and vectors, on each other
    "Vector Magnitude": ["Pythagorean Theorem"],
    "Dot Product": ["Vector Magnitude", "Trigonometric Ratios"],
    "Cross Product": ["Vector Magnitude", "Trigonometric Ratios", "Determinant"],
    "Vector Projection": ["Dot Product"],
    "Law of Cosines": ["Pythagorean Theorem", "Trigonometric Ratios"],
    "Arc Length and Radians": ["Circle: Circumference and Area"],
    "Solid Angle": ["Sphere: Surface and Volume", "Arc Length and Radians"],
    "Curvature": ["Derivative", "Circle: Circumference and Area"],
    # calculus
    "Fundamental Theorem of Calculus": ["Derivative"],
    "Chain Rule": ["Derivative"],
    "Taylor Series": ["Derivative"],
    "Small-Angle Approximation": ["Taylor Series", "Arc Length and Radians"],
    "Gradient": ["Derivative"],
    "Divergence Theorem": ["Gradient", "Fundamental Theorem of Calculus", "Dot Product"],
    "Stokes' Theorem": ["Gradient", "Cross Product", "Fundamental Theorem of Calculus"],
    # mechanics
    "Kinematic Equations": ["Derivative", "Fundamental Theorem of Calculus"],
    "Momentum and Impulse": ["Vector Magnitude"],
    "Conservation of Momentum": ["Momentum and Impulse", "Newton's Third Law"],
    "Work": ["Dot Product", "Fundamental Theorem of Calculus"],
    "Kinetic Energy": ["Work", "Kinematic Equations"],
    "Work–Energy Theorem": ["Work", "Kinetic Energy", "Chain Rule"],
    "Gravitational Potential Energy": ["Work"],
    "Conservation of Mechanical Energy": ["Kinetic Energy", "Gravitational Potential Energy"],
    "Power": ["Work", "Derivative"],
    "Torque": ["Cross Product"],
    "Angular Momentum": ["Cross Product", "Momentum and Impulse", "Moment of Inertia"],
    "Centripetal Acceleration": ["Vector Magnitude", "Derivative"],
    "Simple Harmonic Motion": ["Hooke's Law", "Derivative", "Trigonometric Ratios"],
    "Pendulum Period": ["Simple Harmonic Motion", "Small-Angle Approximation", "Arc Length and Radians"],
    "Mechanical Advantage": ["Work"],
    # existing equations, back to their prerequisites
    "Newton's Second Law": ["Momentum and Impulse", "Derivative"],
    "Law of Universal Gravitation": ["Vector Magnitude", "Sphere: Surface and Volume"],
    "Kepler's Second Law": ["Angular Momentum"],
    "Kepler's Third Law": ["Centripetal Acceleration", "Law of Universal Gravitation"],
    "Escape Velocity": ["Conservation of Mechanical Energy", "Gravitational Potential Energy"],
    "Vis-Viva Equation": ["Conservation of Mechanical Energy"],
    "Cauchy's Stress Theorem": ["Dot Product"],
    "Coulomb's Law": ["Vector Magnitude", "Sphere: Surface and Volume"],
    "Electric Field": ["Vector Magnitude"],
    "Gauss's Law": ["Divergence Theorem", "Solid Angle"],
    "Gauss's Law for Magnetism": ["Divergence Theorem"],
    "Faraday's Law of Induction": ["Stokes' Theorem"],
    "Ampère–Maxwell Law": ["Stokes' Theorem"],
    "Poisson's Equation": ["Gradient"],
    "Lorentz Force": ["Cross Product"],
    "Continuity Equation": ["Divergence Theorem"],
    "Fourier's Law of Heat Conduction": ["Gradient"],
    "Heat Equation": ["Gradient", "Chain Rule"],
    "Newton's Law of Cooling": ["Derivative"],
    "Bernoulli's Equation": ["Conservation of Mechanical Energy"],
    "Betz Limit": ["Kinetic Energy", "Continuity Equation"],
    "Tsiolkovsky Rocket Equation": ["Conservation of Momentum", "Fundamental Theorem of Calculus"],
    "Specific Impulse": ["Momentum and Impulse"],
    "Snell's Law": ["Trigonometric Ratios"],
    "Bragg's Law": ["Trigonometric Ratios"],
    "Diffraction Grating Equation": ["Trigonometric Ratios", "Small-Angle Approximation"],
    "Euler's Identity": ["Taylor Series"],
    "Fourier Transform": ["Euler's Identity"],
    "Radioactive Decay Law": ["Derivative"],
    "Half-Life": ["Radioactive Decay Law"],
    "Elastic Wave Equation": ["Derivative"],
    "Wave Equation": ["Derivative"],
    "Geodesic Equation": ["Curvature"],
    "FLRW Metric": ["Curvature"],
    "Einstein Field Equations": ["Curvature"],
    "Euler–Lagrange Equation": ["Derivative", "Fundamental Theorem of Calculus"],
    "Schrödinger Equation": ["Derivative"],
}

# ------------------------------------------------------------------ hooks into the engineering half
# machine / skill -> new equations, via the "Equations" relation those DBs already have
MACHINE_EQUATIONS = {
    "Brushed DC Motor": ["Torque", "Power"],
    "Induction Motor": ["Torque", "Power"],
    "Brushless Permanent-Magnet Motor": ["Torque", "Power"],
    "Alternator": ["Torque", "Power"],
    "Otto Four-Stroke Engine": ["Torque", "Moment of Inertia"],
    "Diesel Engine": ["Torque", "Moment of Inertia"],
    "Stirling Engine": ["Moment of Inertia"],
    "Watt Steam Engine": ["Power", "Torque"],
    "Steam Turbine": ["Angular Momentum", "Torque"],
    "Gas Turbine (Jet Engine)": ["Newton's Third Law", "Conservation of Momentum", "Angular Momentum"],
    "Pelton Wheel": ["Kinetic Energy", "Gravitational Potential Energy", "Angular Momentum"],
    "Francis Turbine": ["Gravitational Potential Energy", "Angular Momentum"],
    "Kaplan Turbine": ["Gravitational Potential Energy", "Angular Momentum"],
    "Wind Turbine": ["Kinetic Energy", "Power"],
    "Solid-Propellant Rocket Motor": ["Newton's Third Law", "Conservation of Momentum", "Momentum and Impulse"],
    "Liquid-Propellant Rocket Engine": ["Newton's Third Law", "Conservation of Momentum", "Momentum and Impulse"],
}
SKILL_EQUATIONS = {
    "Rigging a Load with Pulleys": ["Mechanical Advantage", "Work", "Friction"],
    "Essential Knots": ["Friction"],
    "Anchoring into Masonry": ["Friction"],
    "Squaring with the 3-4-5 Rule": ["Trigonometric Ratios", "Law of Cosines"],
    "Turning on a Lathe": ["Circle: Circumference and Area", "Torque"],
    "Tapping a Thread": ["Torque", "Mechanical Advantage"],
    "Sharpening an Edge": ["Friction"],
}


def ensure_requires_relation():
    """Create Requires as a dual self-relation (synced half: Required By). Idempotent."""
    ds = call("GET", f"https://api.notion.com/v1/data_sources/{EQ_DS}")
    if "Requires" in ds["properties"]:
        print("  Requires relation already exists")
        return
    for endpoint, body in [
        (f"https://api.notion.com/v1/data_sources/{EQ_DS}",
         {"properties": {"Requires": {"relation": {"data_source_id": EQ_DS, "type": "dual_property",
                                                    "dual_property": {"synced_property_name": "Required By"}}}}}),
        (f"https://api.notion.com/v1/databases/{EQ_DB}",
         {"properties": {"Requires": {"relation": {"database_id": EQ_DB, "type": "dual_property",
                                                    "dual_property": {"synced_property_name": "Required By"}}}}}),
    ]:
        try:
            call("PATCH", endpoint, body)
            print("  created Requires / Required By via", endpoint.split("/v1/")[1].split("/")[0])
            return
        except urllib.error.HTTPError as e:
            print("  attempt failed:", e.code, e.read().decode()[:200])
    sys.exit("could not create the Requires relation — stopping before any linking")


def union_relation(page, prop, ids):
    """Payload that unions ids into page's relation prop, or {} if nothing new."""
    cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
    new = cur | set(ids)
    return {prop: {"relation": [{"id": x} for x in sorted(new)]}} if new != cur else {}


def main():
    print("equations")
    schema = ensure_props(EQ_DS, {}, "equations")
    ensure_select_options(EQ_DS, "Field", sorted({e[2] for e in EQUATIONS}), "equations")
    sync_rows(EQ_DS, schema,
              [{"Name": n, "Equation": eq, "Field": f, "Named After": na, "Symbols": sy, "Significance": sig, "Year": y}
               for n, eq, f, na, sy, sig, y in EQUATIONS], "equations")

    print("\nrequires")
    ensure_requires_relation()
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
    missing = set()
    changed = edges = 0
    for name, prereqs in REQUIRES.items():
        page = pages.get(name)
        if not page:
            missing.add(f"Requires:{name}")
            continue
        ids = []
        for q in prereqs:
            if q in pages:
                ids.append(pages[q]["id"])
            else:
                missing.add(f"Requires:{name} -> {q}")
        payload = union_relation(page, "Requires", ids)
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
        edges += len(ids)
    print(f"  equations: updated {changed} · {edges} requires-edges (Required By fills in by itself)")

    print("\nmachines and skills")
    eq_ids = {n: p["id"] for n, p in pages.items()}
    for label, ds, table in (("machines", MACHINES_DS, MACHINE_EQUATIONS), ("skills", SKILLS_DS, SKILL_EQUATIONS)):
        rows = {title_of(p, "Name"): p for p in query_all(ds) if title_of(p, "Name")}
        changed = edges = 0
        for name, eqn in table.items():
            page = rows.get(name)
            if not page:
                missing.add(f"{label}:{name}")
                continue
            ids = [eq_ids[q] for q in eqn if q in eq_ids]
            missing.update(f"{label}:{name} -> {q}" for q in eqn if q not in eq_ids)
            payload = union_relation(page, "Equations", ids)
            if payload:
                call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
            edges += len(ids)
        print(f"  {label}: updated {changed} · {edges} links")

    if missing:
        print("\nunresolved names ignored:")
        for m in sorted(missing):
            print("  ", m)
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
