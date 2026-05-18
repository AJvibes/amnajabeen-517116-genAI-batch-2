ArgusScorer — Argument Quality Scorer
A rigorous, unflattering evaluation of your reasoning — on logic, evidence, clarity, depth, and bias.
ArgusScorer is a full-stack web application that uses AI to analyze and score written arguments across five critical dimensions. It helps students, debaters, researchers and writers identify logical flaws, weak evidence, and bias in their reasoning — and then automatically rewrites their argument to a higher standard.
🖼️ Screenshots


Argument Scorer Interface:


Complete interface overview
Strengthen Argument

Visual workflow for strengthening arguments
Comparison Page

Argument comparison visuals
Scoring Result

Input argument and view generated score
Strengthen & Multi-Turn Debate

AI rewrites weak argument, then improves argument using multi-turn debate
Weak vs Strong Comparison

Analysis showing strength difference between arguments
🔍 What is ArgusScorer?
Most writing tools tell you how to write better — fix your grammar, vary your sentence length, add transitions. ArgusScorer does something different: it tells you why your reasoning is weak and gives you a score breakdown with specific, quoted evidence from your own argument.
It is built around a simple idea: a well-written argument is worthless if the logic is bad. ArgusScorer forces you to confront that.
Who is it for?
Students submitting essays, debate prep, or critical thinking assignments
Researchers stress-testing their claims before peer review
Debaters identifying weaknesses an opponent would exploit
Anyone who wants to think and write more rigorously
❓ Why This Project?
Most AI writing tools are designed to validate you. They suggest synonyms, improve flow, and make your writing sound more confident — regardless of whether your argument actually holds up.
ArgusScorer was built to do the opposite: to be the harshest, most honest reviewer you can have before a real audience sees your work. It evaluates reasoning quality, not surface-level writing quality.
The evaluation is also transparent — every weakness is quoted directly from your text, every score has a clickable explanation, and the "Strengthen" feature shows exactly what changed and why.
⚙️ How It Works
ArgusScorer is now a full-stack application — Flask backend with React frontend, SQLite database for persistence.
Tech Stack
Table
Layer	Technology
Backend	Flask + SQLite
AI Inference	Groq API — llama-3.3-70b-versatile
Frontend	React 18 (UMD via CDN)
Database	SQLite (file-based, zero config)
Styling	Inline CSS + Google Fonts
Build	None — open the file directly
Architecture
plain
Copy
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │ ←──→ │ Flask Server │ ←──→ │  Groq API   │
│  (React)    │      │  (Python)    │      │  (LLM)      │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ↓
                      ┌──────────────┐
                      │   SQLite     │
                      │  (History)   │
                      └──────────────┘
