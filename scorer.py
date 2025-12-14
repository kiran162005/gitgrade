def calculate_score(data):
    breakdown = {
        "Code Quality & Structure": 0,
        "Documentation": 0,
        "Commits & Consistency": 0,
        "Tests & Maintainability": 0,
        "Tech Stack Usage": 0,
    }

    # Documentation
    if data["has_readme"]:
        breakdown["Documentation"] = 15

    # Tests
    if data["has_tests"]:
        breakdown["Tests & Maintainability"] = 15

    # Commits
    commit_count = len(data["commits"])
    if commit_count > 20:
        breakdown["Commits & Consistency"] = 20
    elif commit_count > 5:
        breakdown["Commits & Consistency"] = 10

    # Tech stack
    if len(data["languages"]) > 0:
        breakdown["Tech Stack Usage"] = 15

    # Structure
    if len(data["contents"]) > 5:
        breakdown["Code Quality & Structure"] = 15

    score = sum(breakdown.values())

    if score < 40:
        level = "Beginner 🔴"
    elif score < 70:
        level = "Intermediate 🟡"
    else:
        level = "Advanced 🟢"

    return score, level, breakdown
