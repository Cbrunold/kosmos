# The Tomes — every shot in pool, as lessons

A syllabus for the cue-sports shelf. Ten tomes, each a family of shots, each lesson
one thing the table asks of you. The order is the order the physics arrives in:
first the ball goes straight, then it goes at an angle, then the tip height, then
the tip's side, then the rails, then everything else the rails and the other balls
allow — and last, the shots that leave the cloth, which the lab does not integrate
yet.

Sources: the three skills already on the Notion Skills DB (*The Cut Shot*, *Follow,
Draw and Stun*, *Using Side*), the twelve cue-sports glossary terms, the equations
shelf (`scripts/seed_billiards.py`), and Dr Dave Alciatore's syllabus — the five
volumes of the *Video Encyclopedia of Pool Shots* (VEPS I basic shot-making and
position · II english and position control · III safety and strategy · IV banks,
kicks and advanced shots · V skill and specialty shots), the Billiard University
Exam I (fundamentals) / Exam II (skills) split, and the FAQ index at
drdavepoolinfo.com (30°/90° rules, banks and kicks, carom and kiss, cling/skid,
combinations, drag, draw, follow, frozen balls, jump, kiss-back, lag, massé,
pattern play, position control, pre-shot routine, …).

**Lab** says what `/billiards` does with the lesson today:
`sim` — the shot lab integrates it on the engine's constants ·
`partial` — the physics is there but not the drill, or a simplification bites ·
`none` — off the table for now. Each lesson names the shelf equation it rests on.

Existing on the site: three skills, five drills (stop-shot, draw and follow
ladders, cut rainbow, bank ladder), eight layouts, three diamond systems, the
cushion lab, the slide → roll lab, the run-out. Everything below marked *new*
would be a row on the Skills DB, a drill in `DRILLS`, or a layout in `LAYOUTS`.

---

## Tome 0 — The Stance (before the ball moves)

Not physics, and not in the lab — but BU Exam I is mostly this, and every tome after
assumes it. One skill page, "The Stroke", would carry it.

| # | Lesson | What it is | Dr Dave | Lab |
|---|--------|------------|---------|-----|
| 0.1 | Stance and alignment | Feet, hips, chin on the cue line; the vision centre — where the cue sits under your eyes | Fundamentals; Eyes and Vision | none |
| 0.2 | Bridge | Open, closed, rail, over-a-ball, mechanical bridge | Bridge | none |
| 0.3 | Grip | Loose, wrist neutral, the effective mass in the speed-transfer equation | Grip; *Cue-to-Ball Speed Transfer* | none |
| 0.4 | The stroke | Pendulum, pause, follow-through; acceleration through the ball | Fundamentals; *Cue-to-Ball Speed Transfer* | none |
| 0.5 | Pre-shot routine | Decide standing, aim standing, get down, feathers, deliver | Pre-Shot Routine | none |
| 0.6 | Chalk, miscue, cue and tip | Why a miscue is a friction limit at b ≈ R/2; tip hardness, low-deflection shafts | Miscue; Cue Tip; Cue | partial — the miscue limit is on *Tip Offset and Spin* |

---

## Tome I — The Straight Line

Straight-in shots, where the object ball's path is not in question and only the cue
ball's is. This is the existing skill *Follow, Draw and Stun*, split into its parts
and given speed control.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 1.1 | Centre ball, straight in | Pocket it; watch the cue ball skid then roll | *Slide to Roll* (2/7 of the speed lost to the skid) | VEPS I | sim — slide → roll tab |
| 1.2 | The stop shot | Cue ball arrives sliding with no spin: dead stop | *Slide to Roll*; *Coefficient of Restitution* (0.92 → it creeps; a touch of draw fixes it) | Stun; BU Exam I | sim — stop-shot ladder |
| 1.3 | Stun as a state, not a shot | Sliding at contact, whatever the tip height was at the cue; distance and speed decide it | *Slide to Roll*; *Tip Offset and Spin* | 30°/90° Rules; Stun | sim — the `slideState` phase readout |
| 1.4 | Follow | Above centre: skid, then the topspin the collision left alone curves it on | *Tip Offset and Spin*; *Slide to Roll* | Follow; NV L.83 | sim — follow ladder |
| 1.5 | Draw | Below centre: backspin survives contact, cloth reverses it; distance goes as v² | *Tip Offset and Spin*; *Slide to Roll* | Draw | sim — draw ladder |
| 1.6 | The drag shot | Draw played soft and long so the backspin dies on the way and the ball arrives rolling slowly — the soft-speed shot with a firm stroke | *Slide to Roll*; *Rolling Resistance* | Drag Shot | partial — the slide lab shows the crossing; no drill *(new drill)* |
| 1.7 | Speed control and the lag | How far a rolling ball goes: d = v₀²/2μ_r g; one, two, three table-lengths | *Rolling Resistance* | Lag Shot; BU Exam I speed-control drills | partial — the report gives stop distances; no lag drill *(new drill)* |
| 1.8 | The long straight | Distance exposes a crooked stroke; why the pocket narrows with pace | *Rolling Resistance*; pocket-narrowing model | VEPS I | sim — "The long straight" layout |

