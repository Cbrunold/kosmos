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
  SKILLS (3)     — The Cut Shot, Follow Draw and Stun, Using Side: tools, steps,
                   safety, how it fails, done when; each linked to its equations.
                   New Skills category: Cue sports.

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
# name, category, difficulty, summary, science, tools, steps, safety, fails, done, equations
SKILLS = [
    ("The Cut Shot", "Cue sports", "Beginner",
     "Pocketing a ball that is not straight in — where to send the cue ball, and where it goes afterwards.",
     "The object ball leaves along the line joining the two centres at contact, whatever you do; so aim the cue ball at the ghost-ball position, one ball's width from the object ball on the far side from the pocket. The cue ball leaves along the tangent line at right angles to that (the ninety-degree rule), carrying sin θ of the speed while the object ball takes cos θ. Friction between the balls throws the object ball a degree or two off the geometric line, more on slow shots and thin cuts — allow for it, or the long ones rattle. A rolling cue ball then curves forward off the tangent line to about 30° from where it was going; a stunned one keeps the tangent.",
     "A table, a cue, chalk; a spare ball to stand in for the ghost while learning; a straight edge or a laser to check the tangent line.",
     "Stand behind the object ball and sight the line from pocket through its centre; mark where the ghost ball must sit.\nAddress the cue ball with the cue on the line to the ghost ball's centre, not to the object ball.\nStroke through with stun (a touch below centre) at medium speed; watch the object ball's line and the cue ball's.\nRepeat at half-ball: the cue ball should leave at ninety degrees and the object ball with three-quarters of the pace.\nOn slow, thin cuts, aim a hair fuller than the geometry says — that is throw.\nWhen it drops ten times running, take the spare ball away and see the ghost without it.",
     "Nothing but pride. Chalk the tip before every shot so a miscue does not send the cue ball off the table.",
     "Aiming at the object ball's edge instead of the ghost ball's centre — always undercut. Forgetting throw on slow cuts — undercut again. Unintended side from a crooked stroke, which both squirts the cue ball and throws the object ball. Reading the cue ball's line as the aim line and scratching along the tangent.",
     "On a half-ball cut you can name, before you shoot, which cushion the cue ball will reach — and it does, ten times in a row.",
     ["Ninety-Degree Rule", "Ghost-Ball Aim", "Throw", "Thirty-Degree Rule", "Conservation of Momentum", "Vector Projection"]),
    ("Follow, Draw and Stun", "Cue sports", "Intermediate",
     "Where the cue ball ends up: controlling it with the height of the tip on the ball.",
     "The tip's height above or below centre gives the ball spin — ⅖ mR² of moment of inertia means half a radius of offset spins it about as fast as it would roll — and the collision does not touch that spin: the object ball takes the line of centres, the cue ball takes the tangent line, and only then does the cloth's friction turn its topspin into forward curve (follow) or its backspin into a return (draw). A ball hit at centre skids first and rolls after losing two-sevenths of its speed; hit it just below centre so it is still sliding at contact and it stops dead on a straight shot — stun. Speed matters as much as height: the same draw stroke at twice the speed pulls back four times as far, because the skid distance goes as the square of it.",
     "A table and cue; chalk; a striped ball, so you can see whether it is skidding or rolling on the way to the object ball.",
     "Set a straight-in shot at a metre. Hit at centre, medium: the cue ball follows a little — it was rolling by contact.\nSame shot a tip below centre: it stops. That is stun; find the height and speed at which it stops dead.\nTwo tips below, firmer: it comes back. Note how far, then hit the same height harder and watch it come back further.\nA tip above centre: it follows through the object ball's place. Watch how it holds the tangent line first, then bends.\nNow at half-ball: stun keeps ninety degrees, follow bends to about thirty, draw pulls back to about ninety the other way.\nPlay position: pick a landing zone before each shot and stop when three in five land there.",
     "Keep the bridge hand still and the tip low only as far as the ball allows — a draw stroke that digs into the cloth tears it and can jump the ball.",
     "Decelerating through the ball, so the tip barely spins it. Cueing too low without enough speed: the ball is rolling before it arrives and follows instead of drawing. Judging draw by height alone and ignoring distance — spin dies over a long shot. Elevating the cue to reach below centre, which adds a curve you did not want.",
     "From a straight-in shot at a metre you can stop the cue ball dead, bring it back a hand's width, and back a metre, on demand.",
     ["Tip Offset and Spin", "Slide to Roll", "Thirty-Degree Rule", "Ninety-Degree Rule", "Torque", "Moment of Inertia", "Friction"]),
    ("Using Side", "Cue sports", "Advanced",
     "English — side spin — and the four things it does at once, three of which you did not ask for.",
     "A tip left or right of centre spins the ball about a vertical axis. On the way to the object ball that spin does almost nothing to the cue ball's path — except squirt, a small deflection off the cue's line that is a property of the cue's front-end mass, and swerve, a curve back the other way from cloth friction if the cue is at all elevated. At the object ball it throws the object ball sideways by friction, up to a few degrees, the opposite way to the spin. At the cushion it adds to or subtracts from the along-rail speed: running side lengthens the rebound and keeps the ball alive, reverse shortens it and kills it. Players use side for the cushions and pay for it at the object ball; the skill is knowing the price.",
     "Table and cue; chalk; a cue whose squirt you know — most modern low-deflection shafts move the front mass back for exactly this reason.",
     "Straight-in shot, cue level, one tip of right: watch the cue ball squirt left and the object ball throw left — both small, both real.\nSame shot with the cue slightly elevated: swerve brings the cue ball back toward the line. Learn your cue's balance of the two at the speed you play.\nCue ball to a cushion, no object ball: strike with running side and see the angle open; with reverse, close.\nCombine: a cut where the cue ball must go three rails — pick side for the cushions, then aim a touch thicker for the throw.\nPlay the shot without side first, every time; add side only when the position needs it.",
     "Extreme side needs a chalked tip and a level cue; a miscue at speed sends the ball off the table.",
     "Using side out of habit on shots that need none. Correcting for squirt at one speed and playing at another. Forgetting throw and missing the object ball thick. Elevating the cue for reach and getting swerve you did not plan on. Judging the cushion by a table you played last week.",
     "You can pocket a medium cut with a tip of either side and land the cue ball in a called zone off two cushions — and can say beforehand which way the object ball will throw.",
     ["Tip Offset and Spin", "Throw", "Cushion Rebound", "Friction", "Ninety-Degree Rule"]),
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
    s_schema = ensure_props(SKILLS_DS, {}, "skills")
    ensure_select_options(SKILLS_DS, "Category", sorted({s[1] for s in SKILLS}), "skills")
    sync_rows(SKILLS_DS, s_schema,
              [{"Name": n, "Category": cat, "Difficulty": d, "Summary": su, "The Science": sci, "Tools": t,
                "Steps": st, "Safety": sa, "How It Fails": fa, "Done When": dn}
               for n, cat, d, su, sci, t, st, sa, fa, dn, _ in SKILLS], "skills")
    skills = {title_of(p, "Name"): p for p in query_all(SKILLS_DS) if title_of(p, "Name")}
    eq_ids = {n: p["id"] for n, p in pages.items()}
    changed = edges = 0
    for n, *_, eqn in SKILLS:
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
