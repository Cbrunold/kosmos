import http from 'node:http';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
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
  '/equations': 'equations.html',
  '/constants': 'constants.html',
};
// A page that failed to deploy should 404, not take the whole site down with it.
// This used to be an unguarded readFileSync inside a map: adding /timeline to
// PAGES and deploying the HTML to the wrong directory put the process into a
// crash loop, and every other page went with it.
const CONTENT = {};
const missing = [];
for (const [route, file] of Object.entries(PAGES)) {
  try {
    CONTENT[route] = readFileSync(join(here, 'public', file));
  } catch (e) {
    missing.push(`${route} (${file}: ${e.code || e.message})`);
  }
}

const STARTED_AT = Date.now();   // /health reports it, so a deploy can tell a fresh process from a stale one
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
  if ((req.method === 'GET' || req.method === 'HEAD') && CONTENT[route]) {
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-cache',   // always revalidate so deploys show up immediately
    });
    return res.end(CONTENT[route]);
  }
  if (req.method === 'GET' && req.url === '/health') {
    return json(res, 200, {
      ok: missing.length === 0,
      analyzer: hasKey,
      pages: Object.keys(CONTENT).length,
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
  console.log(`kosmos listening on 127.0.0.1:${PORT} — ${Object.keys(CONTENT).length}/${Object.keys(PAGES).length} pages (analyzer: ${hasKey ? 'enabled' : 'DISABLED — set ANTHROPIC_API_KEY'})`);
  if (missing.length) console.error(`MISSING PAGES, serving 404 for: ${missing.join(', ')}`);
});