---

## Tome II — The Cut

The existing skill *The Cut Shot*, as a full tome. Where the object ball goes, and
the first answer to where the cue ball goes.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 2.1 | Ghost ball | Aim the cue ball's centre 2R behind the object ball on the pocket line | *Ghost-Ball Aim* | Aiming; DAM | sim — practice mode draws the ghost |
| 2.2 | Ball-hit fractions | Full, ¾, ½ (30°), ¼ (48.6°), ⅛: f = 1 − sin θ | *Ghost-Ball Aim* | Aiming; Fractional-ball aiming | sim — `fraction` in the report |
| 2.3 | The tangent line — the 90° rule | Stunned cue ball leaves at right angles to the object ball; v_OB = v cos θ, v_CB = v sin θ | *Ninety-Degree Rule* | 30°/90° Rules | sim — tangent drawn on every shot |
| 2.4 | The 30° rule — the peace sign | Rolling cue ball bends forward off the tangent to ≈30° for ¼–¾ hits | *Thirty-Degree Rule* | 30°/90° Rules | sim — `deflect` in the report |
| 2.5 | Cut-induced throw | Slow and thin throws the object ball a degree or three toward the cue ball's line; aim thinner | *Throw* (Alciatore's μ(v) fit) | Throw; Cut Shot | sim — contact & throw tab |
| 2.6 | The thin cut | ⅛-ball and under; the throw column is the aim | *Throw*; *Ghost-Ball Aim* | Cut Shot | sim — "Thin cut, long way home" layout |
| 2.7 | Back cuts | Cutting away from your natural sight line; the same ghost, a harder picture | — | Cut Shot | partial — no layout *(new layout)* |
| 2.8 | Frozen to the rail — rail-first and ball-first | The object ball on the cushion: hit rail first or ball first, and what the rail's friction does to each | *Cushion Rebound*; *Throw* | Frozen Balls; Rail cut shots | sim — "Frozen to the rail" layout |
| 2.9 | Cling, skid, kick | Chalk on the contact point doubles μ; the object ball goes thick for no reason you did | *Throw* (μ ≈ 0.06 → 0.12) | Cling/Skid/Kick | partial — μ is a constant per shot; no random skid |
| 2.10 | The hanger and the jaws | A ball in the mouth: pocket speed, shelf depth, rattles | pocket model (mouth, shelf, narrowing) | Hanger; Pocket | sim — `atMouth` / rattle |
| 2.11 | The cut rainbow | ±8° to ±70° in ten steps, one pocket | all of the above | BU Exam I cut drills | sim — cut rainbow drill |

---

## Tome III — Height: position with follow, draw and stun

Tome I's tip heights applied to Tome II's angles. This is where position play begins:
the cue ball's final path is the tangent line bent by whatever spin survived.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 3.1 | Stun on a cut | Cue ball holds the tangent line; the cleanest position tool there is | *Ninety-Degree Rule* | Cue Ball Control; 90° rule | sim |
| 3.2 | Stun run-through and stun-back | A little roll or a little draw on a near-straight shot: the cue ball moves a hand's width along the line of centres, no more | *Slide to Roll*; *Ninety-Degree Rule* | Stun; Position Control | sim |
| 3.3 | Follow on a cut | Tangent first, then the 30° bend; faster bends less | *Thirty-Degree Rule* | Follow; NV L.83 | sim |
| 3.4 | Draw on a cut | Tangent first, then pulled back — to about 90° the other way on a half-ball | *Slide to Roll*; *Ninety-Degree Rule* | Draw | sim |
| 3.5 | The trisect system | Where a drawn cue ball goes on a medium cut: the final direction trisects the angle between the tangent and the reverse of the aim line | *Slide to Roll* | Trisect system; BU Boot Camp | partial — the sim gives it; not drawn as a system *(new overlay)* |
| 3.6 | Speed against height | Same height, twice the speed: four times the skid; the two dials of position | *Slide to Roll* | Cue Ball Control | sim — slide → roll tab |
| 3.7 | Natural angles and the rail | Where the tangent line meets a cushion and what comes back: one-rail position | *Cushion Rebound*; *Thirty-Degree Rule* | Position Control; VEPS I | sim — rails rebound live |
| 3.8 | Landing zones | Pick a zone before the shot; three in five | — | Position Control; BU Exam I | partial — "called pocket / pocket speed" conditions; no zone target *(new condition)* |
| 3.9 | The line-up and the L | The two classic position drills | all | Drills; Pattern Play | sim — both layouts |

