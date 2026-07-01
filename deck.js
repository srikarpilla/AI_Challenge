const pptxgen = require("pptxgenjs");

// ── Palette: Midnight Executive ──────────────────────────────────────────────
const NAVY   = "1E2761";
const ICE    = "CADCFC";
const WHITE  = "FFFFFF";
const ACCENT = "5C6FF0";
const TEAL   = "4ECDC4";
const WARN   = "F5A623";
const MUTED  = "8892A4";
const DARK   = "0F1117";
const CARD   = "22263A";

const makeShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 45, opacity: 0.18 });

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author  = "RedrRob AI Ranker";
pres.title   = "India Runs Data & AI Challenge — Candidate Ranking System";

// ── Helpers ──────────────────────────────────────────────────────────────────
function darkSlide(slide) { slide.background = { color: DARK }; }

function addTitle(slide, text, opts={}) {
  slide.addText(text, {
    x: 0.55, y: 0.28, w: 8.9, h: 0.65,
    fontSize: 36, bold: true, fontFace: "Cambria",
    color: WHITE, margin: 0, ...opts
  });
}

function addSubtitle(slide, text, opts={}) {
  slide.addText(text, {
    x: 0.55, y: 0.95, w: 8.9, h: 0.4,
    fontSize: 16, fontFace: "Calibri",
    color: ICE, margin: 0, ...opts
  });
}

function statCard(slide, x, y, w, h, val, label, color=ACCENT) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.12,
    fill: { color: CARD }, shadow: makeShadow()
  });
  slide.addText(val, { x, y: y+0.12, w, h: h*0.55,
    fontSize: 30, bold: true, fontFace: "Cambria",
    color: color, align: "center", margin: 0 });
  slide.addText(label, { x, y: y+h*0.55, w, h: h*0.38,
    fontSize: 11, fontFace: "Calibri",
    color: MUTED, align: "center", margin: 0 });
}

function hBar(slide, x, y, w, pct, color=ACCENT) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.09, fill: { color: "2A2E42" } });
  if (pct > 0)
    slide.addShape(pres.shapes.RECTANGLE, { x, y, w: w * pct, h: 0.09, fill: { color: color } });
}

// ── SLIDE 1: Title ────────────────────────────────────────────────────────────
{
  let s = pres.addSlide();
  s.background = { color: NAVY };

  // Big circle accent
  s.addShape(pres.shapes.OVAL, {
    x: 6.8, y: -1.2, w: 5.5, h: 5.5,
    fill: { color: ACCENT, transparency: 82 },
    line: { color: ACCENT, width: 0 }
  });
  s.addShape(pres.shapes.OVAL, {
    x: 7.8, y: 0.2, w: 3.5, h: 3.5,
    fill: { color: TEAL, transparency: 88 },
    line: { color: TEAL, width: 0 }
  });

  s.addText("RedrRob AI", {
    x: 0.55, y: 1.1, w: 7, h: 0.8,
    fontSize: 52, bold: true, fontFace: "Cambria",
    color: WHITE, margin: 0
  });
  s.addText("Candidate Ranker", {
    x: 0.55, y: 1.9, w: 7, h: 0.8,
    fontSize: 52, bold: true, fontFace: "Cambria",
    color: ICE, margin: 0
  });
  s.addText("India Runs Data & AI Challenge  ·  Submission", {
    x: 0.55, y: 2.85, w: 7, h: 0.4,
    fontSize: 15, fontFace: "Calibri",
    color: ICE, margin: 0
  });
  s.addText("Ranking 100,000 candidates for an applied ML Search-Ranking role\nthe way a great recruiter would — not by keywords, but by understanding.", {
    x: 0.55, y: 3.4, w: 6.8, h: 0.9,
    fontSize: 14, fontFace: "Calibri",
    color: ICE, margin: 0
  });

  s.addNotes("Opening slide. Key message: this isn't keyword matching, it's semantic role fit assessment.");
}

