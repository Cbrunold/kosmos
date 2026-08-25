# kosmos

A multi-disciplinary science portal — a personal atlas of the physical world
and what lives in it.
Live at **https://kosmos.yeahborhood.com**.

Notion is the source of truth for authored content; this repo is the source of
truth for code and the normalised data snapshots. Sync is one-way, Notion → repo.

## Pages

| Route        | What's there |
|--------------|--------------|
| `/`          | Tile launcher in four groups (Matter & Earth, Cosmos & Physics, Making & Doing, Reference) with live stats per section, and a search bar over everything the site holds (`/` to focus, `?q=` to deep-link a query) |
| `/elements`  | Interactive periodic table (11 lenses incl. crustal rarity and concentration factor, temperature + discovery sliders), sources & extraction per element, and the AI photo analyzer |
| `/minerals`  | 3,100+ minerals with formula, elemental makeup (mass %), hardness and density, filterable by contained element; gemstone shelf, rock families, silicate classes |
| `/cosmos`    | The Local Group mapped by true distance (log-radial, 44 members), celestial object classes, the stellar spectral sequence, observatories, a discovery timeline, missions, instruments and researchers |
| `/forces`    | The four fundamental interactions |
| `/mines`     | World map of ~90 flagship mines, and for each raw material its ore minerals, typical grade, concentration factor, and ore-to-product process |
| `/machines`  | The canonical engines and machines — how each works, its cycle drawn as a p–V loop, efficiency, materials, inventors; cross-linked to equations, elements and skills |
| `/skills`    | Hands-on techniques with the science behind them — tools, steps, safety, how it fails, how you know it worked; linked to elements, equations and machines. Includes three cue-sports skills that run on the billiards equations |
| `/billiards` | The physics of the pool table — a live shot lab (cut angle, speed, tip height, side, distance → tangent line, ghost ball, throw, slide-to-roll, stop distances), a cushion lab, the constants quoted from pool-sauce-engine, and the equations and skills it rests on |
| `/glossary`  | The terms the site uses, defined once and traced at build time to every page whose text uses them |
| `/explainers`| The people, channels and organisations that explain this material — with the glossary terms each covers, computed from the same matcher |
| `/life`      | The molecular machinery, asked the questions /machines asks of an engine — how it works, what it is made of, what it costs — each entry chipping through to the elements it cannot run without |
| `/solar`     | The nine orbits, computed live in the browser from Keplerian elements — play, scrub to any date 1800-2050, log or linear radius |
| `/impacts`   | What extraction costs, by mechanism — how each harm arises, what reduces it, where it is documented, how many mines on the site it applies to, and the physics it runs on (Darcy, Stokes, hydrostatics) |
| `/timeline`  | The universe's history on a log axis of seconds — Planck epoch to heat death, cross-linked to the equations and theories |
| `/theories`  | Theory shelf from Ptolemy to the holographic principle — status, proponents, and the equations each rests on; sortable chronologically |
| `/equations` | Equations, laws and definitions with symbols decoded, filterable by domain and field; each shows what it *requires* (with the full path down to the foundations) and what requires it; sortable by year or foundations-first |
| `/constants` | CODATA constants with uncertainties, SI units, prefixes |
| `/fr/…`      | The whole site in French — every route above under `/fr/`, with an EN · FR switch on every page. Derived from the English pages at build time through `data/i18n/fr.json` (see `scripts/i18n.py`) |

## Layout

