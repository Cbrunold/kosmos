# kosmos

A multi-disciplinary science portal — a personal atlas of the physical world.
Live at **https://kosmos.yeahborhood.com**.

Notion is the source of truth for authored content; this repo is the source of
truth for code and the normalised data snapshots. Sync is one-way, Notion → repo.

## Pages

| Route        | What's there |
|--------------|--------------|
| `/`          | Tile launcher with live stats per section |
| `/elements`  | Interactive periodic table (9 lenses, temperature + discovery sliders) and the AI photo analyzer |
| `/minerals`  | 3,000+ minerals searchable and filterable by contained element; gemstone shelf, rock families, silicate classes |
| `/cosmos`    | Field guide to celestial object classes, the stellar spectral sequence, instruments, researchers |
| `/forces`    | The four fundamental interactions |
| `/theories`  | Theory shelf with status tracking (accepted / speculative / disproved) |

## Layout

```
server.js                     Node server: static pages + POST /api/analyze
public/                       Built pages (generated — see scripts/build.py)
web/                          Page sources: templates, shared.css, analyzer parts
data/chemistry/elements.json  Normalised element data (scripts/fetch_elements.py)
data/notion-all.json          All other Notion sources (scripts/fetch_all.py)
scripts/build.py              web/ + data → public/*.html
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

To ship an update: copy `server.js` and `public/*.html` to `/opt/kosmos/`
and `systemctl restart kosmos`.
