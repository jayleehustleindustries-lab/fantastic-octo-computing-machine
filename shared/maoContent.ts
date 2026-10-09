/**
 * Site copy shared by the page and the "Ask Jay" assistant's knowledge, so the
 * two can't drift apart. Prices are deliberately absent: they are revealed
 * only after an application is qualified.
 */

export const SERVICES = [
  { code: "S/01", title: "FITNESS PLANS", desc: "Programmed 12-week body recomposition blocks. Progressive overload, conditioning, mobility, nutrition guardrails — engineered around your life.", features: ["CUSTOM SPLIT + LIFT PROGRESSIONS","WEEKLY CHECK-INS & AUDITS","NUTRITION GUARDRAILS"] },
  { code: "S/02", title: "PERSONAL TRAINING", desc: "1:1 sessions and remote coaching with the JayLee Hustle Industries standard — every rep logged, every session reviewed.", features: ["LIVE OR REMOTE SESSIONS","FORM AUDITS + VIDEO REVIEW","ACCOUNTABILITY LOOP"] },
  { code: "S/03", title: "HUSTLE COACHING", desc: "Mindset, discipline, and operating systems for athletes, founders, and grinders. Train the body, sharpen the operator.", features: ["DAILY OPS + DISCIPLINE FRAMEWORK","QUARTERLY OBJECTIVE SETTING","MENTAL CONDITIONING"] },
];

export const TIERS = [
  {
    code: "INV/01", title: "FOUNDATION", badge: null, priceKey: "FOUNDATION_PRICE",
    desc: "Entry tier for committed operators. Weekly programming restructures + monthly Zoom call with Coach Jay. Custom 12-week recomposition block with ongoing adjustments.",
    features: ["Custom 12-week recomposition block","Weekly programming restructures","Monthly Zoom call with Coach Jay","Nutrition guardrails + macro plan","Scheduled messaging Mon–Fri","Program review after week 4 + 8"],
    cta: "APPLY FOR FOUNDATION"
  },
  {
    code: "INV/02", title: "RECOMP", badge: "FLAGSHIP", priceKey: "RECOMP_PRICE",
    desc: "The flagship transformation. Weekly programming restructures + weekly Zoom calls with Coach Jay. Full body recomposition, form audits, direct line to Coach Jay. Built for the prospect who is done starting over.",
    features: ["Everything in FOUNDATION","Weekly programming restructures","Weekly Zoom call with Coach Jay","Weekly 1:1 form audit","Custom recovery + sleep protocol","Direct messaging with an agreed response window","Full body recomposition focus"],
    cta: "APPLY FOR RECOMP"
  },
  {
    code: "INV/03", title: "LEGACY", badge: null, priceKey: "LEGACY_PRICE",
    desc: "Premium tier for high-performing operators. Twice-weekly programming restructures + Zoom calls. Full body recomposition, intensive coaching, direct line to Coach Jay. By application only.",
    features: ["Everything in RECOMP","Twice-weekly programming restructures","Twice-weekly Zoom calls with Coach Jay","Intensive form audits + video review","Priority messaging during agreed support hours","Custom recovery + sleep protocol","Direct text access with boundaries confirmed before start"],
    cta: "APPLY FOR LEGACY"
  },
];

/** Remap: the one product visitors can buy without applying. Price comes from the server (REMAP_PRICE_CENTS). */
export const REMAP = {
  name: "REMAP",
  tagline: "Your program, your numbers. Built the day you buy it.",
  desc: "A personal training program built around your body, schedule and equipment, plus the exact calorie and macro targets to go with it. Self-guided: no application, no waiting.",
  features: [
    "Custom program: 8–12 weeks for beginners, 6–8 intermediate, up to 6 advanced",
    "Phase-by-phase training with sets, reps, rest and effort targets",
    "Your BMR and daily burn (activity multiplier included)",
    "Daily calorie target + protein, carb and fat grams",
    "How to eat to hit them, and how to adjust as you go",
    "Progression, deload and weekly check-in rules",
  ],
};