---

## Tome IV — Side: the best use of side spin

The existing skill *Using Side*, as a tome. The rule of the tome: side does four
things, and you asked for one of them.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 4.1 | What side is | Tip left or right: spin about a vertical axis; how long it lasts (μ_sp) | *Tip Offset and Spin* | English | sim |
| 4.2 | Squirt | The cue ball leaves opposite the side, ≈2.5° at full side — a cue constant, not a table one | squirt constant (5° per b/R) | Cue Ball Deflection; Squirt | sim — shot lab applies it |
| 4.3 | Swerve | Any elevation curves the ball back toward the aim while it slides; long soft shots with side bend visibly | swerve k = 0.08 | Swerve | sim — a modelled curve, not full massé |
| 4.4 | Net deflection — squirt against swerve | The two cancel at one speed and distance; play at that speed or learn the offset | squirt + swerve | Effective squirt; BHE/FHE | partial — the sim adds them; no calibration drill *(new drill)* |
| 4.5 | Spin-induced throw | Side throws the object ball the opposite way, up to a few degrees, most on slow shots | *Throw* | Throw; English | sim — contact & throw tab |
| 4.6 | Inside and outside | Outside english cancels cut-induced throw (gearing — no throw at all at the right amount); inside adds to it | *Throw* | Gearing english; Inside/outside | sim |
| 4.7 | Running side | Surface moving against travel at the rail: friction speeds the ball along, the angle lengthens | *Cushion Rebound* (μ_c) | English; Cushion | sim — cushion lab |
| 4.8 | Reverse side | Shortens the angle, kills the speed; the ball can even come back the way it went | *Cushion Rebound* | English | sim — cushion lab `reversed` |
| 4.9 | Side for position — two and three rails | Choose the side for the cushions, then pay at the object ball | all of the tome | Position Control; VEPS II | sim |
| 4.10 | Backhand and fronthand english | Pivoting the aim to absorb squirt: the pivot length of your cue | squirt constant | BHE/FHE aiming | none — a cue property the lab does not expose *(new skill page)* |
| 4.11 | The no-side test | Play every shot without side first; add it only when the position demands it | — | Advice | sim — the discipline, not a feature |

---

## Tome V — Banks

The object ball off a cushion into a pocket. The mirror is the first lie everyone is
told; the rest of the tome is the corrections.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 5.1 | Bank vocabulary | Cross-side, cross-corner, long bank, short bank, straight-back | — | Banks and Kicks (terminology) | partial — `planBank` names the rail only |
| 5.2 | The mirror | Reflect the pocket through the rail; exact only for a ball that loses nothing | *Cushion Rebound* | Banks | sim — two-rail mirror system |
| 5.3 | Speed shortens the bank | Rubber gives back less the harder it is hit (e_c = 0.87 − 0.04 v); firm banks go short | cushion deadening | Bank speed effects | sim — `bankCandidates` sweeps ρ from 0.7 to 5 |
| 5.4 | Cut angle and the bank | Cutting the object ball into the rail gives it side (collision-induced spin) and throws it; the bank walks | *Throw*; *Cushion Rebound* | Bank cut effects | partial — a struck ball leaves without spin of its own |
| 5.5 | English on a bank | Running side on the cue ball transfers a little to the object ball; reverse holds it | *Cushion Rebound* | Bank english effects | partial — spin does not cross a collision |
| 5.6 | Banking the cue ball | The cue ball off a rail into a ball or a pocket — a kick with intent (see Tome VI) | *Cushion Rebound* | Banks and Kicks | sim |
| 5.7 | Kiss-back and double kiss | The object ball comes back into the cue ball, or the cue ball into it: when it happens and when it is the shot | *Ninety-Degree Rule* | Kiss-Back Shot; Double Kiss | sim — every ball is live, so it happens |
| 5.8 | The bank ladder | Ten positions, cross-side | all | BU Exam II banks | sim — bank ladder drill |

