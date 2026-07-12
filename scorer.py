"""
scorer.py

Graduated, weighted scoring instead of flat yes/no checks. Each category is
scored on a 0-1 completeness ratio against realistic thresholds, then scaled
to its weight. This is the deterministic pre-filter layer - fast, free,
and designed to feel earned rather than arbitrary.
"""

WEIGHTS = {
    "Documentation": 20,
    "Commit Quality": 20,
    "Test Coverage": 20,
    "Tech Stack Depth": 15,
    "Project Structure": 15,
    "Maintenance Activity": 10,
}


def _clamp(ratio):
    return max(0.0, min(1.0, ratio))


def calculate_score(data):
    breakdown = {}

    # --- Documentation: graduated by README length, not just existence ---
    readme_size = data.get("readme_size", 0)
    if not data["has_readme"]:
        doc_ratio = 0.0
    else:
        # 1500+ chars treated as a genuinely useful README
        doc_ratio = _clamp(readme_size / 1500)
        doc_ratio = max(doc_ratio, 0.25)  # having *a* README is worth something
    breakdown["Documentation"] = round(doc_ratio * WEIGHTS["Documentation"])

    # --- Commit Quality: count + message quality, not just count ---
    commit_messages = data.get("commit_messages", [])
    commit_count = len(commit_messages)
    count_ratio = _clamp(commit_count / 25)

    meaningful_msgs = [
        m for m in commit_messages
        if len(m.strip()) > 10 and m.strip().lower() not in ("update", "fix", "changes", "wip")
    ]
    quality_ratio = _clamp(len(meaningful_msgs) / max(commit_count, 1))

    commit_ratio = 0.6 * count_ratio + 0.4 * quality_ratio
    breakdown["Commit Quality"] = round(commit_ratio * WEIGHTS["Commit Quality"])

    # --- Test Coverage: presence only (API doesn't give us a real ratio without cloning) ---
    test_ratio = 1.0 if data["has_tests"] else 0.0
    breakdown["Test Coverage"] = round(test_ratio * WEIGHTS["Test Coverage"])

    # --- Tech Stack Depth: more languages = more integration complexity, up to a point ---
    lang_count = len(data.get("languages", {}))
    stack_ratio = _clamp(lang_count / 3)
    breakdown["Tech Stack Depth"] = round(stack_ratio * WEIGHTS["Tech Stack Depth"])

    # --- Project Structure: top-level file/folder count as a rough proxy ---
    content_count = len(data.get("contents", []))
    structure_ratio = _clamp(content_count / 8)
    breakdown["Project Structure"] = round(structure_ratio * WEIGHTS["Project Structure"])

    # --- Maintenance Activity: recent-looking commit volume ---
    activity_ratio = _clamp(commit_count / 15)
    breakdown["Maintenance Activity"] = round(activity_ratio * WEIGHTS["Maintenance Activity"])

    score = sum(breakdown.values())

    if score < 40:
        level = "Beginner 🔴"
    elif score < 70:
        level = "Intermediate 🟡"
    else:
        level = "Advanced 🟢"

    return score, level, breakdown