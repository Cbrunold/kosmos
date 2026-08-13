
  // ---------- analyzer: photo -> elemental breakdown ----------
  const symToZ = Object.fromEntries(E.map((e) => [e.sym, e.z]));
  let analysisMap = null; // z -> massPercent
  let analysisLensBtn = null;
  const astrip = document.getElementById('astrip');
  const astatus = document.getElementById('astatus');

  const abtn = document.createElement('button');
  abtn.className = 'abtn';
  abtn.textContent = '⚛ analyze an object';
  abtn.title = 'Photograph or upload an object — Claude breaks it down into elements';
  const afile = document.createElement('input');
  afile.type = 'file';
  afile.accept = 'image/*';
  afile.style.display = 'none';
  document.querySelector('header.top').append(abtn, afile);
  abtn.addEventListener('click', () => afile.click());
  afile.addEventListener('change', () => { if (afile.files[0]) runAnalysis(afile.files[0]); afile.value = ''; });

  function setStatus(msg, cls) {
    astatus.textContent = msg || '';
    astatus.className = 'astatus' + (cls ? ' ' + cls : '');
  }

  async function downscale(file) {
    const url = URL.createObjectURL(file);
    try {
      const img = await new Promise((ok, bad) => {
        const i = new Image();
        i.onload = () => ok(i);
        i.onerror = () => bad(new Error('Could not read that image.'));
        i.src = url;
      });
      const scale = Math.min(1, 1568 / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = Math.round(img.width * scale);
      c.height = Math.round(img.height * scale);
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      return c.toDataURL('image/jpeg', 0.85);
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  async function runAnalysis(file) {
    astrip.classList.add('on');
    document.getElementById('aobject').textContent = '';
    document.getElementById('aconf').textContent = '';
    document.getElementById('asummary').textContent = '';
    document.getElementById('amats').innerHTML = '';
    document.getElementById('acaveats').textContent = '';
    abtn.disabled = true;
    try {
      const dataUrl = await downscale(file);
      document.getElementById('athumb').src = dataUrl;
      setStatus('Claude is looking at your photo', 'busy');
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: dataUrl.split(',')[1], mediaType: 'image/jpeg' }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `Analysis failed (${res.status}).`);
      renderAnalysis(data);
    } catch (e) {
      setStatus(e.message, 'err');
    } finally {
      abtn.disabled = false;
    }
  }

  function renderAnalysis(a) {
    setStatus('');
    document.getElementById('aobject').textContent = a.object || 'Unknown object';
    document.getElementById('aconf').textContent = (a.confidence || '?') + ' confidence';
    document.getElementById('asummary').textContent = a.summary || '';
    document.getElementById('acaveats').textContent = a.caveats || '';

    const mats = document.getElementById('amats');
    mats.innerHTML = '';
    for (const m of (a.materials || []).slice(0, 6)) {
      const d = document.createElement('div');
      d.className = 'amat';
      const row = document.createElement('div');
      row.className = 'mrow';
      const nm = document.createElement('span');
      nm.textContent = m.name + (m.note ? ` — ${m.note}` : '');
      const pct = document.createElement('span');
      pct.className = 'pct';
      pct.textContent = `${Math.round(m.sharePercent)}%`;
      row.append(nm, pct);
      const bar = document.createElement('div');
      bar.className = 'mbar';
      const fill = document.createElement('div');
      fill.style.width = Math.min(100, Math.max(2, m.sharePercent)) + '%';
      bar.appendChild(fill);
      d.append(row, bar);
      mats.appendChild(d);
    }

    analysisMap = {};
    for (const el of a.elements || []) {
      const z = symToZ[el.symbol];
      if (z && el.massPercent > 0) analysisMap[z] = { pct: el.massPercent, source: el.source, name: el.name };
    }
    if (Object.keys(analysisMap).length === 0) {
      setStatus('No elements identified in this photo.', '');
      return;
    }
    registerAnalysisLens();
    analysisLensBtn.click();
  }

  function registerAnalysisLens() {
    const pcts = Object.values(analysisMap).map((v) => Math.max(0.01, v.pct));
    const lo = Math.log10(Math.min(...pcts));
    const hi = Math.log10(Math.max(...pcts));
    LENSES.analysis = {
      name: 'Analysis',
      seq: true,
      solid: true,
      t: (e) => {
        const m = analysisMap[e.z];
        if (!m) return null;
        return hi === lo ? 1 : (Math.log10(Math.max(0.01, m.pct)) - lo) / (hi - lo);
      },
      color: (e) => {
        const t = LENSES.analysis.t(e);
        return t == null ? null : heat(t);
      },
      value: (e) => {
        const m = analysisMap[e.z];
        return m ? `${+m.pct.toPrecision(3)}% of mass · ${m.source}` : 'not present in this object';
      },
      range: () => [`${+Math.min(...pcts).toPrecision(2)}%`, `${+Math.max(...pcts).toPrecision(2)}% of mass (log scale)`],
    };
    if (!analysisLensBtn) {
      analysisLensBtn = document.createElement('button');
      analysisLensBtn.className = 'lens';
      analysisLensBtn.textContent = 'Analysis';
      analysisLensBtn.setAttribute('aria-pressed', 'false');
      analysisLensBtn.addEventListener('click', () => {
        lens = 'analysis';
        for (const x of lensesBox.children) x.setAttribute('aria-pressed', 'false');
        analysisLensBtn.setAttribute('aria-pressed', 'true');
        document.getElementById('tempwrap').classList.remove('on');
        document.getElementById('yearwrap').classList.remove('on');
        paint();
      });
      lensesBox.appendChild(analysisLensBtn);
    }
  }

  // ghost elements absent from the analysis when the Analysis lens is active
  const basePaint = paint;
  paint = function () {
    basePaint();
    if (lens === 'analysis' && analysisMap) {
      for (const e of E) if (!analysisMap[e.z]) tiles[e.z].classList.add('ghost');
    }
  };

  document.getElementById('aclear').addEventListener('click', () => {
    astrip.classList.remove('on');
    analysisMap = null;
    delete LENSES.analysis;
    if (analysisLensBtn) { analysisLensBtn.remove(); analysisLensBtn = null; }
    lens = 'cat';
    lensesBox.children[0].click();
  });
