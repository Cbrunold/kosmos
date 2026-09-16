
  // ---------- molecule: a formula -> its atoms on the table, and a drawn structure for the shelf ----------
  // The analyzer above answers "what is this heap made of, by mass". This answers the other
  // question a chemistry T-shirt asks: "which atoms, and how many, make one molecule". The
  // composition is computed here from the formula and the atomic masses in Notion; the drawing
  // is hand-laid in data/chemistry/molecules.json and exists only for the shelf.
  const MOLS = JSON.parse(document.getElementById('moldata').textContent).molecules;
  const SUBS = '₀₁₂₃₄₅₆₇₈₉';
  const subscript = (s) => String(s).replace(/\d/g, (d) => SUBS[+d]);
  const massOf = Object.fromEntries(E.map((e) => [e.sym, e.atomicMass]));

  // "C8H10N4O2", "Ca(OH)2", "CH₃COOH" -> {C: 8, H: 10, ...}; throws on anything that is not a formula
  function parseFormula(str) {
    const s = str.replace(/[₀-₉]/g, (c) => SUBS.indexOf(c)).replace(/\s+/g, '');
    let i = 0;
    const num = () => { let n = ''; while (i < s.length && /\d/.test(s[i])) n += s[i++]; return n ? +n : 1; };
    const group = (close) => {
      const out = {};
      while (i < s.length) {
        const c = s[i];
        if (c === close) { i++; return out; }
        let part;
        if (c === '(' || c === '[') { i++; part = group(c === '(' ? ')' : ']'); }
        else if (/[A-Z]/.test(c)) {
          let sym = c; i++;
          if (/[a-z]/.test(s[i] || '')) sym += s[i++];
          if (!(sym in symToZ)) throw new Error(`${sym} is not an element`);
          part = { [sym]: 1 };
        } else throw new Error(`unexpected “${c}”`);
        const n = num();
        for (const [k, v] of Object.entries(part)) out[k] = (out[k] || 0) + v * n;
      }
      if (close) throw new Error('a parenthesis is not closed');
      return out;
    };
    const counts = group(null);
    if (!Object.keys(counts).length) throw new Error('nothing to read');
    return counts;
  }
  // Hill order: C, then H, then the rest alphabetically — everything alphabetical without carbon.
  // One key per compound, so "CH3COOH" finds acetic acid on the shelf.
  const hill = (counts) => {
    const first = counts.C ? ['C', ...(counts.H ? ['H'] : [])] : [];
    const rest = Object.keys(counts).filter((k) => !first.includes(k)).sort();
    return [...first, ...rest].map((k) => k + (counts[k] > 1 ? counts[k] : '')).join('');
  };
  const shelfByKey = new Map(MOLS.map((m) => [hill(parseFormula(m.formula)), m]));

  function composition(counts) {
    const atoms = Object.values(counts).reduce((s, n) => s + n, 0);
    const known = Object.keys(counts).every((k) => massOf[k] != null);
    const total = known ? Object.entries(counts).reduce((s, [k, n]) => s + massOf[k] * n, 0) : null;
    const rows = Object.entries(counts)
      .map(([sym, n]) => ({ sym, n, z: symToZ[sym], name: byZ[symToZ[sym]].name, pct: total ? (massOf[sym] * n / total) * 100 : null }))
      .sort((a, b) => (b.pct ?? 0) - (a.pct ?? 0) || b.n - a.n);
    return { rows, total, atoms };
  }

  // ---- the drawing: a skeletal formula, the convention the T-shirt uses. Unlabelled vertices are
  // carbons; hydrogens on carbon are implied; a double bond is a second line on the ring side.
  const BOND = 34, PAD = 22, LABEL_R = 9, GAP = 4.2;
  function drawMolecule(mol) {
    const NS = 'http://www.w3.org/2000/svg';
    const pts = mol.atoms.map((a) => ({ x: a.x * BOND, y: -a.y * BOND }));
    const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
    const x0 = Math.min(...xs) - PAD, y0 = Math.min(...ys) - PAD;
    const w = Math.max(...xs) - Math.min(...xs) + 2 * PAD, h = Math.max(...ys) - Math.min(...ys) + 2 * PAD;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', `${x0.toFixed(1)} ${y0.toFixed(1)} ${w.toFixed(1)} ${h.toFixed(1)}`);
    svg.setAttribute('width', Math.round(w));
    svg.setAttribute('height', Math.round(h));
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', `${mol.name}, skeletal formula`);
    const label = (a) => (a.lbl != null ? a.lbl : a.el === 'C' ? '' : a.el);
    const nbrs = mol.atoms.map(() => []);
    for (const [a, b] of mol.bonds) { nbrs[a].push(b); nbrs[b].push(a); }
    const line = (x1, y1, x2, y2) => {
      const l = document.createElementNS(NS, 'line');
      l.setAttribute('x1', x1.toFixed(1)); l.setAttribute('y1', y1.toFixed(1));
      l.setAttribute('x2', x2.toFixed(1)); l.setAttribute('y2', y2.toFixed(1));
      svg.appendChild(l);
    };
    for (const [a, b, order] of mol.bonds) {
      const A = pts[a], B = pts[b];
      const len = Math.hypot(B.x - A.x, B.y - A.y);
      const ux = (B.x - A.x) / len, uy = (B.y - A.y) / len;   // along the bond
      const px = -uy, py = ux;                                 // across it
      // pull each end back from a written label so the line does not run through the letters
      const ta = label(mol.atoms[a]) ? LABEL_R : 0, tb = label(mol.atoms[b]) ? LABEL_R : 0;
      const ax = A.x + ux * ta, ay = A.y + uy * ta, bx = B.x - ux * tb, by = B.y - uy * tb;
      const offset = (s, shrink = 0) => line(ax + px * GAP * s + ux * shrink, ay + py * GAP * s + uy * shrink,
                                             bx + px * GAP * s - ux * shrink, by + py * GAP * s - uy * shrink);
      if (order === 1) line(ax, ay, bx, by);
      else if (order === 3) { line(ax, ay, bx, by); offset(-1); offset(1); }
      else if (nbrs[a].length === 1 || nbrs[b].length === 1) { offset(-0.5); offset(0.5); }   // C=O: two symmetric lines
      else {
        // the second line goes on the side the other neighbours are — inside a ring
        const others = [...nbrs[a].filter((k) => k !== b), ...nbrs[b].filter((k) => k !== a)];
        const cx = others.reduce((s, k) => s + pts[k].x, 0) / others.length - (A.x + B.x) / 2;
        const cy = others.reduce((s, k) => s + pts[k].y, 0) / others.length - (A.y + B.y) / 2;
        line(ax, ay, bx, by);
        offset(cx * px + cy * py >= 0 ? 1 : -1, 5);
      }
    }
    mol.atoms.forEach((a, i) => {
      const txt = label(a);
      if (!txt) return;
      const t = document.createElementNS(NS, 'text');
      t.setAttribute('x', pts[i].x.toFixed(1));
      t.setAttribute('y', pts[i].y.toFixed(1));
      t.setAttribute('class', 'matom');
      t.textContent = txt;
      const z = symToZ[a.el];
      if (z) {
        const title = document.createElementNS(NS, 'title');
        title.textContent = byZ[z].name;
        t.appendChild(title);
        t.addEventListener('click', () => select(z, true));
      }
      svg.appendChild(t);
    });
    return svg;
  }

  // ---- the strip
  const mstrip = document.getElementById('mstrip');
  const mformula = document.getElementById('mformula');
  const mpick = document.getElementById('mpick');
  const mstatus = document.getElementById('mstatus');
  let molMap = null;        // z -> {n, pct}
  let molLensBtn = null;
  mpick.append(new Option('from the shelf…', ''));
  for (const m of MOLS) mpick.append(new Option(`${m.name} · ${subscript(m.formula)}`, m.slug));

  const mbtn = document.createElement('button');
  mbtn.className = 'abtn';
  mbtn.textContent = '⌬ draw a molecule';
  mbtn.title = 'Type a formula or pick a molecule — its atoms light up on the table, with the structure drawn';
  document.querySelector('header.top').append(mbtn);
  mbtn.addEventListener('click', () => {
    if (!molMap) showShelf(MOLS[0]);
    mstrip.classList.add('on');
    mstrip.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });

  function setMStatus(msg, cls) {
    mstatus.textContent = msg || '';
    mstatus.className = 'mstatus' + (cls ? ' ' + cls : '');
  }

  function showShelf(m) {
    mpick.value = m.slug;
    mformula.value = m.formula;
    showMolecule({ name: m.name, formula: m.formula, kind: m.kind, note: m.note, counts: parseFormula(m.formula), shelf: m });
  }

  function tryFormula(raw) {
    const v = raw.trim();
    if (!v) return;
    mstrip.classList.add('on');
    let counts;
    try { counts = parseFormula(v); } catch (e) { setMStatus(`Could not read “${v}” — ${e.message}.`, 'err'); return; }
    const shelf = shelfByKey.get(hill(counts));
    if (shelf) { showShelf(shelf); return; }
    mpick.value = '';
    showMolecule({ name: subscript(v), formula: null, counts });
  }

  function showMolecule({ name, formula, kind, note, counts, shelf }) {
    mstrip.classList.add('on');
    setMStatus('');
    const comp = composition(counts);
    document.getElementById('mname').textContent = name;
    const mass = comp.total ? `${+comp.total.toFixed(2)} g/mol` : '';
    document.getElementById('mform').textContent = [formula && subscript(formula), mass].filter(Boolean).join(' · ');
    document.getElementById('mkind').textContent = kind ? vocab(kind) : '';
    document.getElementById('mnote').textContent = note || '';

    const draw = document.getElementById('mdraw');
    draw.innerHTML = '';
    if (shelf) draw.appendChild(drawMolecule(shelf));
    else {
      const p = document.createElement('p');
      p.className = 'mnodraw';
      p.textContent = 'No drawing for this formula — the shelf holds the structures. The table still shows its atoms.';
      draw.appendChild(p);
    }

    const box = document.getElementById('mcomp');
    box.innerHTML = '';
    for (const r of comp.rows) {
      const d = document.createElement('div');
      d.className = 'mel';
      const sym = document.createElement('button');
      sym.className = 'msym';
      sym.textContent = r.sym;
      sym.title = `inspect ${r.name}`;
      sym.addEventListener('click', () => select(r.z, true));
      const nm = document.createElement('span');
      nm.textContent = r.name;
      const n = document.createElement('span');
      n.className = 'mn';
      n.textContent = `${r.n} atom${r.n === 1 ? '' : 's'}`;
      const pct = document.createElement('span');
      pct.className = 'mpct';
      pct.textContent = r.pct == null ? 'no mass in Notion' : `${+r.pct.toPrecision(3)}%`;
      const bar = document.createElement('div');
      bar.className = 'mbar';
      const fill = document.createElement('div');
      fill.style.width = Math.min(100, Math.max(2, r.pct ?? 0)) + '%';
      bar.appendChild(fill);
      d.append(sym, nm, n, pct, bar);
      box.appendChild(d);
    }
    if (!comp.total) setMStatus('Some atomic masses are missing from Notion, so only the atom counts are shown.');

    molMap = {};
    for (const r of comp.rows) molMap[r.z] = { n: r.n, pct: r.pct };
    registerMolLens(comp.atoms);
    molLensBtn.click();
    history.replaceState(null, '', `?molecule=${encodeURIComponent(shelf ? shelf.slug : hill(counts))}${location.hash}`);
  }

  function registerMolLens(atoms) {
    const max = Math.max(...Object.values(molMap).map((v) => v.pct ?? 0)) || 1;
    LENSES.molecule = {
      name: 'Molecule',
      seq: true,
      solid: true,
      absent: 'not in the molecule',
      t: (e) => { const m = molMap[e.z]; return m ? (m.pct == null ? 1 : m.pct / max) : null; },
      color: (e) => { const t = LENSES.molecule.t(e); return t == null ? null : heat(t); },
      value: (e) => {
        const m = molMap[e.z];
        if (!m) return 'not in this molecule';
        return `${m.n} of ${atoms} atoms` + (m.pct == null ? '' : ` · ${+m.pct.toPrecision(3)}% of mass`);
      },
      range: () => ['0%', `${+max.toPrecision(3)}% of mass`],
    };
    if (!molLensBtn) {
      molLensBtn = document.createElement('button');
      molLensBtn.className = 'lens';
      molLensBtn.textContent = 'Molecule';
      molLensBtn.setAttribute('aria-pressed', 'false');
      molLensBtn.addEventListener('click', () => {
        lens = 'molecule';
        for (const x of lensesBox.children) x.setAttribute('aria-pressed', 'false');
        molLensBtn.setAttribute('aria-pressed', 'true');
        document.getElementById('tempwrap').classList.remove('on');
        document.getElementById('yearwrap').classList.remove('on');
        paint();
        if (sel) renderDetail(byZ[sel]);
      });
      lensesBox.appendChild(molLensBtn);
    }
  }

  // ghost the elements the molecule has none of while its lens is active
  const paintBeforeMolecule = paint;
  paint = function () {
    paintBeforeMolecule();
    if (lens === 'molecule' && molMap) {
      for (const e of E) if (!molMap[e.z]) tiles[e.z].classList.add('ghost');
    }
  };

  mformula.addEventListener('change', () => tryFormula(mformula.value));
  mformula.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') { ev.preventDefault(); tryFormula(mformula.value); } });
  mpick.addEventListener('change', () => {
    const m = MOLS.find((x) => x.slug === mpick.value);
    if (m) showShelf(m);
  });
  document.getElementById('mclear').addEventListener('click', () => {
    mstrip.classList.remove('on');
    molMap = null;
    delete LENSES.molecule;
    if (molLensBtn) { molLensBtn.remove(); molLensBtn = null; }
    mformula.value = '';
    mpick.value = '';
    if (lens === 'molecule') (analysisLensBtn || lensesBox.children[0]).click();
    history.replaceState(null, '', location.pathname + location.hash);
  });

  // deep link: /elements?molecule=caffeine, or any formula: /elements?molecule=C8H10N4O2
  const wantedMolecule = new URLSearchParams(location.search).get('molecule');
  if (wantedMolecule) {
    const m = MOLS.find((x) => x.slug === wantedMolecule.toLowerCase());
    if (m) showShelf(m); else tryFormula(wantedMolecule);
  }
