
// ---- the shared header (scripts/chrome.py): the sections panel, and one search engine
// for every page. The index (/search.json) is fetched on the first keystroke, never on
// load. KosmosSearch.attach() wires an input + results box; the home page's hero search
// uses it too, so there is one scorer and one renderer for the whole site.
window.KosmosSearch = (() => {
  const KINDS = {
    page:           ['section',       'var(--ink-2)'],
    element:        ['elements',      'var(--c-blue)'],
    mineral:        ['minerals',      'var(--c-teal)'],
    gemstone:       ['gemstones',     'var(--c-teal)'],
    equation:       ['equations',     'var(--c-amber)'],
    constant:       ['constants',     'var(--c-teal)'],
    unit:           ['units',         'var(--c-teal)'],
    theory:         ['theories',      'var(--c-pink)'],
    event:          ['timeline',      'var(--c-bronze)'],
    researcher:     ['researchers',   'var(--c-violet)'],
    discovery:      ['discoveries',   'var(--c-cyan)'],
    observatory:    ['observatories', 'var(--c-bronze)'],
    mission:        ['missions',      'var(--c-blue)'],
    instrument:     ['instruments',   'var(--c-violet)'],
    object:         ['objects',       'var(--c-amber)'],
    'spectral type':['spectral types','var(--c-violet)'],
    'object class': ['object classes','var(--c-violet)'],
    mine:           ['mines',         'var(--c-bronze)'],
    machine:        ['machines',      'var(--c-amber)'],
    skill:          ['skills',        'var(--c-green)'],
    term:           ['glossary',      'var(--c-slate)'],
    explainer:      ['explainers',    'var(--c-red)'],
    impact:         ['impacts',       'var(--c-cyan)'],
    life:           ['life',          'var(--c-green)'],
    force:          ['forces',        'var(--c-red)'],
  };
  const KIND_ORDER = Object.keys(KINDS);
  // the French mirror: every result stays inside /fr/
  const LANG_PREFIX = document.documentElement.lang === 'fr' ? '/fr' : '';

  // NFKD, not NFD: it also folds subscripts and superscripts, so "H₀" is searchable as "h0"
  const fold = (s) => (s || '').toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '');
  const words = (s) => s.split(/[^a-z0-9]+/).filter(Boolean);

  let INDEX = null, loading = null;

  function load(stat) {
    if (INDEX) return Promise.resolve(INDEX);
    if (loading) return loading;
    if (stat) stat.textContent = 'loading…';
    loading = fetch('/search.json').then((r) => r.json()).then((d) => {
      INDEX = d.items.map(([kind, name, sub, text, href]) => ({
        kind, name, sub, text, href,
        fn: fold(name), fs: fold(sub), ft: fold(text),
      }));
      if (stat) stat.textContent = `${INDEX.length.toLocaleString('en')} entries`;
      return INDEX;
    }).catch(() => { if (stat) stat.textContent = 'index unavailable'; loading = null; });
    return loading;
  }

  function score(it, tokens) {
    let s = 0;
    for (const t of tokens) {
      if (it.fn === t) s += 12;                                  // "gold" → Gold
      else if (words(it.fn).includes(t)) s += 10;                // "einstein" → Albert Einstein, not Einsteinium
      else if (words(it.fs).includes(t)) s += 10;                // "fe" → Iron: the symbol lives in the subtitle
      else if (it.fn.startsWith(t)) s += 8;
      else if (words(it.fn).some((w) => w.startsWith(t))) s += 6;
      else if (it.fn.includes(t)) s += 4;
      else if (it.fs.includes(t)) s += 2.5;
      else if (it.ft.includes(t)) s += 1;
      else return 0;                                             // every token must hit somewhere
    }
    if (it.kind === 'page') s += 1.5;      // a section is usually what a one-word query means
    return s + Math.max(0, 2 - it.fn.length / 30);   // nudge shorter names up on ties
  }

  function highlight(name, tokens) {
    const el = document.createElement('span');
    const f = fold(name);
    // mark the first token's first occurrence — enough to show why it matched.
    // Folding can change the string length (ligatures, ℃ → °C); only mark when it did not.
    const t = tokens.find((x) => f.includes(x));
    const i = t && f.length === name.length ? f.indexOf(t) : -1;
    if (i < 0) { el.textContent = name; return el; }
    el.append(name.slice(0, i));
    const m = document.createElement('mark'); m.textContent = name.slice(i, i + t.length); el.appendChild(m);
    el.append(name.slice(i + t.length));
    return el;
  }

  // input: the <input>; box: the results container; stat: an optional element that
  // shows the index size; prefix: class prefix for the rows ('' on home, 'kh-' in the
  // header); shortcut: whether "/" focuses this box (home only — other pages have their
  // own filter boxes on that key)
  function attach({ input, box, stat = null, prefix = '', shortcut = false }) {
    const PER_GROUP = 5;
    const q = input;
    const cls = (n) => prefix + n;
    let rows = [], active = -1, timer = null;

    function close() { box.hidden = true; q.setAttribute('aria-expanded', 'false'); }

    function render(query) {
      const tokens = fold(query).split(/\s+/).filter(Boolean);
      box.textContent = ''; rows = []; active = -1;
      if (!tokens.length || !INDEX) { close(); return; }
      const hits = [];
      for (const it of INDEX) { const sc = score(it, tokens); if (sc > 0) hits.push([sc, it]); }
      hits.sort((a, b) => b[0] - a[0] || a[1].name.localeCompare(b[1].name));
      box.hidden = false; q.setAttribute('aria-expanded', 'true');
      if (!hits.length) {
        const e = document.createElement('div'); e.className = cls('rempty'); e.textContent = `Nothing matches “${query.trim()}”.`;
        box.appendChild(e); return;
      }
      const groups = new Map();
      for (const [, it] of hits) { if (!groups.has(it.kind)) groups.set(it.kind, []); groups.get(it.kind).push(it); }
      for (const kind of KIND_ORDER) {
        const list = groups.get(kind); if (!list) continue;
        const [label, color] = KINDS[kind];
        const g = document.createElement('div'); g.className = cls('rgroup');
        const h = document.createElement('div'); h.className = cls('rhead');
        const dot = document.createElement('span'); dot.className = cls('dot'); dot.style.background = color;
        const n = document.createElement('span'); n.className = cls('n'); n.textContent = list.length;
        h.append(dot, document.createTextNode(label), n);
        g.appendChild(h);
        for (const it of list.slice(0, PER_GROUP)) {
          const a = document.createElement('a');
          a.className = cls('rrow'); a.href = LANG_PREFIX + it.href; a.setAttribute('role', 'option'); a.dataset.i = rows.length;
          const rn = document.createElement('div'); rn.className = cls('rn'); rn.appendChild(highlight(it.name, tokens));
          if (it.sub) { const rs = document.createElement('span'); rs.className = cls('rs'); rs.textContent = it.sub; rn.appendChild(rs); }
          a.appendChild(rn);
          if (it.text) { const rt = document.createElement('div'); rt.className = cls('rt'); rt.textContent = it.text; a.appendChild(rt); }
          a.addEventListener('mousemove', () => setActive(+a.dataset.i));
          g.appendChild(a); rows.push(a);
        }
        if (list.length > PER_GROUP) {
          const m = document.createElement('div'); m.className = cls('rmore');
          m.textContent = `+ ${list.length - PER_GROUP} more ${label} — keep typing to narrow`;
          g.appendChild(m);
        }
        box.appendChild(g);
      }
      const f = document.createElement('div'); f.className = cls('rfoot');
      f.textContent = `${hits.length.toLocaleString('en')} result${hits.length === 1 ? '' : 's'} across ${groups.size} section${groups.size === 1 ? '' : 's'} · ↑↓ to move · Enter to open · Esc to clear`;
      box.appendChild(f);
    }

    function setActive(i) {
      if (active >= 0 && rows[active]) rows[active].setAttribute('aria-selected', 'false');
      active = i;
      if (active >= 0 && rows[active]) { rows[active].setAttribute('aria-selected', 'true'); rows[active].scrollIntoView({ block: 'nearest' }); }
    }

    q.addEventListener('input', () => {
      clearTimeout(timer);
      const v = q.value;
      if (!v.trim()) { render(''); return; }
      if (INDEX) { timer = setTimeout(() => render(v), 40); return; }   // loaded: debounce
      load(stat).then(() => { if (q.value === v) render(v); });        // loading: render the latest query once it lands
    });
    q.addEventListener('focus', () => { load(stat); if (q.value.trim() && INDEX) render(q.value); });
    q.addEventListener('keydown', (ev) => {
      if (ev.key === 'ArrowDown') { ev.preventDefault(); if (rows.length) setActive(Math.min(rows.length - 1, active + 1)); }
      else if (ev.key === 'ArrowUp') { ev.preventDefault(); if (rows.length) setActive(Math.max(0, active - 1)); }
      else if (ev.key === 'Enter') { if (active >= 0 && rows[active]) { ev.preventDefault(); location.href = rows[active].href; } else if (rows.length) { ev.preventDefault(); location.href = rows[0].href; } }
      else if (ev.key === 'Escape') { q.value = ''; render(''); q.blur(); }
    });
    if (shortcut) {
      document.addEventListener('keydown', (ev) => {
        if (ev.key === '/' && !ev.metaKey && !ev.ctrlKey && !ev.altKey && document.activeElement !== q
            && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '')) {
          ev.preventDefault(); q.focus();
        }
      });
    }
    document.addEventListener('click', (ev) => { if (!q.parentElement.contains(ev.target)) close(); });
    return { render, load: () => load(stat) };
  }

  return { attach };
})();

(() => {
  const hdr = document.querySelector('.khdr');
  if (!hdr) return;
  const btn = hdr.querySelector('.kh-menu'), panel = hdr.querySelector('.kh-panel');
  const setOpen = (on) => { panel.hidden = !on; btn.setAttribute('aria-expanded', String(on)); };
  btn.addEventListener('click', () => setOpen(panel.hidden));
  document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape' && !panel.hidden) { setOpen(false); btn.focus(); } });
  document.addEventListener('click', (ev) => { if (!panel.hidden && !hdr.contains(ev.target)) setOpen(false); });
  const q = hdr.querySelector('.kh-q');
  if (q) KosmosSearch.attach({ input: q, box: hdr.querySelector('.kh-results'), prefix: 'kh-' });
})();
