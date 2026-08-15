"""Seed the Space Missions [DB] in Notion.

The last empty database, and the only one whose schema needed nothing beyond
two additions: `Name` really was the title here, and `Launch Date` / `End Date`
are genuinely the right type. Everywhere else on this site a date property
invited invented precision and got replaced with a year number — but a launch
is a real instant, recorded to the day and often to the second. Apollo 11 left
at 13:32 UTC on 16 July 1969. Using a year there would be throwing away
precision rather than protecting against it.

Adds `Agency` and `Destination`, which the table lacked, so a mission is
legible without reading the objective.

`Mission_ID` is deliberately left empty. It is presumably meant for COSPAR /
NSSDCA designations (Apollo 11 is 1969-059A), and those are exactly the kind of
identifier that looks authoritative and is trivially checkable — so they should
be copied from the NSSDC catalogue rather than recalled. Better an empty column
than 36 plausible-looking wrong ones.

End Date is left empty for missions still running; the Status select carries
that instead. For the ones that ended, it is the date of loss, final
transmission, or deliberate disposal, whichever ended the mission.

Idempotent, and never overwrites a field already filled in.
Run on the VPS:  python3 scripts/seed_missions.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import ensure_props, ensure_select_options, sync_rows  # noqa: E402

MISSIONS_DS = "6c10e82f-8044-43f2-b936-58bf54d4873b"

AGENCIES = ["NASA", "ESA", "Roscosmos", "JAXA", "ISRO", "CNSA", "International"]
STATUSES = ["Completed", "On-going", "Failed", "Planned"]

NEW_PROPS = {
    "Agency": {"select": {"options": [{"name": a} for a in AGENCIES]}},
    "Destination": {"rich_text": {}},
}

# name, launch, end (None = still running), status, agency, destination, objective
MISSIONS = [
    ("Sputnik 1", "1957-10-04", "1958-01-04", "Completed", "Roscosmos", "Low Earth orbit",
     "A polished 58 cm sphere with four trailing antennas, beeping on 20 and 40 MHz. It carried no "
     "instruments worth the name and did almost nothing, and it changed the century."),
    ("Luna 2", "1959-09-12", "1959-09-14", "Completed", "Roscosmos", "The Moon",
     "The first object from Earth to reach another world, which it did by hitting it. It also "
     "established that the Moon has no appreciable magnetic field."),
    ("Vostok 1", "1961-04-12", "1961-04-12", "Completed", "Roscosmos", "Low Earth orbit",
     "Gagarin, one orbit, 108 minutes. The capsule was flown almost entirely from the ground — "
     "nobody knew whether a human could function in weightlessness."),
    ("Mariner 2", "1962-08-27", "1963-01-03", "Completed", "NASA", "Venus",
     "The first successful planetary flyby. It found a surface hot enough to melt lead, ending "
     "a century of speculation about jungles under the clouds."),
    ("Mariner 4", "1964-11-28", "1967-12-21", "Completed", "NASA", "Mars",
     "Twenty-one photographs, taken on tape and played back over eight hours. They showed craters "
     "and no canals, and the Mars of fiction died that week."),
    ("Apollo 8", "1968-12-21", "1968-12-27", "Completed", "NASA", "The Moon",
     "The first crewed flight to leave Earth orbit, ten orbits of the Moon, and Earthrise — a "
     "photograph taken almost by accident that is often credited with starting the environmental "
     "movement."),
    ("Apollo 11", "1969-07-16", "1969-07-24", "Completed", "NASA", "The Moon",
     "The guidance computer had about 4 KB of writable memory and threw overflow alarms during "
     "descent; Armstrong flew the last stretch manually with seconds of fuel remaining."),
    ("Apollo 13", "1970-04-11", "1970-04-17", "Failed", "NASA", "The Moon",
     "An oxygen tank ruptured 320,000 km out. The mission failed completely and the crew came back "
     "alive, which is the only reason anyone remembers it."),
    ("Pioneer 10", "1972-03-02", "2003-01-23", "Completed", "NASA", "Jupiter",
     "First through the asteroid belt and first past Jupiter, carrying the engraved plaque. The "
     "last faint signal came 31 years after launch."),
    ("Pioneer 11", "1973-04-06", "1995-11-24", "Completed", "NASA", "Saturn",
     "Used Jupiter's gravity to reach Saturn, and flew through the ring plane to prove the route "
     "was safe for the Voyagers behind it."),
    ("Mariner 10", "1973-11-03", "1975-03-24", "Completed", "NASA", "Mercury and Venus",
     "The first mission to use a gravity assist, swinging past Venus to reach Mercury — the "
     "technique every outer-planet mission has depended on since."),
    ("Viking 1", "1975-08-20", "1982-11-13", "Completed", "NASA", "Mars",
     "The first fully successful Mars landing. Its biology package returned results that were "
     "ambiguous then and are still argued over now."),
    ("Voyager 2", "1977-08-20", None, "On-going", "NASA", "Interstellar space",
     "Launched sixteen days before Voyager 1, and still the only spacecraft to have visited Uranus "
     "or Neptune. A planetary alignment that made the route possible recurs every 175 years."),
    ("Voyager 1", "1977-09-05", None, "On-going", "NASA", "Interstellar space",
     "The most distant human object, over 24 billion km out and still returning data on a few "
     "watts from a plutonium source that is slowly running down. Its radio signal takes 22 hours "
     "to arrive."),
    ("Venera 13", "1981-10-30", "1982-03-01", "Completed", "Roscosmos", "Venus",
     "Survived 127 minutes on the surface at 457 °C and 89 atmospheres — designed for 32 — and "
     "sent back the first colour photographs of another planet's surface."),
    ("STS-51-L (Challenger)", "1986-01-28", "1986-01-28", "Failed", "NASA", "Low Earth orbit",
     "Lost 73 seconds after launch. The O-ring failure mode had been documented and the launch "
     "temperature objected to the night before."),
    ("Galileo", "1989-10-18", "2003-09-21", "Completed", "NASA", "Jupiter",
     "Its high-gain antenna never unfurled, cutting the data rate by a factor of ten thousand. The "
     "mission was salvaged by rewriting the onboard compression from Earth, and it still found "
     "evidence for an ocean under Europa's ice."),
    ("Hubble Space Telescope", "1990-04-24", None, "On-going", "NASA", "Low Earth orbit",
     "Launched with a mirror ground to the wrong shape by 2.2 micrometres, corrected by astronauts "
     "in 1993, and serviced five times. The only telescope ever repaired in orbit."),
    ("Mars Pathfinder", "1996-12-04", "1997-09-27", "Completed", "NASA", "Mars",
     "Landed inside airbags, bounced fifteen times, and released Sojourner — the first rover to "
     "move on another planet, at a top speed of one centimetre per second."),
    ("Cassini–Huygens", "1997-10-15", "2017-09-15", "Completed", "International", "Saturn",
     "Huygens landed on Titan and found rivers of methane. Cassini was deliberately flown into "
     "Saturn at the end so that it could never contaminate Enceladus, whose ocean it had discovered."),
    ("International Space Station", "1998-11-20", None, "On-going", "International", "Low Earth orbit",
     "Assembled from more than forty flights and continuously crewed since November 2000 — the "
     "longest unbroken human presence off Earth."),
    ("Mars Climate Orbiter", "1998-12-11", "1999-09-23", "Failed", "NASA", "Mars",
     "Entered the atmosphere 170 km too low and broke up. One team's software produced "
     "pound-seconds where another expected newton-seconds, and nothing in between caught it."),
    ("Spirit and Opportunity", "2003-06-10", "2018-06-10", "Completed", "NASA", "Mars",
     "Designed for 90 sols each. Spirit lasted six years, Opportunity fourteen and 45 km, and "
     "ended in a dust storm with a final transmission about falling battery voltage."),
    ("Rosetta", "2004-03-02", "2016-09-30", "Completed", "ESA", "Comet 67P",
     "Ten years and four gravity assists to reach a comet, then the first orbit and the first "
     "landing. Philae bounced twice, ended up in shadow, and worked for 60 hours on battery."),
    ("New Horizons", "2006-01-19", None, "On-going", "NASA", "The Kuiper Belt",
     "The fastest launch ever attempted, and still nine and a half years to Pluto — which was "
     "reclassified as a dwarf planet seven months after it left."),
    ("Kepler", "2009-03-07", "2018-10-30", "Completed", "NASA", "Cygnus and Lyra",
     "Stared at 150,000 stars for four years without moving, measuring dimmings of a hundredth of "
     "a percent. It found over 2,600 planets and made 'how many are there' a statistical question."),
    ("Juno", "2011-08-05", None, "On-going", "NASA", "Jupiter",
     "In a wide polar orbit that spends as little time as possible in Jupiter's radiation belts, "
     "which would otherwise destroy the electronics within months."),
    ("Curiosity", "2011-11-26", None, "On-going", "NASA", "Mars",
     "Too heavy for airbags, so it was lowered on cables from a rocket-powered sky crane that then "
     "flew away and crashed deliberately. It has since confirmed Gale Crater once held a lake."),
    ("Gaia", "2013-12-19", "2025-03-27", "Completed", "ESA", "Earth–Sun L2",
     "Measured positions, distances and motions for nearly two billion stars — about 1% of the "
     "galaxy, and more than every survey before it combined."),
    ("Parker Solar Probe", "2018-08-12", None, "On-going", "NASA", "The Sun",
     "Has flown through the solar corona behind a 2,500 °C carbon shield, and is the fastest "
     "object humans have built at around 690,000 km/h at perihelion."),
    ("Chang'e 4", "2018-12-07", None, "On-going", "CNSA", "The Moon's far side",
     "The first landing on the far side, which needs a relay satellite beyond the Moon because "
     "there is no line of sight to Earth from there."),
    ("Perseverance and Ingenuity", "2020-07-30", None, "On-going", "NASA", "Mars",
     "Caching samples for a return mission that does not yet exist. Ingenuity, carried as a "
     "technology demonstration expected to manage five flights, made 72 in air 1% as dense as Earth's."),
    ("DART", "2021-11-24", "2022-09-26", "Completed", "NASA", "Asteroid Dimorphos",
     "Flew into an asteroid at 22,500 km/h and shortened its orbit by 32 minutes — far more than "
     "predicted, because the ejecta pushed back. The first demonstration that deflection works."),
    ("James Webb Space Telescope", "2021-12-25", None, "On-going", "International", "Earth–Sun L2",
     "Unfolded through 344 single-point failures after launch, every one of which worked, at a "
     "distance where no repair is possible. It sees galaxies from 300 million years after the Big Bang."),
    ("Artemis I", "2022-11-16", "2022-12-11", "Completed", "NASA", "The Moon",
     "An uncrewed test flight around the Moon and back, and the first launch of the rocket "
     "intended to return people there."),
    ("Chandrayaan-3", "2023-07-14", "2023-08-23", "Completed", "ISRO", "The Moon's south pole",
     "The first landing near the lunar south pole, where permanently shadowed craters are thought "
     "to hold water ice, and four years after Chandrayaan-2 crashed attempting it."),
    ("Europa Clipper", "2024-10-14", None, "On-going", "NASA", "Europa",
     "Will make roughly fifty close passes of Europa rather than orbiting it, spending most of its "
     "time outside Jupiter's radiation belts so the instruments survive long enough to matter."),
]


def main():
    schema = ensure_props(MISSIONS_DS, NEW_PROPS, "missions")
    ensure_select_options(MISSIONS_DS, "Status", STATUSES, "missions")
    ensure_select_options(MISSIONS_DS, "Agency", AGENCIES, "missions")
    sync_rows(MISSIONS_DS, schema,
              [{"Name": n, "Launch Date": launch, "End Date": end, "Status": st,
                "Agency": ag, "Destination": dest, "Objective": obj}
               for n, launch, end, st, ag, dest, obj in MISSIONS],
              "missions")
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