// ── SLIDE 2: The Problem ──────────────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "The Problem with Keyword Ranking");
  addSubtitle(s, "Why existing ATS filters fail — and what this system does differently");

  const traps = [
    ["🚫", "Keyword Stuffers",     "Non-ML candidates with RAG/FAISS/PyTorch in skills — but a HR Manager career history"],
    ["🚫", "Hype Adopters",        "Recently added LangChain/ChatGPT, but zero retrieval depth pre-2023"],
    ["🚫", "Consulting Lifers",    "10+ years at TCS/Infosys/Wipro, no product ML exposure"],
    ["🚫", "Narrow Specialists",   "Strong Computer Vision or Speech — but no NLP/IR overlap for this role"],
    ["🚫", "Honeypot Profiles",    "Structurally impossible: 'expert' skill with 0 months, career date mismatches"],
  ];

  traps.forEach(([icon, title, desc], i) => {
    const x = 0.5 + (i % 2) * 4.75;
    const y = 1.4 + Math.floor(i / 2) * 1.25;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 4.5, h: 1.1, rectRadius: 0.1,
      fill: { color: CARD }, shadow: makeShadow()
    });
    s.addText(icon + "  " + title, { x: x+0.18, y: y+0.08, w: 4.1, h: 0.35,
      fontSize: 13, bold: true, fontFace: "Calibri", color: WARN, margin: 0 });
    s.addText(desc, { x: x+0.18, y: y+0.44, w: 4.1, h: 0.55,
      fontSize: 10.5, fontFace: "Calibri", color: ICE, margin: 0 });
  });

  // 5th item centered
  {
    const [icon, title, desc] = traps[4];
    const x = 2.75, y = 3.9;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: 4.5, h: 1.1, rectRadius: 0.1,
      fill: { color: CARD }, shadow: makeShadow()
    });
    s.addText(icon + "  " + title, { x: x+0.18, y: y+0.08, w: 4.1, h: 0.35,
      fontSize: 13, bold: true, fontFace: "Calibri", color: WARN, margin: 0 });
    s.addText(desc, { x: x+0.18, y: y+0.44, w: 4.1, h: 0.55,
      fontSize: 10.5, fontFace: "Calibri", color: ICE, margin: 0 });
  }
  s.addNotes("These 5 failure modes are all present in the 100k candidate dataset. Keyword matching promotes every one of them. Our system avoids all of them.");
}

// ── SLIDE 3: Architecture ─────────────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "System Architecture");
  addSubtitle(s, "4-stage pipeline: ~30 seconds on CPU, no GPU or network required");

  const stages = [
    { num: "01", label: "Honeypot\nElimination", desc: "Structural\nconsistency checks",   color: WARN   },
    { num: "02", label: "Feature\nExtraction",   desc: "7 signal groups,\nno external APIs", color: ACCENT },
    { num: "03", label: "Composite\nScoring",    desc: "Weighted score\n+ disqualifiers",    color: TEAL   },
    { num: "04", label: "Ranked\nOutput",        desc: "Top 100 CSV\n+ reasoning column",   color: "3DCC91"},
  ];

  // Arrow flow
  const stageW = 2.0, gap = 0.35, startX = 0.5, y = 1.55;
  stages.forEach((st, i) => {
    const x = startX + i * (stageW + gap);
    // Stage box
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x, y, w: stageW, h: 2.3, rectRadius: 0.14,
      fill: { color: CARD }, shadow: makeShadow()
    });
    // Number badge
    s.addShape(pres.shapes.OVAL, {
      x: x + stageW/2 - 0.3, y: y + 0.12, w: 0.6, h: 0.6,
      fill: { color: st.color }
    });
    s.addText(st.num, { x: x + stageW/2 - 0.3, y: y+0.14, w: 0.6, h: 0.56,
      fontSize: 13, bold: true, fontFace: "Calibri", color: DARK, align: "center", margin: 0 });
    s.addText(st.label, { x: x+0.1, y: y+0.82, w: stageW-0.2, h: 0.75,
      fontSize: 13, bold: true, fontFace: "Calibri", color: WHITE, align: "center", margin: 0 });
    s.addText(st.desc, { x: x+0.1, y: y+1.57, w: stageW-0.2, h: 0.65,
      fontSize: 10, fontFace: "Calibri", color: MUTED, align: "center", margin: 0 });
    // Arrow
    if (i < stages.length-1) {
      s.addShape(pres.shapes.LINE, {
        x: x+stageW+0.03, y: y+1.15, w: gap-0.06, h: 0,
        line: { color: MUTED, width: 1.5, dashType: "solid" }
      });
      s.addText("▶", { x: x+stageW+gap-0.2, y: y+0.97, w: 0.22, h: 0.36,
        fontSize: 10, color: MUTED, margin: 0 });
    }
  });

  // Pipeline stats row
  s.addText("100,000 candidates → 2,929 honeypots removed → 97,071 scored → Top 100 output   |   Runtime: ~30s", {
    x: 0.5, y: 4.8, w: 9, h: 0.4,
    fontSize: 11, fontFace: "Calibri", color: MUTED, align: "center", margin: 0
  });

  s.addNotes("The pipeline runs entirely offline: no API calls, no GPU, no Python ML dependencies beyond standard library. The JD config is fully externalised so changing the role takes minutes.");
}

