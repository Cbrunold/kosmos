import http from 'node:http';
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, extname, join } from 'node:path';
import Anthropic from '@anthropic-ai/sdk';

const here = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 3002);

const PAGES = {
  '/': 'home.html',
  '/elements': 'index.html',
  '/index.html': 'index.html',
  '/minerals': 'minerals.html',
  '/cosmos': 'cosmos.html',
  '/forces': 'forces.html',
  '/theories': 'theories.html',
  '/timeline': 'timeline.html',
  '/mines': 'mines.html',
  '/machines': 'machines.html',
  '/skills': 'skills.html',
  '/glossary': 'glossary.html',
  '/scales': 'scales.html',
  '/universe': 'universe.html',
  '/solar': 'solar.html',
  '/life': 'life.html',
  '/people': 'people.html',
  '/explainers': 'explainers.html',
  '/impacts': 'impacts.html',
  '/billiards': 'billiards.html',
  '/equations': 'equations.html',
  '/constants': 'constants.html',
  '/search.json': 'search.json',   // the index behind the search box, fetched on first keystroke
  '/sitemap.xml': 'sitemap.xml',   // both written by scripts/build.py (see scripts/chrome.py)
  '/robots.txt': 'robots.txt',
};
// The French mirror: /fr and /fr/<route> serve public/fr/<file>, which scripts/build.py derives
// from the English pages through data/i18n/fr.json. Same health rules: a missing file 404s alone.
for (const [route, file] of Object.entries({ ...PAGES })) {
  if (!file.endsWith('.html')) continue;
  PAGES[route === '/' ? '/fr' : '/fr' + route] = 'fr/' + file;
}
PAGES['/fr/'] = 'fr/home.html';
const TYPE = (file) => ({ json: 'application/json; charset=utf-8', xml: 'application/xml; charset=utf-8',
                          txt: 'text/plain; charset=utf-8' }[file.split('.').pop()] || 'text/html; charset=utf-8');

// Static assets (public/assets): the home banner and anything else binary the build
// copies rather than writes. Read once at boot like the pages, so a request never
// touches the disk; an absent directory is not fatal, for the same reason a missing
// page is not — the rest of the site still serves. The filename carries its own
// version (kosmos-banner-v2.webp), so unlike the pages these can be cached hard.
const ASSET_TYPE = { '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg',
                     '.svg': 'image/svg+xml', '.avif': 'image/avif',
                     // the entity pages' shared stylesheet and script, content-hashed by the build
                     '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8' };
const ASSETS = {};
try {
  for (const name of readdirSync(join(here, 'public', 'assets'))) {
    const type = ASSET_TYPE[extname(name).toLowerCase()];
    if (type) ASSETS['/assets/' + name] = { body: readFileSync(join(here, 'public', 'assets', name)), type };
  }
} catch { /* no assets directory: the site is text, it still serves */ }
// A page that failed to deploy should 404, not take the whole site down with it.
// This used to be an unguarded readFileSync inside a map: adding /timeline to
// PAGES and deploying the HTML to the wrong directory put the process into a
// crash loop, and every other page went with it.
const CONTENT = {};
const ETAG = {};       // per route, from the bytes: a redeploy that changes nothing keeps the tag
const missing = [];
const etagOf = (buf) => '"' + createHash('sha1').update(buf).digest('base64url').slice(0, 22) + '"';
// ---- the entity pages: public/entities/<route>/<slug>.html and public/entities/fr/…, one file per
// entity per language, written by the build and never committed. A few kilobytes each; all in memory.
let nEntities = 0;
try {
  for (const rel of readdirSync(join(here, 'public', 'entities'), { recursive: true })) {
    if (!rel.endsWith('.html')) continue;
    const route = '/' + rel.replace(/\\/g, '/').replace(/\.html$/, '');
    PAGES[route] = 'entities/' + rel.replace(/\\/g, '/');
    nEntities++;
  }
} catch (e) {
  console.error(`no entity pages (${e.message}) — the build writes them; server.js falls back to rewriting the shelf`);
}
for (const [route, file] of Object.entries(PAGES)) {
  try {
    CONTENT[route] = readFileSync(join(here, 'public', file));
    ETAG[route] = etagOf(CONTENT[route]);
  } catch (e) {
    missing.push(`${route} (${file}: ${e.code || e.message})`);
  }
}

const STARTED_AT = Date.now();   // /health reports it, so a deploy can tell a fresh process from a stale one
const LAST_MODIFIED = new Date(STARTED_AT).toUTCString();   // pages are loaded at boot, so that is when they changed
const SITE = 'https://kosmos.yeahborhood.com';

