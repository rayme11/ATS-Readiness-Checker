# ATS Insight

> Open-source resume ATS readiness analyzer — free, local, transparent.

ATS Insight helps job seekers understand how their resumes may perform against
Applicant Tracking Systems (ATS) and recruiter screening.  
It runs **100 % locally on your machine** — no account required, no data sent externally.

Built and maintained by [Ray Maldonado](https://www.linkedin.com/in/rmaldonado)

> **Educational project.** This tool was built from scratch — idea to running app —
> to explore what an ATS readiness checker looks like under the hood, and how modern
> LLM models can be layered on top of rule-based analysis. See the
> [Disclaimer & Context](#disclaimer--context) section for the full story.

---

## Preview

![ATS Readiness Report — score card, category breakdown, strengths and risks](docs/screenshots/report-preview.png)

*Score card · Category breakdown · Strengths & risks · AI feedback panel*

---

## What It Does

Upload a resume (PDF, DOCX, or TXT), optionally paste a job description, and receive:

| Output | Description |
|---|---|
| **Overall ATS Score (0–100)** | Weighted composite across five categories |
| **Resume Structure** | Detects missing sections, contact info gaps |
| **Parsing Safety** | Flags multi-column layouts, symbols, tables |
| **Keyword Relevance** | Matches your resume terms against the JD |
| **Achievement Quality** | Checks for metrics and action verbs |
| **Recruiter Readability** | Location, bullet consistency, line length |
| **Recommendations** | Prioritised, practical improvement list |
| **AI Feedback** | Optional deeper narrative (Ollama, Groq, OpenAI, or Anthropic) |
| **LLM Suitability Panel** | Rates the active AI engine across 5 dimensions; compares all providers |

---

## Architecture

The diagram below shows how data flows through the app — from the file you upload
to the score and feedback you receive.  
Update this section whenever modules are added or the pipeline changes.

```mermaid
flowchart TD
    User(["👤 User"])

    subgraph UILayer["🖥️  UI — app/ui/"]
        Upload["upload_page.py\nUpload Resume · Paste JD"]
        Settings["settings_page.py\nAI Provider Settings"]
        Results["results_page.py\nScore · Keywords · Recs · AI Feedback"]
    end

    subgraph CoreLayer["⚙️  Core Engine — app/core/"]
        Parser["parser.py\nPDF · DOCX · TXT extraction"]
        Extractor["extractor.py\nSection detection"]
        FmtCheck["formatting_checker.py\nATS formatting risk checks"]
        KW["keyword_matcher.py\nJD keyword comparison"]
        Scorer["scorer.py\nWeighted 0–100 scoring"]
        Recs["recommendations.py\nPrioritised suggestions"]
    end

    subgraph AILayer["🤖  AI Layer — app/ai/"]
        LLMClient["llm_client.py\nProvider abstraction"]
        Ollama["🟢 Ollama\nFree · Runs locally"]
        OpenAI_["🟠 OpenAI\nBring your own key"]
        NoAI["🔵 None\nRule-based only"]
    end

    subgraph ModelLayer["📦  Data Models — app/models/"]
        RM["resume_models.py"]
        SM["scoring_models.py"]
    end

    User -->|"Upload file + paste JD"| Upload
    User -->|"Choose AI mode"| Settings
    Upload --> Parser
    Parser --> Extractor
    Extractor --> FmtCheck
    Extractor --> KW
    FmtCheck --> Scorer
    KW --> Scorer
    Scorer --> Recs
    Recs --> Results
    Scorer --> Results
    Settings --> LLMClient
    LLMClient --> Ollama
    LLMClient --> OpenAI_
    LLMClient --> NoAI
    LLMClient -->|"Optional AI feedback"| Results
    Results -->|"Score · Weaknesses · Recs"| User
    Parser -.->|uses| RM
    Scorer -.->|uses| SM
```

> **Five AI providers** are supported: None (rule-based), Ollama (local), Groq (free cloud),
> OpenAI (BYOK), and Anthropic Claude (BYOK). The architecture diagram above shows the
> canonical three — the full provider list is in the AI Modes table below.

> **Solid arrows** = data / control flow.  
> **Dashed arrows** = module dependency (uses a data model).  
> The AI layer sits outside the required path — the app works fully without it.

---

## AI Modes

ATS Insight supports **five AI modes**. Choose based on your setup and whether you're running locally or hosting online:

| Mode | Cost | Local run | Hosted / online | How to enable |
|---|---|---|---|---|
| **None (default)** | Free | ✅ | ✅ | Nothing extra |
| **Ollama — Local AI** | Free | ✅ | ❌ local server only | Install Ollama + pull a model |
| **Groq — Free Cloud** | Free | ✅ | ✅ | Free key from [console.groq.com](https://console.groq.com) |
| **OpenAI — Your Key** | Pay-per-use | ✅ | ✅ | Paste your API key in the Settings tab |
| **Anthropic Claude — Your Key** | Pay-per-use | ✅ | ✅ | Paste your API key in the Settings tab |

> **Default mode is none** — full scoring and recommendations with zero setup.  
> **Best free local option:** Ollama (your hardware, no data leaves your machine).  
> **Best free online option:** Groq (free developer tier, no credit card required).

> ⚠️ **Common misconceptions:**  
> A **ChatGPT Plus** subscription does NOT include API access — OpenAI API is billed separately.  
> A **Claude.ai Pro** subscription does NOT include API access — Anthropic API is billed separately.

---

## How to Use ATS Insight

You have two options:

| Option | Details |
|---|---|
| **Run locally** | Clone the repo, install dependencies, run with Streamlit — full control, works offline, Ollama supported |
| **Run free online** | *(Coming soon)* — No install needed; use Groq (free tier) or your own API key for AI features |

> The hosted online version is **TBD** and will be linked here once available.  
> For now, follow the local setup below — it takes about 5 minutes.

---

## Quick Start

### 1 — Prerequisites

- Python 3.11 or newer
- `pip` (comes with Python)
- A terminal (macOS Terminal, iTerm2, VS Code integrated terminal, etc.)

### 2 — Clone or download the project

```bash
git clone https://github.com/rayme11/ATS-Readiness-Checker.git
cd ATS-Readiness-Checker
```

### 3 — Create a virtual environment

```bash
python -m venv .venv
```

### 4 — Activate the virtual environment

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of your terminal prompt.

### 5 — Install dependencies

```bash
pip install -r requirements.txt
```

### 6 — Copy the environment file

```bash
cp .env.example .env
```

Leave `.env` as-is for the default rule-based mode.  
See [AI Configuration](#ai-configuration) below to enable Ollama or OpenAI.

### 7 — Run the app

```bash
streamlit run app/main.py
```

Streamlit will print a local URL (usually `http://localhost:8501`).  
Open it in your browser — the app is ready to use.

---

## AI Configuration

### Option A — Ollama (Free, Runs Locally)

Ollama lets you run open-source LLMs like Llama 3 on your own hardware.
No API key, no usage cost, no data leaves your machine.

**Step 1 — Install Ollama**

```bash
# macOS (Homebrew)
brew install ollama

# Or download the installer from https://ollama.ai
```

**Step 2 — Start the Ollama server**

```bash
ollama serve
# Leave this terminal open (or run it as a background service)
```

**Step 3 — Pull a model** (one-time download, ~4 GB for llama3)

```bash
ollama pull llama3
```

Other good free models:
```bash
ollama pull mistral       # faster, slightly smaller
ollama pull llama3.2      # newer, more capable
ollama pull gemma2        # Google's open model
```

**Step 4 — Start the app**

Open a new terminal, navigate to the project folder, activate the virtual environment, and launch Streamlit:

```bash
cd ATS-Readiness-Checker
source .venv/bin/activate
streamlit run app/main.py
```

Streamlit will print a local URL (usually `http://localhost:8501`). Open it in your browser.

**Step 5 — Enable Ollama in ATS Insight**

Open the **AI Settings** tab in the app, select **Ollama — Free & Local**,
then click **Test Connection** to confirm it's working.

---

### Option B — OpenAI (Bring Your Own Key)

If you already have an OpenAI API key and prefer GPT-4o quality feedback:

1. Get a key at https://platform.openai.com/api-keys
2. Open the **AI Settings** tab in the app
3. Select **OpenAI — Bring Your Own Key**
4. Paste your key into the password field

**Security note:**  
Your key is stored in Streamlit session memory only.  
It is never written to disk or sent anywhere except directly to OpenAI's API.  
It is cleared when you close or refresh the browser tab.

You can also set it via `.env` for convenience during local development:
```bash
# .env  (never commit this file)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

---

### Option C — Groq (Free Tier, Works Locally and Hosted)

Groq runs open-source models (Llama 3, Mistral, Gemma) in the cloud via blazing-fast
inference hardware. The developer free tier requires **no credit card**.

1. Sign up at <https://console.groq.com> and create an API key
2. Open the **AI Settings** tab in the app
3. Select **Groq — Free Tier**
4. Paste your key (starts with `gsk_`)

**Why Groq is ideal for hosted deployments:**  
Unlike Ollama (which needs a local server), Groq's API works from anywhere —
your laptop, a cloud VM, or Streamlit Community Cloud. Free tier limits are
generous enough for typical resume analysis use.

```bash
# .env  (local development convenience)
AI_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama3-8b-8192
```

Available free models:
| Model | Best for |
|---|---|
| `llama3-8b-8192` | Fast, good quality (recommended) |
| `llama3-70b-8192` | Higher quality, slightly slower |
| `mixtral-8x7b-32768` | Long context windows |
| `gemma2-9b-it` | Google's open model |

---

### Option D — Anthropic Claude (Bring Your Own Key)

Claude models (Haiku, Sonnet, Opus) offer strong reasoning on structured text.

> ⚠️ A **Claude.ai Pro** subscription does **not** include API access.
> API keys are obtained and billed separately at <https://console.anthropic.com>.

1. Get a key at <https://console.anthropic.com>
2. Open the **AI Settings** tab in the app
3. Select **Anthropic Claude — Bring Your Own Key**
4. Paste your key (starts with `sk-ant-`)

```bash
# .env  (local development convenience)
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

| Model | Cost | Notes |
|---|---|---|
| `claude-3-haiku-20240307` | Cheapest | Fast, great for summaries |
| `claude-3-5-sonnet-20241022` | Mid | Best quality/cost balance |
| `claude-3-opus-20240229` | Premium | Highest quality, most expensive |

---

## Security & Privacy

This section covers how API keys and resume data are handled in both run modes.

### Key principles (apply to all providers)

- **Keys entered in the UI** are stored only in Streamlit's server-side session state.
  They are **never** written to disk, never logged, and never forwarded to third parties.
  They are cleared automatically when the browser tab is closed or refreshed.
- **Resume content** is processed entirely in memory and is never written to disk or stored.
- **All API calls** go directly from the app to the chosen provider (OpenAI, Groq, Anthropic).
  The app acts as a local proxy — only the prompts it constructs are sent, not raw resume bytes.

### Local run

| Item | Recommendation |
|---|---|
| `.env` file | Copy from `.env.example`, fill in keys, **never commit it** |
| `.gitignore` | Ensure `.env` and `.venv/` are listed (already done in this repo) |
| Ollama | Zero network exposure — the LLM runs entirely on your machine |
| API keys in UI | Session-only; cleared on tab close |

### Hosted / online run (e.g. Streamlit Community Cloud, Render, Railway)

| Item | Recommendation |
|---|---|
| **Your own default key** | Use the platform's **Secrets Manager** — never use a `.env` file in production |
| **User-supplied keys** | Entered via the Settings UI — same session-only guarantee as local |
| **Ollama** | Not usable by end-users unless you provision Ollama on the server itself |
| **Groq** | ✅ Recommended free option for hosted apps — cloud API, works anywhere |
| **HTTPS** | All major hosting platforms enforce HTTPS, so keys are encrypted in transit |
| **Cross-user isolation** | Each Streamlit session is isolated — one user's keys are never visible to another |

> 🔒 **No secrets are stored between sessions.** When a user closes the tab their API key
> is gone. They will need to re-enter it on the next visit. This is intentional.

---
## Running Tests

```bash
# From the repo root, with .venv activated
pytest tests/ -v
```

Expected output:
```
tests/test_parser.py          - 5 tests
tests/test_scorer.py          - 7 tests
tests/test_keyword_matcher.py - 7 tests
```

---

## Project Structure

```
ATS-Readiness-Checker/          ← repo root (you are here)
├── app/
│   ├── main.py               ← Streamlit entry point  →  streamlit run app/main.py
│   ├── config.py             ← Environment variable loading
│   ├── ui/
│   │   ├── upload_page.py    ← File upload + JD input
│   │   ├── results_page.py   ← Score display + recommendations
│   │   └── settings_page.py  ← AI provider configuration
│   ├── core/
│   │   ├── parser.py         ← PDF / DOCX / TXT extraction
│   │   ├── extractor.py      ← Section detection
│   │   ├── formatting_checker.py  ← ATS formatting risk checks
│   │   ├── keyword_matcher.py     ← JD keyword comparison
│   │   ├── scorer.py              ← Weighted category scoring
│   │   └── recommendations.py    ← Prioritised suggestion builder
│   ├── ai/
│   │   ├── llm_client.py     ← Ollama, OpenAI, Groq, Anthropic client abstraction
│   │   ├── prompts.py        ← Prompt templates
│   │   └── ai_feedback.py    ← High-level AI feedback functions
│   └── models/
│       ├── resume_models.py  ← ParsedResume, ResumeContact, etc.
│       └── scoring_models.py ← ScoringResult, CategoryScore, etc.
├── tests/
│   ├── test_parser.py
│   ├── test_scorer.py
│   └── test_keyword_matcher.py
├── sample_data/
│   └── sample_jd.txt         ← Example job description for testing
├── .streamlit/
│   └── config.toml           ← Auto-reload on save + poll-watcher settings
├── .vscode/
│   └── tasks.json            ← Cmd+Shift+B launches the app
├── .env.example              ← Copy to .env and fill in
├── .venv/                    ← Virtual environment (gitignored)
├── requirements.txt
├── LICENSE                   ← MIT
└── README.md                 ← This file
```

---

## Scoring Breakdown

| Category | Weight | What is checked |
|---|---|---|
| **Resume Structure** | 20 % | Email, phone, Experience, Education, Skills, Summary sections |
| **Parsing Safety** | 20 % | Symbols, multi-column layout, tables, date consistency |
| **Keyword Relevance** | 30 % | Term overlap between resume and job description |
| **Achievement Quality** | 15 % | Metrics/numbers, action verbs |
| **Recruiter Readability** | 15 % | Location format, bullet consistency, line length |

---

## Honest Limitations

- **Multi-column PDFs** are handled by column-aware layout analysis, but very complex
  designs (3+ columns, heavy graphics, scanned/image PDFs) may still extract imperfectly.
  Plain single-column PDFs give the cleanest results.
- ATS systems vary widely — this tool simulates common patterns, not every platform.
- Keyword matching is heuristic. It does not replicate any specific recruiter software.
- AI feedback quality depends on the model you choose. Ollama models may be less
  polished than GPT-4o but are completely free.
- Ollama first-run responses can take 30–120 s while the model loads into memory.
  Subsequent requests in the same session are faster.

---

## Build Status

| Phase | Status | Description |
|---|---|---|
| Phase 0 — Setup | ✅ Done | Project structure, virtual env, dependencies |
| Phase 1 — Parsing | ✅ Done | PDF, DOCX, TXT extraction |
| Phase 2 — Section Detection | ✅ Done | Experience, Skills, Education, etc. |
| Phase 3 — Formatting Checks | ✅ Done | Symbols, columns, dates, contact info |
| Phase 4 — Keyword Matching | ✅ Done | Resume vs JD term comparison |
| Phase 5 — Scoring Engine | ✅ Done | Weighted 0-100 category scoring |
| Phase 6 — Recommendations | ✅ Done | Prioritised actionable suggestions |
| Phase 7 — Streamlit UI | ✅ Done | Upload, results, settings pages |
| Phase 8 — AI Integration | ✅ Done | Ollama (free local) + OpenAI (BYOK) |
| Phase 9 — Multi-provider AI | ✅ Done | Groq (free), Anthropic, security model |
| Phase 10 — PDF Column Parsing | ✅ Done | Two-column layout detection; column-aware word extraction |
| Phase 11 — Section Detection v2 | ✅ Done | 60+ heading aliases, Title Case, inline split, cross-line merge |
| Phase 12 — Modern UI | ✅ Done | Dark theme, card layouts, chip tags, hero score banner |
| Phase 13 — LLM Suitability Panel | ✅ Done | Per-provider star ratings + side-by-side compare table |
| Phase 14 — Ollama Reliability | ✅ Done | Model warm-up ping, 300 s timeout, structured error messages |
| Phase 15 — Dev Experience | ✅ Done | Auto-reload on save, VS Code task, `.streamlit/config.toml` |
| Phase 16 — GitHub Polish | 🔜 Next | Screenshots, CI workflow, badges |
| Phase 17 — Productisation | 🔜 Future | Save history, resume comparison, auth |

---

## Development — Auto-reload on Save

The app is configured to **automatically rerun** in the browser whenever you save a
Python file — no manual refresh needed.

This is enabled via `.streamlit/config.toml`:
```toml
[server]
runOnSave    = true
fileWatcherType = "poll"   # reliable on Google Drive / network mounts
pollInterval    = 1000     # check every 1 second
```

### Starting the app

**Option 1 — VS Code task (recommended)**
```
Cmd+Shift+B  →  ▶ Run ATS Insight
```
Or: Command Palette (`Cmd+Shift+P`) → *Tasks: Run Build Task*.

**Option 2 — Terminal**
```bash
source .venv/bin/activate
streamlit run app/main.py --server.runOnSave true --server.fileWatcherType poll
```

> The `--server.fileWatcherType poll` flag is important if your project lives on
> Google Drive or any network-mounted path — macOS native filesystem events are
> unreliable on those paths.

---

## Changelog

### 2026-04-12 — Section Detection v2 + Modern UI + LLM Panel

**Section detection overhaul (`app/core/extractor.py`)**
- Expanded `SECTION_HEADINGS` from ~25 to 60+ aliases covering common resume
  variations: `executive summary`, `career objective`, `additional professional
  experience`, `core leadership`, `work background`, `training`, and more
- `_is_heading()` now handles ALL-CAPS, Title Case, and prefix matching with
  generous length tolerance (was broken for headings longer than ~30 chars)
- New `_preprocess_lines()` runs two passes before section splitting:
  - **Cross-line merge** — `"EDUCATION &"` + `"CERTIFICATIONS"` → one heading
  - **Inline split** — `"EDUCATION Validated automation…"` → heading + body
- Terminal logging shows every detected section and field mapping

**Column-aware PDF extraction (`app/core/parser.py`)**
- Replaced simple `page.extract_text()` with per-word x-position clustering
- Detects two-column layouts and extracts each column independently so section
  headings no longer collide with sidebar content from the opposite column
- Falls back gracefully to standard extraction for single-column pages
- Full `logging` instrumentation (page count, layout type, char count)

**Modern dark UI (`app/main.py`, `app/ui/results_page.py`, `app/ui/upload_page.py`)**
- Global CSS injected at startup: dark slate theme (`#0f172a`), Inter font, styled
  tabs, buttons, inputs, selects, expanders, and alerts
- Hero score banner with gradient card, large score number, colored label pill,
  and animated progress bar
- Category breakdown as top-bordered cards (color-coded by score tier)
- Strengths/weaknesses in tinted panel boxes
- Keyword chips rendered as colored pill tags instead of comma-separated text
- Recommendation items as indigo left-border cards
- Upload page with hero intro card, drop-zone, word-count indicator, and
  color-coded AI engine badge

**LLM Suitability Panel (`app/ui/results_page.py`)**
- Collapsible expander on every results page showing the active AI engine's
  description, best-for note, limitations, and ★ star ratings across:
  Resume Understanding · Keyword Analysis · Feedback Quality · Speed · Privacy
- Side-by-side comparison table of all five providers; active one highlighted

**Ollama reliability (`app/ai/llm_client.py`, `app/main.py`)**
- Read timeout raised from 120 s → 300 s
- `_warm_model()` pre-ping ensures weights are loaded before the main request,
  preventing silent stalls during cold start
- `ConnectionError` and `Timeout` caught separately with human-readable messages
- UI shows structured error card with actionable tips instead of raw exception

**Dev experience**
- `.streamlit/config.toml` — `runOnSave = true`, `fileWatcherType = poll`
- `.vscode/tasks.json` — `Cmd+Shift+B` launches the app with correct flags

---

## Contributing & Branching Strategy

This project follows a simple, clean branching model that keeps `main` always stable
while allowing free development on `dev` and short-lived feature branches.

### Branch Map

```
main          ← stable, deployable, protected
  └── dev     ← integration branch — all features land here first
        ├── feature/my-feature     ← new functionality
        ├── fix/my-bug-fix         ← bug corrections
        └── hotfix/critical-patch  ← urgent fixes (merges to main AND dev)
```

### Rules

| Branch | Purpose | Who merges into it |
|---|---|---|
| `main` | Production-ready, always green | PRs from `dev` (or `hotfix/*`) only |
| `dev` | Active development integration | PRs from `feature/*` and `fix/*` |
| `feature/*` | One feature or improvement per branch | Creator, via PR into `dev` |
| `fix/*` | Bug fix not urgent enough for hotfix | Creator, via PR into `dev` |
| `hotfix/*` | Critical fix that can't wait for `dev` | Creator, via PR into `main` AND `dev` |

### Step-by-Step: Starting New Work

**1 — Make sure your local `dev` is up to date**
```bash
git checkout dev
git pull origin dev
```

**2 — Create your feature branch from `dev`**
```bash
git checkout -b feature/your-feature-name
# examples:
#   feature/add-pdf-export
#   fix/keyword-score-edge-case
#   hotfix/crash-on-empty-resume
```

**3 — Do your work, commit often with clear messages**
```bash
git add .
git commit -m "feat: add PDF export button to results page"
# Prefix conventions:
#   feat:     new feature
#   fix:      bug fix
#   docs:     README or comment changes
#   test:     test-only changes
#   refactor: code restructuring without behaviour change
#   chore:    tooling, config, deps
```

**4 — Push your branch and open a Pull Request into `dev`**
```bash
git push origin feature/your-feature-name
# Then open a PR on GitHub: base = dev, compare = your branch
```

**5 — After review, merge into `dev`. When `dev` is stable, merge into `main`**
```bash
git checkout main
git merge dev --no-ff
git push origin main
```

### Setting Up the `dev` Branch (First Time)

If `dev` doesn't exist yet in the repo:
```bash
git checkout -b dev
git push -u origin dev
```
Then set `dev` as the default branch for PRs in GitHub:
*Settings → Branches → Default branch → change to `dev`*

### Protecting `main` on GitHub

Go to *Settings → Branches → Add branch protection rule* for `main`:
- ✅ Require a pull request before merging
- ✅ Require at least 1 approval
- ✅ Require status checks to pass (once CI is added)
- ✅ Do not allow force pushes

> Contributions are welcome once the MVP is stable and published.
> Check open issues or discussions before starting large features.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Disclaimer & Context

### ATS Insight is an estimator, not a certified ATS

This tool simulates common ATS and recruiter screening patterns based on publicly
known best practices. It **does not replicate any specific commercial ATS product**,
and results should be treated as one data point alongside your own judgement —
not as a guarantee of how any employer's hiring system will process your resume.

---

### What is an ATS, really?

At its core, an Applicant Tracking System (ATS) is a **keyword matching and
ranking engine**. When you submit a resume online, the ATS:

1. Parses your document into plain text (stripping fonts, tables, columns)
2. Extracts terms and compares them against the job description and a internal
   keyword dictionary maintained by the employer or recruiter
3. Scores or ranks candidates based on term overlap, required qualifications, and
   configurable rules
4. Surfaces the highest-ranked resumes to a human reviewer

The sophisticated parts — ranking weights, synonym libraries, semantic matching,
skills taxonomies, and compliance filters — are **proprietary algorithms** owned
by each vendor. No two ATS platforms behave identically.

### Commercial ATS platforms (what companies actually buy)

These are the industry-leading platforms hiring teams pay for. Each has its own
parsing engine, scoring logic, and integration ecosystem:

| Platform | Typical Customer | Pricing |
|---|---|---|
| [**Workday**](https://www.workday.com/en-us/products/human-capital-management/recruiting.html) | Large enterprise (Fortune 500) | Enterprise contract ($$$$) |
| [**Greenhouse**](https://www.greenhouse.com) | Mid-size tech companies | Per-seat SaaS (~$6k–$25k/yr) |
| [**Lever**](https://www.lever.co) | Growth-stage startups | Per-seat SaaS |
| [**iCIMS**](https://www.icims.com) | Enterprise & staffing firms | Enterprise contract |
| [**Taleo** (Oracle)](https://www.oracle.com/human-capital-management/taleo/) | Large enterprise | Enterprise contract |
| [**SmartRecruiters**](https://www.smartrecruiters.com) | Mid-market | Freemium → SaaS |
| [**BambooHR**](https://www.bamboohr.com) | SMBs | Per-employee SaaS |
| [**Jobvite**](https://www.jobvite.com) | Mid-size & enterprise | Enterprise SaaS |

Because their algorithms are **closed-source and proprietary**, no third-party tool
(including this one) can simulate them exactly. What open-source tools like ATS Insight
can do is encode the publicly documented best practices that most platforms share:
clear section headings, keyword density, standard formatting, quantified achievements.

---

### Why this project was built

ATS Insight started as a learning exercise with a specific goal:

> *Build a non-trivial, end-to-end software project — from a blank folder to a
> deployable web application — using AI and LLM models as active collaborators
> in the design, coding, and iteration process.*

Every component was built and refined iteratively:
- **Document parsing** — handling real-world PDFs with multi-column layouts
- **Section detection** — pattern matching and heuristics tuned on actual resumes
- **Scoring model** — a transparent, weighted formula you can read and question
- **LLM integration** — connecting local (Ollama) and cloud (Groq, OpenAI, Anthropic)
  models to provide narrative feedback beyond what rule-based checks can express
- **Modern web UI** — Streamlit, styled to look like a real browser application

The project is intentionally **open and transparent**: the scoring formula is
documented, the keyword matching algorithm is readable, and nothing is hidden
behind a paid wall. The goal is education — understanding what happens to your
resume between the "Submit" button and a recruiter's inbox.

---

### References & Further Reading

The claims in this README are grounded in published research and industry reporting.
The sources below are a good starting point if you want to go deeper.

#### Research & reports

| Source | What it covers |
|---|---|
| Fuller, J. & Raman, M. (2021). [**Hidden Workers: Untapped Talent**](https://www.hbs.edu/managing-the-future-of-work/Pages/research.aspx). Harvard Business School / Accenture. | Found that ATS filters discard millions of qualified candidates; documents how keyword-gating works in practice. Widely cited in policy and HR circles. |
| Bogen, M. & Rieke, A. (2018). [**Help Wanted: An Examination of Hiring Algorithms, Equity, and Bias**](https://upturn.org/work/help-wanted/). Upturn. | Audits how automated screening tools — including ATS — encode bias into hiring pipelines. Explains the scoring mechanism in plain language. |
| Raghavan, M. et al. (2020). [**Mitigating Bias in Algorithmic Hiring**](https://dl.acm.org/doi/10.1145/3351095.3372828). *ACM FAccT 2020*. | Peer-reviewed. Analyses automated screening models including keyword-based ATS, algorithmic ranking, and fairness implications. |
| Sanchez-Monedero, J. et al. (2020). [**What Does It Mean to "Solve" the Problem of Discrimination in Hiring?**](https://dl.acm.org/doi/10.1145/3351095.3372849). *ACM FAccT 2020*. | Peer-reviewed. Shows that resume-parsing tools reduce resumes to term-frequency vectors — reinforcing the "keyword matching at its core" framing. |
| SHRM. [**Using AI in HR & Recruiting**](https://www.shrm.org/topics-tools/topics/artificial-intelligence). Society for Human Resource Management. | Practitioner-focused; explains how HR departments configure and use ATS tools day-to-day. |

#### How ATS parsing actually works (technical)

These academic papers focus on the NLP and information-extraction techniques that
commercial ATS vendors use internally:

- **Resume Entity Extraction / NER** — Search Google Scholar:
  [`"resume parsing" NLP named entity recognition`](https://scholar.google.com/scholar?q=resume+parsing+NLP+named+entity+recognition)
- **Job–Resume Matching** — Search Google Scholar:
  [`"job description resume matching" relevance ranking`](https://scholar.google.com/scholar?q=job+description+resume+matching+relevance+ranking)
- **Automated Candidate Screening** — Search Google Scholar:
  [`"applicant tracking system" keyword screening algorithm`](https://scholar.google.com/scholar?q=applicant+tracking+system+keyword+screening+algorithm)

> The short version: most resume-parsing engines apply rule-based NER to extract
> structured fields (name, email, skills, titles, dates), then compute term-frequency
> overlap between resume tokens and JD tokens to produce a ranking score.
> That is exactly what this project implements — openly and without a paywall.

---

## Author

Built by [Ray Maldonado](https://www.linkedin.com/in/rmaldonado)  
Feedback, ideas, and contributions are welcome.
