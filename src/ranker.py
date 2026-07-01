"""
src/ranker.py

End-to-end ranking pipeline.

Usage
-----
  python src/ranker.py                            # default paths
  python src/ranker.py --input path/to/candidates.jsonl --output outputs/submission.csv
  python src/ranker.py --top 200 --explain        # emit score breakdown in CSV
  python src/ranker.py --dry-run                  # process first 5000 rows only

The script is designed to run on a laptop CPU in < 5 minutes for 100k
candidates (no GPU, no network required during ranking).
"""

import argparse
import csv
import json
import sys
import os
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.honeypot import detect_honeypot
from src.features import extract_features
from src.score import score_candidate


DEFAULT_INPUT  = os.path.join(ROOT, "data", "candidates.jsonl")
DEFAULT_OUTPUT = os.path.join(ROOT, "outputs", "ranked_submission.csv")


def run_pipeline(input_path, output_path, top_n=100, explain=False, dry_run=False, verbose=True):
    t0 = time.time()

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    results   = []
    n_total   = 0
    n_honey   = 0
    n_scored  = 0
    batch_log = 10_000

    if verbose:
        print(f"[{_ts()}] Reading candidates from: {input_path}")
        if dry_run:
            print("  [DRY RUN] Processing first 5,000 rows only.")

    with open(input_path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            n_total += 1
            if dry_run and n_total > 5_000:
                break

            try:
                candidate = json.loads(line)
            except json.JSONDecodeError as e:
                if verbose:
                    print(f"  [WARN] Could not parse line {n_total}: {e}")
                continue

            # ── Honeypot filter ───────────────────────────────────────────
            is_hp, hp_reasons = detect_honeypot(candidate)
            if is_hp:
                n_honey += 1
                continue

            # ── Feature extraction + scoring ──────────────────────────────
            feats = extract_features(candidate)
            score = score_candidate(feats)
            n_scored += 1

            row = {
                "rank":          None,
                "candidate_id":  candidate["candidate_id"],
                "score":         score,
                "name":          candidate["profile"].get("anonymized_name", ""),
                "current_title": candidate["profile"].get("current_title", ""),
                "yoe":           candidate["profile"].get("years_of_experience", ""),
                "location":      candidate["profile"].get("location", ""),
                "country":       candidate["profile"].get("country", ""),
            }

            if explain:
                row.update({
                    "must_have_score":      round(feats["must_have_score"], 4),
                    "retrieval_evid":       round(feats["retrieval_evid"], 4),
                    "vectordb_evid":        round(feats["vectordb_evid"], 4),
                    "eval_evid":            round(feats["eval_evid"], 4),
                    "python_evid":          round(feats["python_evid"], 4),
                    "title_role_fit":       round(feats["title_role_fit"], 4),
                    "title_category":       feats["title_category"],
                    "ml_years":             round(feats["ml_years"], 2),
                    "nice_score":           round(feats["nice_score"], 4),
                    "exp_band_score":       round(feats["experience_band_score"], 4),
                    "location_score":       round(feats["location_score"], 4),
                    "notice_score":         round(feats["notice_score"], 4),
                    "availability_score":   round(feats["availability_score"], 4),
                    "consulting_only":      int(feats["consulting_only"]),
                    "narrow_cv_speech":     int(feats["narrow_cv_speech"]),
                    "langchain_only":       int(feats["langchain_only_recent"]),
                    "pure_research":        int(feats["pure_research_signal"]),
                    "open_to_work":         int(bool(feats["signals"].get("open_to_work_flag"))),
                    "notice_days":          feats["signals"].get("notice_period_days", ""),
                    "github_score":         feats["signals"].get("github_activity_score", ""),
                    "recruiter_resp_rate":  feats["signals"].get("recruiter_response_rate", ""),
                })

            results.append(row)

            if verbose and n_total % batch_log == 0:
                elapsed = time.time() - t0
                print(f"  [{_ts()}] Processed {n_total:,} | scored {n_scored:,} | "
                      f"honeypot {n_honey} | {elapsed:.1f}s elapsed")

    # ── Sort and assign ranks ─────────────────────────────────────────────
    results.sort(key=lambda r: r["score"], reverse=True)
    top = results[:top_n]
    for i, r in enumerate(top, 1):
        r["rank"] = i

    # ── Write CSV ─────────────────────────────────────────────────────────
    if top:
        fieldnames = list(top[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(top)

    elapsed_total = time.time() - t0
    if verbose:
        print(f"\n[{_ts()}] ── Pipeline complete ──────────────────────────────────")
        print(f"  Candidates processed : {n_total:,}")
        print(f"  Honeypots removed    : {n_honey} ({n_honey/max(n_total,1)*100:.2f}%)")
        print(f"  Candidates scored    : {n_scored:,}")
        print(f"  Top {top_n} written to   : {output_path}")
        print(f"  Total time           : {elapsed_total:.1f}s")
        if top:
            print(f"  Score range (top {top_n}) : {top[-1]['score']:.2f} – {top[0]['score']:.2f}")

    return top


def _ts():
    return datetime.now().strftime("%H:%M:%S")


def main():
    parser = argparse.ArgumentParser(
        description="RedrRob AI Candidate Ranker — ranks candidates for an AI/ML search-ranking role."
    )
    parser.add_argument("--input",    default=DEFAULT_INPUT,  help="Path to candidates.jsonl")
    parser.add_argument("--output",   default=DEFAULT_OUTPUT, help="Path for ranked_submission.csv")
    parser.add_argument("--top",      type=int, default=100,  help="Number of candidates to output (default 100)")
    parser.add_argument("--explain",  action="store_true",    help="Include score-breakdown columns in output CSV")
    parser.add_argument("--dry-run",  action="store_true",    help="Process only the first 5,000 rows (for quick testing)")
    args = parser.parse_args()

    run_pipeline(
        input_path  = args.input,
        output_path = args.output,
        top_n       = args.top,
        explain     = args.explain,
        dry_run     = args.dry_run,
    )


if __name__ == "__main__":
    main()
