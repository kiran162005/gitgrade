import os
import streamlit as st

from analyzer import analyze_repo, assess_real_world_relevance
from scorer import calculate_score
from roadmap import generate_roadmap
from github_client import parse_repo_url, GitGradeError
from file_sampler import sample_repo_files
from llm_analyzer import generate_llm_review, LLMUnavailableError
import cache


st.set_page_config(
    page_title="GitGrade",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; max-width: 1100px; }
    div[data-testid="stMetric"] {
        background: rgba(128,128,128,0.08);
        border: 1px solid rgba(128,128,128,0.15);
        border-radius: 10px;
        padding: 14px 18px;
    }
    div[data-testid="stMetricValue"] {
        white-space: normal;
        overflow: visible;
        font-size: 1.4rem;
        line-height: 1.3;
    }
    div[data-testid="stExpander"] { border-radius: 10px; }
    .gg-evidence {
        font-size: 0.8rem;
        opacity: 0.65;
        margin-top: -6px;
        margin-bottom: 10px;
    }
    .gg-card {
        border-left: 3px solid rgba(128,128,128,0.3);
        padding: 6px 12px;
        margin-bottom: 10px;
    }
    .gg-card.strength { border-left-color: #2ecc71; }
    .gg-card.weakness { border-left-color: #e67e22; }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.title("📊 GitGrade")
st.caption("Repository evaluation engine — deterministic scoring layer + LLM code review grounded in your actual source files")

llm_configured = bool(os.environ.get("GROQ_API_KEY"))
if not llm_configured:
    st.sidebar.warning(
        "GROQ_API_KEY not set — running in heuristic-only mode. "
        "Add a free Groq API key as an environment variable to enable "
        "LLM-grounded code review."
    )

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Analysis Options")

repo_url = st.sidebar.text_input(
    "🔗 GitHub Repository URL",
    placeholder="https://github.com/user/repo"
)

show_breakdown = st.sidebar.checkbox("Show Score Breakdown", value=True)
show_strengths = st.sidebar.checkbox("Show Strengths & Weaknesses", value=True)
show_roadmap = st.sidebar.checkbox("Show Improvement Roadmap", value=True)
use_llm = st.sidebar.checkbox(
    "Use LLM code review", value=llm_configured, disabled=not llm_configured
)

score_format = st.sidebar.radio(
    "Score Format",
    ["Numeric (0–100)", "Level Only"],
    horizontal=True
)

analyze_btn = st.sidebar.button("🚀 Analyze Repository")

if "gg_result" not in st.session_state:
    st.session_state.gg_result = None

# ---------------- RUN ANALYSIS (computation only, on click) ----------------
if analyze_btn:
    if not repo_url:
        st.warning("Please enter a GitHub repository URL.")
    else:
        try:
            with st.spinner("Fetching repository data..."):
                data = analyze_repo(repo_url)
                owner, repo_name = parse_repo_url(repo_url)

            score, level, breakdown = calculate_score(data)
            heuristic_strengths, heuristic_weaknesses, heuristic_roadmap = generate_roadmap(data)
            relevance_level, relevance_signals = assess_real_world_relevance(data)

            llm_result = None
            llm_error = None

            if use_llm:
                cache_key = cache.make_key(owner, repo_name, data.get("latest_sha"))
                cached = cache.get(cache_key)

                if cached:
                    llm_result = cached
                    st.toast("Loaded LLM review from cache — no new API call made.", icon="⚡")
                else:
                    with st.spinner("Sampling source files and running LLM review..."):
                        try:
                            sampled_files = sample_repo_files(
                                owner, repo_name, data["default_branch"]
                            )
                            llm_result = generate_llm_review(data, sampled_files)
                            cache.set(cache_key, llm_result)
                        except LLMUnavailableError as e:
                            llm_error = str(e)

            st.session_state.gg_result = {
                "owner": owner, "repo_name": repo_name, "data": data,
                "score": score, "level": level, "breakdown": breakdown,
                "heuristic_strengths": heuristic_strengths,
                "heuristic_weaknesses": heuristic_weaknesses,
                "heuristic_roadmap": heuristic_roadmap,
                "relevance_level": relevance_level, "relevance_signals": relevance_signals,
                "llm_result": llm_result, "llm_error": llm_error,
            }
        except GitGradeError as e:
            st.session_state.gg_result = None
            st.error(f"Couldn't analyze this repository: {e}")
        except Exception as e:
            st.session_state.gg_result = None
            st.error(f"Unexpected error while analyzing this repository: {e}")

# ---------------- RENDER (every rerun, reads from session_state) ----------------
r = st.session_state.gg_result

if r is None:
    st.markdown("## 👋 Welcome to GitGrade")
    st.write(
        """
        **GitGrade** evaluates GitHub repositories using two layers:
        cheap, deterministic heuristics (README, tests, commit history, tech
        stack) as a fast pre-filter, plus an LLM that reads a sampled set of
        your actual source files and grounds every strength/weakness in a
        specific file — not a generic vibe check.
        """
    )
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔍 What this tool analyzes")
        st.write(
            """
            - Code structure & organization
            - Documentation quality
            - Commit consistency
            - Test presence
            - Tech stack usage
            - Actual sampled source code (LLM mode)
            """
        )
    with col2:
        st.markdown("### 📤 What you get")
        st.write(
            """
            - 📊 Overall score & level
            - 🧠 Strengths and weaknesses, each tied to a real file
            - 🛣️ Concrete improvement roadmap
            - 📥 Downloadable evaluation report
            """
        )
    st.info("👉 Enter a GitHub repository URL in the sidebar and click **Analyze Repository** to begin.")

def render_results(r):
    try:
        owner, repo_name, data = r["owner"], r["repo_name"], r["data"]
        score, level, breakdown = r["score"], r["level"], r["breakdown"]
        heuristic_strengths = r["heuristic_strengths"]
        heuristic_weaknesses = r["heuristic_weaknesses"]
        heuristic_roadmap = r["heuristic_roadmap"]
        relevance_level, relevance_signals = r["relevance_level"], r["relevance_signals"]
        llm_result, llm_error = r["llm_result"], r["llm_error"]

        st.success(f"Analysis complete for **{owner}/{repo_name}**")

        # ---------------- SCORE CARD ----------------
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Score", f"{score}/100" if score_format == "Numeric (0–100)" else level.split()[0])
        m2.metric("Level", level.split()[0])
        m3.metric("Real-World Fit", relevance_level)
        m4.metric("Review Mode", "LLM" if llm_result else "Heuristic")

        if llm_result:
            st.markdown(f"> {llm_result.get('summary', '')}")

        st.divider()

        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown("#### 📊 Score Breakdown")
            if show_breakdown:
                max_points = {"Documentation": 20, "Commit Quality": 20, "Test Coverage": 20,
                              "Tech Stack Depth": 15, "Project Structure": 15, "Maintenance Activity": 10}

                bars_html = ""
                for k, v in breakdown.items():
                    cap = max_points.get(k, max(v, 1))
                    pct = int((v / cap) * 100) if cap else 0
                    bars_html += f"""
                    <div style="margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; font-size:0.85rem; margin-bottom:3px;">
                            <span>{k}</span><span>{v} / {cap}</span>
                        </div>
                        <div style="background:rgba(128,128,128,0.15); border-radius:6px; height:10px; overflow:hidden;">
                            <div style="background:#4c8bf5; width:{pct}%; height:100%; border-radius:6px;"></div>
                        </div>
                    </div>
                    """
                st.markdown(bars_html, unsafe_allow_html=True)

        with col2:
            st.markdown("#### 🧪 Repository Health")
            st.write(f"{'✅' if data['has_readme'] else '❌'}  README present")
            st.write(f"{'✅' if data['has_tests'] else '❌'}  Test coverage")
            st.write(f"{'✅' if data['languages'] else '❌'}  Tech stack defined")

            st.markdown("#### 🌍 Real-World Applicability")
            for signal in relevance_signals:
                st.write(f"• {signal}")

            st.markdown("#### 💻 Tech Stack")
            if data["languages"]:
                st.write(", ".join(data["languages"].keys()))
            else:
                st.write("No language data found.")

        st.divider()

        # ---------------- STRENGTHS & WEAKNESSES ----------------
        if show_strengths:
            st.markdown(
                "#### Code Review — " +
                ("LLM-grounded, cited to source files" if llm_result else "Heuristic signals")
            )
            col1, col2 = st.columns(2)

            if llm_result:
                with col1:
                    st.markdown("**✅ Strengths**")
                    for s in llm_result["strengths"]:
                        st.markdown(f'<div class="gg-card strength">{s["point"]}</div>'
                                    f'<div class="gg-evidence">📄 {s["evidence_file"]}</div>',
                                    unsafe_allow_html=True)
                with col2:
                    st.markdown("**⚠️ Areas to Improve**")
                    for w in llm_result["weaknesses"]:
                        st.markdown(f'<div class="gg-card weakness">{w["point"]}</div>'
                                    f'<div class="gg-evidence">📄 {w["evidence_file"]}</div>',
                                    unsafe_allow_html=True)
            else:
                if llm_error:
                    st.info(f"LLM review unavailable, showing heuristic results instead. ({llm_error})")
                with col1:
                    st.markdown("**✅ Strengths**")
                    for s in heuristic_strengths:
                        st.markdown(f'<div class="gg-card strength">{s}</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown("**⚠️ Areas to Improve**")
                    for w in heuristic_weaknesses:
                        st.markdown(f'<div class="gg-card weakness">{w}</div>', unsafe_allow_html=True)

            st.divider()

        # ---------------- ROADMAP ----------------
        if show_roadmap:
            st.markdown("#### 🛣️ Improvement Roadmap")
            roadmap_items = llm_result["roadmap"] if llm_result else heuristic_roadmap
            source_note = "Generated from your sampled source code" if llm_result else "Based on heuristic signals"
            st.caption(f"{source_note} · ordered by likely impact")
            for i, step in enumerate(roadmap_items, 1):
                st.markdown(f"**{i}.** {step}")

        # ---------------- DOWNLOAD REPORT ----------------
        strengths_text = (
            "\n".join(f"- {s['point']} (see {s['evidence_file']})" for s in llm_result["strengths"])
            if llm_result else "\n".join(heuristic_strengths)
        )
        weaknesses_text = (
            "\n".join(f"- {w['point']} (see {w['evidence_file']})" for w in llm_result["weaknesses"])
            if llm_result else "\n".join(heuristic_weaknesses)
        )
        roadmap_text = "\n".join(
            llm_result["roadmap"] if llm_result else heuristic_roadmap
        )

        report_text = f"""GitGrade Evaluation Report

        Repository: {owner}/{repo_name}
        Score: {score}/100
        Level: {level}
        Mode: {'LLM-grounded review' if llm_result else 'Heuristic-only review'}

        Strengths:
        {strengths_text}

        Weaknesses:
        {weaknesses_text}

        Roadmap:
        {roadmap_text}
        """
        st.download_button(
            "📥 Download Evaluation Report",
            report_text,
            file_name="gitgrade_report.txt"
        )

        st.caption(
            "Heuristic scores reflect deterministic signals (README, tests, commits, "
            "tech stack). When LLM review is enabled, strengths/weaknesses/roadmap are "
            "generated by reading a sampled subset of your actual source files."
        )

    except Exception as e:
        st.error(f"Something went wrong while rendering results: {e}")
        st.exception(e)

if r is not None:
    render_results(r)