export const TERMS = [
  { code: "G/00", term: "FOUNDER — MEET COACH JAY", def: "Founder of JayLee Hustle Industries. Author of the MAO Framework. Coach to the Operators on this platform — every protocol on this site comes from his system, not a textbook. Coach Jay built the MAO Framework in the field — not in a classroom. Every Operator on the roster is coached against the same standard he holds himself to. Adaptation is the game." },
  { code: "G/01", term: "OPERATOR", def: "A high-output founder, executive, or career professional whose physical conditioning is the lever that compounds every other system in their life. We do not coach hobbyists. We coach Operators." },
  { code: "G/02", term: "MAO (MASSIVE ACTION ORIENTATION)", def: "The proprietary JayLee framework: a triad of physical conditioning, neural optimization, and strict accountability. Every protocol is engineered to compound across all three planes simultaneously — not in isolation." },
  { code: "G/03", term: "SWARM ECOSYSTEM", def: "The MAO operating model that connects programming, check-ins, communication, and evidence review around each Operator. Automation is introduced only where the supporting systems are configured and supervised." },
];

export const COACH = {
  name: "Jordan Lee (\"Coach Jay\")",
  base: "Hot Springs, Arkansas",
  company: "JayLee Fit, part of JayLee Hustle Industries LLC",
  bio: [
    "Jordan Lee — \"Coach Jay\" — is the founder of JayLee Fit (JayLee Hustle Industries LLC), based in Hot Springs, Arkansas. He built his coaching approach on one belief: sustainable progress comes from realistic systems, not extreme programs that fall apart in week two. MAO is his operating framework for consistent training and accountability.",
    "Jordan coaches founders, athletes, and busy dads specifically because he understands the life — the early mornings, the packed schedules, the guilt of putting yourself last. His approach strips away the noise and builds programs that actually fit your week, your equipment, and your energy. Home-based training. No gym required. Real accountability.",
  ],
  blocks: [
    { label: "SPECIALIZATIONS", items: ["Athletic performance","Fat loss","Functional strength","Metabolic efficiency","GLP-1 adaptation","Wearable data integration","12-week specialization programs"] },
    { label: "COACHING APPROACH", items: ["Progressive programming","Nutrition guardrails","Human review","Habit accountability","Plans built around real schedules"] },
    { label: "MISSION", items: ["Build disciplined, capable bodies and operators through programmed recomposition and a relentless accountability loop."] },
    { label: "METHOD", items: ["Hustle First","Recomp over Vanity","Consistency over Intensity","Accountability Loop","Repeat for 12 weeks"] },
  ],
};

export const APPLICATION_STEPS = [
  "Phase 1 — Identity: name, email, phone (optional), location/timezone.",
  "Phase 2 — Mission profile: goal, training frequency, training history, current stats.",
  "Phase 3 — Logistics & commitment: hours per week, equipment, biggest obstacle, willingness to log.",
  "Phase 4 — Readiness: why now, start window, and two acknowledgments.",
  "Coach Jay reviews every completed application personally and sends next steps to qualified applicants. Package pricing is shown once all four phases are complete.",
];

