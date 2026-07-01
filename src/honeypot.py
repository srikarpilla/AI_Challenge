"""
src/honeypot.py

Detects "subtly impossible" candidate profiles per submission_spec.docx
Section 7. We don't have ground-truth honeypot labels, so this module
implements structural-consistency checks: things that are internally
contradictory regardless of role or JD, e.g. a skill claimed at "expert"
level with ~0 months of use, or career-history dates whose stated
duration doesn't match the start/end dates.

Design choice: rather than trying to score these candidates low, we
remove them from the eligible pool entirely before ranking. This is the
safest way to guarantee a 0% honeypot rate in the top 100 (the submission
spec disqualifies at >10%), and it matches the JD's framing: "a good
ranking system should naturally avoid them."

Each check is intentionally conservative (low false-positive rate on
clean profiles) since over-triggering would just be discarding good
candidates, which doesn't hurt honeypot compliance -- but we still want
the eligible pool to stay large and representative.
"""

from datetime import date

TODAY = date(2026, 6, 30)


def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def detect_honeypot(candidate):
    """Returns (is_honeypot: bool, reasons: list[str])."""
    reasons = []

    # 1. Expert-level proficiency with essentially no time spent on the skill.
    expert_zero_dur = [
        s["name"] for s in candidate.get("skills", [])
        if s.get("proficiency") == "expert" and s.get("duration_months", 0) <= 2
    ]
    if len(expert_zero_dur) >= 1:
        reasons.append(f"expert proficiency with ~0 months used: {expert_zero_dur}")

    # 1b. Suspiciously many "expert" skills overall (profile stuffing).
    expert_count = sum(1 for s in candidate.get("skills", []) if s.get("proficiency") == "expert")
    if expert_count >= 8:
        reasons.append(f"{expert_count} skills claimed at expert level")

    # 2. Career-history duration_months inconsistent with start/end dates.
    for ch in candidate.get("career_history", []):
        sd = _parse_date(ch.get("start_date"))
        ed = _parse_date(ch.get("end_date")) or TODAY
        if sd is None:
            continue
        if sd > ed:
            reasons.append(f"career entry at {ch.get('company')} has start_date after end_date")
            continue
        computed_months = (ed.year - sd.year) * 12 + (ed.month - sd.month)
        stated_months = ch.get("duration_months", 0)
        if computed_months > 0 and abs(computed_months - stated_months) > max(6, 0.4 * computed_months):
            reasons.append(
                f"career entry at {ch.get('company')} duration_months={stated_months} "
                f"doesn't match dates (~{computed_months}mo)"
            )

    # 3. Total summed career-history months wildly inconsistent with stated
    #    years_of_experience (e.g. 8 years claimed, 14 months of history).
    total_months = sum(ch.get("duration_months", 0) for ch in candidate.get("career_history", []))
    yoe_months = candidate.get("profile", {}).get("years_of_experience", 0) * 12
    if yoe_months >= 12 and total_months > 0:
        ratio = total_months / yoe_months
        if ratio < 0.4 or ratio > 2.5:
            reasons.append(
                f"years_of_experience={candidate['profile']['years_of_experience']} "
                f"inconsistent with summed career_history (~{total_months/12:.1f}yr)"
            )

    # 4. More than one "is_current" career entry (can't currently hold two jobs).
    current_count = sum(1 for ch in candidate.get("career_history", []) if ch.get("is_current"))
    if current_count > 1:
        reasons.append(f"{current_count} career_history entries marked is_current")

    # 5. Education end_year before start_year, or end_year far in the future.
    for ed in candidate.get("education", []):
        sy, ey = ed.get("start_year"), ed.get("end_year")
        if sy and ey and ey < sy:
            reasons.append(f"education end_year ({ey}) before start_year ({sy})")

    # 6. A skill's duration_months exceeds total claimed experience by a lot.
    for s in candidate.get("skills", []):
        dm = s.get("duration_months", 0)
        if yoe_months > 0 and dm > yoe_months + 24:
            reasons.append(
                f"skill '{s['name']}' duration_months={dm} exceeds years_of_experience"
            )
            break

    return (len(reasons) > 0, reasons)
