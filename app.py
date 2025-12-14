
import streamlit as st
from analyzer import analyze_repo
from scorer import calculate_score
from roadmap import generate_roadmap
from analyzer import assess_real_world_relevance


st.set_page_config(
    page_title="GitGrade",
    page_icon="📊",
    layout="wide"
)

# ---------------- HEADER ----------------
st.title("📊 GitGrade")
st.caption("AI + Code Analysis + Developer Profiling")

# ---------------- SIDEBAR ----------------
st.sidebar.header("⚙️ Analysis Options")

repo_url = st.sidebar.text_input(
    "🔗 GitHub Repository URL",
    placeholder="https://github.com/user/repo"
)

show_breakdown = st.sidebar.checkbox("Show Score Breakdown", value=True)
show_strengths = st.sidebar.checkbox("Show Strengths & Weaknesses", value=True)
show_roadmap = st.sidebar.checkbox("Show Personalized Roadmap", value=True)

score_format = st.sidebar.radio(
    "Score Format",
    ["Numeric (0–100)", "Level Only"],
    horizontal=True
)

analyze_btn = st.sidebar.button("🚀 Analyze Repository")

# ---------------- WELCOME DASHBOARD ----------------
if not analyze_btn:
    st.markdown("## 👋 Welcome to GitGrade")

    st.write(
        """
        **GitGrade** is an AI mentor-style tool that evaluates GitHub repositories
        using real-world engineering signals — similar to how recruiters and mentors
        review projects.
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
            - Real-world project readiness
            """
        )

    with col2:
        st.markdown("### 📤 What you get")
        st.write(
            """
            - 📊 Overall score & level  
            - 🧠 Strengths and weaknesses  
            - 🛣️ Personalized improvement roadmap  
            - 📥 Downloadable evaluation report
            """
        )

    st.info("👉 Enter a GitHub repository URL in the sidebar and click **Analyze Repository** to begin.")


# ---------------- MAIN LOGIC ----------------
if analyze_btn:
    if not repo_url:
        st.warning("Please enter a GitHub repository URL.")
    else:
        with st.spinner("Analyzing repository..."):
            data = analyze_repo(repo_url)
            score, level, breakdown = calculate_score(data)
            strengths, weaknesses, roadmap = generate_roadmap(data)
            relevance_level, relevance_signals = assess_real_world_relevance(data)


        st.success("Analysis Complete ✅")

        # ---------------- SCORE CARD ----------------
        col1, col2 = st.columns([2, 1])

        with col1:
            if score_format == "Numeric (0–100)":
                st.markdown(f"## 📊 Score: **{score}/100**")
            st.markdown(f"### 🎯 Level: **{level}**")

        with col2:
            st.markdown("### 🧪 Repository Health")
            st.write(f"📄 README: {'✅' if data['has_readme'] else '❌'}")
            st.write(f"🧪 Tests: {'✅' if data['has_tests'] else '❌'}")
            st.write(f"💻 Tech Stack: {'✅' if data['languages'] else '❌'}")

            # ---------------- REAL-WORLD APPLICABILITY ----------------
            st.subheader("🌍 Real-World Applicability")

            st.markdown(f"**Relevance Level:** {relevance_level}")

            for signal in relevance_signals:
                st.write(f"- {signal}")


        st.divider()

        # ---------------- TECH STACK ----------------
        st.subheader("💻 Tech Stack Used")
        if data["languages"]:
            for lang, val in data["languages"].items():
                st.write(f"- {lang}")
        else:
            st.write("No language data found.")

        # ---------------- SCORE BREAKDOWN ----------------
        if show_breakdown:
            with st.expander("📊 Score Breakdown"):
                for k, v in breakdown.items():
                    st.write(f"{k}: {v}")

        # ---------------- STRENGTHS & WEAKNESSES ----------------
        if show_strengths:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("✅ Strengths")
                for s in strengths:
                    st.write(f"- {s}")

            with col2:
                st.subheader("⚠️ Areas to Improve")
                for w in weaknesses:
                    st.write(f"- {w}")

        # ---------------- ROADMAP ----------------
        if show_roadmap:
            st.subheader("🛣️ Personalized Improvement Roadmap")
            st.info(
                "This roadmap is generated in a mentor-style order, focusing on the most impactful improvements first."
            )
            for i, step in enumerate(roadmap, 1):
                st.write(f"{i}. {step}")

        # ---------------- DOWNLOAD REPORT ----------------
        report_text = f"""
GitGrade Evaluation Report

Score: {score}/100
Level: {level}

Strengths:
{chr(10).join(strengths)}

Weaknesses:
{chr(10).join(weaknesses)}

Roadmap:
{chr(10).join(roadmap)}
"""
        st.download_button(
            "📥 Download Evaluation Report",
            report_text,
            file_name="gitgrade_report.txt"
        )

        st.caption(
            "Note: This evaluation is heuristic-based and reflects real-world engineering review signals rather than absolute correctness."
        )
