import requests

def analyze_repo(repo_url):
    parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
    owner, repo = parts[0], parts[1]

    base = f"https://api.github.com/repos/{owner}/{repo}"

    data = {}

    data["repo"] = requests.get(base).json()
    data["contents"] = requests.get(f"{base}/contents").json()
    commits = requests.get(f"{base}/commits").json()
    data["commits"] = commits if isinstance(commits, list) else []
    data["languages"] = requests.get(f"{base}/languages").json()

    # README check
    readme = requests.get(f"{base}/readme")
    data["has_readme"] = readme.status_code == 200

    # Test folder check
    data["has_tests"] = any(
        item["name"].lower() in ["test", "tests", "__tests__"]
        for item in data["contents"]
    )

    return data

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
