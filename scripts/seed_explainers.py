"""Create and seed Explainers [DB]: the people, channels and organisations that
explain the science the rest of the site catalogues.

Deliberately NOT the Researchers DB. That one is 188 historical scientists with
lifespans and relations into Theories, Discoveries, Timeline and Machines —
people who did the work. This is people who explain the work, and two thirds of
them are not people at all: Veritasium is a channel, BlueDot Impact is an
organisation running a course. Kind tells them apart.

Like the glossary, what this does NOT store is what each one covers in terms the
site already defines: build.py matches the Covers prose against every glossary
term and computes those chips at build time, and the same match puts each
explainer under the terms it covers on /glossary. Add a term in Notion and the
explainers that talk about it find it themselves.

Idempotent: creates the database if missing, backfills empty fields, never
overwrites an edit someone has made in Notion.
Run on the VPS:  ./deploy.sh seed_explainers
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_glossary import find_ds  # noqa: E402
from seed_theories import call, ensure_props, ensure_select_options, sync_rows  # noqa: E402

PARENT_PAGE = "278879ef-bfcb-46e1-bdfb-7f9beb7b7197"   # Physical Sciences
TITLE = "Explainers [DB]"

KINDS = ["Person", "Channel", "Organisation"]
FIELDS = ["Physics", "Astronomy & Cosmology", "Chemistry", "Earth & Mining",
          "Engineering", "Workshop", "Mathematics", "General science", "AI safety"]
MEDIA = ["YouTube", "Podcast", "Book", "Course", "Blog", "Lectures"]

# name, kind, field, media, behind it, covers, url
#
# "Covers" is prose on purpose: it is what the glossary traces, so it should read
# like a sentence and name the concepts plainly rather than list keywords.
EXPLAINERS = [
    # ---- physics & cosmology
    ("Sean Carroll", "Person", "Astronomy & Cosmology", ["Podcast", "Book", "Lectures"], "",
     "A theoretical physicist who writes and podcasts about entropy and the arrow of time, quantum mechanics and the many-worlds interpretation, general relativity, spacetime and cosmology. The Mindscape podcast runs long interviews; the Biggest Ideas series works through the equations themselves.",
     "https://www.preposterousuniverse.com/"),
    ("PBS Space Time", "Channel", "Astronomy & Cosmology", ["YouTube"], "Matt O'Dowd",
     "Graduate-level cosmology and field theory for a general audience: general relativity, black holes and event horizons, quantum field theory, dark matter and dark energy, the cosmic microwave background and the expansion of the universe.",
     "https://www.youtube.com/@pbsspacetime"),
    ("Dr. Becky", "Channel", "Astronomy & Cosmology", ["YouTube", "Book"], "Becky Smethurst",
     "An astrophysicist on supermassive black holes, galaxy evolution and how they are actually observed, with a monthly round-up of new results and a steady line in explaining what a paper does and does not show.",
     "https://www.youtube.com/@DrBecky"),
    ("Cool Worlds", "Channel", "Astronomy & Cosmology", ["YouTube"], "David Kipping",
     "Exoplanets, habitability and the search for life, from an astronomer who works on the detection methods — transits, radial velocity, exomoons — and is unusually careful about what the evidence supports.",
     "https://www.youtube.com/@CoolWorldsLab"),
    ("Anton Petrov", "Channel", "Astronomy & Cosmology", ["YouTube"], "",
     "A near-daily read of new astronomy and astrophysics papers — neutron stars, pulsars, quasars, gamma-ray bursts, solar activity — summarised the day they appear.",
     "https://www.youtube.com/@whatdamath"),
    ("Sixty Symbols", "Channel", "Physics", ["YouTube"], "Brady Haran, with Nottingham physicists",
     "Working physicists talking through one symbol or idea at a time: entropy, the fine-structure constant, relativity, quantum tunnelling, the Planck length. Unscripted, and better for it.",
     "https://www.youtube.com/@sixtysymbols"),
    ("MinutePhysics", "Channel", "Physics", ["YouTube"], "Henry Reich",
     "Short whiteboard explanations of special and general relativity, quantum mechanics, symmetry and conservation, and why the sky is dark at night.",
     "https://www.youtube.com/@minutephysics"),
    ("Sabine Hossenfelder", "Channel", "Physics", ["YouTube", "Book"], "",
     "A theoretical physicist on quantum gravity, particle physics beyond the standard model, dark matter alternatives and the state of the field, with a persistent scepticism about where its funding goes.",
     "https://www.youtube.com/@SabineHossenfelder"),
    ("Angela Collier", "Channel", "Physics", ["YouTube"], "",
     "Long, discursive talks from a computational astrophysicist on dark matter, general relativity, the sociology of physics and how physics research actually gets done.",
     "https://www.youtube.com/@acollierastro"),
    ("AlphaPhoenix", "Channel", "Physics", ["YouTube"], "Brian Haidet",
     "Physics questions settled by building the experiment: measuring the speed of electricity in a wire, imaging shock waves, chasing down what a field really does rather than what the textbook says it does.",
     "https://www.youtube.com/@AlphaPhoenixChannel"),
    ("The Feynman Lectures on Physics", "Organisation", "Physics", ["Book", "Lectures"], "Caltech",
     "The 1960s Caltech lecture course, free to read online in full: mechanics, radiation and heat, then electromagnetism and matter, then quantum mechanics, in the clearest first-principles prose the subject has.",
     "https://www.feynmanlectures.caltech.edu/"),
    ("HyperPhysics", "Organisation", "Physics", ["Blog"], "Rod Nave, Georgia State University",
     "A concept map of undergraduate physics — thermodynamics, electricity and magnetism, quantum and nuclear physics — where every page is one screen and every term links to the one behind it.",
     "http://hyperphysics.phy-astr.gsu.edu/hbase/index.html"),
    ("The Royal Institution", "Organisation", "General science", ["YouTube", "Lectures"], "",
     "Public lectures from the institution that has been giving them since 1825, including the Christmas Lectures, on everything from combustion and electromagnetism to modern cosmology.",
     "https://www.youtube.com/@TheRoyalInstitution"),
    # ---- general science
    ("Veritasium", "Channel", "General science", ["YouTube"], "Derek Muller",
     "Science explained by first finding the misconception: electricity and how energy actually travels in a circuit, relativity, resonance, radioactivity and half-life, and a long-running interest in why the intuitive answer is usually wrong.",
     "https://www.youtube.com/@veritasium"),
    ("Kurzgesagt", "Channel", "General science", ["YouTube"], "",
     "Animated explanations at cosmic scale — black holes, the heat death of the universe, nuclear energy, the Fermi paradox — built on cited sources and released with the reading list attached.",
     "https://www.youtube.com/@kurzgesagt"),
    ("SmarterEveryDay", "Channel", "General science", ["YouTube"], "Destin Sandlin",
     "An engineer taking apart the physical world with high-speed cameras: fluid dynamics, ballistics, flight, resonance and rotation, usually by going to where the thing is actually made.",
     "https://www.youtube.com/@smartereveryday"),
    ("Steve Mould", "Channel", "General science", ["YouTube"], "",
     "Small, strange physical effects explained properly — non-Newtonian fluids, siphons, capillary action, magnetism, the chain fountain that now carries his name.",
     "https://www.youtube.com/@SteveMould"),
    ("Physics Girl", "Channel", "General science", ["YouTube"], "Dianna Cowern",
     "Demonstration-led physics — plasma, light and optics, sound and resonance, superconductors — aimed at people who have not decided whether physics is for them.",
     "https://www.youtube.com/@physicsgirl"),
    ("Mark Rober", "Channel", "Engineering", ["YouTube"], "",
     "Engineering as spectacle from a former NASA engineer: build a machine to answer a silly question, and teach the mechanics, materials and control systems on the way through.",
     "https://www.youtube.com/@MarkRober"),
    ("Quanta Magazine", "Organisation", "General science", ["Blog", "YouTube"], "Simons Foundation",
     "Reported journalism on mathematics, physics and biology that stays close to the research — quantum computing, black holes, prime numbers, the standard model — written for readers who want the actual result.",
     "https://www.quantamagazine.org/"),
    # ---- mathematics
    ("3Blue1Brown", "Channel", "Mathematics", ["YouTube"], "Grant Sanderson",
     "Animated mathematics built around what the objects look like: linear algebra and eigenvectors, calculus and derivatives, differential equations, the Fourier transform, and neural networks from the gradient up.",
     "https://www.youtube.com/@3blue1brown"),
    ("Numberphile", "Channel", "Mathematics", ["YouTube"], "Brady Haran",
     "Mathematicians on brown paper: prime numbers, infinity and cardinality, topology, famous unsolved problems, and the occasional proof that a beloved result is not what people think.",
     "https://www.youtube.com/@numberphile"),
    ("Stand-up Maths", "Channel", "Mathematics", ["YouTube", "Book"], "Matt Parker",
     "Recreational mathematics done seriously — geometry, probability and how badly people reason about it, numerical methods, and spreadsheets pushed far past their intended use.",
     "https://www.youtube.com/@standupmaths"),
    # ---- chemistry
    ("Periodic Videos", "Channel", "Chemistry", ["YouTube"], "Brady Haran, with Martyn Poliakoff",
     "A video for every element in the periodic table, filmed in a working Nottingham chemistry department, plus the reactions, the glassware and the stories behind the names.",
     "https://www.youtube.com/@periodicvideos"),
    ("NileRed", "Channel", "Chemistry", ["YouTube"], "Nigel Braun",
     "Long-form practical organic chemistry: multi-step syntheses run at the bench, with the purification, the failures and the reasoning about why a reduction or an oxidation goes the way it does.",
     "https://www.youtube.com/@NileRed"),
    ("Cody's Lab", "Channel", "Earth & Mining", ["YouTube"], "Cody Reeder",
     "Ore to metal at small scale — panning and prospecting, smelting, leaching, electrolysis and refining — done in the field and the back garden rather than described.",
     "https://www.youtube.com/user/theCodyReeder"),
    # ---- earth & mining
    ("Nick Zentner", "Person", "Earth & Mining", ["YouTube", "Lectures"], "Central Washington University",
     "Field and lecture-hall geology of the Pacific Northwest: plate tectonics, basalt floods, glacial megafloods, and how to read a landscape for the events that made it.",
     "https://www.youtube.com/@GeologyNick"),
    ("GeologyHub", "Channel", "Earth & Mining", ["YouTube"], "",
     "Short reports on volcanic activity, earthquakes, ore deposits and mineral occurrences as they happen, with the geological setting explained each time.",
     "https://www.youtube.com/@GeologyHub"),
    # ---- engineering & machines
    ("Practical Engineering", "Channel", "Engineering", ["YouTube"], "Grady Hillhouse",
     "Civil infrastructure explained with tabletop models: dams and spillways, foundations and soil mechanics, the power grid, water treatment, and the failure modes each is designed against.",
     "https://www.youtube.com/@PracticalEngineeringChannel"),
    ("Real Engineering", "Channel", "Engineering", ["YouTube"], "Brian McManus",
     "The engineering behind aircraft, turbines, batteries and materials, worked through with the numbers — efficiency, thermal limits, why an alloy or a cycle was chosen over the alternative.",
     "https://www.youtube.com/@RealEngineering"),
    ("Technology Connections", "Channel", "Engineering", ["YouTube"], "Alec Watson",
     "How ordinary machines actually work and why they were designed that way — heat pumps and refrigeration cycles, induction cooking, lighting, recording formats and the logic of obsolete standards.",
     "https://www.youtube.com/@TechnologyConnections"),
    ("Applied Science", "Channel", "Engineering", ["YouTube"], "Ben Krasnow",
     "Laboratory instruments built from scratch — electron microscope, X-ray source, mass spectrometer — with the vacuum technique, electronics and materials handling shown in full.",
     "https://www.youtube.com/@AppliedScience"),
    ("Breaking Taps", "Channel", "Engineering", ["YouTube"], "Zachary Tong",
     "Microscopy, microfabrication and precision measurement at home: electron beams, photolithography, thin films, and careful experiments on what small structures really do.",
     "https://www.youtube.com/@BreakingTaps"),
    ("Huygens Optics", "Channel", "Engineering", ["YouTube"], "Jeroen Mostert",
     "Optical fabrication and metrology — grinding and polishing surfaces to a fraction of a wavelength, interferometry, thin-film coatings, and how flatness is measured at all.",
     "https://www.youtube.com/@HuygensOptics"),
    ("Scott Manley", "Channel", "Engineering", ["YouTube"], "",
     "Orbital mechanics and spaceflight engineering — delta-v, transfer orbits, rocket propulsion and staging — from an astronomer who explains launches as they happen.",
     "https://www.youtube.com/@scottmanley"),
    ("Everyday Astronaut", "Channel", "Engineering", ["YouTube"], "Tim Dodd",
     "Rocket engines and launch vehicles in depth: combustion cycles, propellant choices, reusability and heat shielding, usually with the engineers who designed them.",
     "https://www.youtube.com/@EverydayAstronaut"),
    # ---- workshop
    ("This Old Tony", "Channel", "Workshop", ["YouTube"], "",
     "Machining explained by someone doing it — lathe and mill work, tolerances and fits, tool geometry, welding and heat treatment — under a running commentary that hides how careful the teaching is.",
     "https://www.youtube.com/@ThisOldTony"),
    ("Clickspring", "Channel", "Workshop", ["YouTube"], "Chris",
     "Clock and instrument making to museum standard: hand tool work, silver soldering, gear cutting, hardening and tempering, and a long reconstruction of the Antikythera mechanism.",
     "https://www.youtube.com/@Clickspring"),
    ("Blondihacks", "Channel", "Workshop", ["YouTube"], "Quinn Dunki",
     "Home shop machining taught step by step — turning, milling, threading, measurement and workholding — with the mistakes left in and explained.",
     "https://www.youtube.com/@Blondihacks"),
    # ---- adjacent
    ("BlueDot Impact", "Organisation", "AI safety", ["Course"], "",
     "Free structured online courses on AI safety and alignment, run in cohorts with facilitated discussion and a reading curriculum — the main on-ramp for people moving into the field from elsewhere.",
     "https://bluedot.org/"),
]


def main():
    ds = find_ds(TITLE)
    if not ds:
        db = call("POST", "https://api.notion.com/v1/databases", {
            "parent": {"type": "page_id", "page_id": PARENT_PAGE},
            "title": [{"type": "text", "text": {"content": TITLE}}],
            "initial_data_source": {"properties": {
                "Name": {"title": {}},
                "Kind": {"select": {"options": [{"name": k} for k in KINDS]}},
                "Field": {"select": {"options": [{"name": f} for f in FIELDS]}},
                "Medium": {"multi_select": {"options": [{"name": m} for m in MEDIA]}},
                "Behind It": {"rich_text": {}},
                "Covers": {"rich_text": {}},
                "URL": {"url": {}},
            }},
        })
        ds = db["data_sources"][0]["id"]
        print("created", TITLE, ds)
    else:
        print(TITLE, "exists:", ds)
    schema = ensure_props(ds, {
        "Kind": {"select": {"options": [{"name": k} for k in KINDS]}},
        "Field": {"select": {"options": [{"name": f} for f in FIELDS]}},
        "Medium": {"multi_select": {"options": [{"name": m} for m in MEDIA]}},
        "Behind It": {"rich_text": {}},
        "Covers": {"rich_text": {}},
        "URL": {"url": {}},
    }, "explainers")
    ensure_select_options(ds, "Kind", KINDS, "explainers")
    ensure_select_options(ds, "Field", FIELDS, "explainers")
    sync_rows(ds, schema,
              [{"Name": n, "Kind": k, "Field": f, "Medium": m or None,
                "Behind It": b or None, "Covers": c, "URL": u or None}
               for n, k, f, m, b, c, u in EXPLAINERS],
              "explainers", key="Name")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
