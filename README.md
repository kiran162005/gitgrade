# 📊 GitGrade — Hybrid Heuristic + LLM GitHub Repository Evaluator

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.1-orange)
![Free Tier](https://img.shields.io/badge/Cost-Free%20Tier%20Only-brightgreen)

## 🌐 Live Demo
🔗 https://gitgrade-pqs4ynji9jj9xyidsbnjvz.streamlit.app/

## 🔍 Problem Statement
A GitHub repository reflects a developer's real skills, but it's hard to know
how a project actually reads from a recruiter or mentor's perspective —
whether the structure, documentation, and code quality are actually solid,
or just look busy from the commit graph.

GitGrade evaluates a public GitHub repository and turns it into a **score,
file-grounded code review, and an actionable improvement roadmap** — built
entirely on free-tier services, so anyone can run it without a credit card.

Originally built for the GitGrade Hackathon (UnsaidTalks Education).

---

## 📑 Table of Contents
- [Architecture](#-architecture)
- [What GitGrade Does](#-what-gitgrade-does)
- [Example Output](#-example-output)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)
- [Running Locally](#-running-locally)
- [Honest Notes & Limitations](#-honest-notes--limitations)
- [Roadmap / Future Work](#-roadmap--future-work)

---

## 🏗️ Architecture

GitGrade runs in two layers:

### 1. Heuristic layer (deterministic, instant, free)
Weighted scoring across six categories, each on a graduated 0–1 completeness
ratio rather than a flat yes/no check:

| Category | Weight | What it measures |
|---|---|---|
| Documentation | 20 | README existence *and* length/depth |
| Commit Quality | 20 | Commit count + message quality (penalizes "fix", "wip") |
| Test Coverage | 20 | Presence of a test directory |
| Tech Stack Depth | 15 | Number of languages used, capped at a realistic ceiling |
| Project Structure | 15 | Top-level file/folder count as a structure proxy |
| Maintenance Activity | 10 | Recent commit volume |

### 2. LLM review layer (Groq, free tier)
The heuristic layer can score structure, but can't explain *why* a repo is
good or bad. GitGrade samples a ranked subset of the repo's actual files
(entry points, README, tests, and other high-signal files, capped to a token
budget) and sends that code to Llama 3.1 via Groq's free API. The model
returns strengths, weaknesses, and a roadmap where **every claim is tied to
a specific file path** — not a generic verdict.

If `GROQ_API_KEY` isn't set, or the LLM call fails for any reason, GitGrade
automatically falls back to the heuristic-only review. The app never breaks
because of the LLM layer — it degrades gracefully.

```
GitHub URL
    │
    ▼
┌─────────────────┐      ┌──────────────────┐
│  github_client   │─────▶│   analyzer.py    │
│  (auth + fetch)  │      │ (repo metadata)   │
└─────────────────┘      └──────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                              ▼
          ┌──────────────────┐          ┌──────────────────┐
          │    scorer.py      │          │  file_sampler.py  │
          │ (heuristic score)  │          │ (ranked sampling) │
          └──────────────────┘          └──────────────────┘
                                                    │
                                                    ▼
                                          ┌──────────────────┐
                                          │  llm_analyzer.py  │
                                          │ (Groq, cited)      │
                                          └──────────────────┘
                                                    │
                                                    ▼
                                          cache.py (SHA-keyed)
```

### File sampling strategy
A repo can have thousands of files — you can't send all of it to an LLM.
Files are ranked by a scoring heuristic (entry-point names, README, test
files, mid-sized source files favored over huge dumps or tiny stubs) and
sampled until a small token budget is used. The budget is deliberately
conservative — tuned to stay well under Groq's free-tier rate limit (6,000
tokens/minute) with real headroom, after being adjusted against actual
`429`/`413` rate-limit errors hit during development.

### Caching
LLM results are cached locally, keyed by `owner/repo@commit-sha`.
Re-analyzing the same commit is instant and makes zero additional Groq API
calls — important given the free-tier rate limit.

### Auth & error handling
GitHub API calls support an optional `GITHUB_TOKEN` (raises the rate limit
from 60 requests/hour to 5,000/hour). Private repos, invalid URLs, empty
repos, and rate-limit hits all return clean, specific error messages instead
of a stack trace.

---

## 🎯 What GitGrade Does
Given a public GitHub repository URL, GitGrade:
- Fetches repository metadata via the GitHub REST API
- Scores six weighted, graduated categories (see architecture above)
- Samples real source files and runs an LLM code review grounded in them
- Produces a score, level, file-cited strengths/weaknesses, and a concrete roadmap
- Lets you download the full evaluation as a text report

---

## 📄 Example Output

```
Overall Score: 70/100        Level: Advanced
Real-World Fit: Medium       Review Mode: LLM-grounded

Score Breakdown
  Documentation ........ 20 / 20
  Commit Quality ....... 16 / 20
  Test Coverage ......... 0 / 20
  Tech Stack Depth ..... 15 / 15
  Project Structure ..... 9 / 15
  Maintenance Activity . 10 / 10

Strengths
  ✅ Clear, well-structured README.md that covers features and stack
     📄 README.md
  ✅ Well-defined ESLint config with React + JS rules
     📄 client/eslint.config.js

Areas to Improve
  ⚠️ No tests exist for the drawing canvas component
     📄 client/src/App.jsx
  ⚠️ Commit history could be grouped into more meaningful commits
     📄 (git log)

Roadmap
  1. Write unit tests for the drawing canvas component
  2. Group related commits into smaller, meaningful units
  3. List project dependencies explicitly in the README
```

---

## 📁 Project Structure

```
gitgrade/
├── app.py              # Streamlit UI, orchestrates the full flow
├── github_client.py     # Authenticated GitHub API calls + error handling
├── analyzer.py           # Repo metadata + real-world relevance heuristic
├── scorer.py              # Weighted, graduated heuristic scoring
├── file_sampler.py         # Ranks + samples files within a token budget
├── llm_analyzer.py          # Groq API call, JSON parsing, file-grounded review
├── roadmap.py                 # Heuristic fallback strengths/weaknesses/roadmap
├── cache.py                     # Local JSON cache, keyed by repo + commit SHA
├── requirements.txt
└── README.md
```

---

## ⚙️ Tech Stack
- **App/UI:** Streamlit
- **GitHub data:** GitHub REST API (authenticated, graceful rate-limit handling)
- **LLM review:** Groq API, Llama 3.1 8B Instant (free tier)
- **Caching:** local JSON cache keyed by repo + commit SHA
- **Language:** Python 3.9+

---

## 🚀 Running Locally

```bash
git clone https://github.com/kiran162005/gitgrade.git
cd gitgrade
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Set your API keys as environment variables before launching (both are free
to obtain, and both are optional — the app runs in heuristic-only mode
without them):

```powershell
$env:GITHUB_TOKEN="your_github_personal_access_token"     # optional, raises rate limit
$env:GROQ_API_KEY="your_groq_api_key"                      # optional, enables LLM review
streamlit run app.py
```

- GitHub token: https://github.com/settings/tokens (classic, no scopes needed for public repos)
- Groq API key (free tier): https://console.groq.com/keys

---

## 📌 Honest Notes & Limitations
- The heuristic score is a signal, not a certification — it reflects
  observable repo hygiene, not code correctness.
- The LLM review reads a *sample* of files, not the entire repository, to
  stay within the free-tier token budget. For very large repos, some files
  won't be seen by the model, and the sampling heuristic could occasionally
  miss a relevant file.
- The LLM sometimes attributes a weakness (e.g. "no tests exist") to a file
  like `README.md` rather than the actual absence of a test directory —
  reasonable, but worth knowing the citation isn't always the literal source
  of evidence.
- Built and tuned against real constraints during development — including
  Groq's live rate limits and a broken numpy build encountered on Windows —
  rather than only tested against a clean demo environment.

## 🔭 Roadmap / Future Work
- Persist cache in a lightweight database instead of a local JSON file, for
  multi-user deployments
- Add per-IP rate limiting on the deployed app to protect the shared Groq
  quota from abuse
- Expand file sampling to include a lightweight AST-based ranking instead of
  filename/size heuristics alone
- Add authenticated GitHub OAuth flow so users can analyze their own private
  repos