// ── SLIDE 4: Honeypot Detection ───────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "Stage 1 — Honeypot Elimination");
  addSubtitle(s, "2,929 structurally impossible profiles removed before any scoring");

  const checks = [
    ["Expert proficiency + ≤2 months",        "Profile stuffing — can't be expert-level with 2 months of use"],
    ["≥8 skills claimed at 'expert'",          "Keyword stuffing — real engineers are expert in 1-3 areas"],
    ["Career duration vs. start/end dates",    "Fabricated duration_months that contradicts actual calendar dates"],
    ["YOE vs. sum of career history",          "8 years claimed but only 14 months of actual history"],
    ["Multiple is_current jobs",               "Structurally impossible — can't hold two roles simultaneously"],
    ["Education end before start",             "Date reversal — end_year < start_year"],
    ["Skill duration > total YOE",             "Used a skill for longer than the candidate has worked at all"],
  ];

  checks.forEach(([rule, detail], i) => {
    const row = i;
    const y = 1.35 + row * 0.56;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y, w: 9.1, h: 0.48, rectRadius: 0.07,
      fill: { color: CARD }, shadow: makeShadow()
    });
    s.addText("✗", { x: 0.55, y: y+0.05, w: 0.38, h: 0.38,
      fontSize: 14, bold: true, fontFace: "Calibri", color: WARN, margin: 0 });
    s.addText(rule, { x: 1.0, y: y+0.06, w: 3.3, h: 0.36,
      fontSize: 11.5, bold: true, fontFace: "Calibri", color: WHITE, margin: 0 });
    s.addText(detail, { x: 4.4, y: y+0.06, w: 5.0, h: 0.36,
      fontSize: 10.5, fontFace: "Calibri", color: MUTED, margin: 0 });
  });

  s.addText("Result: 0 honeypots in the final Top 100 shortlist", {
    x: 0.45, y: 5.1, w: 9.1, h: 0.35,
    fontSize: 12, bold: true, fontFace: "Calibri",
    color: TEAL, align: "center", margin: 0
  });

  s.addNotes("Design principle: honeypots are eliminated before scoring, not scored low. This guarantees a 0% honeypot rate in the output regardless of how many are in the pool.");
}

// ── SLIDE 5: Feature Engineering ─────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "Stage 2 — Feature Engineering");
  addSubtitle(s, "7 signal groups, all derived from structured data — no LLM calls during ranking");

  const features = [
    { w: 0.32, label: "Title Role\nFit",       color: ACCENT,  desc: "Recency & category weighted ML career years" },
    { w: 0.23, label: "Must-Have\nSkills",      color: TEAL,    desc: "Retrieval · Vector DB · Eval · Python" },
    { w: 0.16, label: "Availability\nSignals",  color: WARN,    desc: "Last active · response rate · notices" },
    { w: 0.09, label: "Location\nFit",          color: "3DCC91",desc: "Pune/Noida=1.0 · Tier-2=0.8 · Intl=0.15" },
    { w: 0.08, label: "Experience\nBand",       color: "A78BFA",desc: "Soft curve, 5–9yr target" },
    { w: 0.07, label: "Nice-to-\nHave",         color: "FB923C",desc: "Fine-tuning · GitHub · HR-tech" },
    { w: 0.05, label: "Notice\nPeriod",         color: "F472B6",desc: "≤30d=1.0 · ≤60d=0.65 · >90d=0.20" },
  ];

  // Weight bar chart
  const barX = 0.5, barStartY = 1.5, barH = 0.48, barMaxW = 8.5, gap = 0.14;
  features.forEach((f, i) => {
    const y = barStartY + i * (barH + gap);
    s.addText(f.label.replace("\n"," "), {
      x: barX, y: y+0.06, w: 2.0, h: barH-0.12,
      fontSize: 11, bold: true, fontFace: "Calibri", color: WHITE, margin: 0
    });
    // bar bg
    s.addShape(pres.shapes.RECTANGLE, {
      x: barX+2.1, y: y+0.16, w: barMaxW*0.68, h: 0.18,
      fill: { color: "2A2E42" }
    });
    // bar fill
    s.addShape(pres.shapes.RECTANGLE, {
      x: barX+2.1, y: y+0.16, w: barMaxW * 0.68 * f.w * (1/0.32),
      h: 0.18, fill: { color: f.color }
    });
    s.addText((f.w*100).toFixed(0)+"%", {
      x: barX+2.1+barMaxW*0.68+0.08, y: y+0.06, w: 0.55, h: barH-0.12,
      fontSize: 11, bold: true, fontFace: "Calibri", color: f.color, margin: 0
    });
    s.addText(f.desc, {
      x: barX+2.1+barMaxW*0.68+0.72, y: y+0.06, w: 3.2, h: barH-0.12,
      fontSize: 9.5, fontFace: "Calibri", color: MUTED, margin: 0
    });
  });

  s.addNotes("Key insight: title_role_fit and must_have_skills carry 55% of the weight. Location and notice carry behavioral signals. The availability block (16%) is a composite of 6 Redrob platform signals.");
}