```
server.js                     Node server: static pages + POST /api/analyze
public/                       Built pages + search.json (generated — see scripts/build.py)
web/billiards.template.html   The shot lab: the billiards equations integrated in the browser (sliding→rolling,
                              restitution, throw with Alciatore's μ(v), cushion impulse) on the constants below
web/                          Page sources: templates, shared.css, analyzer parts
data/chemistry/elements.json  Normalised element data (scripts/fetch_elements.py)
data/notion-all.json          All other Notion sources (scripts/fetch_all.py)
scripts/build.py              web/ + data → public/*.html, then public/fr/*.html (build_fr)
scripts/i18n.py               The French mirror: extracts every reader-facing string from a built English
                              page (text runs with their inline markup, title/placeholder/aria attributes,
                              JS literals in screen-facing contexts, and the embedded JSON data by per-page
                              rules — prose and entity names yes; enum-like keys the page JS filters and
                              colours on, no; slugs never), applies data/i18n/fr.json, rewrites internal
                              links to /fr/, adds <html lang="fr"> and the language switch. Deterministic,
                              no key needed: an untranslated string stays English and is counted
scripts/translate.py          Fills data/i18n/fr.json: builds, extracts, sends what the cache lacks to
                              claude-opus-5 in batches (stdlib urllib, like every script here), saves
                              after each batch, prunes stale strings, rebuilds. First run is the whole
                              site; after that, only what changed in Notion or a template.
                              ./deploy.sh translate on the VPS (the key lives in /opt/kosmos/.env)
data/i18n/fr.json             English → French, keyed by sha1 of the English; the English kept beside it
                              so it is reviewable. Edit a French value by hand and it sticks until the
                              English changes
scripts/link_equations.py     Curated cross-link graph → the Equations DB "Related" relation
scripts/link_elements.py      Equation → element graph → the Equations DB "Elements" relation
                              (dual-property: each element page gets an "Equations" backlink)
scripts/link_minerals.py      Equation → mineral graph → the Equations DB "Minerals" relation
                              (dual-property; only minerals present in the Minerals DB)
scripts/link_cosmos.py        Equation → spectral types / celestial objects / instruments /
                              theories — four dual-property relations, one script
scripts/seed_constants.py     Creates + seeds the Constants and Units databases (CODATA 2022,
                              IAU nominal, Planck 2018 / SH0ES 2022)
scripts/link_constants.py     Constant → equation graph ("appears in" chips)
scripts/seed_theories.py      Fills the Theories and Researchers databases (both already existed
                              but were near-empty); adds missing schema properties and backfills
                              blank fields without overwriting anything a human set
scripts/link_theories.py      Theory → researcher (Proponent) and theory → equation relations,
                              from the maps in seed_theories.py
scripts/seed_abundance.py     Adds "Crustal Abundance" (ppm by mass) to the Elements DB and
                              fills all 118 rows — the data behind the Rarity lens
scripts/seed_timeline.py      Creates + seeds the Cosmic Timeline DB (30 events, Planck epoch to
                              heat death) and links each to its equations and theories. Sorted on
                              "Seconds After Big Bang" — cosmic time is a number, not a date
scripts/seed_discoveries.py   Seeds the Observatories and Discoveries DBs, adds the observers the
                              Researchers DB was missing, and wires discoverer / observatory /
                              instrument relations. Reuses the helpers in seed_theories.py
scripts/seed_missions.py      Seeds the Space Missions DB (37, Sputnik to Europa Clipper). The one
                              table that keeps real dates: a launch is a recorded instant, unlike a
                              founding year. Mission_ID left empty — see the docstring
scripts/link_timeline_people.py
                              Adds a Researchers relation to the Cosmic Timeline ("people whose
                              work is about this epoch" — distinct from a theory's Proponent) and
                              seeds it; also adds researchers the other seeds missed
scripts/seed_mining.py        Ore grade / ore minerals / mined-as / extraction onto the Elements DB
                              (72 elements) and ~90 flagship mines with coordinates into Mines [DB],
                              related to the elements they produce. The concentration factor
                              (grade ÷ crustal abundance) is derived at build time, never stored
scripts/make_basemap.py       Natural Earth 110m land → web/land-110m.svgpath (run once, committed)
scripts/fetch_webmineral.py   Formula, molecular weight, density, hardness and mass-% composition
                              for every mineral from webmineral.com → data/chemistry/webmineral.json
                              (committed; the Minerals DB was a broken parse of this very source)
scripts/seed_minerals_fix.py  Rewrites the Minerals DB from that file — Formula, true Molar Mass,
                              per-element MASS % (replacing counts that were wrong), clears the
                              derived columns — and adds the ore minerals the DB lacked
scripts/seed_engineering.py   The engineering half: ~30 machines and ~22 hands-on skills into two
                              new DBs, plus the cycle equations (Carnot, Otto, Diesel, Brayton, COP,
                              Betz…) and ~30 inventors they link to. build.py draws each heat
                              engine's p–V cycle from the cycle name
scripts/seed_glossary.py      Creates + seeds Glossary [DB] (~205 terms with domain, definition,
                              aliases). "Appears in" links are computed by build.py, never stored
scripts/seed_nobel.py         Adds a Nobel field to the Researchers DB and marks the laureates on
                              file; `--diff LIST` reports which names in a list are not researchers yet
scripts/seed_localgroup.py    Seeds the Local Group (44 members) into Celestial_Objects — distance in
                              light-years, morphology, subgroup, notes. build.py draws the log-radial
                              map on /cosmos; uncertain masses are left blank
scripts/notion_peek.py        Read-only: prints the schema, row count and sample rows of any Notion
                              data source whose title matches — for writing seeds against unseen DBs
scripts/seed_life.py          Creates + seeds Life [DB] (16 molecular machines) with an Elements
                              column that chips through to the periodic table, where seed_biology.py
                              has put the matching biological role
scripts/seed_biology.py       Adds Biological Role + Class to the Elements DB (34 filled) and
                              Biological Role to the Minerals DB (18 biominerals)
scripts/seed_biologists.py    Adds 19 biologists to the Researchers DB, which had none
scripts/seed_solar.py         Creates + seeds Solar System [DB] (9 bodies + the Sun) with Standish's
                              Keplerian elements and per-century rates. No positions are stored:
                              /solar solves Kepler's equation client-side for whatever date is set
scripts/seed_impacts.py       Creates + seeds Mining Impacts [DB] (18 mechanisms — acid mine drainage,
                              tailings dam failure, silicosis…) with mechanism, mitigation and a
                              documented case. Where names mine Types, so build.py counts how many
                              mines on the site each applies to; nothing is stored per-site
scripts/seed_foundations.py   The mathematics the physics is written in, and the mechanics it forgot:
                              vectors & geometry (13), calculus (8), mechanics (18) into the Equations
                              DB, plus a Requires / Required By dual self-relation — a dependency
                              graph, distinct from the looser Related web — with ~100 edges, many
                              from existing equations back to their new prerequisites; and hooks
                              from Machines and Skills to torque, power, friction and the rest.
                              Also wires the cycle family (Carnot, Otto, Diesel, Brayton, COP…),
                              which had no equation links at all. Re-runnable: unions, never resets
scripts/seed_fluids_waves.py  Fluids (12: hydrostatics, Pascal, Archimedes, viscosity, Reynolds,
                              Poiseuille, Stokes, Darcy, drag, Torricelli, hydraulic power, capillary
                              rise) and waves (7: v = fλ, standing waves, refractive index, thin lens,
                              inverse-square, Rayleigh criterion, decibel), with Requires edges into
                              the foundations and back from Navier–Stokes, Doppler, redshift and the
                              rest. Hooks: hydro turbines, soldering/brazing/casting, every telescope,
                              and a new Impacts ↔ Equations dual relation (Darcy on drainage, Stokes
                              on tailings) that /impacts and /equations both render
scripts/seed_billiards.py     The physics of the pool table — companion to the pool-sauce-engine
                              repo, which integrates these equations while this shelf states them.
                              Ten equations (ninety-degree rule, ghost-ball aim, throw, tip offset →
                              spin, slide-to-roll, thirty-degree rule, cushion rebound, cue-to-ball
                              speed transfer in a Billiards field; restitution and rolling resistance
                              in Mechanics), all with Requires edges onto momentum, energy, friction,
                              torque and projection; and three Skills in a Cue sports category (The
                              Cut Shot, Follow Draw and Stun, Using Side). build.py attaches a lookup
                              table to the ninety-degree rule quoting poolsauce/constants.py, so the
                              shelf and the engine never disagree on a number
scripts/seed_explainers.py    Creates + seeds Explainers [DB] (~40 people, channels and organisations
                              who explain the material — not the Researchers DB, which is who did the
                              work). The glossary terms each covers are computed by build.py from the
                              Covers prose, and the same match lists them on /glossary
deploy/                       systemd unit + nginx site as deployed on the VPS
```

