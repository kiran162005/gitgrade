"""
file_sampler.py

A real repo can have thousands of files - you can't hand all of it to an LLM.
This module ranks files by how much signal they likely carry and fetches
just enough content to stay within a token budget.
"""

from github_client import fetch_file_tree, fetch_file_content

# Rough chars-per-token estimate for budgeting (no tokenizer dependency)
CHARS_PER_TOKEN = 4
# Groq's free tier caps at 6000 tokens/minute total (prompt + completion).
# Budget file content conservatively so prompt+completion stays well under that.
DEFAULT_TOKEN_BUDGET = 3000

ENTRY_POINT_NAMES = {
    "main.py", "app.py", "index.js", "index.ts", "server.py", "manage.py",
    "index.html", "main.go", "main.rs", "program.cs", "application.java",
}

SKIP_DIR_MARKERS = {
    "node_modules", "__pycache__", "venv", ".venv", "dist", "build",
    ".git", "vendor", "target", ".next", "coverage",
}

SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".ttf",
    ".lock", ".zip", ".tar", ".gz", ".pdf", ".mp4", ".mp3", ".exe",
    ".pyc", ".class", ".jar",
}

CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".cpp",
    ".c", ".cs", ".rb", ".php", ".swift", ".kt",
}


def _is_skippable(path):
    lower = path.lower()
    if any(f"/{marker}/" in f"/{lower}/" for marker in SKIP_DIR_MARKERS):
        return True
    if any(lower.endswith(ext) for ext in SKIP_EXTENSIONS):
        return True
    return False


def _score_file(item):
    """Higher score = more useful to sample. Pure heuristic ranking."""
    path = item["path"]
    name = path.rsplit("/", 1)[-1].lower()
    size = item.get("size", 0)
    score = 0

    if name in ENTRY_POINT_NAMES:
        score += 100
    if name == "readme.md":
        score += 90
    if "test" in path.lower() or "spec" in path.lower():
        score += 40
    if any(name.endswith(ext) for ext in CODE_EXTENSIONS):
        score += 30
    if "/" not in path:  # root-level files are often more structurally important
        score += 10

    # Mid-sized files tend to carry more real logic than tiny stubs or huge dumps
    if 200 <= size <= 20000:
        score += 15
    elif size > 50000:
        score -= 20

    return score


def sample_repo_files(owner, repo, branch, token_budget=DEFAULT_TOKEN_BUDGET):
    """
    Returns a list of {path, content} dicts for the highest-signal files
    that fit within the token budget.
    """
    try:
        tree = fetch_file_tree(owner, repo, branch)
    except Exception:
        return []

    candidates = [item for item in tree if not _is_skippable(item["path"])]
    candidates.sort(key=_score_file, reverse=True)

    char_budget = token_budget * CHARS_PER_TOKEN
    used_chars = 0
    sampled = []

    for item in candidates:
        if used_chars >= char_budget:
            break
        if len(sampled) >= 5:  # cap file count regardless of budget left
            break

        content = fetch_file_content(owner, repo, item["path"], branch)
        if not content:
            continue

        # Trim any single file so it can't eat the whole budget alone
        max_file_chars = 1400
        trimmed = content[:max_file_chars]

        sampled.append({"path": item["path"], "content": trimmed})
        used_chars += len(trimmed)

    return sampled