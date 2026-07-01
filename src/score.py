"""
src/score.py

Converts extracted features into a final composite score (0-100).

Design principle: disqualifiers are applied as multipliers AFTER the
base score is computed, not by zeroing out individual components. This
means a candidate who is borderline on a disqualifier gets gracefully
penalised rather than instantly eliminated, preserving the ranked-list
diversity that recruiters care about.

Honeypots are eliminated BEFORE scoring (see src/honeypot.py).
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import jd_config as cfg


def score_candidate(feats):
    """
    feats: dict returned by features.extract_features()
    Returns: float in [0, 100]
    """
    W = cfg.WEIGHTS

    base = (
        W["title_role_fit"]   * feats["title_role_fit"]
      + W["must_have_skills"] * feats["must_have_score"]
      + W["experience_band"]  * feats["experience_band_score"]
      + W["nice_to_have"]     * feats["nice_score"]
      + W["location_fit"]     * feats["location_score"]
      + W["notice_period"]    * feats["notice_score"]
      + W["availability"]     * feats["availability_score"]
    )  # 0.0 – 1.0

    # -----------------------------------------------------------------------
    # Soft disqualifiers (from submission_spec.docx "What NOT to rank")
    # -----------------------------------------------------------------------
    penalty = 1.0

    # "Only knows ML via recent generative-AI hype" -- no real retrieval depth
    if feats["langchain_only_recent"]:
        penalty *= 0.35

    # "Computer vision/speech specialist with no NLP/IR overlap"
    if feats["narrow_cv_speech"]:
        penalty *= 0.45

    # "Only worked at consulting/services firms their entire career"
    if feats["consulting_only"]:
        penalty *= 0.50

    # "Academic researcher with no production system experience"
    if feats["pure_research_signal"]:
        penalty *= 0.60

    # No must-have signals at all -- likely keyword stuffer
    if feats["must_have_score"] < 0.05 and feats["title_role_fit"] < 0.20:
        penalty *= 0.25

    # -----------------------------------------------------------------------
    # Positive nudge: candidates with verified retrieval stack signal who are
    # open to work + low notice get a small boost to surface them above
    # otherwise-similar profiles.
    # -----------------------------------------------------------------------
    boost = 1.0
    if feats["retrieval_evid"] >= 0.5 and feats["vectordb_evid"] >= 0.4:
        if feats["signals"].get("open_to_work_flag"):
            boost = 1.06
        if feats["signals"].get("notice_period_days", 999) <= 30:
            boost = min(1.10, boost * 1.04)

    final = base * penalty * boost
    return round(min(100.0, max(0.0, final * 100.0)), 4)