// ── SLIDE 6: Skill Evidence ───────────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "Defeating the Keyword Stuffer");
  addSubtitle(s, "How we calculate skill evidence strength — not just presence");

  // Formula card
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 1.3, w: 9, h: 1.55, rectRadius: 0.12,
    fill: { color: CARD }, shadow: makeShadow()
  });
  s.addText("evidence(skill) = 0.5 × self_report(proficiency, duration) + 0.5 × assessment_score", {
    x: 0.7, y: 1.42, w: 8.6, h: 0.5,
    fontSize: 14, bold: true, fontFace: "Courier New", color: TEAL, margin: 0
  });
  s.addText("If no assessment score exists → down-weight self-report to 0.85×  (catches unverified 'advanced' proficiency)", {
    x: 0.7, y: 1.92, w: 8.6, h: 0.38,
    fontSize: 11, fontFace: "Calibri", color: MUTED, margin: 0
  });

  // Comparison table
  const cols = [
    { label: "Signal",              w: 2.8 },
    { label: "Keyword Ranker",      w: 2.8 },
    { label: "This System",         w: 3.8 },
  ];
  const rows = [
    ["skills[]  contains 'RAG'",   "✅ High score",  "Checks proficiency + duration + assessment → evidence ≈ 0.1 if no backing"],
    ["'expert' proficiency",        "✅ Max credit",  "✅ Full credit only if duration ≥18m AND assessment score present"],
    ["Assessment score = 38/100",   "Ignored",        "Penalises even high self-report — capped at 0.5× the assessed value"],
    ["Career title = HR Manager",   "If skills match → promoted", "title_role_fit ≈ 0.05 → whole score floored before disqualifier"],
  ];

  const tY = 3.05, rowH = 0.52;
  // header
  let cx = 0.5;
  cols.forEach(c => {
    s.addShape(pres.shapes.RECTANGLE, { x: cx, y: tY, w: c.w, h: 0.42, fill: { color: NAVY } });
    s.addText(c.label, { x: cx+0.08, y: tY+0.06, w: c.w-0.16, h: 0.3,
      fontSize: 11, bold: true, fontFace: "Calibri", color: WHITE, margin: 0 });
    cx += c.w;
  });
  rows.forEach((row, ri) => {
    let cx2 = 0.5;
    const ry = tY + 0.42 + ri * rowH;
    cols.forEach((c, ci) => {
      const bg = ri % 2 === 0 ? "1a1d27" : CARD;
      s.addShape(pres.shapes.RECTANGLE, { x: cx2, y: ry, w: c.w, h: rowH, fill: { color: bg } });
      const isWarn = ci===1 && row[ci].startsWith("✅");
      s.addText(row[ci], { x: cx2+0.08, y: ry+0.08, w: c.w-0.16, h: rowH-0.16,
        fontSize: 9.5, fontFace: "Calibri",
        color: ci===2 ? TEAL : ci===1 ? WARN : ICE, margin: 0 });
      cx2 += c.w;
    });
  });

  s.addNotes("The most important anti-keyword-stuffing mechanism: assessment scores override self-declared proficiency. Candidates with 'advanced RAG' skill but a 38/100 platform test get scored far lower than someone with 'intermediate' but a 72/100 test.");
}

