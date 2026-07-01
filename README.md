# RedrRob AI Candidate Ranker

> **India Runs Data & AI Challenge — Submission**
> Rank 100,000 candidates for an applied ML / search-ranking role the way a great recruiter would — not by keywords, but by understanding.

---

## Quick Start

```bash
# 1. Install dependencies (only 3 — no GPU, no network needed for ranking)
pip install anthropic flask python-docx

# 2. Place candidates.jsonl in data/
#    (or symlink: ln -s /path/to/candidates.jsonl data/candidates.jsonl)

# 3. Run full pipeline (100k candidates, ~30s on a laptop CPU)
python src/ranker.py

# 4. Produce the challenge-compliant submission CSV
python src/submission.py

# 5. Validate it
python outputs/validate_submission.py outputs/final_submission.csv
# → Submission is valid.

# 6. Launch the interactive sandbox (optional)
python sandbox/app.py
# Open http://localhost:5000
```

---

## Repo Structure

```
redrob-ranker/
├── config/
│   └── jd_config.py          ← All JD-specific knowledge (vocab, weights, tiers)
├── src/
│   ├── honeypot.py           ← Structural-consistency anomaly detector
│   ├── features.py           ← Feature extraction & normalization
│   ├── score.py              ← Weighted composite scorer + disqualifier multipliers
│   ├── ranker.py             ← End-to-end CLI pipeline (produces ranked_submission.csv)
│   └── submission.py         ← Produces the challenge-compliant final_submission.csv
├── sandbox/
│   └── app.py                ← Flask web UI with AI-powered candidate explanations
├── data/
│   └── candidates.jsonl      ← 100k candidate pool (symlink or copy here)
├── outputs/
│   ├── final_submission.csv  ← Challenge submission (candidate_id, rank, score, reasoning)
│   └── ranked_submission.csv ← Full score breakdown (for debugging / analysis)
├── requirements.txt
└── README.md
```

---

## How It Works

### Problem Insight

The dataset is deliberately adversarial. It contains:
- **Keyword stuffers** — non-ML candidates whose skill arrays include "RAG", "FAISS", "PyTorch" etc. but whose job titles, summaries, and career histories tell a completely different story.
- **Honeypot profiles** — structurally impossible records (e.g. "expert" proficiency in a skill with 0 months of use, or career durations that contradict stated start/end dates).
- **Hype adopters** — people who recently added ChatGPT and LangChain to their profile but have no prior retrieval/ML depth.
- **Narrow specialists** — strong computer vision or speech engineers with no NLP/IR overlap.
- **Consulting lifers** — candidates who have only ever worked at large IT services firms with no product exposure.

Keyword matching promotes all of these incorrectly. The system below avoids every trap.

---

### Stage 1 — Honeypot Elimination (`src/honeypot.py`)

Before scoring, we remove structurally impossible profiles:

| Check | Trigger |
|---|---|
| Expert proficiency + ≤2 months usage | Profile stuffing |
| Career `duration_months` inconsistent with start/end dates | Date fabrication |
| Claimed YOE wildly inconsistent with sum of career history | Inflated experience |
| Multiple simultaneous `is_current` jobs | Impossible overlap |
| Education end\_year before start\_year | Date reversal |
| Skill duration exceeds total career length | Arithmetic impossibility |

**Result:** 2,929 honeypots removed (2.93% of 100k). Zero honeypots in the top 100.

---

### Stage 2 — Feature Extraction (`src/features.py`)

Seven feature groups, all computed without external APIs:

#### 1. Title-Weighted ML Role Fit
Instead of matching the current title only, we walk the full career history and compute a recency-weighted sum of ML-relevant experience:

```
ml_years = Σ (duration_years × category_weight × recency_weight)
```

- `category_weight`: 1.0 for AI/ML core titles, 0.4 for adjacent tech, 0.05 for non-tech
- `recency_weight`: decays from 1.0 → 0.35 as the role ages (linear, 8yr half-life)
- **AI-native industry bonus**: ×1.4 multiplier when industry ∈ {AI/ML, Voice AI, Conversational AI…}
- **Production language bonus**: +0.6yr if the candidate's own summary mentions ≥2 production ML terms

`title_role_fit = min(1.0, ml_years / 4.5) × current_title_multiplier`

#### 2. Must-Have Skills (30% of final score)
The JD names four mandatory competency pillars. We measure evidence strength for each — blending self-reported proficiency + duration with the platform's verified assessment scores (when available):

```
evidence(skill) = 0.5 × self_report(proficiency, duration) + 0.5 × assessment_score
```
If no assessment exists, we down-weight self-report to 0.85× (catches keyword stuffers with unverified "advanced" proficiency and 2 months usage).