---

## Tome VI — Kicks

The cue ball off a cushion first. The diamond systems — a calculator bolted to the
rails — and where the arithmetic drifts.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 6.1 | One-rail kick — the mirror | Reflect the target through the rail; correct for speed and for the side the cue ball picks up | *Cushion Rebound* | Kick Shots; NV L.76 | sim — the cushion lab, and the two-rail system with one rail |
| 6.2 | Two-rail kick — the mirror | Reflect twice; pure geometry until the rubber has its say | *Cushion Rebound* | Two-rail kick system; NV L.76 | sim — two-rail mirror system |
| 6.3 | Three-rail kick — corner five | The carom player's system: running side at a firm even pace is part of the system | *Cushion Rebound* (μ_c) | Corner-5 system; NV L.77 | sim — corner five |
| 6.4 | The plus system | Short-rail-first three-rail kicks | *Cushion Rebound* | Plus system | none *(new diamond system)* |
| 6.5 | Kicking to scratch, kicking to hit | The same geometry used for a safety or a foul | — | Kick Shots | sim — "three rails — scratch it" |
| 6.6 | Kick speed and side | Zero the side and watch corner five stop working; hit hard and watch the mirror go short | cushion deadening; μ_c | Kicking master class | sim |
| 6.7 | Hooked — kick at it | Two balls in the way; which system and why | all | BU Exam II kicks | sim — "Hooked" layout, "kick first" condition |

---

## Tome VII — Other balls: combinations, caroms, kisses, frozen balls

Every ball on the table is live in the lab. This tome is the shots that use it.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 7.1 | The combination | Ghost ball twice; the errors multiply with distance | *Ghost-Ball Aim*; *Throw* | Combination Shots | sim |
| 7.2 | Throw on a combo | The first ball throws the second; slow combos go thick | *Throw* | Combination Shots | sim |
| 7.3 | Frozen combinations | Two balls touching: the second goes along the line of centres, plus throw — up to 5°, and the "dead" combo is not | *Throw*; *Ninety-Degree Rule* | Frozen Balls | sim |
| 7.4 | The carom (billiard) | Cue ball off an object ball into another, or into a pocket: the tangent line is the aim | *Ninety-Degree Rule*; *Thirty-Degree Rule* | Carom and Kiss Shots | sim — "carom after" condition |
| 7.5 | The kiss shot | The object ball off another object ball; the 90° rule for the struck one | *Ninety-Degree Rule* | Kiss Shots | sim |
| 7.6 | Cue ball frozen to the rail or to a ball | Where the tip can reach; the push-through and the double hit and why they are fouls | — | Frozen Balls; Double Hit | none — no rules engine for the double hit |
| 7.7 | Clusters and break-outs | Using a rolling cue ball or an object ball to open a cluster on the way to position | *Thirty-Degree Rule*; *Rolling Resistance* | Pattern Play; VEPS III | sim — "nothing else moves" condition inverted |

---

## Tome VIII — Safety and strategy

VEPS III and BU Exam II. The shots where the pocket is not the point.

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 8.1 | The stop-shot safety | Stun the cue ball behind a blocker; the simplest hook | *Slide to Roll* | Safety Play | sim — "safety" condition |
| 8.2 | The roll-up | Soft, ball frozen to a rail or a cluster, cue ball nearby | *Rolling Resistance* | Safety Play | sim |
| 8.3 | The two-way shot | A shot that leaves a safety if it misses | — | Two-way shots | partial — two conditions at once |
| 8.4 | Kick safeties and distance | When a hit is enough and a pocket is not | Tome VI | Safety Play | sim |
| 8.5 | Pattern play — key balls | Plan three balls ahead; the key ball to the money ball | Tome III | Pattern Play; VEPS III | sim — the run-out |
| 8.6 | Nine-ball and eight-ball patterns | Lowest ball first; solids and stripes; the break-out ball | — | Games; 8-ball strategy | partial — the run-out plays nine-ball only |
| 8.7 | Ball in hand | Where to put it: the straight-in stop shot, the shape for the next two | Tome I | Ball-in-hand | partial — the cue ball drags anywhere; no BIH prompt |

---

## Tome IX — The Break

