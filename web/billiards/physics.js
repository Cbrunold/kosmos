// ---- the physics of /billiards: every function that moves a ball, and nothing that draws one.
// build.py inlines this into the page; node loads it for test/billiards/physics.test.cjs. The
// constants come in as C — data/billiards/constants.json, key: value — and roster() returns the
// balls on the table for shoot(): the page passes its state, the tests pass nothing and get two.
//
// Conventions, for every ball b: p position (m), v velocity (m/s), s the "spin surface velocity"
// (what the spin would give the contact point, reversed — equals v when rolling), z the side
// spin's surface speed, slid the seconds spent sliding. Slip is v − s.
function kosmosBilliardsPhysics(C, opts = {}) {
  const roster = opts.roster || (() => null);
  const R = C.R, M = C.M, G = C.G;
  const E_BB = C.E_BB;                 // ball–ball restitution
  let MU_S = C.MU_S, MU_R = C.MU_R, MU_SP = C.MU_SP;   // cloth: sliding, rolling, spinning
  let E_C = Math.sqrt(C.CUSHION_ENERGY);       // cushion keeps 3/4 of the energy → 0.87 of the speed
  // ---- what a table preset may change under a running page: the cloth and the rubber, never the
  // geometry. set() returns what is in force; current() reads it without touching anything.
  let K = { MU_S, MU_R, MU_SP, CUSHION_ENERGY: C.CUSHION_ENERGY };
  function set(over) {
    K = { MU_S: C.MU_S, MU_R: C.MU_R, MU_SP: C.MU_SP, CUSHION_ENERGY: C.CUSHION_ENERGY, ...(over || {}) };
    MU_S = K.MU_S; MU_R = K.MU_R; MU_SP = K.MU_SP; E_C = Math.sqrt(K.CUSHION_ENERGY);
    bankCache.clear();   // a bank plan is the sim's own rail model, which just changed
    return K;
  }
  const current = () => K;
  const MU_C = C.MU_C;                  // cushion friction — literature, not in constants.py
  const muBB = (v) => C.MU_BB_FIT[0] + C.MU_BB_FIT[1] * Math.exp(-C.MU_BB_FIT[2] * v);   // Alciatore's fit — literature
  const TABLE_L = C.TABLE[0], TABLE_W = C.TABLE[1];
  const RP = C.RP;                // 4½ in mouth → 0.0572 m capture radius on the ball's centre
  const SHELF_C = C.SHELF[0], SHELF_S = C.SHELF[1];   // pocket shelf depth, a per-pocket variable: 1⅝ in corner, ⅜ in side (WPA typicals)
  const POCKETS = [
    { p: [0, 0], name: 'top-left corner', shelf: SHELF_C }, { p: [TABLE_L / 2, 0], name: 'top side', shelf: SHELF_S }, { p: [TABLE_L, 0], name: 'top-right corner', shelf: SHELF_C },
    { p: [0, TABLE_W], name: 'bottom-left corner', shelf: SHELF_C }, { p: [TABLE_L / 2, TABLE_W], name: 'bottom side', shelf: SHELF_S }, { p: [TABLE_L, TABLE_W], name: 'bottom-right corner', shelf: SHELF_C },
  ];
  // the axis points into the pocket: the line a ball is judged against at the mouth
  for (const P of POCKETS) {
    P.side = P.p[0] === TABLE_L / 2;
    P.axis = P.side ? [0, P.p[1] === 0 ? -1 : 1] : [P.p[0] === 0 ? -Math.SQRT1_2 : Math.SQRT1_2, P.p[1] === 0 ? -Math.SQRT1_2 : Math.SQRT1_2];
  }
  const SQ_R = C.SQUIRT_DEG_PER_BR * Math.PI / 180;    // squirt: radians of cue-ball deflection per unit b/R of side (2.5° at max side) — a cue constant
  const SW_K = C.SW_K;                 // swerve: lateral g-fraction at full side while the ball slides — the cue's slight natural elevation

  const deg = (r) => r * 180 / Math.PI, rad = (d) => d * Math.PI / 180;
  const vadd = (a, b) => [a[0] + b[0], a[1] + b[1]], vsub = (a, b) => [a[0] - b[0], a[1] - b[1]];
  const vmul = (a, k) => [a[0] * k, a[1] * k], vlen = (a) => Math.hypot(a[0], a[1]);
  const vdot = (a, b) => a[0] * b[0] + a[1] * b[1], vunit = (a) => { const l = vlen(a); return l ? vmul(a, 1 / l) : [0, 0]; };
  const perp = (a) => [-a[1], a[0]];   // rotate +90°
  const dist2 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  const pocketAt = (p) => { for (let i = 0; i < 6; i++) if (dist2(p, POCKETS[i].p) <= RP) return i; return -1; };
  const inside = (p) => p[0] > R && p[0] < TABLE_L - R && p[1] > R && p[1] < TABLE_W - R;

  // ---- the rails, live in the main sim: the cushion model (restitution √0.75, friction, side)
  // applied at whichever rail the ball crosses. Side spin transfers: running lengthens, reverse checks.
  const RAILS = [{ ax: 0, lim: R, dir: 1, name: 'left' }, { ax: 0, lim: TABLE_L - R, dir: -1, name: 'right' }, { ax: 1, lim: R, dir: 1, name: 'top' }, { ax: 1, lim: TABLE_W - R, dir: -1, name: 'bottom' }];
  function bounce(b) {
    for (const r of RAILS) {
      const past = r.dir > 0 ? b.p[r.ax] < r.lim : b.p[r.ax] > r.lim;
      const into = r.dir > 0 ? b.v[r.ax] < 0 : b.v[r.ax] > 0;
      if (!past || !into) continue;
      const ta = 1 - r.ax, vn = Math.abs(b.v[r.ax]);
      const e = Math.max(C.CUSHION_E_MIN, E_C - C.CUSHION_DEADEN * vn);   // rubber deadens with pace: √0.75 at a touch, ~0.55 at a break
      const Jn = M * vn * (1 + e);
      // sign of the side spin's surface velocity along the rail at this cushion's contact point
      const zs = r.ax === 1 ? r.dir : -r.dir;
      const slip = b.v[ta] + zs * b.z;
      const Jt = Math.sign(slip) * Math.min(MU_C * Jn, (2 / 7) * M * Math.abs(slip));
      b.v[ta] -= Jt / M;
      b.z -= zs * 2.5 * Jt / M;
      b.v[r.ax] = r.dir * e * vn;
      b.p[r.ax] = 2 * r.lim - b.p[r.ax];
      return r;   // truthy for the counters; the rail itself for anything numbering the cushions
    }
    return null;
  }

  // ---- one ball on cloth: velocity v, "spin surface velocity" s (the velocity the spin would give at the
  // contact point, reversed — equals v when rolling), side spin surface speed z. Advance by dt.
  // Slip u = v − s: friction μ_s g against û, spin surface velocity gains (5/2) μ_s g along û. Rolling: μ_r g.
  function step(b, dt) {
    const u = vsub(b.v, b.s), ul = vlen(u);
    if (ul > 1e-4) {
      if (b.z) {   // side + the cue's slight natural elevation: the path swerves while the ball slides
        const sp0 = vlen(b.v);
        if (sp0 > 0.05) b.v = vadd(b.v, vmul(perp(vmul(b.v, 1 / sp0)), SW_K * G * Math.max(-0.5, Math.min(0.5, b.z / (2.5 * sp0))) * dt));
      }
      const uh = vmul(u, 1 / ul);
      const tRoll = 2 * ul / (7 * MU_S * G);
      if (dt >= tRoll) {   // finish the slide exactly, then roll for the rest
        const vf = vadd(vmul(b.v, 5 / 7), vmul(b.s, 2 / 7));
        b.p = vadd(b.p, vsub(vmul(b.v, tRoll), vmul(uh, 0.5 * MU_S * G * tRoll * tRoll)));
        b.v = vf; b.s = vf; b.slid += tRoll;
        return step(b, dt - tRoll);
      }
      b.p = vadd(b.p, vsub(vmul(b.v, dt), vmul(uh, 0.5 * MU_S * G * dt * dt)));
      b.v = vsub(b.v, vmul(uh, MU_S * G * dt));
      b.s = vadd(b.s, vmul(uh, 2.5 * MU_S * G * dt));
      b.slid += dt;
    } else {
      const sp = vlen(b.v);
      if (sp < 1e-4) { b.v = [0, 0]; b.s = [0, 0]; return; }
      const dec = Math.min(sp, MU_R * G * dt);
      const vh = vmul(b.v, 1 / sp);
      b.p = vadd(b.p, vsub(vmul(b.v, dt), vmul(vh, 0.5 * MU_R * G * dt * dt)));
      b.v = vmul(vh, sp - dec); b.s = b.v;
    }
    if (b.z) { const dz = 2.5 * MU_SP * G * dt; b.z = Math.abs(b.z) <= dz ? 0 : b.z - Math.sign(b.z) * dz; }
  }
  const stopDistance = (b) => {   // from a state: remaining slide + roll, along the current line
    const u = vsub(b.v, b.s), ul = vlen(u);
    const vf = ul > 1e-4 ? vadd(vmul(b.v, 5 / 7), vmul(b.s, 2 / 7)) : b.v;
    let d = 0;
    if (ul > 1e-4) { const t = 2 * ul / (7 * MU_S * G); d += vlen(vsub(vmul(b.v, t), vmul(vunit(u), 0.5 * MU_S * G * t * t))); }
    return d + vlen(vf) ** 2 / (2 * MU_R * G);
  };
  // slide → roll off the tip, closed form for an uninterrupted ball: slip u = v(1 − 2.5·tip) decays at (7/2)μ_s g,
  // so the slide lasts t = 2u/(7 μ_s g) — linear in the strike — and covers d ∝ v²; it then rolls at 5v(1+tip)/7.
  const slideOut = (v, tip) => {
    const u = v * (1 - 2.5 * tip);   // + for stun and draw, − when struck above natural-roll height
    const t = 2 * Math.abs(u) / (7 * MU_S * G);
    return { t, d: v * t - Math.sign(u) * 0.5 * MU_S * G * t * t, vRoll: 5 * v * (1 + tip) / 7 };
  };
  // ---- the mouth. A ball at a mouth drops if it has the roll to clear the shelf and hangs if not — but
  // first the jaws decide whether to take it at all. The mouth a pocket offers narrows with pace
  // (POCKET_NARROW per m/s, to POCKET_NARROW_FLOOR), measured against how far the ball's path passes
  // from the pocket point; a side pocket also refuses a ball more than SIDE_ACCEPT_DEG off the
  // perpendicular, narrowing likewise. A refused ball rattles: it rebounds off the pocket's axis like
  // rail, loses a bite to the jaw, and is put back outside the mouth to carry on.
  function atMouth(b, pk) {   // -> 'drop' | 'hang' | 'rattle' | 'pass' (not really arriving)
    const P0 = POCKETS[pk], v = vlen(b.v);
    if (v > 1e-6) {
      const dir = vmul(b.v, 1 / v);
      const into = vdot(dir, P0.axis);
      if (into <= 0.05) return 'pass';
      const narrow = Math.max(C.POCKET_NARROW_FLOOR, 1 - C.POCKET_NARROW * v);
      const off = Math.abs(dir[0] * (P0.p[1] - b.p[1]) - dir[1] * (P0.p[0] - b.p[0]));   // the path's miss of the pocket point
      const tooWide = off > RP * narrow;
      const tooShallow = P0.side && into < Math.cos(rad(C.SIDE_ACCEPT_DEG * narrow));
      if (tooWide || tooShallow) return 'rattle';
    }
    return stopDistance(b) >= P0.shelf ? 'drop' : 'hang';
  }
  function rattle(b, pk) {
    const P0 = POCKETS[pk], n = P0.axis;
    const vn = vdot(b.v, n);
    if (vn > 0) {
      const e = Math.max(C.CUSHION_E_MIN, E_C - C.CUSHION_DEADEN * vn);
      b.v = vmul(vsub(b.v, vmul(n, (1 + e) * vn)), 1 - MU_C);   // rail restitution along the axis, and the jaw's bite
      b.s = b.v.slice(); b.z *= 0.5;
    }
    const away = vsub(b.p, P0.p), d = vlen(away);
    b.p = vadd(P0.p, vmul(d > 1e-6 ? vmul(away, 1 / d) : vmul(n, -1), RP + 1e-3));
    b.rattled = (b.rattled || 0) + 1; b.rattleAt = pk;
  }

  // roll a ball until it stops or reaches a mouth, rebounding off the rails on the way; track path length
  // and the closest approach to the target pocket. At a mouth it drops only with the roll left to carry
  // that pocket's shelf — else it hangs in the jaws.
  const trace = (b, dt, keep, P, maxI = 9000) => {
    const pts = keep ? [b.p.slice()] : null;
    let pocket = null, hang = null, dropSpeed = 0, len = 0, minPD = P ? dist2(b.p, P) : Infinity, rattles = 0;
    for (let i = 0; i < maxI; i++) {
      const px0 = b.p[0], py0 = b.p[1];
      step(b, dt);
      len += Math.hypot(b.p[0] - px0, b.p[1] - py0);
      if (keep) pts.push(b.p.slice());
      if (P) { const dd = dist2(b.p, P); if (dd < minPD) minPD = dd; }
      const pk = pocketAt(b.p);
      if (pk >= 0) {
        const m = atMouth(b, pk);
        if (m === 'drop') { pocket = pk; dropSpeed = vlen(b.v); break; }
        if (m === 'hang') { hang = pk; break; }
        if (m === 'rattle') { rattle(b, pk); rattles++; continue; }
      }
      bounce(b);
      if (vlen(b.v) < 1e-3) break;
    }
    return { pts, pocket, hang, dropSpeed, len, minPD, slid: b.slid, dt, rattles };
  };

  // ---- two balls meeting, both possibly moving: normal impulse with restitution in the relative frame,
  // friction (throw) impulse from the relative surface slip, capped at gearing. Returns the report data.
  function collide(A, B) {
    {   // back both balls up along their motion to the exact touching point — the timestep overshoots
      const d0 = dist2(A.p, B.p), nc0 = vunit(vsub(B.p, A.p));
      const closing = vdot(vsub(A.v, B.v), nc0);
      if (closing > 1e-6 && d0 < 2 * R) {
        const tau = Math.min((2 * R - d0) / closing, 0.012);
        A.p = vsub(A.p, vmul(A.v, tau)); B.p = vsub(B.p, vmul(B.v, tau));
      }
    }
    const nc = vunit(vsub(B.p, A.p)), tc = perp(nc);
    const rv = vsub(A.v, B.v);
    const vnr = vdot(rv, nc);
    if (vnr <= 1e-6) {   // touching but not closing: just ease them apart
      const d = dist2(A.p, B.p);
      if (d < 2 * R - 1e-6) { const push = (2 * R - d) / 2 + 1e-5; A.p = vsub(A.p, vmul(nc, push)); B.p = vadd(B.p, vmul(nc, push)); }
      return null;
    }
    const dc = vlen(A.v) > 1e-6 ? vunit(A.v) : nc;
    const vc = vlen(A.v), sc = vdot(A.s, dc), rollingAtContact = vlen(vsub(A.v, A.s)) < 0.02;
    const th = Math.acos(Math.max(-1, Math.min(1, vdot(dc, nc))));
    const vt = vdot(rv, tc);
    const Jn = M * vnr * (1 + E_BB) / 2;
    const uh = vt - A.z + B.z;                           // relative surface slip along the tangent, side spins included
    const uz = -vdot(vsub(A.s, B.s), nc);
    const ul = Math.hypot(uh, uz), mu = muBB(ul);
    let Jh = 0;
    if (ul > 1e-6) Jh = Math.min(mu * Jn * Math.abs(uh) / ul, M * Math.abs(uh) / 7);   // gearing cap
    const td = Math.sign(uh) || 0;
    const zA = A.z, sA = A.s.slice();
    A.v = vsub(vsub(A.v, vmul(nc, Jn / M)), vmul(tc, td * Jh / M));
    B.v = vadd(vadd(B.v, vmul(nc, Jn / M)), vmul(tc, td * Jh / M));
    const d = dist2(A.p, B.p);
    if (d < 2 * R) { const push = (2 * R - d) / 2 + 1e-5; A.p = vsub(A.p, vmul(nc, push)); B.p = vadd(B.p, vmul(nc, push)); }
    return { nc, tc, dc, th, vc, sc, rollingAtContact, vn: vnr, vt, Jn, Jh, throwDeg: Jn > 1e-9 ? deg(Math.atan2(Jh / M, Jn / M)) : 0, throwDir: td, mu, ul, contactP: A.p.slice(), vA: A.v.slice(), vB: B.v.slice(), sA, zA };
  }

  // ---- a one-rail bank: when the direct line to the pocket is dead, send the object ball off a cushion
  // instead. A cushion is no mirror — restitution deadens with pace, cloth friction shortens the rebound, and
  // the roll the ball carries into the rail bends it long again — so the contact point is solved numerically:
  // the sim's own single-ball trace, run at a nominal pace over candidate points, picks the one that drops.
  // The plan is geometry (cue-independent), so it's cached per object-ball position and pocket.
  const BANK_V = 1.5;
  const bankCache = new Map();
  function bankCandidates(obP, P, pkI) {
    const key = pkI + '|' + obP[0].toFixed(3) + ',' + obP[1].toFixed(3);
    const hitC = bankCache.get(key);
    if (hitC) return hitC;
    const out = [];
    for (const r of RAILS) {
      const ax = r.ax, ta = 1 - ax, lim = r.lim, span = ta === 0 ? TABLE_L : TABLE_W;
      const ho = Math.abs(obP[ax] - lim), hk = Math.abs(P[ax] - lim);
      if (ho < 0.03 || hk < 0.08) continue;                       // ball frozen to that rail, or the pocket sits on it
      if ((obP[ax] - lim) * (P[ax] - lim) < 0) continue;
      const tryB = (Bta) => {                                     // roll the object ball at that rail point, watch where it goes
        if (Bta < R + 0.01 || Bta > span - R - 0.01) return null;
        const B = [0, 0]; B[ax] = lim; B[ta] = Bta;
        if (pocketAt(B) >= 0) return null;                        // that's a mouth, not rubber
        const d = vunit(vsub(B, obP));
        const tr = trace({ p: obP.slice(), v: vmul(d, BANK_V), s: [0, 0], z: 0, slid: 0 }, 0.004, false, P, 4000);
        return { B, d, pot: tr.pocket === pkI, hang: tr.hang === pkI, miss: tr.minPD };
      };
      const bAt = (rho) => obP[ta] + (P[ta] - obP[ta]) * ho / (ho + rho * hk);   // rho 1 = mirror, big = flat
      let best = null;
      const consider = (c) => { if (c && (!best || (c.pot && !best.pot) || (c.pot === best.pot && c.miss < best.miss))) best = c; };
      for (let i = 0; i <= 20; i++) consider(tryB(bAt(0.7 + i * (5 - 0.7) / 20)));
      if (best) {                                                 // refine around the winner
        const step2 = Math.abs(bAt(5) - bAt(0.7)) / 20;
        for (let i = -4; i <= 4; i++) if (i) consider(tryB(best.B[ta] + i * step2 / 4));
      }
      if (best && (best.pot || best.hang || best.miss < RP * 2))
        out.push({ ...best, rail: ax === 0 ? (r.dir > 0 ? 'left' : 'right') : (r.dir > 0 ? 'top' : 'bottom') });
    }
    if (bankCache.size > 40) bankCache.clear();
    bankCache.set(key, out);
    return out;
  }
  function planBank(cbP, obP, P, pkI) {
    const cands = [];
    for (const c of bankCandidates(obP, P, pkI)) {
      const ghost = vsub(obP, vmul(c.d, 2 * R));
      const dv = vsub(ghost, cbP), dst = vlen(dv), dAim = vunit(dv);
      const cut = vdot(dAim, c.d);
      if (!(cut > Math.cos(rad(88)) && dst > 0.03)) continue;
      cands.push({ B: c.B, d: c.d, ghost, dAim, dst, cut, pot: c.pot, rail: c.rail });
    }
    if (!cands.length) return null;
    cands.sort((a, b) => (b.pot - a.pot) || (b.cut - a.cut));   // a dropping bank first, then the fullest hit
    return cands[0];
  }

  // ---- the shot. aim = {pk} for practice (ghost-ball aim at a pocket) or {deg} for pro (the player's own line).
  // Every ball on the table is live: the cue ball is launched and the whole roster plays out — combos, caroms,
  // clusters and breaks. The reports describe the cue ball's first contact.
  function shoot(cbP, obP, aim, v0, tip, side, lite) {
    const pro = aim.deg !== undefined;
    const pkI = pro ? null : aim.pk;
    const P = pkI == null ? null : POCKETS[pkI].p, name = pkI == null ? null : POCKETS[pkI].name;
    let n = P ? vunit(vsub(P, obP)) : null;              // pocket line (practice guides + target classification)
    let ghost = n ? vsub(obP, vmul(n, 2 * R)) : null;
    let dAim, dst, bank = null;
    if (pro) { const a = rad(aim.deg); dAim = [Math.cos(a), Math.sin(a)]; dst = Math.max(0.001, dist2(cbP, obP) - 2 * R); }
    else {
      const dv = vsub(ghost, cbP); dst = vlen(dv); dAim = vunit(dv);
      if (!(vdot(dAim, n) > Math.cos(rad(88)) && dst > 0.03)) {
        const bk = planBank(cbP, obP, P, pkI);   // no direct line — go for the bank
        if (bk) { bank = bk; n = bk.d; ghost = bk.ghost; dAim = bk.dAim; dst = bk.dst; }
      }
    }
    const t = n ? perp(n) : null;
    const feasible = pro || (vdot(dAim, n) > Math.cos(rad(88)) && dst > 0.03);
    const base = { pro, feasible, ghost, ob0: obP, n, t, dAim, P, pkI, name, dst, v0, side, bank };
    if (!feasible) return base;
    if (aim.off) { const o = rad(aim.off); dAim = [dAim[0] * Math.cos(o) - dAim[1] * Math.sin(o), dAim[0] * Math.sin(o) + dAim[1] * Math.cos(o)]; }
    const sq = -SQ_R * side;                             // squirt: the cue ball leaves opposite the side used
    const d0 = [dAim[0] * Math.cos(sq) - dAim[1] * Math.sin(sq), dAim[0] * Math.sin(sq) + dAim[1] * Math.cos(sq)];
    // ---- the roster
    const st = roster() || { balls: [{ n: 0, p: cbP }, { n: 1, p: obP }], tgtIdx: () => 1 };   // the tests pass no roster
    const tgt = st.tgtIdx();
    const bodies = st.balls.map((b, i) => ({
      n: b.n, p: i === 0 ? cbP.slice() : i === tgt ? obP.slice() : b.p.slice(),
      v: [0, 0], s: [0, 0], z: 0, slid: 0, len: 0, rails: 0, pocket: null, hang: null, potStep: 0, dropSpeed: 0,
      minPD: Infinity, pts: lite ? null : [], moving: false,
    }));
    const cue = bodies[0], obB = bodies[tgt];
    cue.v = vmul(d0, v0); cue.s = vmul(d0, 2.5 * v0 * tip); cue.z = 2.5 * v0 * side; cue.moving = true;
    if (P) obB.minPD = dist2(obB.p, P);
    if (!lite) for (const b of bodies) b.pts.push(b.p.slice());
    const dt = lite ? 0.005 : 0.002;
    const maxI = lite ? 3000 : 14000;
    let hit = null, contactStep = null, cueRailsPre = 0;
    const cueContacts = [];   // every ball the cue ball touches, in order — the conditions' ledger
    for (let i = 0; i < maxI; i++) {
      let any = false;
      for (const b of bodies) {
        if (b.moving && b.pocket == null && b.hang == null) {
          const px0 = b.p[0], py0 = b.p[1];
          step(b, dt);
          b.len += Math.hypot(b.p[0] - px0, b.p[1] - py0);
          if (vlen(b.v) < 1e-3) { b.v = [0, 0]; b.moving = false; } else any = true;
        }
        if (!lite) b.pts.push(b.p.slice());
      }
      for (let a = 0; a < bodies.length; a++) {
        const A = bodies[a];
        if (!A.moving || A.pocket != null || A.hang != null) continue;
        for (let c = 0; c < bodies.length; c++) {
          if (c === a) continue;
          const B = bodies[c];
          if (B.pocket != null || B.hang != null) continue;
          if (dist2(A.p, B.p) >= 2 * R) continue;
          const ev = collide(A, B);
          if (ev) {
            if (vlen(B.v) > 1e-3) { B.moving = true; any = true; }
            if (a === 0) cueContacts.push(B.n); else if (c === 0) cueContacts.push(A.n);
            if (hit == null && a === 0) { hit = { ...ev, ball: B.n, isTarget: c === tgt }; contactStep = i; cue.slid = 0; cueRailsPre = cue.rails; }
          }
        }
      }
      for (const b of bodies) {
        if (b.pocket != null || b.hang != null) continue;
        if (b === obB && P) { const dd = dist2(b.p, P); if (dd < b.minPD) b.minPD = dd; }
        if (!b.moving) continue;
        const pk = pocketAt(b.p);
        if (pk >= 0) {
          const m = atMouth(b, pk);
          if (m === 'rattle') { rattle(b, pk); continue; }
          if (m !== 'pass') {
            if (m === 'drop') { b.pocket = pk; b.dropSpeed = vlen(b.v); } else b.hang = pk;
            b.potStep = i; b.moving = false; b.v = [0, 0];
            continue;
          }
        }
        if (bounce(b)) b.rails++;
      }
      if (!any) break;
    }
    const cs = contactStep == null ? null : contactStep + 1;
    const mkTrace = (b, from) => ({ pts: lite ? null : b.pts.slice(from), pocket: b.pocket, hang: b.hang, dropSpeed: b.dropSpeed, len: b.len, minPD: b.minPD, slid: b.slid, dt, potStep: b.potStep,
                                    rattled: b.rattled || 0, rattleAt: b.rattleAt ?? null });
    if (hit == null) {
      return { ...base, pre: lite ? [cbP] : cue.pts, preDt: dt, dt, reached: false, cbPre: cue.pocket, cbPreHang: cue.hang, simBalls: bodies, tgtIdx: tgt, cueContacts, cueRails: cue.rails, cueRailsPre: cue.rails };
    }
    // ---- report data, from the cue ball's first contact
    const cbAfter = { v: hit.vA, s: hit.sA };
    const stopOB = stopDistance({ v: hit.vB, s: [0, 0] }), stopCB = stopDistance(cbAfter);
    const vfCB = vlen(vsub(cbAfter.v, cbAfter.s)) > 1e-4 ? vadd(vmul(cbAfter.v, 5 / 7), vmul(cbAfter.s, 2 / 7)) : cbAfter.v;
    const slideLen = (() => { const u = vlen(vsub(hit.vA, hit.sA)); if (u < 1e-4) return 0; const tr = 2 * u / (7 * MU_S * G); const uh2 = vunit(vsub(hit.vA, hit.sA)); return vlen(vsub(vmul(hit.vA, tr), vmul(uh2, 0.5 * MU_S * G * tr * tr))); })();
    return {
      ...base, pre: lite ? [cbP] : cue.pts.slice(0, cs + 1), preDt: dt, dt, reached: true, cbPre: null, cbPreHang: null,
      nc: hit.nc, tc: hit.tc, dc: hit.dc, contactP: hit.contactP, th: hit.th, vc: hit.vc, sc: hit.sc,
      rollingAtContact: hit.rollingAtContact, tip, cbz: hit.zA,
      vn: hit.vn, vt: hit.vt, Jn: hit.Jn, Jh: hit.Jh, throwDeg: hit.throwDeg, throwDir: hit.throwDir, mu: hit.mu, ul: hit.ul,
      vOB: hit.vB, vCB: hit.vA, vfCB, stopOB, stopCB,
      obTrace: mkTrace(obB, cs), cbTrace: mkTrace(cue, cs), slideLen,
      eOB: hit.vc > 1e-6 ? vlen(hit.vB) ** 2 / (hit.vc * hit.vc) : 0, fraction: 1 - Math.sin(hit.th),
      deflect: vlen(vfCB) > 1e-3 ? deg(Math.acos(Math.max(-1, Math.min(1, vdot(vunit(vfCB), hit.dc))))) : null,
      firstBall: hit.ball, firstIsTarget: hit.isTarget, simBalls: bodies, tgtIdx: tgt, contactStep: cs,
      cueContacts, cueRails: cue.rails, cueRailsPre,
    };
  }

  // ---- slide → roll: slide distance against strike, for the current tip, with the object ball's distance drawn in
  // Where the ball is in its life at a given distance. Off the tip it carries velocity v and a spin whose
  // surface speed is 2.5·v·tip; the difference between them is slip, and friction kills slip at (7/2)μ_s g
  // while it takes v down (or up, if you put more spin on than rolling needs) at μ_s g. Everything draw and
  // stun mean is the stretch before slip runs out.
  function slideState(v0, tip, d) {
    const a = MU_S * G, u0 = v0 * (1 - 2.5 * tip), sg = Math.sign(u0) || 0;
    const tr = 2 * Math.abs(u0) / (7 * a);                     // when it takes up natural roll
    const dr = v0 * tr - sg * 0.5 * a * tr * tr;               // and how far that took
    const vr = v0 - sg * a * tr;
    if (d >= dr) {                                             // already rolling by then; it just slows
      const v2 = Math.sqrt(Math.max(0, vr * vr - 2 * MU_R * G * (d - dr)));
      return { phase: 'rolling', v: v2, s: v2, ratio: 1, tr, dr, vr, alive: v2 > 1e-3 };
    }
    let t;
    if (Math.abs(sg) < 0.5) t = d / Math.max(1e-6, v0);
    else if (sg > 0) { const disc = v0 * v0 - 2 * a * d; t = disc <= 0 ? tr : (v0 - Math.sqrt(disc)) / a; }
    else t = (-v0 + Math.sqrt(v0 * v0 + 2 * a * d)) / a;
    t = Math.min(Math.max(0, t), tr);
    const v = v0 - sg * a * t, sp = 2.5 * v0 * tip + sg * 2.5 * a * t;
    const ratio = v > 1e-6 ? sp / v : 0;
    return { phase: ratio < -0.03 ? 'draw' : ratio <= 0.05 ? 'stun' : ratio < 0.97 ? 'drag' : 'rolling', v, s: sp, ratio, tr, dr, vr, alive: v > 1e-3 };
  }

  function cushion(aDeg, v, side) {
    const a = rad(aDeg);
    const vx = v * Math.cos(a), vy = v * Math.sin(a);           // along the rail, into the rail
    const e = Math.max(C.CUSHION_E_MIN, E_C - C.CUSHION_DEADEN * vy);                   // same deadening-with-pace as the main sim
    const z = 2.5 * v * side;                                    // surface speed from side spin at the contact
    const slip = vx - z;                                         // running side (z > 0) reduces the slip
    const Jn = M * vy * (1 + e);
    const Jt = Math.min(MU_C * Jn, (2 / 7) * M * Math.abs(slip)) * (Math.sign(slip) || 0);
    const vx2 = vx - Jt / M, vy2 = e * vy;
    return { vx, vy, vx2, vy2, e, out: deg(Math.atan2(vy2, Math.abs(vx2))), reversed: vx2 < 0, speed: Math.hypot(vx2, vy2) / v, noSide: deg(Math.atan2(e * vy, Math.max(1e-6, vx - Math.min(MU_C * (1 + e) * vy, (2 / 7) * Math.abs(vx))))) };
  }

  return { set, current, atMouth, R, M, G, E_BB, MU_S, MU_R, MU_SP, E_C, MU_C, muBB, TABLE_L, TABLE_W, RP, SHELF_C, SHELF_S, POCKETS, SQ_R, SW_K, deg, rad, vadd, vsub, vmul, vlen, vdot, vunit, perp, dist2, pocketAt, inside, RAILS, bounce, step, stopDistance, slideOut, trace, collide, bankCandidates, planBank, shoot, slideState, cushion };
}
if (typeof module !== 'undefined') module.exports = kosmosBilliardsPhysics;