## The page

All 118 elements, laid out on the standard 18-column table with the f-block
below. Color lenses: category, state at an adjustable temperature (drag from
−273 °C to 5750 °C and watch things melt and boil), s/p/d/f block, natural
origin, and heatmaps for mass, density (log), melting/boiling points, and
discovery year with a "known by year" time slider. Clicking an element shows
every property from Notion, including its gaps — missing values render as
dashes, never invented numbers.

The category palette was validated for color-blind safety in both light and
dark mode. Two data quirks are handled honestly: alkali metals carry only a
`#Metal` tag in Notion, so that category is derived from group 1 and labeled
as derived; elements with unknown chemical properties get a neutral outlined
tile rather than a fake category color.

## The analyzer

**⚛ analyze an object** photographs or uploads an image, which `server.js`
sends to Claude (`claude-opus-5`) with a strict JSON schema. The response —
object, confidence, materials with mass shares, elemental composition, honest
caveats — renders as a summary strip plus an "Analysis" lens: the object's
elements light up on the table as a log-scale mass heatmap, everything else
ghosts out.

Guardrails: images are downscaled client-side, requests are rate-limited per
IP (10 per 10 minutes), refusals and upstream errors surface as readable
messages, and without `ANTHROPIC_API_KEY` the endpoint degrades to a clear
"not configured" response while the rest of the site works.

## Running