| Pillar | Skills | Weight |
|---|---|---|
| Retrieval / Embeddings | FAISS, Pinecone, Semantic Search, RAG, Sentence Transformers… | 30% |
| Vector Databases | Qdrant, Weaviate, pgvector, Elasticsearch, OpenSearch… | 30% |
| Evaluation Frameworks | Learning to Rank, MLOps, MLflow, W&B, Feature Engineering | 20% |
| Python ML Stack | Python, PyTorch, TensorFlow, scikit-learn | 20% |

#### 3. Experience Band
Soft Gaussian penalty around the JD's 5–9 year target. Candidates at 3yr lose ~40%; candidates at 12yr lose ~25%.

#### 4. Nice-to-Have Skills (7%)
Fine-tuning (LoRA, QLoRA, PEFT), GitHub activity score, HR/marketplace industry exposure, distributed systems depth.

#### 5. Location (9%)
Pune/Noida → 1.0; Hyderabad/Mumbai/Delhi NCR/Bangalore → 0.8; Other India → 0.55 (0.4 if not willing to relocate); Outside India → 0.15.

#### 6. Notice Period (5%)
≤30 days → 1.0; ≤60 → 0.65; ≤90 → 0.40; >90 → 0.20.

#### 7. Availability Signals (16%)
Composite of: days since last active (32%), open-to-work flag (10%), recruiter response rate (28%), interview completion rate (15%), offer acceptance rate (10%), verified contact (5%).

---

### Stage 3 — Scoring (`src/score.py`)

Disqualifiers are applied as **multipliers**, not hard zeroes — so they gracefully penalise borderline cases:

| Disqualifier | Multiplier |
|---|---|
| LangChain-hype-only (no retrieval depth pre-2023) | ×0.35 |
| Narrow CV/speech specialist (no NLP/IR overlap) | ×0.45 |
| Consulting-only career (all TCS / Infosys / Wipro etc.) | ×0.50 |
| Academic researcher (no production system language) | ×0.60 |
| No must-have signal AND no role fit | ×0.25 |

A small **availability boost** (up to ×1.10) rewards candidates who both have deep retrieval skills AND are open to work with short notice — exactly the people a recruiter wants to call first.

---

### Stage 4 — Sandbox UI (`sandbox/app.py`)

A Flask single-file web app with:
- One-click ranking of the full 100k pool
- Filter pills: Open to Work, Notice ≤30d, India Only
- Per-candidate score breakdown bars (must-have, role fit, availability, ML years)
- **AI-powered recruiter explanation** via Claude claude-sonnet-4-6 — click any card → get a plain-English explanation of why they ranked where they did and what to probe in the interview
- CSV download

---

## Submission Stats

| Metric | Value |
|---|---|
| Total candidates | 100,000 |
| Honeypots removed | 2,929 (2.93%) |
| Eligible after filtering | 97,071 |
| Pipeline runtime | ~30s (CPU only) |
| Top score | 98.26 |
| Score at rank 100 | 82.85 |

### Top 10 Preview

| Rank | Candidate | Title | Location | Score |
|---|---|---|---|---|
| 1 | Vikram Banerjee | Recommendation Systems Engineer | Pune | 98.26 |
| 2 | Ayaan Goyal | NLP Engineer | Pune | 97.33 |
| 3 | Ritu Nair | Machine Learning Engineer | Bangalore | 95.91 |
| 4 | Shreya Tiwari | Senior NLP Engineer | Indore | 93.98 |
| 5 | Priya Sethi | Recommendation Systems Engineer | Bangalore | 93.77 |

---

## Design Decisions

**Why no embeddings / vector search for ranking?**
The candidate pool is 100k records, CPU-only, no network. Computing embeddings for every profile would take 20+ minutes and require a local model. Feature engineering runs in 30 seconds and is fully explainable — better for a recruiter-facing system where you need to justify every rank.

**Why are disqualifiers multipliers not hard filters?**
A candidate who worked at TCS but then joined an AI startup is different from one who spent 12 years only at IT services firms. Multipliers handle nuance; binary filters don't.

**Why does the self-report evidence down-weight when no assessment score is available?**
The dataset deliberately places AI skill keywords onto non-AI candidate profiles. A skills array alone is unreliable. The platform assessment scores (when present) are the most trustworthy signal; without them, we require both high proficiency AND meaningful duration before awarding full credit.

---

## Extending to Production

- Swap `jd_config.py` for a new JD: the engine is JD-agnostic.
- Add semantic text similarity: embed job description + candidate summaries with `sentence-transformers/all-MiniLM-L6-v2` and blend the cosine score as an additional feature (weight ~0.15).
- Add LLM re-ranking: send the top 500 candidates to Claude claude-sonnet-4-6 with the JD and ask it to score them 1-10 on fit, then use that as a final re-rank signal.
- A/B test against recruiter shortlists to calibrate weights.
