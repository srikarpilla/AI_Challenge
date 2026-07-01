"""
src/features.py

Pure feature engineering -- no scoring weights live here, only extraction
and normalization logic. See src/score.py for how these features are
combined into a final score, and config/jd_config.py for the JD-specific
vocab driving the matching.
"""

import re
from datetime import date

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import jd_config as cfg

TODAY = date(2026, 6, 30)

_PROF_WEIGHT = {"beginner": 0.40, "intermediate": 0.65, "advanced": 0.85, "expert": 1.0}


def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _title_category(title):
    t = (title or "").strip().lower()
    if t in cfg.AI_ML_CORE_TITLES:
        return "ai_ml_core"
    if t in cfg.ADJACENT_TECH_TITLES:
        return "adjacent_tech"
    return "non_tech"


def _skill_lookup(skills):
    """name(lower) -> dict(proficiency, endorsements, duration_months)"""
    return {s["name"].strip().lower(): s for s in skills}


def _skill_evidence(skill_dict, assessment_scores, name):
    """0-1 evidence strength for a single named skill, blending self-report
    (proficiency + duration) with the platform-verified assessment score
    when available. This is what catches keyword-stuffed 'expert' skills
    with near-zero duration and no assessment backing."""
    s = skill_dict.get(name)
    if not s:
        return 0.0
    dur = s.get("duration_months", 0) or 0
    prof = _PROF_WEIGHT.get(s.get("proficiency", "beginner"), 0.4)
    self_report = min(1.0, dur / 18.0) * prof

    assess = None
    for k, v in (assessment_scores or {}).items():
        if k.strip().lower() == name:
            assess = v / 100.0
            break

    if assess is not None:
        return 0.5 * self_report + 0.5 * assess
    # No platform assessment exists for this skill: trust self-report less.
    return 0.85 * self_report


def _category_evidence(skill_dict, assessment_scores, category_set):
    if not skill_dict:
        return 0.0
    return max((_skill_evidence(skill_dict, assessment_scores, name) for name in category_set), default=0.0)


def compute_ml_role_years(career_history, summary_text):
    """Recency- and category-weighted years of AI/ML-relevant experience,
    plus a light bonus for first-person production-ML language in the
    candidate's own summary (more trustworthy than career_history
    descriptions, which are deliberately noisy/decoupled in this dataset)."""
    total = 0.0
    for ch in career_history:
        dur_years = (ch.get("duration_months", 0) or 0) / 12.0
        cat = _title_category(ch.get("title"))
        cat_weight = {"ai_ml_core": 1.0, "adjacent_tech": 0.40, "non_tech": 0.05}[cat]
        if (ch.get("industry") or "").strip().lower() in cfg.AI_NATIVE_INDUSTRIES:
            cat_weight = min(1.0, cat_weight * 1.4)

        ed = _parse_date(ch.get("end_date")) or TODAY
        months_ago = max(0, (TODAY.year - ed.year) * 12 + (TODAY.month - ed.month))
        recency_weight = max(0.35, 1.0 - months_ago / 96.0)

        total += dur_years * cat_weight * recency_weight

    bonus = 0.0
    text = (summary_text or "").lower()
    production_hits = sum(
        1 for kw in ("recommendation system", "ranking", "retrieval", "search system",
                      "embeddings", "shipped", "production", "matching engine")
        if kw in text
    )
    if production_hits >= 2:
        bonus = 0.6
    elif production_hits == 1:
        bonus = 0.25

    return total + bonus


def detect_consulting_only(career_history, current_company):
    companies = {ch.get("company", "").strip().lower() for ch in career_history}
    companies.add((current_company or "").strip().lower())
    companies.discard("")
    if not companies:
        return False
    return companies.issubset(cfg.CONSULTING_COMPANIES)