```
npm install
ANTHROPIC_API_KEY=sk-ant-... node server.js   # http://127.0.0.1:3002
```

To refresh data from Notion and rebuild the pages:

```
NOTION_TOKEN=ntn_... python3 scripts/fetch_elements.py
NOTION_TOKEN=ntn_... python3 scripts/fetch_all.py
python3 scripts/build.py
```

## Deployment

Runs on the yeahborhood VPS as `kosmos.service` (port 3002) behind nginx with
its own Let's Encrypt cert — configs in `deploy/`. Secrets live in
`/opt/kosmos/.env` (see `.env.example`), never in this repo.

To ship an update, from the VPS clone at `/srv/kosmos`:

```
./deploy.sh                       # pull, sync from Notion, build, ship, verify, commit, push
./deploy.sh seed_missions         # ...running scripts/seed_missions.py first (any number, in order)
./deploy.sh --no-fetch            # code-only: skip the Notion pull
```

It stops at the first failure and names the step. Two checks it will not skip:
it waits for `/health` and requires the answering process to have **started
after the restart** — a stale server that never went down would otherwise pass
with the pages it loaded last time — and it requires `missing` to be empty. It
also recovers the state an interrupted run leaves behind (data synced but
uncommitted), and refuses to run if anything outside `data/` and `public/` is
dirty, because that clone is a deploy target, not a workspace.

**Push-to-deploy**: `.github/workflows/deploy.yml` runs the same
`./deploy.sh --no-fetch` over SSH on every push to `main` (and on demand from
the Actions tab, where the arguments can be changed — e.g. to run seeds).
It needs three repository secrets — `DEPLOY_SSH_KEY` (a dedicated
`ssh-keygen -t ed25519` private key whose public half is in the VPS user's
`authorized_keys`), `DEPLOY_HOST`, `DEPLOY_USER` — plus optional
`DEPLOY_PORT`, `DEPLOY_DIR` (default `/srv/kosmos`) and `DEPLOY_KNOWN_HOSTS`
(`ssh-keyscan <host>`; without it the first connection trusts-on-first-use).
Until the secrets exist the job exits green with a warning instead of failing
every push. The workflow skips commits starting with `Sync from Notion`, so
the push `deploy.sh` itself makes at the end of a run does not re-trigger it,
and a concurrency group queues overlapping deploys instead of racing them.

By hand, the equivalent is:

```
cp public/*.html public/*.json /opt/kosmos/public/   # NOT /opt/kosmos — server.js reads public/
cp server.js /opt/kosmos/                # only when routes or the API changed
systemctl restart kosmos
curl -s localhost:3002/health            # {"ok":true,...,"missing":[]}
```

The pages live in `/opt/kosmos/public/`, beside `server.js` at `/opt/kosmos/`.
Copying the HTML flat into `/opt/kosmos/` silently deploys nothing: the files
land where nothing reads them and the old pages keep being served. That is
exactly what happened on 2026-08-15, and it only surfaced as an outage once a
new route was added for a page that had never arrived. The same day, four
hand-typed deploy chains left the VPS clone dirty — three dropped the commit
step, one was killed by `curl` racing the restart — which is why `deploy.sh`
exists.

### Recipe: putting an app on a yeahborhood.com subdomain

How kosmos (and musicator) got their subdomains — reusable for the next app:

1. **DNS** — nothing to do: `*.yeahborhood.com` wildcards to the VPS
   (5.78.43.168), so any new subdomain resolves immediately.
2. **App** — deploy to `/opt/<name>`, listening on `127.0.0.1:<port>`
   (pick a free port; kosmos=3002, musicator=3001). Add a systemd unit
   `/etc/systemd/system/<name>.service` (copy `deploy/kosmos.service`,
   change paths/port), then `systemctl enable --now <name>`.
3. **nginx, HTTP first** — `/etc/nginx/sites-available/<name>` with a
   port-80 block: ACME webroot at `/var/www/acme` + redirect to HTTPS
   (see the first block of `deploy/nginx-kosmos.conf`). Symlink into
   `sites-enabled`, `nginx -t`, reload.
4. **Certificate** — `certbot certonly --nginx -d <name>.yeahborhood.com`.
5. **nginx, HTTPS** — append the 443 block (second block of
   `deploy/nginx-kosmos.conf`): `listen 5.78.43.168:443 ssl` — the
   explicit IP matters, tailscaled holds :443 on the tailnet address —
   pointing `ssl_certificate` at the new cert and proxying to the app's
   port. `nginx -t`, reload. Done.

Certbot renews automatically; the nginx blocks and unit files in
`deploy/` are the living reference.