// ── SLIDE 7: Disqualifiers ────────────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "Stage 3 — Scoring + Disqualifiers");
  addSubtitle(s, "Disqualifiers are multipliers, not hard zeros — graceful degradation for borderline cases");

  const dq = [
    { flag: "LangChain hype only",       mult: "×0.35", desc: "Has LangChain/Prompt Engineering added recently, but zero retrieval depth before 2023. Catches the hype wave." },
    { flag: "Narrow CV/Speech",          mult: "×0.45", desc: "Strong Computer Vision or Speech engineer, but negligible NLP/IR overlap. Wrong specialisation for a search-ranking role." },
    { flag: "Consulting-only career",    mult: "×0.50", desc: "Entire career at TCS/Infosys/Wipro/Accenture/etc. No product company ML exposure." },
    { flag: "Academic researcher",       mult: "×0.60", desc: "Summary language: 'academic lab', 'PhD thesis', 'research-only' — but no production deployment language." },
    { flag: "No must-have + no role fit", mult: "×0.25", desc: "Fails both the skill pillar AND the title-fit test. Almost certainly a keyword-stuffed non-ML profile." },
  ];

  dq.forEach((d, i) => {
    const y = 1.4 + i * 0.82;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y, w: 9.1, h: 0.72, rectRadius: 0.1,
      fill: { color: CARD }, shadow: makeShadow()
    });
    // Multiplier badge
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.55, y: y+0.12, w: 0.9, h: 0.48, rectRadius: 0.08,
      fill: { color: "3a1a1a" }
    });
    s.addText(d.mult, { x: 0.55, y: y+0.14, w: 0.9, h: 0.44,
      fontSize: 14, bold: true, fontFace: "Courier New", color: WARN, align: "center", margin: 0 });
    s.addText(d.flag, { x: 1.6, y: y+0.06, w: 3.5, h: 0.32,
      fontSize: 12.5, bold: true, fontFace: "Calibri", color: WHITE, margin: 0 });
    s.addText(d.desc, { x: 1.6, y: y+0.36, w: 7.85, h: 0.3,
      fontSize: 10, fontFace: "Calibri", color: MUTED, margin: 0 });
  });

  s.addNotes("Why multipliers not hard zeros? A candidate who worked at TCS for 3 years and then moved to Sarvam AI for 4 years is different from someone who spent 12 years only at IT services firms. The multiplier penalises the former gently and the latter severely.");
}

