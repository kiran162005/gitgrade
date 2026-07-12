from github_client import fetch_repo_data, GitGradeError


def analyze_repo(repo_url):
    """Thin wrapper kept for backward compatibility - delegates to github_client,
    which handles auth, errors, and edge cases (private/empty/missing repos)."""
    return fetch_repo_data(repo_url)


def assess_real_world_relevance(data):
    score = 0
    signals = []

    repo_name = data["repo"].get("name", "").lower()

    real_world_keywords = [
        "api", "service", "dashboard", "system", "platform",
        "management", "ecommerce", "ml", "ai", "analysis"
    ]

    if any(word in repo_name for word in real_world_keywords):
        score += 1
        signals.append("Project name suggests real-world use case")

    if data["has_readme"]:
        score += 1
        signals.append("Documentation indicates intent for real usage")

    if len(data["languages"]) > 1:
        score += 1
        signals.append("Multiple technologies used")

    if len(data["contents"]) > 5:
        score += 1
        signals.append("Project has non-trivial structure")

    if score >= 3:
        level = "High"
    elif score == 2:
        level = "Medium"
    else:
        level = "Low"

    return level, signals