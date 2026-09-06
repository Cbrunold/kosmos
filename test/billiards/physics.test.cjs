// The physics of /billiards against what can be worked out on paper.
//
//     node --test test/billiards/physics.test.cjs     (pytest runs this too)
//
// Each test states the claim the page makes and holds the code to it: the ninety-degree
// rule is exact at e = 1 and "4% short" at the engine's 0.92; momentum is kept through a
// collision and energy never made; the integrator's slide distance is the closed form's;
// throw peaks near a half-ball hit; running side rebounds long and reverse short; a straight
// shot at pot weight drops. A change that breaks a claim breaks here, not on the table.
const { test } = require('node:test');
const assert = require('node:assert/strict');
// package.json says type: module, so physics.js is read as text and evaluated — the page
// inlines it the same way, and the file stays a plain script with one function in it
const fs = require('node:fs');
const path = require('node:path');
const make = new Function(fs.readFileSync(path.join(__dirname, '../../web/billiards/physics.js'), 'utf8')
                          + '\nreturn kosmosBilliardsPhysics;')();

const C = Object.fromEntries(require('../../data/billiards/constants.json').constants.map((c) => [c.key, c.value]));
const P = make(C);                                                  // the table as the page has it
const IDEAL = make({ ...C, E_BB: 1, MU_BB_FIT: [0, 0, 0] });          // elastic balls, no friction between them

const near = (a, b, tol, msg) => assert.ok(Math.abs(a - b) <= tol, `${msg}: ${a} vs ${b} (tol ${tol})`);
const ke = (b, M) => 0.5 * M * (b.v[0] ** 2 + b.v[1] ** 2);

// a stun cue ball meeting a resting ball at a cut angle: the two just touching, the cue ball closing
function meet(Ph, cutDeg, v = 1.5, tip = 0) {
  const th = cutDeg * Math.PI / 180;
  const A = { p: [0, 0], v: [v, 0], s: [2.5 * v * tip, 0], z: 0, slid: 0 };
  const B = { p: [2 * Ph.R * Math.cos(th), 2 * Ph.R * Math.sin(th)], v: [0, 0], s: [0, 0], z: 0, slid: 0 };
  const ev = Ph.collide(A, B);
  assert.ok(ev, 'the balls did not collide');
  return { A, B, ev };
}

test('the ninety-degree rule: at e = 1 with no friction a stun cue ball leaves at a right angle to the object ball', () => {
  for (const cut of [10, 20, 30, 45, 60, 75]) {
    const { A, B } = meet(IDEAL, cut);
    const dot = A.v[0] * B.v[0] + A.v[1] * B.v[1];
    near(dot / (Math.hypot(...A.v) * Math.hypot(...B.v)), 0, 1e-9, `cos of the separation angle at a ${cut}° cut`);
  }
});

test('at the engine\'s e = 0.92 the separation falls a few degrees short of ninety — the "4% short" the page reports', () => {
  const { A, B } = meet(IDEAL === P ? P : make({ ...C, MU_BB_FIT: [0, 0, 0] }), 30);   // restitution alone, no throw
  const cos = (A.v[0] * B.v[0] + A.v[1] * B.v[1]) / (Math.hypot(...A.v) * Math.hypot(...B.v));
  const sep = Math.acos(cos) * 180 / Math.PI;
  assert.ok(sep < 90 && sep > 80, `separation ${sep}° should be a little under ninety`);
});

test('momentum is kept through a collision, throw and all', () => {
  for (const cut of [5, 30, 60, 85]) {
    const v = 2;
    const { A, B } = meet(P, cut, v, -0.3);
    near(P.M * (A.v[0] + B.v[0]), P.M * v, 1e-9, `x momentum at ${cut}°`);
    near(P.M * (A.v[1] + B.v[1]), 0, 1e-9, `y momentum at ${cut}°`);
  }
});

test('a collision never makes kinetic energy; an elastic frictionless one keeps it exactly', () => {
  for (const cut of [10, 30, 50, 70]) {
    const v = 1.8;
    const real = meet(P, cut, v);
    assert.ok(ke(real.A, P.M) + ke(real.B, P.M) <= 0.5 * P.M * v * v + 1e-12, `energy grew at ${cut}°`);
    const ideal = meet(IDEAL, cut, v);
    near(ke(ideal.A, P.M) + ke(ideal.B, P.M), 0.5 * P.M * v * v, 1e-12, `elastic energy at ${cut}°`);
  }
});

test('throw is a few degrees, largest near a half-ball hit, and zero for a full hit', () => {
  const rows = [];
  for (let cut = 0; cut <= 85; cut += 5) rows.push([cut, meet(P, cut, 1).ev.throwDeg]);
  near(rows[0][1], 0, 1e-6, 'a full hit has no tangential slip and no throw');
  const [peakCut, peak] = rows.reduce((a, b) => (b[1] > a[1] ? b : a));
  assert.ok(peakCut >= 15 && peakCut <= 45, `throw peaks at a ${peakCut}° cut; expected near half-ball`);
  assert.ok(peak > 0.5 && peak < 6, `peak throw ${peak}° is outside the 0.5–6° the literature gives`);
});

