"""
cache.py

Free, dependency-free caching: a local JSON file keyed by "owner/repo@sha".
Re-analyzing the same repo at the same commit is instant and costs zero
extra GitHub/LLM calls. No database, no paid service - just a file on disk.
"""

import json
import os
import threading

CACHE_PATH = os.path.join(os.path.dirname(__file__), ".gitgrade_cache.json")
_lock = threading.Lock()


def _load():
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data):
    try:
        with open(CACHE_PATH, "w") as f:
            json.dump(data, f)
    except OSError:
        pass  # cache is best-effort; never crash the app over a write failure


def make_key(owner, repo, sha):
    return f"{owner}/{repo}@{sha or 'nosha'}"


def get(key):
    with _lock:
        return _load().get(key)


def set(key, value):
    with _lock:
        data = _load()
        data[key] = value
        _save(data)