Why Groq?
Groq was chosen for two reasons:
Speed — approximately 10x faster than GPT-4 at inference
Free tier — no credit card required, generous rate limits for individual use
Why Flask + SQLite?
API key security — stays server-side in .env, never reaches browser
Persistent history — evaluations survive browser restarts and tab closures
Zero-config database — SQLite is file-based, no setup needed
Easy deployment — single command to run anywhere
🔄 Workflow / Feature Walkthrough
1. Score Tab (§ Score)
Input → Evaluate → Report
Paste or type your argument (10 – 8,000 characters)
Click → Score my argument
Receive a full report card:
Table
Dimension	What it measures
Logic	Are conclusions actually supported by the premises?
Evidence	Are there named studies, statistics, or concrete examples?
Clarity	Is the thesis identifiable? Is the structure followable?
Depth	Does it engage with counterarguments and nuance?
Bias	Does it acknowledge opposing views fairly?
Overall score = weighted average of all five dimensions (bias included as penalty)
Click any score bar to get a 2-3 sentence explanation of exactly why that score was given, with quotes from your text
Weaknesses section quotes your actual phrasing and names the logical flaw type
Improvement Points give concrete, actionable instructions targeting specific claims
Automatically saved to History (SQLite) — survives browser restarts
2. Strengthen Tab (✦ Strengthen)
Rewrite → Verify with Real Score
After scoring, click → Strengthen My Argument
The AI rewrites your argument specifically targeting the scoring rubric:
Adds named studies or documented real-world cases (evidence ≥ 6)
Makes causal chains explicit: If X then Y, because Z (logic ≥ 7)
Addresses counterarguments with reasoning, not dismissal (depth ≥ 7, bias → Low)
The improved argument is displayed side-by-side with your original
A second automatic API call re-scores the improved version with verified real scores — not AI estimates
Score changes are shown in green (improvement) or red (regression)
You can also use this tab without scoring first — paste any argument directly.
3. Compare Tab (⚖ Compare)
Head-to-head argument evaluation
Paste two arguments (yours vs. a peer's, two drafts, etc.)
Both are scored simultaneously in parallel API calls
A judge verdict is generated: which argument wins and why, in exactly 2 sentences
You can choose to save either argument to history or skip saving
4. History Tab (§ History)
Every scored argument is automatically saved to SQLite database
Up to 100 entries stored — survives browser restarts and server restarts
Click any entry to reload the full report
Source label shows whether it came from direct scoring or compare mode
Clear all history with one click
5. Debate Chat (⚔ Multi-Turn Debate)
After scoring, a debate panel appears below the report:
Challenge any weakness: "I disagree with weakness #1"
Dispute a score: "Why is my evidence score so low?"
Ask for improvement paths: "What would make this a 9/10?"
The AI has full context of your argument and scores. It will concede valid points and defend justified scores — no sycophancy.
🚀 Getting Started
Prerequisites
Python 3.8+
A free Groq API key: console.groq.com/keys — no credit card required
Quick Setup
bash
Copy
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/argus-scorer.git
cd argus-scorer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API key
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# 4. Run the server
python app.py

# 5. Open in browser
# http://localhost:5000
Alternative: Download ZIP (no git)
Download ZIP from GitHub
Extract folder
Open terminal in that folder
Follow steps 2-5 above
📁 Project Structure
plain
Copy
argus-scorer/
├── app.py              # Flask backend — API routes, Groq integration, scoring logic
├── database.py         # SQLite helpers for persistence
├── index.html          # React frontend — UI components, API calls
├── requirements.txt    # Python dependencies
├── .env                # API key (not tracked in git)
└── argus_scorer.db     # SQLite database (auto-created on first run)
🔌 API Endpoints
Table
Endpoint	Method	Description
/	GET	Serves the frontend
/api/score	POST	Score a single argument
/api/strengthen	POST	Rewrite & auto-rescore an argument
/api/compare	POST	Compare two arguments
/api/debate	POST	Multi-turn debate chat
/api/explain	POST	Explain a specific dimension score
/api/history	GET	Retrieve all past evaluations
/api/history/<id>	DELETE	Delete a specific history item
/api/history/save	POST	Manually save to history
🧠 Scoring Rubric (How the AI Judges)
The scorer uses a strict rule-based prompt. Key mandatory rules:
plain
Copy
No named studies or statistics        → evidence MUST be ≤ 3
Weak or absent causal reasoning       → logic MUST be ≤ 4
Only one perspective considered       → bias CANNOT be "Low"
Sweeping generalizations              → bias = "High"
Short or underdeveloped argument      → depth MUST be ≤ 4
Every weakness must quote or paraphrase a specific phrase from the argument and name the exact logical flaw type (e.g., hasty generalization, circular reasoning, appeal to popularity).
🛠️ Known Limitations
Groq rate limits — free tier has request limits; heavy use may hit them
No user accounts — history is shared across all users of the same instance
Model hallucination — AI may cite plausible-sounding but non-existent studies in Strengthen output. Always verify
SQLite concurrency — not ideal for high-traffic production; switch to PostgreSQL for scale
🌐 Deployment
Free Hosting (Render)
Push code to GitHub
Connect repo at render.com
Set Build Command: pip install -r requirements.txt
Set Start Command: python app.py
Add environment variable: GROQ_API_KEY
Deploy — get a public URL
Docker (Optional)
dockerfile
Copy
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
🔒 Security Notes
Never commit .env — it contains your API key
All Groq calls are server-side — key never reaches the browser
SQLite database is local — no external DB needed for single-instance deploys
CORS is enabled for development; restrict origins in production
📄 License
MIT — free to use, modify, and deploy.
👤 Author
Developed as a coursework project.
Powered by Groq · Llama 3.3 70B · Flask · React 18
