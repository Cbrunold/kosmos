"""Seed the physics of the pool table: the equations, and the three skills that use them.

Companion to the pool-sauce-engine repo (Rōnin, the Five Pillars): that engine
integrates these equations; this shelf states and explains them, and its lookup
table quotes the engine's own constants.py so the two never disagree on a number.

  EQUATIONS (10) — the ninety-degree rule, ghost-ball aim, throw, tip offset →
                   spin, slide-to-roll, the thirty-degree rule, cushion rebound,
                   cue-to-ball speed transfer (field: Billiards); and two general
                   results the game happens to need — coefficient of restitution
                   and rolling resistance (field: Mechanics). Every one has
                   Requires edges onto momentum, kinetic energy, friction, torque,
                   moment of inertia, angular momentum, vector projection and
                   trigonometry — the shelf earning its keep on a felt table.
  SKILLS (10)    — one per tome of data/billiards/tomes.md: The Stroke, The Cut Shot,
                   Follow Draw and Stun, Using Side, The Bank, The Kick, Combinations
                   and Caroms, The Safety, The Break, Massé and Jump (the last is the
                   tome the lab does not integrate yet, and says so). Tools, steps,
                   safety, how it fails, done when; each linked to its equations and
                   carrying its Tome. Skills category: Cue sports.

Coriolis wrote the first mathematical treatment of all of this in 1835 —
"Théorie mathématique des effets du jeu de billard" — six years after the paper
that gave work and kinetic energy their modern form. Rows he covered carry that
year; the modern rules of thumb (thirty-degree, throw limits) carry none.

Idempotent like the other seeds. Run on the VPS:  ./deploy.sh seed_billiards seed_glossary
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_theories import call, ensure_props, ensure_select_options, query_all, sync_rows, title_of  # noqa: E402

EQ_DS = "638fda32-4a6d-4d65-8349-433ce4f0b698"
SKILLS_DS = "804e17aa-435b-4306-acbb-2ec926b87b10"

BI = "Billiards"
ME = "Mechanics"

# ------------------------------------------------------------------ equations
# name, equation, field, named after, symbols, significance, year
EQUATIONS = [
    ("Ninety-Degree Rule", "v_OB = v cos θ  (along the line of centres);  v_CB = v sin θ  (along the tangent line)", BI, None,
     "v cue-ball speed at contact · θ the cut angle, between the cue ball's path and the line joining the two centres at contact · v_OB object-ball speed · v_CB cue-ball speed after impact, with no spin acting yet",
     "Two equal balls, one at rest, no spin: after the hit they separate at a right angle. The object ball leaves along the line of centres — always, whatever else you do — and the cue ball keeps whatever was perpendicular to that. It is momentum and energy conservation with equal masses, and it is a projection: cos θ of the speed goes one way, sin θ the other, cos²θ of the energy to the object ball. A half-ball hit (θ = 30°) sends 75 % of the energy on. Coriolis set it down in 1835. Real balls bend it a degree or two (restitution, throw), and spin bends the cue ball's path afterwards — but the tangent line is where every cue-ball plan starts.", 1835),
    ("Ghost-Ball Aim", "aim the cue ball's centre at the point 2R from the object ball's centre, on the line to the pocket;  ball-hit fraction f = 1 − sin θ", BI, None,
     "R ball radius · θ cut angle · f the fraction of the object ball's width the cue ball covers at contact: 1 for a full hit, ½ for a half-ball, ¼ for a quarter-ball",
     "Picture the cue ball frozen where it must be at contact — touching the object ball on the far side from the pocket. Its centre is one ball's diameter from the object ball's centre along the pocket line; send the real cue ball there. The fraction the two overlap when seen from the cue is 1 − sin θ, which is why a half-ball hit is a 30° cut and a quarter-ball is 48.6°. Pure geometry; throw adds a correction on top.", 1835),
    ("Coefficient of Restitution", "e = v_separation / v_approach;  head-on, kinetic energy kept = e²", ME, "Isaac Newton",
     "e a number between 0 (perfectly inelastic — they stick) and 1 (perfectly elastic — none lost) · v_approach, v_separation the relative speeds along the line of centres before and after",
     "Newton's experimental law of 1687: how much of the closing speed survives a collision. Phenolic pool balls run about 0.92, so a straight-in stun shot leaves the cue ball creeping forward and the object ball with 85 % of the energy; a cushion returns roughly 0.75 of the energy, so the ball comes off at 87 % of its speed. Steel on steel is 0.9-ish, a superball 0.9, a lump of clay near 0. It is why the ninety-degree rule is really eighty-eight, and why a stop shot needs a touch of draw.", 1687),
    ("Throw", "throw angle ≈ atan(μ v_t / v_n), up to about 5°", BI, None,
     "μ ball-to-ball friction, about 0.06 for clean phenolic · v_t the relative speed of the two surfaces across the contact — from the cut angle, from side spin, or both · v_n the closing speed along the line of centres",
     "During the fifth of a millisecond the balls touch, friction drags the object ball a little off the line of centres, toward the direction the cue ball's surface was sliding. A cut throws the object ball forward of the geometric line (cut-induced throw); side spin throws it left or right (spin-induced throw). Slow shots throw more — the friction has more time relative to the speed — and it saturates once the surfaces stop slipping. Chalk on the contact point can double it. Nobody pockets long, slow cuts without allowing for it.", None),
    ("Tip Offset and Spin", "ω = (5/2) v b / R²  ;  miscue beyond b ≈ R/2", BI, None,
     "ω spin imparted, radians per second · v cue-ball speed off the tip · b the tip's offset from the ball's centre, perpendicular to the cue · R ball radius",
     "Hit off-centre and the impulse has a lever arm; the ball's moment of inertia is ⅖ mR², so the spin is 5/2 · v · b / R². Half a radius of offset — the practical limit before the tip slides off — gives a ball spinning about as fast as it would if it were already rolling at that speed. Above the centre it is follow, below it draw, to the side it is english (and squirt: the cue ball leaves a little off the cue's line, by an amount that is a property of the cue, not the table).", 1835),
    ("Slide to Roll", "rolling when v = ω R;  a stunned ball rolls after t = 2 v₀ / (7 μ_s g), at 5/7 of its speed", BI, None,
     "v linear speed · ω spin · R radius · v₀ speed at the start of the slide · μ_s sliding friction on cloth, about 0.2 · g gravitational acceleration",
     "A ball struck at centre skids first — no spin, so the cloth drags its bottom and spins it up while slowing it down — until the surface speed matches the ball's speed and it rolls. It loses two-sevenths of its speed getting there, in a distance that scales with v₀². Topspin shortens the skid, backspin reverses it: a drawn cue ball skids backward-spinning, stops spinning, then rolls back the way it came. Every follow and draw shot is this transition happening after the collision instead of before it.", 1835),
    ("Thirty-Degree Rule", "a rolling cue ball leaves a ¼- to ¾-ball hit at about 30° from its original line", BI, None,
     "the deflection of the cue ball's final rolling path from its incoming line, for a naturally rolling cue ball and a medium cut",
     "Not a law but a consequence: the ninety-degree rule sends the cue ball down the tangent line, then its topspin — which the collision did not touch — bends it forward as it takes up roll again. Over the middle range of cuts that bend lands the ball near 30° from where it was going, which is why a peace sign held at the object ball predicts where the cue ball ends up. Faster shots and thinner or fuller hits break it; stun (no roll) keeps the ninety.", None),
    ("Rolling Resistance", "d = v₀² / (2 μ_r g)", ME, None,
     "d the distance a rolling ball travels before stopping · v₀ its starting speed · μ_r rolling resistance coefficient — about 0.01 on worsted cloth, 0.002 for a steel wheel on rail · g gravitational acceleration",
     "A rolling body loses energy slowly, to the deformation of the surface and the ball, and the deceleration is nearly constant: μ_r g. On a pool table that is a tenth of a metre per second per second, so a ball at 1 m/s rolls about five metres and speed control is a matter of a few percent. Coulomb measured rolling friction in 1781; the work–energy theorem does the rest.", 1781),
    ("Cushion Rebound", "v_n,out = e_c v_n,in;  the tangential component and side spin lose to cushion friction", BI, None,
     "v_n the speed component into the cushion, before and after · e_c the cushion's speed restitution — about 0.87, from retaining ¾ of the energy · the component along the rail is reduced by friction, and side spin is partly converted to it",
     "The rail gives back most of the speed that hit it square and slows what ran along it, so the ball leaves at a shorter angle than it arrived — more so when it arrives fast. Side spin adds or subtracts to that along-rail component: running english lengthens the angle and keeps the ball moving, reverse shortens it and kills speed. Cushions are rubber, not physics constants; every table plays a little differently, and players test them before a match.", 1835),
    ("Cue-to-Ball Speed Transfer", "v_ball ≈ v_cue · 2 m_cue / (m_cue + m_ball) · (1 + e)/2", BI, None,
     "v_cue the cue's speed at impact · m_cue the mass that actually follows through — the cue, or on a loose grip mostly its front end · m_ball 170 g · e tip–ball restitution, about 0.7–0.9",
     "A heavy cue on a light ball gives the ball more speed than the cue had: with a 540 g cue and a 170 g ball the ideal is about 1.5 times, less the tip's losses. Which is why a firm stroke is about cue speed, not muscle, and why the grip's tightness changes the effective mass but not much else. Momentum conservation and Newton's law of impact, nothing more.", None),
]

# ------------------------------------------------------------------ requires
REQUIRES = {
    "Ninety-Degree Rule": ["Conservation of Momentum", "Kinetic Energy", "Vector Projection", "Trigonometric Ratios"],
    "Ghost-Ball Aim": ["Trigonometric Ratios", "Ninety-Degree Rule"],
    "Coefficient of Restitution": ["Conservation of Momentum", "Kinetic Energy"],
    "Throw": ["Friction", "Ninety-Degree Rule", "Trigonometric Ratios"],
    "Tip Offset and Spin": ["Torque", "Moment of Inertia", "Momentum and Impulse"],
    "Slide to Roll": ["Friction", "Angular Momentum", "Moment of Inertia", "Kinematic Equations"],
    "Thirty-Degree Rule": ["Ninety-Degree Rule", "Slide to Roll"],
    "Rolling Resistance": ["Work–Energy Theorem", "Friction"],
    "Cushion Rebound": ["Coefficient of Restitution", "Friction", "Vector Projection"],
    "Cue-to-Ball Speed Transfer": ["Conservation of Momentum", "Coefficient of Restitution"],
}

# ------------------------------------------------------------------ skills
# name, category, difficulty, summary, science, tools, steps, safety, fails, done, equations, tome
# The tomes are data/billiards/tomes.md — one skill page per tome, in the order the physics arrives.
SKILLS = [
    ("The Stroke", "Cue sports", "Beginner",
     "Before the ball moves: stance, bridge, grip and the stroke itself — the only part of the game that is not physics, and the part every other page assumes.",
     "The cue is a hammer with a long handle, and the ball takes its speed from the cue's speed and its effective mass — the part of the cue that actually follows through, which a loose grip makes the front end and a tight one the whole stick. Which is why a firm shot is about the speed of the tip, not the muscle behind it, and why a stroke that decelerates into the ball barely spins it. Alignment is the rest: the cue must run under the eye that sees straight — the vision centre — or a straight-looking line is not one, and the tip must arrive where you aimed it, which is what the pause at the back and the follow-through are for. A miscue is a friction limit: beyond half a radius off centre the tip slides instead of gripping, chalk or no chalk.",
     "A table and a cue whose weight you know; chalk; a phone on a tripod, filming from behind the cue, because nobody can feel their own stroke.",
     "Stand behind the shot and pick the line standing up; then step in so the cue drops onto that line, chin over it.\nMake the bridge before the grip: hand flat and still, the cue sliding in the groove without touching your fingers on the way through.\nHold the butt where the cue balances a hand behind the middle, fingers a cradle, thumb relaxed; the wrist hangs.\nStroke from the elbow only, the upper arm a fixed pendulum pivot; two or three feathers, a pause at the back, then accelerate through the ball to a stop a hand's width past where it was.\nFilm ten straight-in shots at a metre and watch the tip: it should finish on the line you aimed. If it drifts, the fault is in the bridge or the grip, not the eyes.\nBuild a routine you can name — decide, aim, get down, feather, pause, deliver — and run it on every shot, including the easy ones.",
     "Nothing but the cue: keep the follow-through low so the tip does not dig into the cloth, and never lean the cue on a table edge where it can fall.",
     "Aiming after getting down, so the body has to twist to fix the line. A bridge that slides. Gripping tighter as the stroke speeds up — the effective mass jumps and the ball takes off. Dropping the elbow on the follow-through, which lifts the tip and adds spin you did not ask for. Steering the cue on the last stroke to rescue an aim the feathers had already shown was wrong.",
     "Ten straight-in shots at a metre, filmed, and the tip finishes on the line every time; the cue ball follows dead straight through the object ball's place with no drift to either side.",
     ["Cue-to-Ball Speed Transfer", "Tip Offset and Spin", "Conservation of Momentum"], "Tome 0 — The Stance"),
    ("The Cut Shot", "Cue sports", "Beginner",
     "Pocketing a ball that is not straight in — where to send the cue ball, and where it goes afterwards.",
     "The object ball leaves along the line joining the two centres at contact, whatever you do; so aim the cue ball at the ghost-ball position, one ball's width from the object ball on the far side from the pocket. The cue ball leaves along the tangent line at right angles to that (the ninety-degree rule), carrying sin θ of the speed while the object ball takes cos θ. Friction between the balls throws the object ball a degree or two off the geometric line, more on slow shots and thin cuts — allow for it, or the long ones rattle. A rolling cue ball then curves forward off the tangent line to about 30° from where it was going; a stunned one keeps the tangent.",
     "A table, a cue, chalk; a spare ball to stand in for the ghost while learning; a straight edge or a laser to check the tangent line.",
     "Stand behind the object ball and sight the line from pocket through its centre; mark where the ghost ball must sit.\nAddress the cue ball with the cue on the line to the ghost ball's centre, not to the object ball.\nStroke through with stun (a touch below centre) at medium speed; watch the object ball's line and the cue ball's.\nRepeat at half-ball: the cue ball should leave at ninety degrees and the object ball with three-quarters of the pace.\nOn slow, thin cuts, aim a hair thinner than the geometry says — throw pushes the object ball toward the cue ball's line, so the shot plays fuller than aimed.\nWhen it drops ten times running, take the spare ball away and see the ghost without it.",
     "Nothing but pride. Chalk the tip before every shot so a miscue does not send the cue ball off the table.",
     "Aiming at the object ball's edge instead of the ghost ball's centre — always undercut. Forgetting throw on slow cuts — undercut again. Unintended side from a crooked stroke, which both squirts the cue ball and throws the object ball. Reading the cue ball's line as the aim line and scratching along the tangent.",
     "On a half-ball cut you can name, before you shoot, which cushion the cue ball will reach — and it does, ten times in a row.",
     ["Ninety-Degree Rule", "Ghost-Ball Aim", "Throw", "Thirty-Degree Rule", "Conservation of Momentum", "Vector Projection"], "Tome II — The Cut"),
    ("Follow, Draw and Stun", "Cue sports", "Intermediate",
     "Where the cue ball ends up: controlling it with the height of the tip on the ball.",
     "The tip's height above or below centre gives the ball spin — ⅖ mR² of moment of inertia means half a radius of offset spins it about as fast as it would roll — and the collision does not touch that spin: the object ball takes the line of centres, the cue ball takes the tangent line, and only then does the cloth's friction turn its topspin into forward curve (follow) or its backspin into a return (draw). A ball hit at centre skids first and rolls after losing two-sevenths of its speed; hit it just below centre so it is still sliding at contact and it stops dead on a straight shot — stun. Speed matters as much as height: the same draw stroke at twice the speed pulls back four times as far, because the skid distance goes as the square of it.",
     "A table and cue; chalk; a striped ball, so you can see whether it is skidding or rolling on the way to the object ball.",
     "Set a straight-in shot at a metre. Hit at centre, medium: the cue ball follows a little — it was rolling by contact.\nSame shot a tip below centre: it stops. That is stun; find the height and speed at which it stops dead.\nTwo tips below, firmer: it comes back. Note how far, then hit the same height harder and watch it come back further.\nA tip above centre: it follows through the object ball's place. Watch how it holds the tangent line first, then bends.\nNow at half-ball: stun keeps ninety degrees, follow bends to about thirty, draw pulls back to about ninety the other way.\nPlay position: pick a landing zone before each shot and stop when three in five land there.",
     "Keep the bridge hand still and the tip low only as far as the ball allows — a draw stroke that digs into the cloth tears it and can jump the ball.",
     "Decelerating through the ball, so the tip barely spins it. Cueing too low without enough speed: the ball is rolling before it arrives and follows instead of drawing. Judging draw by height alone and ignoring distance — spin dies over a long shot. Elevating the cue to reach below centre, which adds a curve you did not want.",
     "From a straight-in shot at a metre you can stop the cue ball dead, bring it back a hand's width, and back a metre, on demand.",
     ["Tip Offset and Spin", "Slide to Roll", "Thirty-Degree Rule", "Ninety-Degree Rule", "Torque", "Moment of Inertia", "Friction"], "Tome I — The Straight Line"),
    ("Using Side", "Cue sports", "Advanced",
     "English — side spin — and the four things it does at once, three of which you did not ask for.",
     "A tip left or right of centre spins the ball about a vertical axis. On the way to the object ball that spin does almost nothing to the cue ball's path — except squirt, a small deflection off the cue's line that is a property of the cue's front-end mass, and swerve, a curve back the other way from cloth friction if the cue is at all elevated. At the object ball it throws the object ball sideways by friction, up to a few degrees, the opposite way to the spin. At the cushion it adds to or subtracts from the along-rail speed: running side lengthens the rebound and keeps the ball alive, reverse shortens it and kills it. Players use side for the cushions and pay for it at the object ball; the skill is knowing the price.",
     "Table and cue; chalk; a cue whose squirt you know — most modern low-deflection shafts move the front mass back for exactly this reason.",
     "Straight-in shot, cue level, one tip of right: watch the cue ball squirt left and the object ball throw left — both small, both real.\nSame shot with the cue slightly elevated: swerve brings the cue ball back toward the line. Learn your cue's balance of the two at the speed you play.\nCue ball to a cushion, no object ball: strike with running side and see the angle open; with reverse, close.\nCombine: a cut where the cue ball must go three rails — pick side for the cushions, then correct the aim for the throw that side adds (inside) or cancels (a touch of outside).\nPlay the shot without side first, every time; add side only when the position needs it.",
     "Extreme side needs a chalked tip and a level cue; a miscue at speed sends the ball off the table.",
     "Using side out of habit on shots that need none. Correcting for squirt at one speed and playing at another. Forgetting throw and missing the object ball thick. Elevating the cue for reach and getting swerve you did not plan on. Judging the cushion by a table you played last week.",
     "You can pocket a medium cut with a tip of either side and land the cue ball in a called zone off two cushions — and can say beforehand which way the object ball will throw.",
     ["Tip Offset and Spin", "Throw", "Cushion Rebound", "Friction", "Ninety-Degree Rule"], "Tome IV — Side"),
    ("The Bank", "Cue sports", "Intermediate",
     "The object ball off a cushion into a pocket. The mirror is the first thing everyone is told; the rest is the corrections.",
     "Reflect the pocket through the rail and aim the object ball at the image: exact for a ball that loses nothing at the cushion, which no ball does. The rubber returns about 87 % of the speed that hit it square, less the harder it is hit — so a firm bank comes off shorter than the mirror says and a soft one nearly on it — and friction along the rail takes a bite of the speed running along it. Two things move the bank further: a cut into the rail gives the object ball a little side of its own, and throw from the cue ball shifts where it starts. Cross-side and cross-corner banks are the same geometry with a different image point; a long bank is the same geometry with more distance for the errors to grow in. The kiss — the cue ball still sitting on the object ball's return path — is the one thing the mirror cannot see, and the tangent line predicts it.",
     "A table, a cue, chalk; a straight edge laid along the rail to find the image point while learning; a second ball placed on the mirror line as a marker.",
     "Set a cross-side bank from the middle of the table, object ball a diamond off the rail. Find the image pocket by mirroring across the rail; aim the object ball there at a soft rolling pace and watch it drop.\nSame bank a notch firmer: it comes off short. Note by how much; that is the rail's speed correction, and it is a property of this table.\nMove the cue ball so the shot becomes a cut into the rail: the bank walks in the direction of the cut. Aim a touch fuller into the rail to compensate.\nNow a long bank down the table. Everything doubles — the speed error, the cut error — and pocket speed becomes the only speed that works.\nBefore each bank, draw the tangent line: if the cue ball is going to sit on the object ball's way back, move it with stun or follow first, or the balls kiss.\nRun the bank ladder: ten positions cross-side, up on a pot, down on a miss.",
     "Nothing new; a firm bank into a rail can send the object ball off the table if it is struck with the cue elevated — keep the cue level.",
     "Trusting the mirror at any speed. Playing banks firm because they feel safer, when the rail shortens every firm one. Ignoring the cut into the rail and wondering why the bank went long. Sitting the cue ball on the return line and taking the kiss. Aiming banks at the pocket instead of the image point — the eye wants to.",
     "From a cross-side bank in the middle of the table you can call which side of the pocket the object ball will favour at soft, medium and firm, and drop it at all three.",
     ["Cushion Rebound", "Coefficient of Restitution", "Throw", "Ninety-Degree Rule", "Friction", "Vector Projection"], "Tome V — Banks"),
    ("The Kick", "Cue sports", "Intermediate",
     "The cue ball off a cushion first. The diamond systems are a calculator bolted to the rails — and this is where the arithmetic drifts.",
     "A kick is a bank with the cue ball, so the same rail physics applies — the rebound goes short with pace, friction eats the along-rail speed — with one addition: the cue ball carries whatever side you gave it, and the rail converts that side into along-rail speed. Running side lengthens the rebound and keeps the ball alive; reverse shortens it and kills it. The one-rail and two-rail mirror systems are pure geometry, right at one gentle pace and drifting either side of it. Corner five, the three-rail system every carom player learns, is the opposite kind of thing — an empirical table calibrated for running side at a firm, even pace, so the english is part of the system, not a decoration. Zero the side and the numbers stop working; change the pace and they move.",
     "A table with diamonds you can read; a cue; chalk; a ball to leave on the target spot; the kicks tab of the billiards lab, which draws the system's line over the ball's real path.",
     "Place an object ball behind a blocker so there is no direct line. Mirror it through the nearest rail, aim the cue ball at the image, medium pace, no side: it arrives a little short. Note the correction.\nTwo rails: mirror twice. Same shot at three paces; watch the arrival walk along the rail as the rubber gives less back.\nCorner five: cue ball in the corner-five position, running side, firm and even, aimed at the diamond the system names for the arrival you want. Hit it; then take the side off and hit the same line, and watch the ball miss by a foot.\nKick to hit, then kick to leave the cue ball safe: the same line, a different pace, and the second is the one that wins games.\nHooked in a real layout — two balls between you and the one you owe — choose the system by which rail is clean, not by which you like.",
     "None beyond the usual; a kick struck hard with side and an elevated cue can leave the table.",
     "Playing a two-rail mirror at speed and blaming the rail. Corner five without running side. Forgetting that the object ball you kick at also has to go somewhere — a kick that hits and leaves the cue ball in the open is a foul waiting for the next shot. Reading a diamond system off the wrong reference — the diamonds mark the rail, the ball's path starts a ball's radius inside it.",
     "Hooked behind a ball with no direct line, you can name the rail, the system and the arrival diamond, and hit the target ball first at least four times in five.",
     ["Cushion Rebound", "Coefficient of Restitution", "Friction", "Tip Offset and Spin", "Vector Projection", "Trigonometric Ratios"], "Tome VI — Kicks"),
    ("Combinations and Caroms", "Cue sports", "Intermediate",
     "Shots that need a second ball — combinations, caroms, kisses and frozen pairs. Every ball on the table is live; this is how to use it.",
     "A combination is the ghost-ball aim applied twice, and the errors multiply: a degree wrong at the first ball is several centimetres at the second. Throw is the part the geometry misses. The first ball throws the second the way the cue ball throws the first — a slow combo goes thick, a chalky contact doubles it — and two balls frozen together are not the dead shot they look: the second leaves along the line of centres plus up to five degrees of throw in the direction the first ball's surface was moving. A carom is the cue ball off one ball into another, or into a pocket, and it is the tangent line and the thirty-degree rule with the cue ball as the projectile: stun keeps the ninety, roll bends it forward. A kiss is the same thing for an object ball — off another object ball, at ninety degrees to the line of centres, whatever else is happening.",
     "A table, a cue, chalk; three balls; a straight edge to lay along a frozen pair's line of centres so you can see how far throw moves the shot off it.",
     "Two balls a hand apart on a line to a pocket. Ghost-ball the first onto the second, then the cue ball onto the first; medium pace, stun. Move the first ball a little off the line and watch the miss grow.\nFreeze the pair, pointed a touch away from the pocket. Hit the first full and slow; the second throws toward the pocket. Hit it firm; it does not. Find the pace that pockets it.\nCarom: an object ball near a pocket, a second ball off to the side. Play the cue ball into the second ball with stun so it leaves along the tangent line into the first, and watch the tangent line be the whole aim.\nSame carom with a rolling cue ball: aim it thirty degrees inside the tangent and let the roll bend it there.\nKiss: two object balls, the cue ball on the first; send the first into the second so the second leaves at ninety degrees to their line of centres into a pocket.\nFrozen ball on the rail with the cue ball nearby: the rail-first and ball-first hits give two different lines. Learn both.",
     "Nothing new; a frozen pair struck hard can send the far ball off the table if the pair points at a rail nose.",
     "Aiming a combination at the pocket instead of at the first ball's ghost. Slow combos going thick because throw was forgotten. Calling a frozen pair dead and losing it by five degrees. Playing a carom off a rolling cue ball with the tangent line as the aim — it bends thirty degrees past. Forgetting that the second ball of a combination also has a tangent line, and scratching along it.",
     "Given two balls a hand apart on a line a few degrees off a pocket, you can say before shooting whether pace or throw makes it, and pocket it at the pace you named three times in five; and you can carom the cue ball off one ball into a pocket with stun and with roll, on demand.",
     ["Ghost-Ball Aim", "Throw", "Ninety-Degree Rule", "Thirty-Degree Rule", "Friction", "Conservation of Momentum"], "Tome VII — Other balls"),
    ("The Safety", "Cue sports", "Advanced",
     "The shots where the pocket is not the point: leaving the other player nothing, and planning the run so you never need to.",
     "A safety is cue-ball control with the object ball's destination secondary — the stop shot behind a blocker, the soft roll-up to a cluster, the kick that hits and dies. The physics is the whole rest of the shelf, played softer: the stun that holds the tangent line, the rolling resistance that decides where a slow ball stops, the cushion that kills speed on a reverse-side kick. Distance is the weapon — the further the two balls end from each other and the more of the table between them, the harder the return — and a two-way shot is a pot played so that the miss is a safety too. Pattern play is the same idea in the other direction: choose the order of the balls so each cue ball lands where the next shot is easy, use the key ball to get on the money ball, and keep the natural angles so the position needs no side. Ball in hand is the cheapest shot in the game, and the easiest to waste.",
     "A table, a cue, chalk; a full rack of nine, to play patterns and not single shots; a notebook, because the pattern you did not plan is the one that beat you.",
     "Set a blocker between two pockets and an object ball beyond it. Play the object ball to a rail and stop the cue ball dead behind the blocker with a stun at pot weight.\nRoll-up: object ball frozen to a cushion, cue ball a metre away. Roll it up to touching, or nearly, at the pace that leaves it there; find that pace on this cloth.\nKick safety: hooked, no direct line. Kick to hit with reverse side and a soft pace so the cue ball dies at the rail after contact.\nTwo-way: a long thin cut with the cue ball sent up-table so the miss leaves the object ball on a rail and the cue ball at the far end.\nRack nine, break, and before every shot say the next three: which ball, which side of it, which pocket. Play the run; when it dies, write down the shot that had no plan.\nBall in hand: place the cue ball for a straight-in stop shot that leaves the next two, and refuse anything fancier.",
     "None; soft shots are the safest in the game.",
     "Playing safe when the pot was on. Leaving distance but not a blocker, or a blocker but no distance. Rolling up too firm and leaving a shot. Planning one ball ahead and finding the second needs side and a rail. Taking ball in hand and reaching for the flashy shot. Forgetting that a safety is judged by the return you left, not by how good it looked.",
     "With a blocker on the table you can leave the opponent without a direct hit four times in five, at three distances; and you can rack nine balls, plan the pattern out loud, and finish it without a rail-and-side position shot.",
     ["Slide to Roll", "Rolling Resistance", "Cushion Rebound", "Ninety-Degree Rule", "Thirty-Degree Rule"], "Tome VIII — Safety and strategy"),
    ("The Break", "Cue sports", "Intermediate",
     "The only shot played at full speed, and the one where the physics stops being polite: the cue's speed, the rack's geometry, and where the cue ball should stop.",
     "The ball takes its speed from the cue by momentum: a 540 g cue on a 170 g ball can give the ball half again the cue's speed, less what the tip's restitution loses, so the break is about cue speed and a firm-enough grip, not muscle. Hit the head ball full and the energy goes down the line of centres into the rack; every degree off centre sends a share of it sideways and the cue ball with it. The rack is fifteen or nine balls each frozen to two others, and a frozen pair sends the far ball along the line of centres, so where each ball goes is geometry — the corner balls of a nine-ball rack go to the side pockets, the wing ball to the corner — and pattern racking is that geometry used on purpose. At break speed the rubber gives back barely half what it would at pot weight and the pockets narrow to a fraction of their mouth, which is why a break-speed ball rattles and a hard cue ball crosses the table six times.",
     "A table, a break cue if you have one (a hard tip and a stiff shaft), chalk; a rack or a template; the racks in the billiards lab's layout library, which integrate all sixteen balls.",
     "Rack nine. Cue ball on the head string a hand off centre; aim the head ball full, hit at centre or a touch above, three-quarter speed. Watch which balls went where; that is the rack's geometry, and it repeats.\nSame break at full speed. The cue ball should stop near the middle of the table: if it flies, the hit was off-centre or the tip too high.\nEight-ball: cue ball nearer the rail, aim the second ball of the rack full and firm, follow to bring the cue ball back to the centre.\nSoft break: pot weight plus a little, aimed to send the one ball to a side pocket and the wing ball to a corner, the cue ball dead. It works when the rack is tight and fails when it is not.\nCheck the rack before every break — a gap between the first and second rows sends the whole thing wrong.",
     "The one shot on this shelf that hurts: a break with an elevated cue jumps the cue ball off the table, and a miscue at full speed can split a tip. Level cue, chalk, and nothing behind the far rail you mind hitting.",
     "Hitting the head ball off centre and losing the cue ball. Swinging from the shoulder for power and losing the tip's line. Breaking hard from a loose rack. A tight grip that flies the cue ball because the effective mass jumped. Chasing speed when the soft break was the shot.",
     "From the head string you can break nine and leave the cue ball in the middle third of the table three times in five, with at least one ball down; and you can name, before breaking, which pocket the wing ball is going to.",
     ["Cue-to-Ball Speed Transfer", "Conservation of Momentum", "Coefficient of Restitution", "Kinetic Energy", "Ninety-Degree Rule", "Cushion Rebound"], "Tome IX — The Break"),
    ("Massé and Jump", "Cue sports", "Advanced",
     "The shots that leave the cloth or the level cue — massé, piqué, the jump — and the one tome the billiards lab does not integrate yet.",
     "Everything else on this shelf assumes the cue is level and the balls stay on the cloth; these shots break both. Elevate the cue and the spin axis tilts out of the vertical: the ball goes out along the aim while it slides, and cloth friction on the tilted spin drags it sideways, so it curves — a little at twenty degrees (swerve, the price of side on any elevated shot), a lot at sixty (massé), and straight back at ninety (piqué). Coriolis worked the curve out in 1835: it is the friction force on a sliding ball with a horizontal spin component, and it stops the moment the ball takes up natural roll, which is why massé paths are a curve then a straight line. The jump is the other break: hit down through the ball at thirty to forty-five degrees and the cloth and slate push back, the ball leaves the table on a short parabola, lands with whatever spin it kept, and the ball it clears had nothing to say about it. Neither shot is in the lab yet — it would need cue elevation as an input, the spin as a three-component vector, and a vertical velocity with a bounce off the slate; the roadmap is in data/billiards/tomes.md.",
     "A table you are allowed to do this on, and a cloth you are prepared to mark; a jump cue (short, light, a hard tip); chalk on every stroke; a coach or a video for the massé, because the stroke is learned by feel and unlearned by the same route.",
     "Swerve first: a straight shot at a metre with side, cue elevated twenty degrees. The ball curves; find how far, and whether squirt or swerve wins at your pace.\nSemi-massé: a ball a hand off your line, cue at forty degrees, side and a little low, a short firm stroke. The cue ball goes out, bends round the blocker, and comes back to the line.\nMassé: cue at sixty degrees and more, aim the tip at a point on the ball, stroke down through it and stop the cue dead — the cue does not follow through, the ball does. Start with a curve of a hand's width; the full circle is years away.\nJump: ball a diamond in front of a blocker, jump cue at forty degrees, hit dead centre of the ball's top-back, a short accelerating stroke through it. The ball hops; raise the elevation to hop higher and lose distance.\nEvery one of these ten times, then put the shots away — they are the answer to a hook you could not kick out of, not the first thing to reach for.",
     "The two shots on this shelf that damage things. A massé stroke drives the tip into the cloth and can tear it or split the tip; a jump can send the ball off the table and across the room; both are barred in many halls and on any table not yours. Level cue by default, and elevate only where you are welcome to.",
     "Following through on a massé and burying the tip in the cloth. Scooping a jump — hitting under the ball, which is a foul and lifts nothing. Reaching for the massé when a kick was on. Jumping full balls without a jump cue. Expecting the lab to draw any of it: it stays on the cloth, and says so.",
     "You can swerve a cue ball round a ball a hand off the line and hit the ball behind it three times in five; jump a full ball at a diamond's distance and land inside a hand's width of the aim line; and know, before you get down, that neither was the right shot.",
     ["Tip Offset and Spin", "Slide to Roll", "Friction", "Angular Momentum", "Torque", "Kinematic Equations", "Coefficient of Restitution"], "Tome X — Off the cloth"),
]


def union_relation(page, prop, ids):
    cur = {x["id"] for x in (page["properties"].get(prop, {}).get("relation") or [])}
    new = cur | set(ids)
    return {prop: {"relation": [{"id": x} for x in sorted(new)]}} if new != cur else {}


def main():
    print("equations")
    schema = ensure_props(EQ_DS, {}, "equations")
    ensure_select_options(EQ_DS, "Field", sorted({e[2] for e in EQUATIONS}), "equations")
    sync_rows(EQ_DS, schema,
              [{"Name": n, "Equation": eq, "Field": f, "Named After": na, "Symbols": sy, "Significance": sig, "Year": y}
               for n, eq, f, na, sy, sig, y in EQUATIONS], "equations")

    print("\nrequires")
    if "Requires" not in schema:
        sys.exit("no Requires relation on the Equations DB — run seed_foundations first")
    pages = {title_of(p, "Name"): p for p in query_all(EQ_DS) if title_of(p, "Name")}
    missing = set()
    changed = edges = 0
    for name, prereqs in REQUIRES.items():
        page = pages.get(name)
        if not page:
            missing.add(f"Requires:{name}")
            continue
        ids = [pages[q]["id"] for q in prereqs if q in pages]
        missing.update(f"Requires:{name} -> {q}" for q in prereqs if q not in pages)
        payload = union_relation(page, "Requires", ids)
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
        edges += len(ids)
    print(f"  equations: updated {changed} · {edges} requires-edges")

    print("\nskills")
    s_schema = ensure_props(SKILLS_DS, {"Tome": {"select": {}}}, "skills")
    ensure_select_options(SKILLS_DS, "Category", sorted({s[1] for s in SKILLS}), "skills")
    ensure_select_options(SKILLS_DS, "Tome", [s[11] for s in SKILLS], "skills")
    sync_rows(SKILLS_DS, s_schema,
              [{"Name": n, "Category": cat, "Difficulty": d, "Summary": su, "The Science": sci, "Tools": t,
                "Steps": st, "Safety": sa, "How It Fails": fa, "Done When": dn, "Tome": tome}
               for n, cat, d, su, sci, t, st, sa, fa, dn, _, tome in SKILLS], "skills")
    skills = {title_of(p, "Name"): p for p in query_all(SKILLS_DS) if title_of(p, "Name")}
    eq_ids = {n: p["id"] for n, p in pages.items()}
    changed = edges = 0
    for n, *_, eqn, _tome in SKILLS:
        page = skills.get(n)
        if not page:
            missing.add(f"skills:{n}")
            continue
        ids = [eq_ids[q] for q in eqn if q in eq_ids]
        missing.update(f"skills:{n} -> {q}" for q in eqn if q not in eq_ids)
        payload = union_relation(page, "Equations", ids)
        if payload:
            call("PATCH", f"https://api.notion.com/v1/pages/{page['id']}", {"properties": payload}); changed += 1
        edges += len(ids)
    print(f"  skills: updated {changed} · {edges} equation links")

    if missing:
        print("\nunresolved names ignored:")
        for m in sorted(missing):
            print("  ", m)
    print("\nnow run: python3 scripts/fetch_all.py && python3 scripts/build.py")


if __name__ == "__main__":
    main()