// ---- entity URLs. /equations/pythagorean-theorem is the equations page with that entity's
// title and preview in its head, landing the reader on its card — so a link to one thing
// unfurls as that thing, not as the whole shelf. The map comes from search.json, which
// already names every entity with the page and anchor it lives at; anything else is a 404.
// Bodies are made per request (a few string replacements on the page) rather than cached:
// fifteen hundred variants of a 300KB page would be most of the box's memory.
const ENTITY = {};   // route -> anchor -> { name, sub, text }
try {
  for (const [, name, sub, text, href] of JSON.parse(CONTENT['/search.json'].toString()).items) {
    const [route, anchor] = href.split('#');
    if (!anchor || !/^[a-z0-9-]+$/.test(anchor) || !(PAGES[route] || '').endsWith('.html')) continue;
    (ENTITY[route] ||= {})[anchor] ||= { name, sub, text };
  }
} catch (e) {
  console.error(`entity map: ${e.message}`);
}
const escapeHtml = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');
function entityPage(path) {
  const m = path.match(/^(\/fr)?(\/[a-z]+)\/([a-z0-9-]+)$/);
  if (!m) return null;
  const fr = m[1] || '', route = m[2], anchor = m[3];
  const e = ENTITY[route] && ENTITY[route][anchor];
  const base = CONTENT[fr + route];
  if (!e || !base) return null;
  const title = `${escapeHtml(e.name)} · Kosmos`;
  const desc = escapeHtml((e.text || e.sub || '').slice(0, 200));
  const url = SITE + path;
  const sub = (re, s) => { html = html.replace(re, () => s); };
  let html = base.toString();
  sub(/<title>[^<]*<\/title>/, `<title>${title}</title>`);
  sub(/<meta name="description" content="[^"]*">/, `<meta name="description" content="${desc}">`);
  sub(/<meta property="og:title" content="[^"]*">/, `<meta property="og:title" content="${title}">`);
  sub(/<meta property="og:description" content="[^"]*">/, `<meta property="og:description" content="${desc}">`);
  sub(/<link rel="canonical" href="[^"]*">/, `<link rel="canonical" href="${url}">`);
  sub(/<meta property="og:url" content="[^"]*">/, `<meta property="og:url" content="${url}">`);
  // the page's own openHash() reads location.hash once its script runs; put it there first,
  // and leave the address bar on the hash form every link on the site uses
  sub(/<!--\/khead-->/, `<!--/khead--><script>history.replaceState(null, '', ${JSON.stringify(`${fr}${route}#${anchor}`)});</script>`);
  const body = Buffer.from(html);
  // the tag follows the page's: a redeploy that changes the section page changes every entity's
  return { body, tag: etagOf(Buffer.from(ETAG[fr + route] + path)), type: TYPE(PAGES[route]) };
}
const hasKey = Boolean(process.env.ANTHROPIC_API_KEY);
const client = hasKey ? new Anthropic() : null;

const SCHEMA = {
  type: 'object',
  properties: {
    object: { type: 'string', description: 'Short name of the primary object identified in the photo' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    summary: {
      type: 'string',
      description: 'One or two sentences: what the object is and what it is made of, written for a science-curious reader',
    },
    materials: {
      type: 'array',
      description: 'Main materials the object is made of, largest share first',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          sharePercent: { type: 'number', description: 'Approximate share of the object mass, 0-100' },
          note: { type: 'string', description: 'Brief note, e.g. alloy grade or typical formulation' },
        },
        required: ['name', 'sharePercent', 'note'],
        additionalProperties: false,
      },
    },
    elements: {
      type: 'array',
      description: 'Estimated elemental composition by mass across the whole object, largest first',
      items: {
        type: 'object',
        properties: {
          symbol: { type: 'string', description: 'Standard element symbol, e.g. Fe' },
          name: { type: 'string' },
          massPercent: { type: 'number', description: 'Approximate percent of total mass, 0-100' },
          source: { type: 'string', description: 'Which material(s) this element mainly comes from' },
        },
        required: ['symbol', 'name', 'massPercent', 'source'],
        additionalProperties: false,
      },
    },
    caveats: { type: 'string', description: 'Honest caveats: what is assumed, what cannot be known from a photo' },
  },
  required: ['object', 'confidence', 'summary', 'materials', 'elements', 'caveats'],
  additionalProperties: false,
};

const SYSTEM = `You are the analysis engine of Kosmos, a hobby science portal. Given a photo, identify the single primary object (if several, pick the most prominent) and estimate what it is made of.

Rules:
- Use typical/representative compositions for the object class you identify (e.g. a beverage can: aluminium alloy 3004 body; a wine glass: soda-lime glass). You cannot measure a photo — say so in caveats.
- materials shares should sum to roughly 100. elements massPercent should also sum to roughly 100 and be consistent with the materials.
- Cover at least the elements making up ~95% of mass; group the long tail honestly in caveats rather than inventing trace values.
- Use standard element symbols (H through Og). Water counts as H and O; organic matter as C, H, O, N, etc.
- If the image shows no identifiable object (blank wall, abstract pattern), say so in summary, set confidence low, and return empty materials/elements.`;

function json(res, code, body) {
  const data = JSON.stringify(body);
  res.writeHead(code, { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) });
  res.end(data);
}