test('the integrator slides exactly as far, and as long, as the closed form says', () => {
  for (const [v0, tip] of [[2, 0], [2, -0.3], [3, 0.2], [1.2, -0.5]]) {
    const b = { p: [0, 0], v: [v0, 0], s: [2.5 * v0 * tip, 0], z: 0, slid: 0 };
    let d = 0;
    for (let i = 0; i < 200000; i++) {
      const x0 = b.p[0];
      P.step(b, 1e-4);
      d += Math.abs(b.p[0] - x0);
      if (Math.abs(b.v[0] - b.s[0]) < 1e-4) break;
    }
    const cf = P.slideOut(v0, tip);
    near(b.slid, cf.t, cf.t * 0.01 + 2e-4, `slide time at v ${v0}, tip ${tip}`);
    near(d, cf.d, Math.abs(cf.d) * 0.01 + 1e-4, `slide distance at v ${v0}, tip ${tip}`);
    near(Math.hypot(...b.v), Math.abs(cf.vRoll), Math.abs(cf.vRoll) * 0.01 + 1e-4, `speed when rolling takes over at v ${v0}, tip ${tip}`);
  }
});

test('a rolling ball stops after v² / 2 μ_r g, and stopDistance() says so before it does', () => {
  for (const v of [0.5, 1, 2]) {
    const b = { p: [0, 0], v: [v, 0], s: [v, 0], z: 0, slid: 0 };
    const want = v * v / (2 * P.MU_R * P.G);
    near(P.stopDistance(b), want, 1e-9, `stopDistance at ${v} m/s`);
    let d = 0;
    for (let i = 0; i < 400000 && Math.hypot(...b.v) > 0; i++) { const x0 = b.p[0]; P.step(b, 1e-4); d += b.p[0] - x0; }
    near(d, want, want * 0.005 + 1e-4, `integrated roll-out at ${v} m/s`);
  }
});

test('slideState() agrees with itself: off the tip, at the slide\'s end, and once rolling', () => {
  const v0 = 2, tip = -0.3;
  const cf = P.slideOut(v0, tip);
  const start = P.slideState(v0, tip, 0);
  assert.equal(start.phase, 'draw');
  near(start.ratio, 2.5 * tip, 1e-9, 'spin ratio off the tip is 2.5·tip');
  const end = P.slideState(v0, tip, cf.d);
  assert.equal(end.phase, 'rolling');
  near(end.v, cf.vRoll, 1e-6, 'speed where the roll begins');
  const later = P.slideState(v0, tip, cf.d + 0.5);
  assert.ok(later.v < end.v && later.alive, 'rolling slows it down');
});

test('the cushion: straight in comes straight back at the deadened restitution; running side rebounds long, reverse short', () => {
  for (const v of [0.5, 2, 5]) {
    const c = P.cushion(90, v, 0);
    const e = Math.max(C.CUSHION_E_MIN, P.E_C - C.CUSHION_DEADEN * v);
    near(c.speed, e, 1e-9, `rebound speed ratio at ${v} m/s`);
    near(c.out, 90, 1e-9, 'straight in, straight out');
  }
  const none = P.cushion(45, 2, 0), running = P.cushion(45, 2, 0.4), reverse = P.cushion(45, 2, -0.4);
  assert.ok(running.out < none.out, `running side should rebound flatter: ${running.out}° vs ${none.out}°`);
  assert.ok(reverse.out > none.out, `reverse side should rebound steeper: ${reverse.out}° vs ${none.out}°`);
  // with no side the rail's friction takes from the speed along it while restitution takes from the speed
  // into it, and friction wins: the rebound is steeper than a mirror. (The roll a ball carries into a rail,
  // which bends a rebound long again, is the main sim's business, not this tab's.)
  assert.ok(none.out > 45, );
});

test('bounce() keeps a ball on the table and takes the restitution off its normal speed', () => {
  const b = { p: [P.R - 0.002, 0.6], v: [-1, 0.3], s: [-1, 0.3], z: 0, slid: 0 };
  const rail = P.bounce(b);
  assert.equal(rail && rail.name, 'left');
  assert.ok(b.v[0] > 0 && b.p[0] >= P.R, 'reflected back inside');
  near(b.v[0], Math.max(C.CUSHION_E_MIN, P.E_C - C.CUSHION_DEADEN * 1) * 1, 1e-9, 'normal speed after the rail');
});

test('a ball rolled at a corner pocket drops at pot weight and stops short when too slow', () => {
  const aim = (v) => {
    const from = [0.3, 0.3], d = -1 / Math.SQRT2;
    return P.trace({ p: from.slice(), v: [v * d, v * d], s: [v * d, v * d], z: 0, slid: 0 }, 0.002, false, P.POCKETS[0].p, 20000);
  };
  assert.equal(aim(1.5).pocket, 0, 'drops in the top-left corner');
  const slow = aim(0.25);
  assert.equal(slow.pocket, null); assert.equal(slow.hang, null);
});

test('shoot(): a straight stun shot at pot weight pots the ball and leaves the cue ball nearly dead', () => {
  const S = P.shoot([0.8, 0.8], [0.4, 0.4], { pk: 0 }, 2, 0, 0, true);
  assert.ok(S.feasible && S.reached, 'the cue ball reached the object ball');
  assert.ok(S.th < 0.02, `a straight shot, cut ${S.th} rad`);
  assert.equal(S.obTrace.pocket, 0, 'the object ball dropped in the top-left corner');
  assert.ok(Math.hypot(...S.vCB) < 0.15 * 2, `stun: the cue ball keeps ${Math.hypot(...S.vCB)} m/s of 2`);
  assert.equal(S.firstBall, 1); assert.ok(S.firstIsTarget);
});