| # | Lesson | Shot | Physics on the shelf | Dr Dave | Lab |
|---|--------|------|----------------------|---------|-----|
| 9.1 | Cue speed into ball speed | Effective mass of the cue and the grip; 1.5× the cue's speed in the ideal | *Cue-to-Ball Speed Transfer* | Break | partial — the strike slider is ball speed |
| 9.2 | The nine-ball break | Hit the one full from the box; the wing ball; where the cue ball should stop | *Ninety-Degree Rule*; *Coefficient of Restitution* | Break; VEPS V | sim — nine-ball rack |
| 9.3 | The eight-ball break | Second-ball break, head-on; the cushion floor at break speed (e_c ≥ 0.55) | cushion floor; pocket narrowing floor | Break | sim — eight-ball rack |
| 9.4 | The cut break and the soft break | Trading power for control; the rack's geometry against pattern racking | — | Break; Pattern Racking | sim |

---

## Tome X — Off the cloth (coming soon)

The lab's first assumption is *balls stay on the cloth*, and its second is *the cue
is almost level*. This whole tome is the exception: the cue elevated on purpose. None
of it is integrated in kosmos or in pool-sauce-engine today; the lessons are listed so
the syllabus is complete and the engine work is scoped.

| # | Lesson | Shot | Physics it would need | Dr Dave | Lab |
|---|--------|------|-----------------------|---------|-----|
| 10.1 | Swerve on purpose (semi-massé) | Elevate 20–40°, side and a little below: the ball curves round a blocker | cue elevation as an input; the lateral friction force while sliding, integrated on the cloth (the k = 0.08 model generalised to any elevation) | Massé Shot | none — swerve is a fixed-elevation model |
| 10.2 | The massé | Cue near vertical; the ball goes out along the aim, curves back along the spin axis's projection — Coriolis's own case | full 3D spin vector, the spin axis tilted out of vertical; slide-to-roll with a horizontal spin component; the cue ball's hop off the cloth at impact | Massé Shot; Coriolis 1835 | none |
| 10.3 | The piqué | A short massé with the cue almost vertical, the ball drawn straight back | as 10.2 | Massé Shot | none |
| 10.4 | The jump shot | Elevate 30–45°, hit the cloth through the ball; the ball leaves the table; where it lands and with what spin | vertical velocity from the tip's downward component; a bounce against the slate (restitution); landing spin; a shorter jump cue | Jump Shot; VEPS V | none — no z component |
| 10.5 | Jacked-up over a ball | Elevation you did not want — the unintentional swerve tome IV warned about | as 10.1 | Jacked-up shots; BU Exam II | none |
| 10.6 | The hop on a firm draw or stun | The cue ball skips off the cloth on a hard low hit and skids in the air — why a hard stop shot is "not there" for a moment | z component; a hop model | High-speed video (HSV) | none — noted on the assumptions list |

What Tome X needs from the engine, in order: (1) cue elevation as a shot input;
(2) the spin as a three-component vector, not `s` on the cloth plus `z` about the
vertical; (3) a vertical velocity and a bounce off the slate; (4) the cushion in 3D,
or at least a rule for a ball that arrives airborne. (1) and (2) give 10.1–10.3;
(3) gives 10.4–10.6.

---

## What is already on the site, mapped to the tomes

| On the site | Tome |
|-------------|------|
| Skill *The Cut Shot* | II |
| Skill *Follow, Draw and Stun* | I, III |
| Skill *Using Side* | IV |
| Drills: stop-shot ladder, draw ladder, follow ladder | I |
| Drill: cut rainbow | II |
| Drill: bank ladder | V |
| Diamond systems: two-rail mirror, corner five, scratch it | VI |
| Cushion lab | IV, V, VI |
| Slide → roll lab | I, III |
| Layouts: line-up, the L | III |
| Layouts: frozen to the rail, long straight, thin cut | II |
| Layout: hooked — kick at it | VI |
| Layouts: nine-ball rack, eight-ball rack; the run-out | VIII, IX |
| Conditions: clean hit, no rail, kick first, three rails, called pocket, pocket speed, carom, nothing else moves, safety | VI, VII, VIII |

## Skills DB rows the tomes ask for

Seven new rows in the Cue sports category, one per tome that has no skill page yet
(Tome 0 *The Stroke*; V *The Bank*; VI *The Kick*; VII *Combinations and Caroms*;
VIII *The Safety*; IX *The Break*; X *Massé and Jump* — the last flagged coming
soon), plus a *Tome* select property on the Skills DB so the shelf can group them.
The three existing rows keep their names and take Tome I–IV. The seed lives in
`scripts/seed_billiards.py`, which is idempotent; the rows would be appended to its
`SKILLS` list in the same ten-field shape.