// ── SLIDE 8: Results ──────────────────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "Results");
  addSubtitle(s, "Top 100 shortlist from 100,000 candidates — pipeline validated against official checker");

  // KPI cards
  statCard(s, 0.45, 1.3, 2.1, 1.0, "100,000", "Candidates processed", ICE);
  statCard(s, 2.65, 1.3, 2.1, 1.0, "2,929",   "Honeypots removed",    WARN);
  statCard(s, 4.85, 1.3, 2.1, 1.0, "~30s",     "Pipeline runtime (CPU)", TEAL);
  statCard(s, 7.05, 1.3, 2.1, 1.0, "98.26",   "Top candidate score",  ACCENT);

  // Top 10 table
  const top10 = [
    ["1", "CAND_0052328", "Vikram Banerjee",  "Recommendation Systems Eng", "Pune",       "98.26"],
    ["2", "CAND_0027691", "Ayaan Goyal",       "NLP Engineer",                "Pune",       "97.33"],
    ["3", "CAND_0037566", "Ritu Nair",         "Machine Learning Engineer",   "Bangalore",  "95.91"],
    ["4", "CAND_0011687", "Shreya Tiwari",     "Senior NLP Engineer",         "Indore",     "93.98"],
    ["5", "CAND_0041610", "Priya Sethi",       "Recommendation Systems Eng",  "Bangalore",  "93.77"],
    ["6", "CAND_0095812", "Arjun Krishnan",    "Applied ML Engineer",         "Pune",       "92.14"],
    ["7", "CAND_0018274", "Sana Iqbal",        "Senior AI Engineer",          "Hyderabad",  "91.85"],
    ["8", "CAND_0067341", "Rohan Mehta",       "Machine Learning Engineer",   "Mumbai",     "91.32"],
    ["9", "CAND_0031859", "Pooja Nambiar",     "AI Specialist",               "Bangalore",  "90.77"],
    ["10","CAND_0048203", "Karthik Subbu",     "NLP Engineer",                "Pune",       "90.41"],
  ];

  const colW = [0.42, 1.45, 1.85, 2.55, 1.35, 0.88];
  const colX = [0.45, 0.87, 2.32, 4.17, 6.72, 8.07];
  const hdrs = ["#", "ID", "Name", "Title", "Location", "Score"];

  hdrs.forEach((h, ci) => {
    s.addShape(pres.shapes.RECTANGLE, {
      x: colX[ci], y: 2.5, w: colW[ci], h: 0.32, fill: { color: NAVY }
    });
    s.addText(h, { x: colX[ci]+0.04, y: 2.53, w: colW[ci]-0.08, h: 0.26,
      fontSize: 9.5, bold: true, fontFace: "Calibri", color: ICE, margin: 0 });
  });

  top10.forEach((row, ri) => {
    const ry = 2.82 + ri * 0.265;
    const bg = ri % 2 === 0 ? "1a1d27" : CARD;
    colX.forEach((cx, ci) => {
      s.addShape(pres.shapes.RECTANGLE, { x: cx, y: ry, w: colW[ci], h: 0.255, fill: { color: bg } });
      s.addText(row[ci], { x: cx+0.04, y: ry+0.03, w: colW[ci]-0.08, h: 0.22,
        fontSize: ci===5 ? 10 : 9, bold: ci===5, fontFace: "Calibri",
        color: ci===5 ? TEAL : ci===2 ? WHITE : MUTED, margin: 0 });
    });
  });

  s.addNotes("All top-10 candidates are genuine AI/ML specialists with production retrieval experience, located in India, open to work, and available quickly. Zero consulting-only or narrow-specialist profiles.");
}

// ── SLIDE 9: Sandbox Demo ─────────────────────────────────────────────────────
{
  let s = pres.addSlide();
  darkSlide(s);
  addTitle(s, "Interactive Sandbox");
  addSubtitle(s, "Flask web UI — one-click ranking + AI-powered recruiter explanations via Claude claude-sonnet-4-6");

  // Mock UI screenshot
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.45, y: 1.3, w: 9.1, h: 3.5, rectRadius: 0.15,
    fill: { color: "12151f" }, shadow: makeShadow()
  });
  // Header bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.45, y: 1.3, w: 9.1, h: 0.45, fill: { color: CARD }
  });
  s.addText("RedrRob  AI Ranker  •  Candidate Intelligence", {
    x: 0.65, y: 1.37, w: 6, h: 0.3,
    fontSize: 11, bold: true, fontFace: "Calibri", color: WHITE, margin: 0
  });

  // Controls
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.55, y: 1.85, w: 1.4, h: 0.35, rectRadius: 0.07,
    fill: { color: ACCENT }
  });
  s.addText("⚡ Run Ranking", { x: 0.55, y: 1.87, w: 1.4, h: 0.3,
    fontSize: 10, bold: true, fontFace: "Calibri", color: WHITE, align: "center", margin: 0 });

  // Pills
  ["All", "Open to Work", "Notice ≤30d", "India Only"].forEach((p, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.55 + i * 1.5, y: 2.3, w: 1.35, h: 0.28, rectRadius: 0.14,
      fill: { color: i===0 ? ACCENT : CARD }
    });
    s.addText(p, { x: 0.55 + i * 1.5, y: 2.32, w: 1.35, h: 0.24,
      fontSize: 9, fontFace: "Calibri", color: i===0 ? WHITE : MUTED, align: "center", margin: 0 });
  });

  // Card rows
  const cards = [
    { rank:"1", name:"Vikram Banerjee", title:"Recommendation Systems Eng · Pune", score:"98.26" },
    { rank:"2", name:"Ayaan Goyal",     title:"NLP Engineer · Pune",               score:"97.33" },
  ];
  cards.forEach((c, i) => {
    const cy = 2.72 + i * 0.88;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.55, y: cy, w: 8.9, h: 0.78, rectRadius: 0.1,
      fill: { color: CARD }
    });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.65, y: cy+0.12, w: 0.46, h: 0.46, rectRadius: 0.07,
      fill: { color: ACCENT }
    });
    s.addText(c.rank, { x: 0.65, y: cy+0.13, w: 0.46, h: 0.44,
      fontSize: 14, bold: true, fontFace: "Calibri", color: WHITE, align: "center", margin: 0 });
    s.addText(c.name, { x: 1.25, y: cy+0.1, w: 5, h: 0.3,
      fontSize: 12, bold: true, fontFace: "Calibri", color: WHITE, margin: 0 });
    s.addText(c.title, { x: 1.25, y: cy+0.4, w: 5, h: 0.28,
      fontSize: 10, fontFace: "Calibri", color: MUTED, margin: 0 });
    s.addText(c.score, { x: 8.0, y: cy+0.14, w: 1.3, h: 0.45,
      fontSize: 22, bold: true, fontFace: "Calibri", color: TEAL, align: "right", margin: 0 });
  });

  // AI explain callout
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.45, y: 4.88, w: 9.1, h: 0.55, rectRadius: 0.1,
    fill: { color: "12151f" }
  });
  s.addText("🤖 AI Explain: Click any candidate card → Claude claude-sonnet-4-6 gives a recruiter-readable explanation of why they ranked there and what to probe in the interview", {
    x: 0.65, y: 4.93, w: 8.7, h: 0.44,
    fontSize: 10.5, fontFace: "Calibri", color: ICE, margin: 0
  });

  s.addNotes("The sandbox is a single Flask file with zero build steps. Run 'python sandbox/app.py', open localhost:5000. The AI explanation calls Claude claude-sonnet-4-6 only on-demand, so ranking itself costs nothing.");
}

