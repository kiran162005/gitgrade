"""
llm_analyzer.py

Turns sampled repo files into a genuinely code-grounded review using Groq's
free-tier Llama 3.1 API (same pattern as LegalLens). Every strength/weakness
the LLM returns is tied to a specific sampled file, so this isn't a vague
"AI vibe" verdict - it's reasoning over real code, citation-style.

If GROQ_API_KEY isn't set, or the call fails for any reason, callers fall
back to the pure heuristic roadmap - the app never breaks because of this.
"""

import os
import json
import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # fast + free-tier friendly


class LLMUnavailableError(Exception):
    pass


def _build_prompt(repo_meta, sampled_files):
    file_blocks = "\n\n".join(
        f"### File: {f['path']}\n```\n{f['content']}\n```" for f in sampled_files
    )

    return f"""You are a senior software engineer reviewing a GitHub repository for a
student's portfolio. Be honest and specific - do not flatter, do not invent
things that aren't in the code below.

Repository: {repo_meta.get('repo_name')}
Primary languages: {", ".join(repo_meta.get('languages', {}).keys()) or "unknown"}
Has README: {repo_meta.get('has_readme')}
Has tests: {repo_meta.get('has_tests')}
Commit count sampled: {len(repo_meta.get('commits', []))}

Sampled files (not the full repo - a representative subset):
{file_blocks}

Return ONLY valid JSON (no markdown fences, no preamble) with this exact shape:
{{
  "strengths": [{{"point": "short claim", "evidence_file": "path/to/file.py"}}],
  "weaknesses": [{{"point": "short claim", "evidence_file": "path/to/file.py"}}],
  "roadmap": ["ordered, specific, actionable next step", "..."],
  "summary": "2-3 sentence honest overall verdict"
}}

Rules:
- Every strength and weakness must reference one of the sampled file paths above.
- 3-5 strengths, 3-5 weaknesses, 4-6 roadmap steps.
- Roadmap steps must be concrete (name the file, function, or pattern to add/change),
  not generic advice like "add more tests".
"""


def generate_llm_review(repo_meta, sampled_files):
    """
    Returns a dict with strengths/weaknesses/roadmap/summary, each grounded
    in specific sampled files. Raises LLMUnavailableError if it can't run.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise LLMUnavailableError("GROQ_API_KEY not set.")
    if not sampled_files:
        raise LLMUnavailableError("No files were sampled to analyze.")

    prompt = _build_prompt(repo_meta, sampled_files)

    try:
        resp = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 800,
            },
            timeout=30,
        )
    except Exception as e:
        raise LLMUnavailableError(f"Groq request failed: {e}")

    if resp.status_code != 200:
        snippet = resp.text[:200].replace("\n", " ")
        raise LLMUnavailableError(f"Groq returned HTTP {resp.status_code}: {snippet}")

    try:
        raw_text = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        snippet = resp.text[:200].replace("\n", " ")
        raise LLMUnavailableError(f"Couldn't read Groq response ({e}): {snippet}")

    # Models inconsistently wrap JSON in markdown fences (```json ... ``` or
    # variations) - extracting the outermost {...} block is more robust than
    # stripping fixed prefixes/suffixes.
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end < start:
        snippet = raw_text[:200].replace("\n", " ")
        raise LLMUnavailableError(f"No JSON object found in LLM output: {snippet}")

    json_block = raw_text[start:end + 1]
    try:
        parsed = json.loads(json_block)
    except Exception as e:
        snippet = json_block[:200].replace("\n", " ")
        raise LLMUnavailableError(f"LLM output wasn't valid JSON ({e}): {snippet}")

    for key in ("strengths", "weaknesses", "roadmap", "summary"):
        if key not in parsed:
            raise LLMUnavailableError("LLM response missing expected fields.")

    return parsed