// simple per-IP rate limit: 10 analyses / 10 minutes
const hits = new Map();
function limited(ip) {
  const now = Date.now();
  const arr = (hits.get(ip) || []).filter((t) => now - t < 600_000);
  if (arr.length >= 10) return true;
  arr.push(now);
  hits.set(ip, arr);
  return false;
}

async function analyze(imageB64, mediaType) {
  const response = await client.beta.messages.create({
    model: 'claude-opus-5',
    max_tokens: 8000,
    betas: ['server-side-fallback-2026-07-01'],
    fallbacks: 'default',
    system: SYSTEM,
    output_config: { format: { type: 'json_schema', schema: SCHEMA } },
    messages: [{
      role: 'user',
      content: [
        { type: 'image', source: { type: 'base64', media_type: mediaType, data: imageB64 } },
        { type: 'text', text: 'Identify this object and break down its elemental composition.' },
      ],
    }],
  });

  if (response.stop_reason === 'refusal') {
    const err = new Error('Claude declined to analyze this image.');
    err.status = 422;
    throw err;
  }
  const text = response.content.find((b) => b.type === 'text')?.text;
  if (!text) {
    const err = new Error('Empty response from the model.');
    err.status = 502;
    throw err;
  }
  return JSON.parse(text);
}

const server = http.createServer(async (req, res) => {
  const route = (req.url || '/').split('?')[0].replace(/\/$/, '') || '/';
  const reading = req.method === 'GET' || req.method === 'HEAD';
  const page = reading && (CONTENT[route]
    ? { body: CONTENT[route], tag: ETAG[route], type: TYPE(PAGES[route]) }
    : entityPage(route));
  if (page) {
    // no-cache means "ask before reusing", and the ETag is what makes asking cheap: a
    // 345KB page a reader already has costs a 304 and nothing else. nginx turns the tag
    // weak (W/) when it gzips the body, so the comparison ignores that prefix.
    const given = (req.headers['if-none-match'] || '').split(',').map((s) => s.trim().replace(/^W\//, ''));
    if (given.includes(page.tag)) {
      res.writeHead(304, { 'ETag': page.tag, 'Cache-Control': 'no-cache' });
      return res.end();
    }
    res.writeHead(200, {
      'Content-Type': page.type,
      'Content-Length': page.body.length,
      'Cache-Control': 'no-cache',   // always revalidate so deploys show up immediately
      'ETag': page.tag,
      'Last-Modified': LAST_MODIFIED,
    });
    return res.end(req.method === 'HEAD' ? undefined : page.body);
  }
  if ((req.method === 'GET' || req.method === 'HEAD') && ASSETS[route]) {
    const asset = ASSETS[route];
    res.writeHead(200, {
      'Content-Type': asset.type,
      'Content-Length': asset.body.length,
      'Cache-Control': 'public, max-age=31536000, immutable',   // the version is in the filename
    });
    return res.end(req.method === 'HEAD' ? undefined : asset.body);
  }
  if (req.method === 'GET' && req.url === '/health') {
    return json(res, 200, {
      ok: missing.length === 0,
      analyzer: hasKey,
      pages: Object.keys(CONTENT).length,
      assets: Object.keys(ASSETS).length,
      missing,           // empty on a good deploy; names the files on a bad one
      startedAt: STARTED_AT,
      pid: process.pid,
    });
  }
  if (req.method === 'POST' && req.url === '/api/analyze') {
    if (!hasKey) return json(res, 503, { error: 'The analyzer is not configured yet (missing API key on the server).' });
    const ip = req.headers['x-real-ip'] || req.socket.remoteAddress;
    if (limited(ip)) return json(res, 429, { error: 'Too many analyses — try again in a few minutes.' });

    let size = 0;
    const chunks = [];
    req.on('data', (c) => {
      size += c.length;
      if (size > 12_000_000) { req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', async () => {
      try {
        const body = JSON.parse(Buffer.concat(chunks).toString());
        const { image, mediaType } = body;
        if (!image || !/^image\/(jpeg|png|webp|gif)$/.test(mediaType || '')) {
          return json(res, 400, { error: 'Send { image: <base64>, mediaType: image/jpeg|png|webp|gif }.' });
        }
        const result = await analyze(image, mediaType);
        return json(res, 200, result);
      } catch (e) {
        if (e instanceof Anthropic.RateLimitError) return json(res, 429, { error: 'The model is rate-limited right now — try again shortly.' });
        if (e instanceof Anthropic.APIError) return json(res, 502, { error: `Upstream error (${e.status}).` });
        return json(res, e.status || 500, { error: e.message || 'Analysis failed.' });
      }
    });
    return;
  }
  json(res, 404, { error: 'Not found' });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`kosmos listening on 127.0.0.1:${PORT} — ${Object.keys(CONTENT).length}/${Object.keys(PAGES).length} pages (${nEntities} entity pages), ${Object.keys(ASSETS).length} assets (analyzer: ${hasKey ? 'enabled' : 'DISABLED — set ANTHROPIC_API_KEY'})`);
  if (missing.length) console.error(`MISSING PAGES, serving 404 for: ${missing.join(', ')}`);
});