def detect_narrow_cv_speech(skill_dict, assessment_scores):
    cv_speech = _category_evidence(skill_dict, assessment_scores, cfg.CV_SPEECH_ROBOTICS_SKILLS)
    nlp_ir = max(
        _category_evidence(skill_dict, assessment_scores, cfg.RETRIEVAL_EMBEDDING_SKILLS),
        _category_evidence(skill_dict, assessment_scores, cfg.NLP_LLM_ADJACENT_SKILLS),
    )
    return cv_speech >= 0.5 and nlp_ir < 0.15


def detect_langchain_only_recent(skill_dict, ml_role_years_pre2023):
    recent_ai_only = {"langchain", "prompt engineering", "llms"}
    has_recent_shallow = any(
        skill_dict.get(n) and (skill_dict[n].get("duration_months", 0) or 0) < 12
        for n in recent_ai_only
    )
    has_deep_retrieval = any(
        skill_dict.get(n) and (skill_dict[n].get("duration_months", 0) or 0) >= 12
        for n in cfg.RETRIEVAL_EMBEDDING_SKILLS | cfg.VECTOR_DB_SKILLS
    )
    return has_recent_shallow and not has_deep_retrieval and ml_role_years_pre2023 < 0.5


def detect_pure_research_signal(summary_text):
    text = (summary_text or "").lower()
    research_kw = ("academic lab", "research lab", "phd thesis", "research-only",
                   "published papers", "academia")
    production_kw = ("shipped", "production", "deployed", "real users", "scale")
    has_research = any(kw in text for kw in research_kw)
    has_production = any(kw in text for kw in production_kw)
    return has_research and not has_production


def compute_location_score(profile, signals):
    if (profile.get("country") or "").strip().lower() != "india":
        return 0.15
    loc = (profile.get("location") or "").strip().lower()
    if loc in cfg.LOCATION_TIER_1:
        return 1.0
    if loc in cfg.LOCATION_TIER_2:
        return 0.80
    return 0.55 if signals.get("willing_to_relocate") else 0.40


def compute_notice_score(signals):
    days = signals.get("notice_period_days", 90)
    if days <= 30:
        return 1.0
    if days <= 60:
        return 0.65
    if days <= 90:
        return 0.40
    return 0.20


def compute_availability_score(signals):
    last_active = _parse_date(signals.get("last_active_date"))
    if last_active:
        days_inactive = (TODAY - last_active).days
        recency = max(0.0, 1.0 - days_inactive / 180.0)
    else:
        recency = 0.0

    open_flag = 1.0 if signals.get("open_to_work_flag") else 0.4
    response = signals.get("recruiter_response_rate", 0.0) or 0.0
    interview_completion = signals.get("interview_completion_rate", 0.5) or 0.5

    oar = signals.get("offer_acceptance_rate", -1)
    offer_component = 0.5 if oar is None or oar < 0 else oar

    verif = (
        (1 if signals.get("verified_email") else 0)
        + (1 if signals.get("verified_phone") else 0)
        + (1 if signals.get("linkedin_connected") else 0)
    ) / 3.0

    return (
        0.32 * recency + 0.10 * open_flag + 0.28 * response
        + 0.15 * interview_completion + 0.10 * offer_component + 0.05 * verif
    )


def compute_experience_band_score(yoe):
    if cfg.TARGET_YOE_MIN <= yoe <= cfg.TARGET_YOE_MAX:
        return 1.0
    if yoe < cfg.TARGET_YOE_MIN:
        return max(0.0, 1.0 - (cfg.TARGET_YOE_MIN - yoe) / cfg.TARGET_YOE_MIN)
    return max(0.0, 1.0 - (yoe - cfg.TARGET_YOE_MAX) / 12.0)