// ── Training split data ──────────────────────────────────────────────────────
export const TRAINING_SPLIT = [
  {
    day: "MON", label: "UPPER BODY — PUSH", muscles: "Chest, Shoulders, Triceps", count: 8,
    lifts: [
      { exercise: "Barbell Bench Press", sets: 4, reps: "6–8", rest: "2 min", note: "Primary strength movement — control the descent, 2 sec down" },
      { exercise: "Incline Dumbbell Press", sets: 4, reps: "10–12", rest: "90s", note: "Feel the upper chest stretch at the bottom of every rep" },
      { exercise: "Cable Chest Fly", sets: 3, reps: "12–15", rest: "60s", note: "Full stretch and squeeze — don't rush these" },
      { exercise: "Overhead Dumbbell Press", sets: 4, reps: "10–12", rest: "90s", note: "Keep core braced, don't arch the lower back" },
      { exercise: "Cable Lateral Raises", sets: 4, reps: "15–20", rest: "45s", note: "Light weight, full range — these build width" },
      { exercise: "Rear Delt Cable Fly", sets: 3, reps: "15", rest: "45s", note: "Elbows slightly bent, lead with the elbows" },
      { exercise: "Tricep Rope Pushdowns", sets: 4, reps: "12–15", rest: "60s", note: "Squeeze hard at the bottom, full extension" },
      { exercise: "Overhead Tricep Extension", sets: 3, reps: "12", rest: "60s", note: "Long head emphasis — keep elbows tight" },
    ]
  },
  {
    day: "TUE", label: "LOWER BODY — SQUAT", muscles: "Quads, Glutes, Hamstrings", count: 7,
    lifts: [
      { exercise: "Barbell Back Squat", sets: 4, reps: "5–6", rest: "2.5 min", note: "Top strength slot of the week — brace hard, hit depth, drive through mid-foot" },
      { exercise: "Romanian Deadlift", sets: 4, reps: "8–10", rest: "2 min", note: "Push the hips back, bar stays on the thighs — feel the hamstrings load" },
      { exercise: "Walking Lunges", sets: 3, reps: "12/leg", rest: "90s", note: "Long strides, torso tall — control the knee, no wobble" },
      { exercise: "Leg Press", sets: 3, reps: "12–15", rest: "90s", note: "Full range without the lower back rolling off the pad" },
      { exercise: "Seated Leg Curl", sets: 3, reps: "12–15", rest: "60s", note: "Squeeze a full second at the bottom of every rep" },
      { exercise: "Standing Calf Raise", sets: 4, reps: "15–20", rest: "45s", note: "Pause at the stretch, explode up — no bouncing" },
      { exercise: "Hanging Knee Raise", sets: 3, reps: "12–15", rest: "60s", note: "Slow and controlled — no swinging, exhale at the top" },
    ]
  },
  {
    day: "WED", label: "UPPER BODY — PULL", muscles: "Back, Rear Delts, Biceps", count: 7,
    lifts: [
      { exercise: "Weighted Pull-Ups", sets: 4, reps: "6–8", rest: "2 min", note: "Dead hang to chest-to-bar intent — add load only when all reps are clean" },
      { exercise: "Barbell Row", sets: 4, reps: "8–10", rest: "2 min", note: "Hinge at 45 degrees, pull to the lower ribs — no torso heave" },
      { exercise: "Lat Pulldown", sets: 3, reps: "10–12", rest: "90s", note: "Drive the elbows down, chest up — let the lats do the work" },
      { exercise: "Chest-Supported Row", sets: 3, reps: "12", rest: "90s", note: "Chest glued to the pad kills the momentum — strict reps only" },
      { exercise: "Face Pulls", sets: 3, reps: "15–20", rest: "45s", note: "Rope to the forehead, thumbs back — this is shoulder insurance" },
      { exercise: "Barbell Curl", sets: 3, reps: "10–12", rest: "60s", note: "Elbows pinned to your sides — no swinging the weight up" },
      { exercise: "Hammer Curl", sets: 3, reps: "12", rest: "60s", note: "Neutral grip, slow negative — builds the forearm and brachialis" },
    ]
  },
  {
    day: "THU", label: "CONDITIONING + CORE", muscles: "Engine, Trunk", count: 6,
    lifts: [
      { exercise: "Rower or Bike Intervals", sets: 6, reps: "60s hard / 90s easy", rest: "—", note: "Hard means hard — the last two intervals should be a negotiation" },
      { exercise: "Kettlebell Swings", sets: 4, reps: "20", rest: "60s", note: "Snap the hips, arms are just hooks — power comes from the hinge" },
      { exercise: "Farmer's Carry", sets: 4, reps: "40m", rest: "90s", note: "Heavy. Shoulders packed, walk tall — grip and trunk under load" },
      { exercise: "Plank", sets: 3, reps: "60s", rest: "45s", note: "Squeeze glutes and abs — a plank is a full-body contraction, not a rest" },
      { exercise: "Pallof Press", sets: 3, reps: "12/side", rest: "45s", note: "Resist the rotation — slow press out, slow return" },
      { exercise: "Ab Wheel Rollout", sets: 3, reps: "8–12", rest: "60s", note: "Only roll as far as you can keep the lower back flat" },
    ]
  },
  {
    day: "FRI", label: "LOWER BODY — HINGE", muscles: "Posterior Chain, Glutes", count: 7,
    lifts: [
      { exercise: "Trap Bar Deadlift", sets: 4, reps: "5–6", rest: "2.5 min", note: "Second strength slot — wedge in tight, push the floor away" },
      { exercise: "Front Squat", sets: 3, reps: "8", rest: "2 min", note: "Elbows high, torso vertical — quads and upper back earn their pay" },
      { exercise: "Hip Thrust", sets: 4, reps: "10–12", rest: "90s", note: "Full lockout with a one-second squeeze — chin tucked, ribs down" },
      { exercise: "Bulgarian Split Squat", sets: 3, reps: "10/leg", rest: "90s", note: "The one everybody skips — that's exactly why we do it" },
      { exercise: "Back Extension", sets: 3, reps: "12–15", rest: "60s", note: "Squeeze glutes at the top, don't hyperextend the spine" },
      { exercise: "Seated Calf Raise", sets: 4, reps: "15–20", rest: "45s", note: "Different angle than Tuesday — pause every rep at the stretch" },
      { exercise: "Weighted Decline Sit-Up", sets: 3, reps: "12–15", rest: "60s", note: "Control down, drive up — add load before adding reps" },
    ]
  },
  {
    day: "SAT", label: "FULL BODY — OPERATOR CIRCUIT", muscles: "Total Body, Engine", count: 5,
    lifts: [
      { exercise: "Dumbbell Thrusters", sets: 5, reps: "12", rest: "Circuit", note: "Squat to press in one motion — breathe at the top, keep moving" },
      { exercise: "Renegade Rows", sets: 5, reps: "8/side", rest: "Circuit", note: "Hips square to the floor — the anti-rotation is the exercise" },
      { exercise: "Push-Ups", sets: 5, reps: "15–20", rest: "Circuit", note: "Chest to the floor, full lockout — no half reps in the circuit" },
      { exercise: "Goblet Reverse Lunge", sets: 5, reps: "10/leg", rest: "Circuit", note: "Bell tight to the chest, knee kisses the floor — stay tall" },
      { exercise: "Sled Push or Hill Sprint", sets: 5, reps: "20m / 15s", rest: "2 min between rounds", note: "Finish the round with intent — this is where the week is won" },
    ]
  },
  {
    day: "SUN", label: "ACTIVE RECOVERY — RESET", muscles: "Recovery, Mobility", count: 5,
    lifts: [
      { exercise: "Zone 2 Walk (outdoor)", sets: 1, reps: "45–60 min", rest: "—", note: "Conversational pace, phone on do-not-disturb — this is thinking time" },
      { exercise: "Couch Stretch", sets: 2, reps: "90s/side", rest: "—", note: "Hip flexors take the beating all week — pay them back here" },
      { exercise: "90/90 Hip Switches", sets: 2, reps: "10/side", rest: "—", note: "Smooth transitions, no hands if you can — own the position" },
      { exercise: "Thoracic Openers", sets: 2, reps: "10/side", rest: "—", note: "Desk posture dies here — exhale into every rotation" },
      { exercise: "Box Breathing", sets: 1, reps: "5 min", rest: "—", note: "4s in, 4s hold, 4s out, 4s hold — recovery is a skill, train it" },
    ]
  },
];
