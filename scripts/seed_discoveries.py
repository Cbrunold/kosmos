"""Seed the Observatories [DB] and Discoveries [DB] in Notion.

Both were empty. Discoveries already had a usable schema — a title, a
description, and relations to Researchers, Observatories and Celestial Objects.
Observatories did not: its title property was `Obs_ID` with a separate empty
`Name` text property beside it, the same copy-paste fault that left Cosmology
Events titled `Force ID`. That was repaired before this script was written, and
Founded / Location / Altitude / Notes added, so what remains here is content.

Years are numbers, not the existing `Established` and `Discovery Date` date
properties. Ground observatories are known to the year, space telescopes to the
day, and mixing the two in one date column would either invent precision for
the former or discard it for the latter. Where an exact date is the interesting
part — Neptune found within a degree of prediction on the first night — it is
in the prose instead.

Seeding discoveries needs discoverers, and the Researchers DB was stocked for
the theory shelf: it had Einstein and Dirac but not Hubble, Leavitt or Bell
Burnell. The observers are added here.

Idempotent, and never overwrites a field already filled in.
Run on the VPS:  python3 scripts/seed_discoveries.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import (  # noqa: E402  — shared Notion helpers, auth is lazy
    call, ensure_props, query_all, sync_rows, title_of,
)

OBS_DS = "e4113ed3-07af-4167-8145-183389eb39e1"
DISC_DS = "01fd23ec-32da-466d-89cc-5095269805b7"
RESEARCHER_DS = "4cc8d7c4-9008-4017-a09b-7087720aebd3"
INSTRUMENT_DS = "e72fed70-784c-42d2-be1a-3c833ac7fc63"

# ------------------------------------------------------------------ observers
# The theory shelf brought the theorists; these are the people who looked.
OBSERVERS = [
    ("Tycho Brahe", "1546–1601", "Danish", "Astronomy",
     "The most accurate naked-eye observations ever made — and Kepler's laws came out of them."),
    ("Giovanni Cassini", "1625–1712", "Italian-French", "Astronomy",
     "The division in Saturn's rings, and four of its moons."),
    ("Charles Messier", "1730–1817", "French", "Astronomy",
     "Catalogued 110 fuzzy objects so he would stop mistaking them for comets. Nobody remembers his comets."),
    ("William Herschel", "1738–1822", "German-British", "Astronomy",
     "Found Uranus and doubled the size of the known solar system in one night."),
    ("Urbain Le Verrier", "1811–1877", "French", "Astronomy",
     "Calculated where Neptune had to be from Uranus's wobble, then had someone else point the telescope."),
    ("Johann Galle", "1812–1910", "German", "Astronomy",
     "Looked where Le Verrier said and found Neptune within the hour."),
    ("Jules Janssen", "1824–1907", "French", "Astronomy",
     "Saw an unexplained yellow line in the Sun's spectrum during the 1868 eclipse."),
    ("Norman Lockyer", "1836–1920", "English", "Astronomy",
     "Named that line helium, and founded the journal Nature."),
    ("Wilhelm Röntgen", "1845–1923", "German", "Physics",
     "X-rays, the first Nobel Prize in Physics, and a photograph of his wife's hand."),
    ("Henri Becquerel", "1852–1908", "French", "Physics",
     "Left uranium salts on a wrapped photographic plate in a drawer and found radioactivity."),
    ("Karl Jansky", "1905–1950", "American", "Radio Astronomy",
     "Traced a persistent hiss in a telephone antenna to the centre of the Milky Way, and invented radio astronomy."),
    ("Grote Reber", "1911–2002", "American", "Radio Astronomy",
     "Built a radio telescope in his back garden and made the first radio map of the sky, alone."),
    ("Annie Jump Cannon", "1863–1941", "American", "Astronomy",
     "Classified around 350,000 stellar spectra and devised the OBAFGKM sequence still in use."),
    ("Henrietta Swan Leavitt", "1868–1921", "American", "Astronomy",
     "The Cepheid period–luminosity law — the rung the entire cosmic distance ladder stands on."),
    ("Vesto Slipher", "1875–1969", "American", "Astronomy",
     "Measured the first galaxy redshifts a decade before anyone understood what they meant."),
    ("Arthur Eddington", "1882–1944", "English", "Astrophysics",
     "Tested general relativity at the 1919 eclipse and made Einstein famous overnight."),
    ("Victor Hess", "1883–1964", "Austrian", "Physics",
     "Took an electroscope up in a balloon and found the radiation was coming from above, not below."),
    ("Edwin Hubble", "1889–1953", "American", "Astronomy",
     "Proved the spiral nebulae are separate galaxies, then found they are all rushing away."),
    ("James Chadwick", "1891–1974", "English", "Nuclear Physics",
     "The neutron — the particle that made fission, and everything after it, possible."),
    ("Cecilia Payne-Gaposchkin", "1900–1979", "British-American", "Astrophysics",
     "Worked out that stars are overwhelmingly hydrogen, and was pressured to call the result spurious."),
    ("Clyde Tombaugh", "1906–1997", "American", "Astronomy",
     "Found Pluto at twenty-four by blinking photographic plates until something moved."),
    ("Maarten Schmidt", "1929–2022", "Dutch-American", "Astronomy",
     "Realised 3C 273's baffling spectrum was ordinary hydrogen redshifted by 16% — and quasars existed."),
    ("Arno Penzias", "1933–2024", "American", "Astronomy",
     "Half of the pair who found the microwave background while trying to get rid of it."),
    ("Robert Wilson", "1936–", "American", "Astronomy",
     "The other half. They evicted the pigeons and cleaned the antenna first; the hiss stayed."),
    ("Jocelyn Bell Burnell", "1943–", "Northern Irish", "Astrophysics",
     "Found pulsars as a graduate student. The Nobel went to her supervisor."),
    ("Rainer Weiss", "1932–", "American", "Physics",
     "Designed the interferometer that would eventually catch a gravitational wave, in a 1972 report."),
    ("Kip Thorne", "1940–", "American", "Physics",
     "Worked out what a black hole merger would look like before there was any way to see one."),
    ("Barry Barish", "1936–", "American", "Physics",
     "Turned LIGO from a promising idea into an experiment that actually worked."),
    ("Russell Hulse", "1950–", "American", "Astrophysics",
     "The binary pulsar whose decaying orbit proved gravitational waves are real, forty years early."),
    ("Joseph Taylor", "1941–", "American", "Astrophysics",
     "Tracked that orbit for decades until the agreement with general relativity was undeniable."),
    ("David Jewitt", "1958–", "British-American", "Astronomy",
     "Found the first Kuiper Belt object after five years of searching an empty-looking sky."),
    ("Jane Luu", "1963–", "Vietnamese-American", "Astronomy",
     "Co-discovered it — and with it the belt that would eventually reclassify Pluto."),
]

# ------------------------------------------------------------------ observatories
# name, type, founded, location, altitude m (None in space), notes, instrument names
OBSERVATORIES = [
    ("Paris Observatory", "Ground-based", 1667, "Paris, France", 67,
     "The oldest working observatory in the world. Cassini ran it, and the Paris meridian was the "
     "world's reference until Greenwich won the argument in 1884.", []),
    ("Royal Observatory, Greenwich", "Ground-based", 1675, "London, England", 47,
     "Founded to solve longitude at sea, which it eventually did — though by way of Harrison's "
     "clocks rather than the star charts it was built for. The prime meridian runs through it.", []),
    ("Lick Observatory", "Ground-based", 1888, "Mount Hamilton, California", 1283,
     "The first permanently occupied mountaintop observatory, funded by a real-estate magnate who "
     "is buried under the great refractor.", []),
    ("Yerkes Observatory", "Ground-based", 1897, "Williams Bay, Wisconsin", 334,
     "Its 40-inch refractor is the largest ever built for astronomy and always will be: a lens can "
     "only be supported at its rim, and beyond this size the glass sags under its own weight.", []),
    ("Mount Wilson Observatory", "Ground-based", 1904, "San Gabriel Mountains, California", 1742,
     "Where Hubble established that the spiral nebulae are other galaxies, and then that they are "
     "receding. Arguably the most consequential telescope site in history.", []),
    ("Palomar Observatory", "Ground-based", 1948, "Palomar Mountain, California", 1712,
     "The 200-inch Hale telescope held the record for 45 years. Schmidt identified the first quasar "
     "here in 1963.", []),
    ("Arecibo Observatory", "Ground-based", 1963, "Arecibo, Puerto Rico", 498,
     "A 305 m dish slung across a natural sinkhole. It sent the 1974 interstellar message and found "
     "the first exoplanets; the platform collapsed into the dish in December 2020.", []),
    ("Mauna Kea Observatories", "Ground-based", 1968, "Mauna Kea, Hawaii", 4205,
     "Thirteen telescopes above 40% of the atmosphere and most of its water vapour. Also land held "
     "sacred in Native Hawaiian tradition, and the subject of a long and unresolved dispute.", []),
    ("Very Large Array", "Ground-based", 1980, "Plains of San Agustin, New Mexico", 2124,
     "Twenty-seven dishes that move on rails along a 36 km Y, trading resolution against field of "
     "view by physically rearranging the telescope.", []),
    ("Roque de los Muchachos Observatory", "Ground-based", 1985, "La Palma, Canary Islands", 2396,
     "Home to the Gran Telescopio Canarias, the largest single-aperture optical telescope in "
     "operation, sitting above the trade-wind inversion layer.", []),
    ("W. M. Keck Observatory", "Ground-based", 1993, "Mauna Kea, Hawaii", 4145,
     "Twin 10 m mirrors, each 36 hexagonal segments actively aligned every few seconds. The "
     "segmented design is why telescopes could keep getting bigger.", ["Keck Observatory"]),
    ("Paranal Observatory", "Ground-based", 1998, "Atacama Desert, Chile", 2635,
     "Four 8.2 m telescopes that can be combined into one interferometer. Took the first direct "
     "image of an exoplanet, and tracked stars orbiting the black hole at the galactic centre.",
     ["Very Large Telescope (VLT)"]),
    ("Gemini Observatory", "Ground-based", 1999, "Mauna Kea, Hawaii and Cerro Pachón, Chile", 4213,
     "Twin 8.1 m telescopes, one in each hemisphere, so that between them no part of the sky is "
     "out of reach.", []),
    ("LIGO", "Ground-based", 2002, "Hanford, Washington and Livingston, Louisiana", 142,
     "Two 4 km interferometers measuring length changes of about a ten-thousandth the width of a "
     "proton. Two sites, because a real signal must arrive at both.", []),
    ("South Pole Telescope", "Ground-based", 2007, "Amundsen–Scott Station, Antarctica", 2800,
     "A 10 m dish on the driest, stillest air on the planet, watching the microwave background "
     "through a sky that barely moves.", []),
    ("Atacama Large Millimeter Array", "Ground-based", 2011, "Chajnantor Plateau, Chile", 5058,
     "Sixty-six dishes at 5,000 m, where the air is too dry and thin to absorb millimetre waves. "
     "Imaged the gaps carved by forming planets in the disc of HL Tauri.",
     ["Atacama Large Millimeter/submillimeter Array (ALMA)"]),
    ("Event Horizon Telescope", "Ground-based", 2017, "Global array, Spain to the South Pole", None,
     "Not one telescope but eight, combined by atomic clocks into an aperture the size of the "
     "Earth. It is the only way to resolve something as small on the sky as M87's shadow.", []),
    ("Vera C. Rubin Observatory", "Ground-based", 2025, "Cerro Pachón, Chile", 2647,
     "Will photograph the entire southern sky every few nights for ten years, producing about "
     "20 terabytes a night and alerting on anything that moves or changes.",
     ["Large Synoptic Survey Telescope (LSST)"]),

    ("COBE", "Space-based", 1989, "Low Earth orbit, 900 km", None,
     "Measured the microwave background as the most perfect black body ever observed, then found "
     "the faint anisotropies that are the seeds of every galaxy.", []),
    ("Hubble Space Telescope", "Space-based", 1990, "Low Earth orbit, 540 km", None,
     "Launched with a mirror ground to the wrong shape by 2.2 micrometres, corrected by spacewalk "
     "in 1993, and productive ever since — the only space telescope ever repaired by hand.",
     ["Hubble Space Telescope (HST)"]),
    ("Chandra X-ray Observatory", "Space-based", 1999, "Highly elliptical Earth orbit", None,
     "X-rays cannot be focused by reflection head-on, so its mirrors are nested cylinders that "
     "graze the light at less than a degree. Weighed the dark matter in the Bullet Cluster.",
     ["Chandra X-ray Observatory"]),
    ("WMAP", "Space-based", 2001, "Earth–Sun L2, 1.5 million km", None,
     "Pinned the age of the universe at 13.7 billion years and the geometry as flat to within 1%.", []),
    ("Spitzer Space Telescope", "Space-based", 2003, "Earth-trailing solar orbit", None,
     "Infrared, so it had to be colder than its own targets; it drifted away from the Earth to stay "
     "cool and ran warm for eleven more years after the coolant ran out.", []),
    ("Kepler", "Space-based", 2009, "Earth-trailing solar orbit", None,
     "Stared at 150,000 stars without blinking and found more than 2,600 planets by measuring "
     "dimmings of a hundredth of a percent.", []),
    ("Planck", "Space-based", 2009, "Earth–Sun L2, 1.5 million km", None,
     "Mapped the microwave background to the precision that every cosmological parameter now "
     "quoted — including the one at the centre of the Hubble tension — rests on.",
     ["Planck Satellite"]),
    ("Gaia", "Space-based", 2013, "Earth–Sun L2, 1.5 million km", None,
     "Measuring positions, distances and motions for nearly two billion stars, which is about 1% of "
     "the galaxy and vastly more than everything before it combined.", []),
    ("James Webb Space Telescope", "Space-based", 2021, "Earth–Sun L2, 1.5 million km", None,
     "6.5 m of gold-coated beryllium that had to unfold through 344 single-point failures after "
     "launch, every one of which worked. Sees the first galaxies, and finds them too bright.",
     ["James Webb Space Telescope (JWST)"]),
]

# ------------------------------------------------------------------ discoveries
# name, year, description, discoverers, observatory
DISCOVERIES = [
    ("The Galilean Moons", 1610,
     "Four points of light beside Jupiter that moved night to night. They orbited something other "
     "than the Earth, which the geocentric model had no room for.",
     ["Galileo Galilei"], None),
    ("The Rings of Saturn", 1655,
     "Galileo saw 'ears' and could not resolve them. Huygens, with a better lens, worked out it was "
     "a flat ring touching the planet nowhere.",
     ["Christiaan Huygens"], None),
    ("The Cassini Division", 1675,
     "A dark gap splitting Saturn's rings in two — the first hint that the rings are not solid but "
     "swarms of particles, shepherded by resonances with the moons.",
     ["Giovanni Cassini"], "Paris Observatory"),
    ("Uranus", 1781,
     "The first planet discovered rather than always known. Herschel took it for a comet, and the "
     "solar system doubled in size once the orbit was worked out.",
     ["William Herschel"], None),
    ("Neptune", 1846,
     "Found by arithmetic. Le Verrier calculated where an unseen planet must sit to explain "
     "Uranus's orbital residuals; Galle pointed a telescope there and had it within an hour, less "
     "than a degree from the prediction.",
     ["Urbain Le Verrier", "Johann Galle"], None),
    ("Helium", 1868,
     "An unexplained yellow line in the Sun's spectrum during a total eclipse. It was named for the "
     "Sun and not found on Earth for another 27 years — the only element discovered off-world first.",
     ["Jules Janssen", "Norman Lockyer"], None),
    ("X-rays", 1895,
     "A screen across the room fluoresced while a covered discharge tube was running. Within months "
     "the effect was being used to photograph bones, before anyone knew what the rays were.",
     ["Wilhelm Röntgen"], None),
    ("Radioactivity", 1896,
     "Uranium salts left on a wrapped photographic plate in a closed drawer, waiting for sunshine "
     "that never came, fogged the plate anyway. The energy was coming from the atom itself.",
     ["Henri Becquerel"], None),
    ("The Electron", 1897,
     "Cathode rays bent by both magnetic and electric fields, giving a charge-to-mass ratio a "
     "thousand times anything expected. The atom had parts.",
     ["J. J. Thomson"], None),
    ("The Atomic Nucleus", 1911,
     "Alpha particles fired at gold foil, and about one in eight thousand came straight back — 'as "
     "if you had fired a 15-inch shell at tissue paper and it bounced'. The positive charge was a point.",
     ["Ernest Rutherford"], None),
    ("Cosmic Rays", 1912,
     "Radiation was assumed to come from the ground, so it should fall with altitude. Hess took an "
     "electroscope to 5,300 m in a balloon and found it rising instead.",
     ["Victor Hess"], None),
    ("The Cepheid Period–Luminosity Law", 1912,
     "Leavitt noticed that the brighter Cepheids in the Magellanic Clouds pulse more slowly. Since "
     "those stars are all at much the same distance, the relation gives absolute brightness — and "
     "therefore distance to anything containing one. Every rung above it depends on this.",
     ["Henrietta Swan Leavitt"], None),
    ("Galaxy Redshifts", 1917,
     "Slipher measured the spectra of spiral nebulae and found almost all of them shifted to the "
     "red. He had the expansion of the universe in hand a decade before anyone could interpret it.",
     ["Vesto Slipher"], None),
    ("The Bending of Starlight", 1919,
     "Eddington photographed stars near the eclipsed Sun and found them displaced by about an "
     "arcsecond — twice the Newtonian value, and what general relativity had predicted.",
     ["Arthur Eddington", "Albert Einstein"], None),
    ("Stars Are Made of Hydrogen", 1925,
     "Payne-Gaposchkin applied the Saha equation to stellar spectra and found hydrogen outnumbering "
     "everything else by orders of magnitude. Told the result was 'clearly impossible', she added a "
     "disclaimer; she was right and it was retracted four years later.",
     ["Cecilia Payne-Gaposchkin"], None),
    ("Andromeda Is a Galaxy", 1924,
     "A Cepheid in M31 put it a million light-years away — far outside the Milky Way. The universe "
     "went from one galaxy to countless in a single plate.",
     ["Edwin Hubble"], "Mount Wilson Observatory"),
    ("The Expansion of the Universe", 1929,
     "Distance plotted against redshift gave a straight line: everything is receding, faster the "
     "further away it is. Lemaître had derived it from theory two years earlier and been ignored.",
     ["Edwin Hubble"], "Mount Wilson Observatory"),
    ("Pluto", 1930,
     "Tombaugh blinked photographic plates for a year looking for a predicted ninth planet. He "
     "found one — though far too small to be the object the prediction called for, which was an error.",
     ["Clyde Tombaugh"], None),
    ("Radio Waves from the Milky Way", 1932,
     "Jansky was hired to find sources of static troubling transatlantic telephone calls. One hiss "
     "rose and set four minutes early each day — sidereal time — and came from Sagittarius.",
     ["Karl Jansky"], None),
    ("The Neutron", 1932,
     "A neutral particle of roughly proton mass, which explained isotopes at a stroke and made "
     "everything in nuclear physics after it possible.",
     ["James Chadwick"], None),
    ("Dark Matter in the Coma Cluster", 1933,
     "Zwicky measured how fast the galaxies were moving and found the cluster needed several "
     "hundred times more mass than its light accounted for. He was ignored for forty years.",
     ["Fritz Zwicky"], None),
    ("The First Radio Map of the Sky", 1938,
     "Reber built a 9 m dish in his back garden, the only radio astronomer in the world for most of "
     "a decade, and surveyed the sky nobody else was listening to.",
     ["Grote Reber"], None),
    ("Quasars", 1963,
     "3C 273's spectrum matched nothing until Schmidt recognised ordinary hydrogen lines redshifted "
     "by 16%. That put it two billion light-years away and radiating more than a hundred galaxies "
     "from a region the size of the solar system.",
     ["Maarten Schmidt"], "Palomar Observatory"),
    ("The Cosmic Microwave Background", 1965,
     "An antenna hiss that would not go away in any direction, at any hour, in any season. They "
     "evicted a pair of pigeons and scrubbed out the droppings; the 3 K signal remained. It was the "
     "afterglow of the Big Bang, and it settled the argument with the steady state.",
     ["Arno Penzias", "Robert Wilson"], None),
    ("Pulsars", 1967,
     "A signal repeating every 1.337 seconds, so regular it was labelled LGM-1 for 'little green "
     "men'. It was a neutron star, spinning — an object predicted in 1934 and never expected to be seen.",
     ["Jocelyn Bell Burnell"], None),
    ("Flat Galaxy Rotation Curves", 1978,
     "Stars at the edges of spiral galaxies orbit as fast as those near the centre, which Newtonian "
     "gravity forbids unless most of the mass is invisible. This is what turned dark matter from a "
     "curiosity into a crisis.",
     ["Vera Rubin"], None),
    ("The Binary Pulsar", 1974,
     "Two neutron stars orbiting each other, losing energy at exactly the rate general relativity "
     "predicts for gravitational radiation. Indirect proof of gravitational waves, four decades "
     "before one was caught directly.",
     ["Russell Hulse", "Joseph Taylor"], "Arecibo Observatory"),
    ("The First Kuiper Belt Object", 1992,
     "After five years of finding nothing, Jewitt and Luu found 1992 QB1 beyond Neptune. Thousands "
     "followed, and Pluto turned out to be one of them rather than a planet.",
     ["David Jewitt", "Jane Luu"], "Mauna Kea Observatories"),
    ("Structure in the Microwave Background", 1992,
     "COBE mapped temperature ripples of one part in a hundred thousand — the density variations "
     "that gravity would grow into every galaxy that exists.",
     ["George Smoot"], "COBE"),
    ("51 Pegasi b", 1995,
     "A Jupiter-mass planet orbiting a Sun-like star every 4.2 days, far closer than any theory "
     "allowed. It was the first planet found around an ordinary star, and it broke planet formation "
     "models immediately.",
     ["Michel Mayor", "Didier Queloz"], None),
    ("The Accelerating Universe", 1998,
     "Distant type Ia supernovae came out fainter than a decelerating universe permits. Two "
     "competing teams got the same unwelcome answer, and dark energy has been unexplained ever since.",
     ["Saul Perlmutter", "Brian Schmidt", "Adam Riess"], None),
    ("The Higgs Boson", 2012,
     "A resonance at 125 GeV in two independent detectors, matching a particle predicted in 1964. "
     "Higgs was in the audience for the announcement, 48 years later.",
     ["Peter Higgs", "François Englert"], None),
    ("Gravitational Waves", 2015,
     "GW150914: two black holes of 36 and 29 solar masses merging 1.3 billion light-years away, "
     "shifting LIGO's 4 km arms by a fraction of a proton's width. The signal was so clean it was "
     "initially suspected of being an injected test.",
     ["Rainer Weiss", "Kip Thorne", "Barry Barish"], "LIGO"),
    ("A Neutron Star Merger, Seen and Heard", 2017,
     "GW170817 arrived as gravitational waves and, 1.7 seconds later, as a gamma-ray burst — then "
     "in every other band as seventy observatories turned to look. The debris was measurably "
     "manufacturing gold.",
     ["Rainer Weiss", "Kip Thorne"], "LIGO"),
    ("The First Image of a Black Hole", 2019,
     "M87*: a ring of light around a shadow two and a half times the Schwarzschild radius, exactly "
     "the size general relativity requires. Assembled from petabytes flown between eight sites on "
     "physical hard drives, because no network could carry it.",
     ["Roger Penrose"], "Event Horizon Telescope"),
]


def main():
    # ---- observers into the existing Researchers DB
    print("researchers")
    r_schema = ensure_props(RESEARCHER_DS, {}, "researchers")
    sync_rows(RESEARCHER_DS, r_schema,
              [{"Name": n, "Lifespan": ls, "Nationality": nat, "Field": f, "Known For": k}
               for n, ls, nat, f, k in OBSERVERS],
              "researchers")

    # ---- observatories
    print("\nobservatories")
    o_schema = ensure_props(OBS_DS, {}, "observatories")
    sync_rows(OBS_DS, o_schema,
              [{"Name": n, "Type": t, "Founded": f, "Location": loc,
                "Altitude (m)": alt, "Notes": notes}
               for n, t, f, loc, alt, notes, _ in OBSERVATORIES],
              "observatories")

    # instruments already in Notion, attached to the sites that operate them
    instruments = {title_of(p, "Name"): p["id"] for p in query_all(INSTRUMENT_DS)
                   if title_of(p, "Name")}
    obs_pages = {title_of(p, "Name"): p for p in query_all(OBS_DS) if title_of(p, "Name")}
    linked, missing = 0, set()
    for name, _, _, _, _, _, instr in OBSERVATORIES:
        page = obs_pages.get(name)
        if not page or not instr:
            continue
        ids = set()
        for i in instr:
            if i in instruments:
                ids.add(instruments[i])
            else:
                missing.add(i)
        cur = {x["id"] for x in (page["properties"].get("Primary_Instruments [DB]", {})
                                 .get("relation") or [])}
        if ids - cur:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}",
                 {"properties": {"Primary_Instruments [DB]": {
                     "relation": [{"id": x} for x in sorted(cur | ids)]}}})
            linked += 1
    if missing:
        print("  unresolved instrument names ignored:", sorted(missing))
    print(f"  instruments: linked {linked} observatories")

    # ---- discoveries
    print("\ndiscoveries")
    d_schema = ensure_props(DISC_DS, {"Year": {"number": {"format": "number"}}}, "discoveries")
    sync_rows(DISC_DS, d_schema,
              [{"Name": n, "Year": y, "Description": desc} for n, y, desc, _, _ in DISCOVERIES],
              "discoveries")

    people = {title_of(p, "Name"): p["id"] for p in query_all(RESEARCHER_DS) if title_of(p, "Name")}
    obs_pages = {title_of(p, "Name"): p for p in query_all(OBS_DS) if title_of(p, "Name")}
    disc_pages = {title_of(p, "Name"): p for p in query_all(DISC_DS) if title_of(p, "Name")}
    changed, edges, unresolved = 0, 0, set()
    for name, _, _, who, obs in DISCOVERIES:
        page = disc_pages.get(name)
        if not page:
            continue
        payload = {}
        ids = set()
        for w in who:
            if w in people:
                ids.add(people[w])
            else:
                unresolved.add(w)
        cur = {x["id"] for x in (page["properties"].get("Discoverer", {}).get("relation") or [])}
        if ids - cur:
            payload["Discoverer"] = {"relation": [{"id": x} for x in sorted(cur | ids)]}
        edges += len(cur | ids)
        if obs:
            if obs in obs_pages:
                oid = obs_pages[obs]["id"]
                curo = {x["id"] for x in (page["properties"].get("Observatory", {})
                                          .get("relation") or [])}
                if oid not in curo:
                    payload["Observatory"] = {"relation": [{"id": x} for x in sorted(curo | {oid})]}
                    edges += 1
            else:
                unresolved.add(obs)
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload})
            changed += 1
    if unresolved:
        print("  unresolved names ignored:", sorted(unresolved))
    print(f"  relations: updated {changed} discoveries · {edges} links")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
