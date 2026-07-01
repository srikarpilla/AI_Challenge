"""
sandbox/app.py

Interactive web sandbox for the RedrRob AI Candidate Ranker.

Features
--------
- Upload any job description (text area or .txt / .docx) and see a ranked
  candidate shortlist in real time against the bundled dataset.
- Click any candidate card to get a natural-language explanation of why
  they ranked where they did (powered by Claude claude-sonnet-4-6 via the
  Anthropic API).
- Download the ranked shortlist as CSV.
- Side panel showing pipeline stats: honeypots removed, score distribution.

Quick start
-----------
  pip install flask anthropic python-docx
  python sandbox/app.py
  Open http://localhost:5000
"""

import json, os, sys, csv, io, time
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template_string

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.honeypot  import detect_honeypot
from src.features  import extract_features
from src.score     import score_candidate
from config        import jd_config as cfg

app = Flask(__name__)

CANDIDATES_JSONL = os.path.join(ROOT, "data", "candidates.jsonl")
_CACHE = {}   # simple in-process cache so re-ranking is fast

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_and_score_all(limit=None):
    """Load, filter honeypots, extract features, score every candidate."""
    if "all" in _CACHE and limit is None:
        return _CACHE["all"]

    results = []
    with open(CANDIDATES_JSONL, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if limit and i >= limit:
                break
            if not line.strip():
                continue
            try:
                c = json.loads(line)
            except Exception:
                continue
            is_hp, _ = detect_honeypot(c)
            if is_hp:
                continue
            feats = extract_features(c)
            score = score_candidate(feats)
            results.append({
                "candidate_id":    c["candidate_id"],
                "name":            c["profile"].get("anonymized_name", ""),
                "current_title":   c["profile"].get("current_title", ""),
                "current_company": c["profile"].get("current_company", ""),
                "years_of_experience": c["profile"].get("years_of_experience", 0),
                "location":        c["profile"].get("location", ""),
                "country":         c["profile"].get("country", ""),
                "headline":        c["profile"].get("headline", ""),
                "summary":         (c["profile"].get("summary") or "")[:400],
                "skills":          [s["name"] for s in c.get("skills", [])[:10]],
                "score":           round(score, 2),
                "must_have":       round(feats["must_have_score"] * 100, 1),
                "ml_years":        round(feats["ml_years"], 1),
                "title_fit":       round(feats["title_role_fit"] * 100, 1),
                "availability":    round(feats["availability_score"] * 100, 1),
                "open_to_work":    bool(c.get("redrob_signals", {}).get("open_to_work_flag")),
                "notice_days":     c.get("redrob_signals", {}).get("notice_period_days", "?"),
                "github_score":    c.get("redrob_signals", {}).get("github_activity_score", None),
                "consulting_only": feats["consulting_only"],
                "narrow_cv":       feats["narrow_cv_speech"],
                "langchain_only":  feats["langchain_only_recent"],
                "_raw":            c,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    if limit is None:
        _CACHE["all"] = results
    return results


def _candidate_profile_text(c_dict):
    """Build a concise text snapshot of a candidate for the AI explainer."""
    lines = [
        f"Name: {c_dict['name']}",
        f"Title: {c_dict['current_title']} at {c_dict['current_company']}",
        f"Experience: {c_dict['years_of_experience']} years",
        f"Location: {c_dict['location']}, {c_dict['country']}",
        f"Headline: {c_dict['headline']}",
        f"Summary: {c_dict['summary']}",
        f"Skills (first 10): {', '.join(c_dict['skills'])}",
        f"Score: {c_dict['score']}/100",
        f"  - Must-have skills: {c_dict['must_have']}%",
        f"  - ML role years: {c_dict['ml_years']}",
        f"  - Title fit: {c_dict['title_fit']}%",
        f"  - Availability: {c_dict['availability']}%",
        f"  - Open to work: {c_dict['open_to_work']}",
        f"  - Notice period: {c_dict['notice_days']} days",
    ]
    if c_dict.get("consulting_only"):   lines.append("Flag: consulting-only career")
    if c_dict.get("narrow_cv"):         lines.append("Flag: narrow CV/speech specialist")
    if c_dict.get("langchain_only"):    lines.append("Flag: recent generative-AI hype only")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/api/rank", methods=["POST"])
def api_rank():
    body   = request.get_json(silent=True) or {}
    top_n  = min(int(body.get("top_n", 100)), 300)
    limit  = int(body.get("limit", 0)) or None   # 0 = all
    t0     = time.time()
    ranked = _load_and_score_all(limit=limit)
    top    = ranked[:top_n]
    total  = len(ranked)
    return jsonify({
        "total_eligible": total,
        "took_ms":        round((time.time() - t0) * 1000),
        "candidates":     top,
    })


@app.route("/api/explain", methods=["POST"])
def api_explain():
    body = request.get_json(silent=True) or {}
    cid  = body.get("candidate_id")

    ranked = _load_and_score_all()
    c_dict = next((r for r in ranked if r["candidate_id"] == cid), None)
    if not c_dict:
        return jsonify({"error": "candidate not found"}), 404

    profile_text = _candidate_profile_text(c_dict)

    prompt = f"""You are an AI recruitment assistant helping a technical recruiter understand why a candidate was ranked the way they were for an applied machine-learning role focused on search ranking and retrieval systems.

Here is the candidate profile and their score breakdown:
{profile_text}

The role requires:
- Hands-on production experience with embeddings-based retrieval systems (semantic search, vector search, RAG)
- Experience with vector databases (FAISS, Pinecone, Qdrant, Weaviate, pgvector, Elasticsearch/OpenSearch)
- Strong Python; ability to build and evaluate ranking systems
- 5–9 years total experience with 4+ in applied ML
- Preferred location: Pune or Noida (India)

Give a concise recruiter-readable explanation (3–5 sentences) of:
1. Why this candidate scored {c_dict['score']}/100
2. What their key strengths are for this role
3. Any concerns or gaps a recruiter should probe in the interview
Keep the tone professional and actionable."""

    try:
        import anthropic
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        explanation = msg.content[0].text
    except Exception as e:
        explanation = f"[AI explanation unavailable: {e}]"

    return jsonify({"candidate_id": cid, "explanation": explanation})


@app.route("/api/download", methods=["GET"])
def api_download():
    top_n  = min(int(request.args.get("top_n", 100)), 300)
    ranked = _load_and_score_all()
    top    = ranked[:top_n]

    output = io.StringIO()
    if top:
        fields = ["rank", "candidate_id", "name", "current_title", "current_company",
                  "years_of_experience", "location", "country", "score",
                  "must_have", "ml_years", "title_fit", "availability",
                  "open_to_work", "notice_days"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for i, r in enumerate(top, 1):
            r2 = dict(r); r2["rank"] = i
            writer.writerow(r2)

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"ranked_candidates_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    )


@app.route("/api/stats", methods=["GET"])
def api_stats():
    ranked = _load_and_score_all()
    scores = [r["score"] for r in ranked]
    buckets = [0]*10
    for s in scores:
        idx = min(9, int(s // 10))
        buckets[idx] += 1
    return jsonify({
        "total_scored": len(scores),
        "top_score": scores[0] if scores else 0,
        "p90_score": scores[int(len(scores)*0.10)] if scores else 0,
        "p50_score": scores[len(scores)//2] if scores else 0,
        "score_distribution": {f"{i*10}-{i*10+9}": buckets[i] for i in range(10)},
    })


# ──────────────────────────────────────────────────────────────────────────────
# HTML / JS front-end (single-file, no build step needed)
# ──────────────────────────────────────────────────────────────────────────────

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RedrRob AI Candidate Ranker</title>
<style>
  :root{
    --bg:#0f1117;--surface:#1a1d27;--card:#22263a;
    --accent:#5c6ff0;--accent2:#4ecdc4;--text:#e8eaf0;
    --muted:#8892a4;--border:#2e3347;--warn:#f5a623;--ok:#3dcc91;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
  header{background:linear-gradient(135deg,#1e2235,#141825);padding:18px 32px;
         border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px}
  .logo{font-size:22px;font-weight:700;color:#fff;letter-spacing:-.5px}
  .logo span{color:var(--accent)}
  .logo-sub{font-size:13px;color:var(--muted);margin-left:4px}
  .controls{background:var(--surface);padding:18px 32px;border-bottom:1px solid var(--border);
            display:flex;gap:16px;align-items:center;flex-wrap:wrap}
  .controls label{font-size:13px;color:var(--muted)}
  .controls input[type=number]{background:#2a2e42;border:1px solid var(--border);color:var(--text);
                                padding:6px 10px;border-radius:6px;width:90px;font-size:14px}
  .btn{padding:8px 20px;border-radius:8px;border:none;cursor:pointer;font-size:14px;
       font-weight:600;transition:all .2s}
  .btn-primary{background:var(--accent);color:#fff}
  .btn-primary:hover{background:#7080f8}
  .btn-outline{background:transparent;border:1px solid var(--border);color:var(--text)}
  .btn-outline:hover{border-color:var(--accent);color:var(--accent)}
  .btn-sm{padding:5px 14px;font-size:12px}
  .main{display:flex;height:calc(100vh - 120px)}
  .sidebar{width:300px;min-width:260px;background:var(--surface);border-right:1px solid var(--border);
           padding:20px 16px;overflow-y:auto}
  .sidebar h3{font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:12px}
  .stat-card{background:var(--card);border-radius:10px;padding:12px 14px;margin-bottom:10px}
  .stat-card .val{font-size:24px;font-weight:700;color:var(--accent2)}
  .stat-card .lbl{font-size:12px;color:var(--muted);margin-top:2px}
  .dist-row{display:flex;align-items:center;gap:6px;margin:4px 0}
  .dist-bar-bg{flex:1;background:#2a2e42;border-radius:3px;height:8px}
  .dist-bar{height:8px;border-radius:3px;background:var(--accent);transition:width .5s}
  .dist-lbl{font-size:11px;color:var(--muted);width:42px;text-align:right}
  .list-panel{flex:1;overflow-y:auto;padding:20px}
  .list-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
  .list-header h2{font-size:18px;font-weight:700}
  .list-header .meta{font-size:13px;color:var(--muted)}
  .candidate-card{background:var(--card);border:1px solid var(--border);border-radius:12px;
                  padding:16px 18px;margin-bottom:12px;cursor:pointer;transition:all .2s}
  .candidate-card:hover{border-color:var(--accent);transform:translateY(-1px)}
  .candidate-card.expanded{border-color:var(--accent2)}
  .card-top{display:flex;align-items:flex-start;gap:14px}
  .rank-badge{background:var(--accent);color:#fff;border-radius:8px;width:36px;height:36px;
              display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0}
  .rank-badge.top3{background:linear-gradient(135deg,#f5a623,#e8890c)}
  .card-info{flex:1}
  .card-name{font-size:15px;font-weight:600}
  .card-title{font-size:13px;color:var(--muted);margin-top:2px}
  .card-meta{font-size:12px;color:var(--muted);margin-top:4px}
  .score-ring{text-align:right;flex-shrink:0}
  .score-val{font-size:22px;font-weight:700;color:var(--accent2)}
  .score-lbl{font-size:11px;color:var(--muted)}
  .bars{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
  .mini-bar{flex:1;min-width:80px}
  .mini-bar .name{font-size:10px;color:var(--muted);margin-bottom:3px}
  .mini-bar .track{background:#2a2e42;border-radius:3px;height:6px}
  .mini-bar .fill{height:6px;border-radius:3px;background:var(--accent)}
  .tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
  .tag{font-size:11px;padding:2px 8px;border-radius:20px;background:#2a2e42;color:var(--muted)}
  .tag.warn{background:#3a2a0e;color:var(--warn)}
  .tag.ok{background:#0e2a20;color:var(--ok)}
  .expand-area{margin-top:14px;padding-top:14px;border-top:1px solid var(--border);display:none}
  .candidate-card.expanded .expand-area{display:block}
  .summary-text{font-size:13px;color:var(--muted);line-height:1.6;margin-bottom:12px}
  .explain-box{background:#12151f;border-radius:8px;padding:12px 14px;font-size:13px;
               line-height:1.7;color:#c5cae0;min-height:60px}
  .explain-box.loading{color:var(--muted);font-style:italic}
  .spinner{display:inline-block;width:14px;height:14px;border:2px solid var(--muted);
           border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;
           vertical-align:middle;margin-right:6px}
  @keyframes spin{to{transform:rotate(360deg)}}
  .status-bar{text-align:center;padding:32px;color:var(--muted);font-size:14px}
  .pills{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}
  .pill{font-size:12px;padding:4px 12px;border-radius:20px;border:1px solid var(--border);
        cursor:pointer;transition:all .2s;color:var(--muted)}
  .pill.active{background:var(--accent);border-color:var(--accent);color:#fff}
  .download-row{margin-top:16px}
</style>
</head>
<body>
<header>
  <div>
    <div class="logo">RedrRob <span>AI Ranker</span><span class="logo-sub">Candidate Intelligence</span></div>
  </div>
</header>

<div class="controls">
  <div>
    <label>Show top</label>
    <input type="number" id="topN" value="50" min="10" max="300" step="10">
    <label style="margin-left:4px">candidates</label>
  </div>
  <button class="btn btn-primary" onclick="loadRanking()">⚡ Run Ranking</button>
  <button class="btn btn-outline" onclick="downloadCSV()">⬇ Download CSV</button>
  <span id="loadStatus" style="font-size:13px;color:var(--muted)"></span>
</div>

<div class="main">
  <!-- Sidebar stats -->
  <div class="sidebar">
    <h3>Pipeline Stats</h3>
    <div class="stat-card">
      <div class="val" id="statTotal">—</div>
      <div class="lbl">Eligible candidates</div>
    </div>
    <div class="stat-card">
      <div class="val" id="statTop">—</div>
      <div class="lbl">Top score</div>
    </div>
    <div class="stat-card">
      <div class="val" id="statP50">—</div>
      <div class="lbl">Median score</div>
    </div>

    <h3 style="margin-top:18px">Score Distribution</h3>
    <div id="distChart"></div>

    <div class="download-row">
      <button class="btn btn-outline btn-sm" style="width:100%" onclick="downloadCSV()">Download full CSV</button>
    </div>
  </div>

  <!-- Candidate list -->
  <div class="list-panel">
    <div class="list-header">
      <h2>Candidate Shortlist</h2>
      <span class="meta" id="listMeta"></span>
    </div>

    <div class="pills">
      <span class="pill active" data-filter="all">All</span>
      <span class="pill" data-filter="open">Open to Work</span>
      <span class="pill" data-filter="fast">Notice ≤30d</span>
      <span class="pill" data-filter="india">India Only</span>
    </div>

    <div id="candidateList"><div class="status-bar">Click <b>Run Ranking</b> to load candidates.</div></div>
  </div>
</div>

<script>
let allCandidates = [];
let activeFilter = 'all';

document.querySelectorAll('.pill').forEach(p => {
  p.addEventListener('click', () => {
    document.querySelectorAll('.pill').forEach(x=>x.classList.remove('active'));
    p.classList.add('active');
    activeFilter = p.dataset.filter;
    renderList(filteredCandidates());
  });
});

function filteredCandidates(){
  if(activeFilter==='open')  return allCandidates.filter(c=>c.open_to_work);
  if(activeFilter==='fast')  return allCandidates.filter(c=>Number(c.notice_days)<=30);
  if(activeFilter==='india') return allCandidates.filter(c=>c.country==='India');
  return allCandidates;
}

async function loadRanking(){
  const topN = parseInt(document.getElementById('topN').value)||50;
  document.getElementById('loadStatus').innerHTML='<span class="spinner"></span>Scoring candidates…';
  document.getElementById('candidateList').innerHTML='<div class="status-bar"><span class="spinner"></span> Running pipeline on 100,000 candidates…</div>';

  const resp = await fetch('/api/rank',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({top_n:topN})
  });
  const data = await resp.json();
  allCandidates = data.candidates;
  document.getElementById('loadStatus').textContent=`Done in ${data.took_ms}ms`;
  document.getElementById('listMeta').textContent=`${data.total_eligible.toLocaleString()} eligible · showing top ${data.candidates.length}`;
  renderList(filteredCandidates());
  loadStats();
}

async function loadStats(){
  const resp = await fetch('/api/stats');
  const s = await resp.json();
  document.getElementById('statTotal').textContent=s.total_scored.toLocaleString();
  document.getElementById('statTop').textContent=s.top_score.toFixed(1);
  document.getElementById('statP50').textContent=s.p50_score.toFixed(1);
  const maxV = Math.max(...Object.values(s.score_distribution));
  let html='';
  for(const [band,count] of Object.entries(s.score_distribution)){
    const pct = maxV>0?Math.round(count/maxV*100):0;
    html+=`<div class="dist-row">
      <span style="font-size:10px;color:var(--muted);width:34px">${band}</span>
      <div class="dist-bar-bg"><div class="dist-bar" style="width:${pct}%"></div></div>
      <span class="dist-lbl">${count.toLocaleString()}</span>
    </div>`;
  }
  document.getElementById('distChart').innerHTML=html;
}

function renderList(candidates){
  if(!candidates.length){
    document.getElementById('candidateList').innerHTML='<div class="status-bar">No candidates match this filter.</div>';
    return;
  }
  const html = candidates.map((c,i)=>{
    const rank = allCandidates.indexOf(c)+1;
    const badgeCls = rank<=3?'rank-badge top3':'rank-badge';
    const flags = [
      c.open_to_work?'<span class="tag ok">Open to Work</span>':'',
      c.notice_days<=30?`<span class="tag ok">Notice: ${c.notice_days}d</span>`:'',
      c.consulting_only?'<span class="tag warn">Consulting Only</span>':'',
      c.narrow_cv?'<span class="tag warn">Narrow CV/Speech</span>':'',
      c.langchain_only?'<span class="tag warn">LangChain Hype</span>':'',
    ].filter(Boolean).join('');
    const skills = (c.skills||[]).slice(0,8).map(s=>`<span class="tag">${s}</span>`).join('');
    return `<div class="candidate-card" id="card-${c.candidate_id}" onclick="toggleCard('${c.candidate_id}')">
      <div class="card-top">
        <div class="${badgeCls}">${rank}</div>
        <div class="card-info">
          <div class="card-name">${c.name}</div>
          <div class="card-title">${c.current_title} · ${c.current_company}</div>
          <div class="card-meta">${c.location}, ${c.country} · ${c.years_of_experience}y exp</div>
        </div>
        <div class="score-ring">
          <div class="score-val">${c.score}</div>
          <div class="score-lbl">/ 100</div>
        </div>
      </div>
      <div class="bars">
        ${miniBar('Must-Have Skills',c.must_have,'#5c6ff0')}
        ${miniBar('Role Fit',c.title_fit,'#4ecdc4')}
        ${miniBar('Availability',c.availability,'#f5a623')}
        ${miniBar('ML Yrs',Math.min(100,c.ml_years*20),'#3dcc91')}
      </div>
      <div class="tags" style="margin-top:8px">${flags}${skills}</div>
      <div class="expand-area">
        <div class="summary-text">${c.summary||'No summary available.'}</div>
        <button class="btn btn-outline btn-sm" onclick="explainCandidate(event,'${c.candidate_id}')">🤖 Explain with AI</button>
        <div class="explain-box" id="explain-${c.candidate_id}" style="margin-top:10px;display:none"></div>
      </div>
    </div>`;
  }).join('');
  document.getElementById('candidateList').innerHTML=html;
}

function miniBar(name,val,color){
  return `<div class="mini-bar">
    <div class="name">${name}</div>
    <div class="track"><div class="fill" style="width:${Math.min(100,val||0)}%;background:${color}"></div></div>
  </div>`;
}

function toggleCard(cid){
  const card = document.getElementById('card-'+cid);
  card.classList.toggle('expanded');
}

async function explainCandidate(e, cid){
  e.stopPropagation();
  const box = document.getElementById('explain-'+cid);
  box.style.display='block';
  box.className='explain-box loading';
  box.innerHTML='<span class="spinner"></span> Asking Claude to explain this ranking…';

  const resp = await fetch('/api/explain',{
    method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({candidate_id:cid})
  });
  const data = await resp.json();
  box.className='explain-box';
  box.innerHTML=data.explanation||data.error||'No explanation available.';
}

function downloadCSV(){
  const topN = document.getElementById('topN').value||100;
  window.location='/api/download?top_n='+topN;
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    print("=" * 60)
    print("  RedrRob AI Candidate Ranker — Sandbox")
    print("  Open http://localhost:5000")
    print("=" * 60)
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
