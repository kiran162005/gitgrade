"""
github_client.py

Handles all communication with the GitHub REST API:
- Token-authenticated requests (5,000 req/hr instead of 60/hr unauthenticated)
- Repo metadata, commits, languages, README
- Recursive file tree + selective file content fetching
- Clean, typed errors instead of raw exceptions / silent failures
"""

import os
import base64
import requests


class GitGradeError(Exception):
    """Base class for all GitGrade-specific errors shown to the user."""
    pass


class InvalidRepoURLError(GitGradeError):
    pass


class RepoNotFoundError(GitGradeError):
    pass


class RepoAccessError(GitGradeError):
    """Raised for private repos, rate limits, or other access issues."""
    pass


class EmptyRepoError(GitGradeError):
    pass


def _headers():
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url, params=None):
    resp = requests.get(url, headers=_headers(), params=params, timeout=15)
    if resp.status_code == 404:
        raise RepoNotFoundError(
            "Repository not found. Check the URL, or it may be private."
        )
    if resp.status_code == 403:
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining == "0":
            raise RepoAccessError(
                "GitHub API rate limit reached. Try again later, or set a "
                "GITHUB_TOKEN environment variable for a higher limit."
            )
        raise RepoAccessError(
            "Access denied by GitHub. The repository may be private."
        )
    resp.raise_for_status()
    return resp


def parse_repo_url(repo_url):
    cleaned = repo_url.strip().rstrip("/")
    if "github.com/" not in cleaned:
        raise InvalidRepoURLError(
            "That doesn't look like a GitHub URL. Expected format: "
            "https://github.com/owner/repo"
        )
    parts = cleaned.split("github.com/")[-1].split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise InvalidRepoURLError(
            "Couldn't parse an owner/repo pair from that URL."
        )
    return parts[0], parts[1]


def fetch_repo_data(repo_url):
    """Fetch metadata, commits, languages, README flag, and top-level contents."""
    owner, repo = parse_repo_url(repo_url)
    base = f"https://api.github.com/repos/{owner}/{repo}"

    data = {"owner": owner, "repo_name": repo}

    data["repo"] = _get(base).json()

    if data["repo"].get("size", 0) == 0:
        raise EmptyRepoError("This repository appears to be empty.")

    contents_resp = _get(f"{base}/contents")
    data["contents"] = contents_resp.json() if contents_resp.status_code == 200 else []

    commits_resp = requests.get(f"{base}/commits", headers=_headers(), timeout=15)
    commits = commits_resp.json() if commits_resp.status_code == 200 else []
    data["commits"] = commits if isinstance(commits, list) else []

    data["languages"] = _get(f"{base}/languages").json()

    readme_resp = requests.get(f"{base}/readme", headers=_headers(), timeout=15)
    data["has_readme"] = readme_resp.status_code == 200
    data["readme_size"] = readme_resp.json().get("size", 0) if data["has_readme"] else 0

    data["commit_messages"] = [
        c.get("commit", {}).get("message", "") for c in data["commits"] if isinstance(c, dict)
    ]

    data["has_tests"] = any(
        isinstance(item, dict) and item.get("name", "").lower() in
        ["test", "tests", "__tests__", "spec"]
        for item in data["contents"]
    )

    data["default_branch"] = data["repo"].get("default_branch", "main")
    data["latest_sha"] = data["commits"][0]["sha"] if data["commits"] else None

    return data


def fetch_file_tree(owner, repo, branch):
    """Fetch the full recursive file tree for the repo (paths + sizes only)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}"
    resp = _get(url, params={"recursive": "1"})
    tree = resp.json().get("tree", [])
    return [item for item in tree if item.get("type") == "blob"]


def fetch_file_content(owner, repo, path, ref):
    """Fetch and decode the text content of a single file. Returns None on failure."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        resp = requests.get(url, headers=_headers(), params={"ref": ref}, timeout=15)
        if resp.status_code != 200:
            return None
        payload = resp.json()
        if payload.get("encoding") != "base64":
            return None
        raw = base64.b64decode(payload["content"])
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return None