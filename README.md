# kosmos

A multi-disciplinary science portal — a personal atlas of the physical world.
Live at **https://kosmos.yeahborhood.com**.

Notion is the source of truth for authored content; this repo is the source of
truth for code and the normalised data snapshots. Sync is one-way, Notion → repo.

## Pages

| Route        | What's there |
|--------------|--------------|
| `/`          | Tile launcher with live stats per section |
| `/elements`  | Interactive periodic table (10 lenses incl. crustal rarity, temperature + discovery sliders) and the AI photo analyzer |
| `/minerals`  | 3,000+ minerals searchable and filterable by contained element; gemstone shelf, rock families, silicate classes |
| `/cosmos`    | Field guide to celestial object classes, the stellar spectral sequence, observatories, a discovery timeline, instruments and researchers |
| `/forces`    | The four fundamental interactions |
| `/timeline`  | The universe's history on a log axis of seconds — Planck epoch to heat death, cross-linked to the equations and theories |
| `/theories`  | Theory shelf from Ptolemy to the holographic principle — status, proponents, and the equations each rests on; sortable chronologically |
| `/equations` | Canonical equations with symbols decoded, filterable by field |
| `/constants` | CODATA constants with uncertainties, SI units, prefixes |

## Layout

```
server.js                     Node server: static pages + POST /api/analyze
public/                       Built pages (generated — see scripts/build.py)
web/                          Page sources: templates, shared.css, analyzer parts
data/chemistry/elements.json  Normalised element data (scripts/fetch_elements.py)
data/notion-all.json          All other Notion sources (scripts/fetch_all.py)
scripts/build.py              web/ + data → public/*.html
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
cp public/*.html /opt/kosmos/public/     # NOT /opt/kosmos — server.js reads public/
cp server.js /opt/kosmos/                # only when routes or the API changed
systemctl restart kosmos
curl -s localhost:3002/health            # {"ok":true,...,"missing":[]}
```

The pages live in `/opt/kosmos/public/`, beside `server.js` at `/opt/kosmos/`.
Copying the HTML flat into `/opt/kosmos/` silently deploys nothing: the files
land where nothing reads them and the old pages keep being served. That is
exactly what happened on 2026-08-15, and it only surfaced as an outage once a
new route was added for a page that had never arrived. `/health` now reports
which pages are missing, so check it after every deploy.

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
