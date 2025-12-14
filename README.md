# 📊 GitGrade – AI-Powered GitHub Repository Evaluator

## 🌐 Live Demo
🔗 **Deployed Application:**  
https://gitgrade-pqs4ynji9jj9xyidsbnjvz.streamlit.app/

## 🔍 Problem Statement
A GitHub repository reflects a developer’s real skills, but many students don’t know
how their projects look from a **recruiter or mentor’s perspective**.

**GitGrade** is an AI mentor-style system that evaluates a public GitHub repository
and converts it into a meaningful **Score, Summary, and Personalized Roadmap**.

This project is built for the **GitGrade Hackathon (UnsaidTalks Education)**.

---

## 🎯 What GitGrade Does
Given a **public GitHub repository URL**, GitGrade:

- Fetches repository data using GitHub’s public API
- Analyzes real-world engineering signals such as:
  - Project structure
  - Documentation presence
  - Commit history
  - Test availability
  - Tech stack usage
  - Real-world applicability
- Provides honest, actionable feedback like an **AI coding mentor**

---

## ⚙️ Key Features

### 📊 Repository Evaluation
- File & folder structure analysis
- README and documentation checks
- Commit consistency analysis
- Test folder detection
- Tech stack identification

### 🧮 Scoring System
- Overall score (0–100)
- Developer level: Beginner / Intermediate / Advanced
- Transparent category-wise breakdown

### 🧠 AI Mentor Feedback
- Strengths & weaknesses
- Clear written summary
- Personalized improvement roadmap

### 🌍 Real-World Applicability
- Evaluates whether the project is a learning exercise or a real-world usable system
- Explains the reasoning using observable repository signals

### 🌐 Web Interface
- Clean and simple UI built using **Streamlit**
- Easy to use for students, mentors, and recruiters

---

## 🛠️ Tech Stack
- **Python**
- **Streamlit**
- **GitHub REST API**
- **Requests**

---

## 🧩 Approach

1. User enters a GitHub repository URL
2. The system fetches public repository data
3. Heuristic-based analysis is applied across multiple dimensions
4. A score, summary, and roadmap are generated
5. Results are displayed in a clean web dashboard

> ⚠️ Note: This evaluation is heuristic-based and focuses on engineering signals,
not absolute correctness.

---

## ▶️ How to Run the Project

### 1️⃣ Install dependencies
```bash
pip install -r requirements.txt