def extract_features(candidate):
    profile = candidate["profile"]
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})

    skill_dict = _skill_lookup(skills)
    assess = signals.get("skill_assessment_scores", {})

    summary_text = f"{profile.get('headline','')} {profile.get('summary','')}"

    ml_years = compute_ml_role_years(career, summary_text)

    # years of ml-relevant experience accrued before 2023 (pre-LLM-hype era)
    pre2023 = 0.0
    for ch in career:
        sd = _parse_date(ch.get("start_date"))
        if sd and sd.year < 2023 and _title_category(ch.get("title")) in ("ai_ml_core", "adjacent_tech"):
            pre2023 += (ch.get("duration_months", 0) or 0) / 12.0

    retrieval_evid = _category_evidence(skill_dict, assess, cfg.RETRIEVAL_EMBEDDING_SKILLS)
    vectordb_evid = _category_evidence(skill_dict, assess, cfg.VECTOR_DB_SKILLS)
    eval_evid = _category_evidence(skill_dict, assess, cfg.EVAL_FRAMEWORK_SKILLS)
    python_evid = _category_evidence(skill_dict, assess, cfg.PYTHON_ML_STACK_SKILLS)
    must_have_score = (
        0.30 * retrieval_evid + 0.30 * vectordb_evid + 0.20 * eval_evid + 0.20 * python_evid
    )

    finetune_evid = _category_evidence(skill_dict, assess, cfg.LLM_FINETUNE_SKILLS)
    github = signals.get("github_activity_score", -1) or -1
    github_bonus = max(0.0, github) / 100.0
    industries = {(ch.get("industry") or "").strip().lower() for ch in career}
    companies = {(ch.get("company") or "").strip().lower() for ch in career}
    companies.add((profile.get("current_company") or "").strip().lower())
    hr_marketplace_bonus = 1.0 if (industries & cfg.HR_MARKETPLACE_INDUSTRIES or companies & cfg.HR_MARKETPLACE_COMPANIES) else 0.0
    distributed_kw = {"kafka", "spark", "kubernetes", "docker", "microservices",
                       "grpc", "hadoop", "apache beam", "apache flink", "kubeflow"}
    dist_evid = _category_evidence(skill_dict, assess, distributed_kw)
    nice_score = 0.35 * finetune_evid + 0.25 * github_bonus + 0.20 * hr_marketplace_bonus + 0.20 * dist_evid

    title_cat = _title_category(profile.get("current_title"))
    title_multiplier = {"ai_ml_core": 1.0, "adjacent_tech": 0.85, "non_tech": 0.5}[title_cat]
    title_role_fit = min(1.0, ml_years / cfg.TARGET_ML_YOE) * title_multiplier

    consulting_only = detect_consulting_only(career, profile.get("current_company"))
    narrow_cv = detect_narrow_cv_speech(skill_dict, assess)
    langchain_only = detect_langchain_only_recent(skill_dict, pre2023)
    pure_research = detect_pure_research_signal(summary_text)
    closed_source_weak = (
        profile.get("years_of_experience", 0) >= 5
        and github == -1
        and not candidate.get("certifications")
    )

    return {
        "candidate_id": candidate["candidate_id"],
        "profile": profile,
        "skill_dict": skill_dict,
        "must_have_score": must_have_score,
        "retrieval_evid": retrieval_evid,
        "vectordb_evid": vectordb_evid,
        "eval_evid": eval_evid,
        "python_evid": python_evid,
        "nice_score": nice_score,
        "finetune_evid": finetune_evid,
        "title_role_fit": title_role_fit,
        "title_category": title_cat,
        "ml_years": ml_years,
        "experience_band_score": compute_experience_band_score(profile.get("years_of_experience", 0)),
        "location_score": compute_location_score(profile, signals),
        "notice_score": compute_notice_score(signals),
        "availability_score": compute_availability_score(signals),
        "consulting_only": consulting_only,
        "narrow_cv_speech": narrow_cv,
        "langchain_only_recent": langchain_only,
        "pure_research_signal": pure_research,
        "closed_source_weak": closed_source_weak,
        "signals": signals,
    }