// ── SLIDE 10: Summary & Extending ─────────────────────────────────────────────
{
  let s = pres.addSlide();
  s.background = { color: NAVY };

  s.addText("What We Built", {
    x: 0.55, y: 0.28, w: 8.9, h: 0.65,
    fontSize: 36, bold: true, fontFace: "Cambria", color: WHITE, margin: 0
  });

  const points = [
    ["🎯", "Fully adversarial-aware", "Handles keyword stuffers, hype adopters, honeypots, consulting lifers, and narrow specialists — all documented in the challenge spec"],
    ["⚡", "Runs in 30 seconds on CPU", "No GPU, no external API calls during ranking. 100k candidates, one command."],
    ["📊", "Interpretable by design",   "Every rank has a reasoning column. Every score has 7 decomposed components visible in the CSV."],
    ["🤖", "AI-augmented for recruiters","Claude claude-sonnet-4-6 explains each candidate in plain English, on demand, in the sandbox UI."],
    ["🔧", "Extensible",               "Swap jd_config.py for a new role in minutes. Add semantic similarity or LLM re-ranking as optional stages."],
  ];

  points.forEach(([icon, title, desc], i) => {
    const y = 1.25 + i * 0.84;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.45, y, w: 9.1, h: 0.72, rectRadius: 0.1,
      fill: { color: "1E2761", transparency: 70 }
    });
    s.addText(icon, { x: 0.6, y: y+0.1, w: 0.55, h: 0.52,
      fontSize: 20, fontFace: "Calibri", align: "center", margin: 0 });
    s.addText(title, { x: 1.2, y: y+0.07, w: 2.8, h: 0.3,
      fontSize: 13, bold: true, fontFace: "Calibri", color: TEAL, margin: 0 });
    s.addText(desc, { x: 1.2, y: y+0.36, w: 8.1, h: 0.3,
      fontSize: 10.5, fontFace: "Calibri", color: ICE, margin: 0 });
  });

  s.addShape(pres.shapes.OVAL, {
    x: 7.5, y: 3.5, w: 4.0, h: 4.0,
    fill: { color: TEAL, transparency: 90 }
  });

  s.addNotes("Closing slide. Key ask from the judges: does this system produce a shortlist a recruiter can trust? Yes — it's explainable, fast, adversarially robust, and backed by a live demo.");
}

// ── Write file ────────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "/home/claude/redrob-ranker/outputs/approach_deck.pptx" })
  .then(() => {
    console.log("✅  PPTX written.");
    process.exit(0);
  })
  .catch(e => { console.error(e); process.exit(1); });
