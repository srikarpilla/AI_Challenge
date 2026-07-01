"""
src/submission.py

Generates the challenge-compliant submission CSV.

Required format (from validate_submission.py):
  Header row:   candidate_id,rank,score,reasoning
  Data rows:    exactly 100, ranks 1-100, score non-increasing,
                tie-break by candidate_id ascending (lexicographic).

Usage
-----
  python src/submission.py
  python src/submission.py --input outputs/ranked_submission.csv --output outputs/final_submission.csv
"""

import argparse, csv, json, os, sys, textwrap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.honeypot import detect_honeypot
from src.features  import extract_features
from src.score     import score_candidate

DEFAULT_INPUT  = os.path.join(ROOT, "data", "candidates.jsonl")
DEFAULT_OUTPUT = os.path.join(ROOT, "outputs", "final_submission.csv")


def _reasoning(feats, rank, score):
    """
    Build a short human-readable reasoning string for the submission CSV.
    Kept to ≤250 chars so it's legible in a spreadsheet cell.
    """
    parts = []

    title = feats["profile"].get("current_title", "")
    yoe   = feats["profile"].get("years_of_experience", 0)
    parts.append(f"{title} ({yoe}yr)")

    ml_yr = feats["ml_years"]
    if ml_yr >= 3:
        parts.append(f"{ml_yr:.1f}yr applied ML")

    ret = feats["retrieval_evid"]
    vdb = feats["vectordb_evid"]
    if ret >= 0.5:
        parts.append("retrieval/embeddings expertise")
    if vdb >= 0.5:
        parts.append("vector-DB experience")

    loc = feats["profile"].get("location", "")
    if feats["location_score"] >= 0.9:
        parts.append(f"preferred location ({loc})")

    nd = feats.get("signals", {}).get("notice_period_days")
    if nd is not None and nd <= 30:
        parts.append(f"notice {nd}d")

    if feats.get("consulting_only"):
        parts.append("NOTE: consulting-only career")
    if feats.get("narrow_cv_speech"):
        parts.append("NOTE: narrow CV/speech specialist")
    if feats.get("langchain_only_recent"):
        parts.append("NOTE: shallow LLM exposure only")

    reason = "; ".join(parts)
    return reason[:250]


def build_submission(input_jsonl=DEFAULT_INPUT, output_csv=DEFAULT_OUTPUT):
    print(f"Building final submission CSV…")

    scored = []
    n_total = n_honey = 0

    with open(input_jsonl, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            n_total += 1
            try:
                c = json.loads(line)
            except Exception:
                continue
            is_hp, _ = detect_honeypot(c)
            if is_hp:
                n_honey += 1
                continue
            feats = extract_features(c)
            score = score_candidate(feats)
            scored.append((score, c["candidate_id"], feats))

    # Sort: score descending, then candidate_id ascending (tie-break per spec)
    scored.sort(key=lambda x: (-x[0], x[1]))

    top100 = scored[:100]

    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (score, cid, feats) in enumerate(top100, 1):
            reason = _reasoning(feats, rank, score)
            writer.writerow([cid, rank, f"{score:.4f}", reason])

    print(f"  Processed     : {n_total:,} candidates")
    print(f"  Honeypots     : {n_honey} removed")
    print(f"  Output        : {output_csv}")
    print(f"  Score range   : {top100[-1][0]:.2f} – {top100[0][0]:.2f}")
    return output_csv


def main():
    parser = argparse.ArgumentParser(description="Produce final submission CSV")
    parser.add_argument("--input",  default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_submission(args.input, args.output)


if __name__ == "__main__":
    main()
