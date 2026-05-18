

# ArgusScorer:

**A rigorous check on your logic, evidence, and clarity. Because sounding smart isn't enough — you actually have to make sense.**

---

## 🚀 What is this?

Most writing tools are obsessed with grammar and style. They tell you to swap "very" for "extremely" and fix your commas. **ArgusScorer is different.**

We focus on the **substance**. It dissects your argument to find the holes in your logic, the weakness in your evidence, and the bias in your perspective.

Think of it as a debate partner who doesn't hold back — pointing out exactly where your reasoning falls apart before a real audience does.

---

## ✨ Why use it?

If you are writing an essay, prepping for a debate, or drafting a research paper, you need more than just "spell check." You need to know if your argument actually holds water.

**This project is built to be the "tough love" you need.** It won't compliment your vocabulary if your conclusion doesn't follow from your premises.

---

## 🛠️ Core Features

### 1. The Scorecard
Paste your text, and we’ll break it down into 5 dimensions:
*   **Logic:** Do your conclusions actually make sense?
*   **Evidence:** Did you cite real studies, or just make claims?
*   **Clarity:** Is your structure easy to follow?
*   **Depth:** Did you consider counter-arguments?
*   **Bias:** Are you being fair to the other side?

**The twist:** It quotes your exact words to show you *why* you got a low score. No vague feedback.

### 2. The Auto-Strengthener
If your score is low, hit the **Strengthen** button.
*   The AI rewrites your argument to meet a higher standard.
*   It adds concrete evidence, fixes logical gaps, and addresses counter-claims.
*   **Transparency:** It shows you the "Before vs. After" and explains exactly what changed.

### 3. Head-to-Head Comparison
Have two versions of an argument? Paste both.
*   We score them simultaneously.
*   You get a "Judge's Verdict" on which one is stronger and why.

### 4. Debate Mode
Don't agree with the score?
*   Jump into a chat with the AI.
*   Challenge the feedback ("Why is my evidence weak?").
*   It defends its reasoning or concedes if you have a point.

---

## 🧠 Under the Hood

We kept the stack modern but simple. No heavy frameworks, just solid tools that work.

| Component | Technology | Why? |
| :--- | :--- | :--- |
| **Backend** | Python (Flask) | Lightweight and easy to deploy. |
| **Database** | SQLite | Zero configuration. Saves your history locally. |
| **AI Brain** | Groq (Llama 3.3) | Incredibly fast (10x faster than GPT-4). |
| **Frontend** | React 18 | Clean, responsive, and interactive UI. |

### The Flow
```text
Your Browser → Flask Server → Groq AI → Result
                        ↓
                   SQLite (Saves History)
```

---

## 🏃‍♂️ Getting Started (It's quick)

You don't need a PhD to run this. Just Python and an API key.

**1. Prerequisites**
*   Python 3.8 or higher.
*   A free **Groq API Key** ([Get it here](https://console.groq.com/keys) — takes 30 seconds).

**2. Install & Run**
Open your terminal in the project folder:

```bash
# Install the libraries
pip install -r requirements.txt

# Add your key to a .env file
echo "GROQ_API_KEY=gsk_your_actual_key_here" > .env

# Start the server
python app.py
```

**3. Open the App**
Go to `http://localhost:5000` in your browser. That's it.

---

## 📂 Project Structure

Everything you need is right here.

```text
argus-scorer/
├── app.py              # The brain: Handles API routes and logic
├── database.py         # The memory: Manages SQLite
├── index.html          # The face: React frontend UI
├── requirements.txt    # The list: Dependencies
├── .env                # The secret: Your API key (don't share this!)
└── argus_scorer.db     # The data: Auto-created database file
```

---

## ⚖️ How the AI Judges

The scorer follows a strict rulebook. It doesn't guess.

*   **No named studies?** → Evidence score gets capped at 3/10.
*   **Weak causal reasoning?** → Logic score gets capped at 4/10.
*   **Ignoring the other side?** → Bias is automatically marked "High".
*   **Short content?** → Depth score drops significantly.

**The Goal:** To force you to think deeper, not just write prettier.

---

## 📌 API Endpoints

If you are a developer looking to tinker:

*   `POST /api/score` — Analyze a single argument.
*   `POST /api/strengthen` — Rewrite an argument to improve it.
*   `POST /api/compare` — Compare two arguments side-by-side.
*   `POST /api/debate` — Chat with the AI about your score.
*   `GET /api/history` — Retrieve your past evaluations.

---

## 🚧 The Fine Print (Limitations)

*   **Rate Limits:** The free Groq tier is fast but has limits. If you spam the "Score" button, you might hit a pause.
*   **Hallucinations:** In "Strengthen" mode, the AI might invent a study name to make a point. **Always verify** real-world facts.
*   **Local History:** Currently, history is stored locally on the machine running the server.

---

## 🌐 Deployment

Want to put this online for free?

1.  Push this code to GitHub.
2.  Create a free account on [Render.com](https://render.com).
3.  Connect your repo.
4.  Add `GROQ_API_KEY` in the environment variables.
5.  Click Deploy.

---

## 👋 Credits

Built to explore how AI can help us think more critically, not just write faster.

**Tech Stack:** Groq · Llama 3.3 · Flask · React · SQLite

---

*Made for thinkers, writers, and anyone who hates bad arguments.*
