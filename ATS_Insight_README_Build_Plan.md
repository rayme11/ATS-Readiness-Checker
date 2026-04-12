# ATS Insight

> Open-source resume analysis tool for ATS readiness, parsing safety, keyword alignment, and recruiter readability.  
> Built to help job seekers understand how resumes may be evaluated by common ATS patterns and human reviewers.

## Vision

ATS Insight is designed as a practical, transparent alternative to paid ATS scoring services.

The goal is not to claim that every ATS works the same way. Instead, this project aims to simulate common ATS and recruiter screening patterns so users can:

- upload a resume
- paste a job description
- receive an ATS readiness score
- identify parsing risks
- see missing keywords
- get practical improvement suggestions

This project is intended to start as a free, open-source tool and later evolve into a product if there is enough value and adoption.

## Core Product Goals

ATS Insight should let a user:

1. Upload a resume file
2. Paste a job description
3. Receive a score from 0 to 100
4. See category-level scoring
5. Understand strengths and risks
6. Get suggestions for improvement
7. Optionally use AI for deeper analysis
8. Eventually run in either:
   - free rule-based mode
   - bring-your-own-API-key mode
   - optional local AI mode

## Product Positioning

This tool should be described honestly.

Good positioning:
- ATS readiness estimator
- Resume parsing and job-match analyzer
- Resume quality and recruiter-readability checker

Avoid making claims like:
- guaranteed ATS pass
- exact ATS simulation for every platform
- guaranteed interview improvement

## Recommended Tech Stack

### Frontend
- Streamlit

### Backend Logic
- Python

### Resume Parsing
- pdfplumber
- python-docx

### Optional AI
- OpenAI API
- later: Ollama for local free models

### Storage
- SQLite for local runs
- optional Postgres later

### Testing
- pytest

## Why This Architecture

This project should be built in layers.

### Layer 1: Free Mode
This mode should work without any API key.

It should use:
- rule-based resume parsing
- formatting checks
- keyword matching
- score calculation
- recommendation generation

### Layer 2: AI Mode
This mode should be optional.

It should use:
- user-provided API key
- deeper feedback
- rewrite suggestions
- stronger job-description comparison
- tailored summary improvements

### Layer 3: Local Model Mode
This can come later.

It should use:
- Ollama
- local open models
- no API cost
- more privacy for advanced users

## Folder Structure

Use this exact structure:

```text
ats-insight/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── ui/
│   │   ├── upload_page.py
│   │   ├── results_page.py
│   │   └── settings_page.py
│   ├── core/
│   │   ├── parser.py
│   │   ├── extractor.py
│   │   ├── scorer.py
│   │   ├── keyword_matcher.py
│   │   ├── formatting_checker.py
│   │   └── recommendations.py
│   ├── ai/
│   │   ├── llm_client.py
│   │   ├── prompts.py
│   │   └── ai_feedback.py
│   └── models/
│       ├── resume_models.py
│       └── scoring_models.py
├── tests/
│   ├── test_parser.py
│   ├── test_scorer.py
│   └── test_keyword_matcher.py
├── sample_data/
│   ├── sample_resume.pdf
│   └── sample_jd.txt
├── .env.example
├── README.md
├── requirements.txt
└── LICENSE
```

## Feature Roadmap

The project should be built in phases, not all at once.

---

# Phase 0 - Project Setup

## Goal
Create a clean local development environment and repository skeleton.

## Tasks
- Create the project folder
- Open in VS Code
- Create Python virtual environment
- Add requirements.txt
- Add README.md
- Add .env.example
- Add folder structure
- Add LICENSE
- Initialize Git
- Push empty skeleton to GitHub

## Suggested Requirements for Initial Setup

```txt
streamlit
pdfplumber
python-docx
pydantic
python-dotenv
pytest
```

## Success Criteria
- Project runs locally
- Folder structure exists
- Dependencies install correctly
- GitHub repo is ready

---

# Phase 1 - Resume Parsing Foundation

## Goal
Allow users to upload a resume and extract clean text.

## Scope
Support:
- PDF
- DOCX
- TXT

## Files to Build
- app/core/parser.py
- tests/test_parser.py

## Responsibilities
parser.py should:
- accept a file path or uploaded file
- detect file type
- extract text
- return normalized plain text

## Initial Rules
- preserve section content
- strip extra whitespace
- return meaningful errors for unsupported files

## Success Criteria
- User can upload PDF/DOCX/TXT
- App extracts readable text
- Tests pass

---

# Phase 2 - Resume Section Detection

## Goal
Identify common resume sections.

## Files to Build
- app/core/extractor.py
- app/models/resume_models.py

## Sections to Detect
- contact
- summary
- experience
- skills
- education
- certifications
- languages

## Logic
Start rule-based.

Use:
- common heading names
- line patterns
- simple heuristics

## Success Criteria
- Extract text into basic sections
- Return structured data model

---

# Phase 3 - ATS Formatting and Parsing Checks

## Goal
Evaluate whether a resume is likely to parse cleanly in ATS systems.

## Files to Build
- app/core/formatting_checker.py

## Checks to Include
- missing standard headings
- inconsistent dates
- too many symbols
- unusual bullets
- multi-column layout risk
- tables risk
- icons or graphics warning
- missing contact clarity
- missing role locations

## Output
Return:
- score for parsing safety
- warnings list
- recommended fixes

## Success Criteria
- Tool can identify common ATS risks
- Results are understandable and actionable

---

# Phase 4 - Job Description Keyword Matching

## Goal
Compare resume text against a pasted job description.

## Files to Build
- app/core/keyword_matcher.py
- tests/test_keyword_matcher.py

## Features
- normalize words
- extract high-signal terms
- find overlapping terms
- find missing terms
- detect title alignment
- calculate keyword match score

## Output
Return:
- matched keywords
- missing keywords
- score
- critical missing terms

## Success Criteria
- Resume and JD can be compared
- Output is useful and easy to read

---

# Phase 5 - Rule-Based Scoring Engine

## Goal
Generate a total ATS readiness score from multiple categories.

## Files to Build
- app/core/scorer.py
- app/models/scoring_models.py
- tests/test_scorer.py

## Recommended Scoring Categories
- resume structure: 20%
- parsing safety: 20%
- keyword relevance: 30%
- achievement quality: 15%
- recruiter readability: 15%

## Scoring Philosophy
The score should be transparent and explainable.

Do not use arbitrary magic numbers without documenting them.

## Output
Return:
- total score
- category scores
- strengths
- weaknesses
- top recommendations

## Success Criteria
- User gets clear 0-100 score
- Category scoring is visible
- Recommendations map to actual scoring issues

---

# Phase 6 - Recommendations Engine

## Goal
Provide practical, prioritized suggestions.

## Files to Build
- app/core/recommendations.py

## Types of Recommendations
- add missing role locations
- rewrite summary for clarity
- remove risky symbols
- convert skills into categories
- add quantified achievements
- include missing keywords from JD
- standardize headings
- improve contact formatting

## Output Style
Keep feedback:
- practical
- short
- prioritized
- non-judgmental

## Success Criteria
- Recommendations feel useful
- Suggestions are connected to actual findings

---

# Phase 7 - Streamlit User Interface

## Goal
Build the first usable local app.

## Files to Build
- app/main.py
- app/ui/upload_page.py
- app/ui/results_page.py

## UI Workflow
1. Upload resume
2. Paste job description
3. Click analyze
4. View:
   - total score
   - category scores
   - matched keywords
   - missing keywords
   - warnings
   - recommendations

## MVP UI Requirements
- simple and clean
- no authentication
- local-first
- easy to demo

## Success Criteria
- User can complete analysis end-to-end
- Output is understandable

---

# Phase 8 - Optional AI Integration

## Goal
Allow users to provide their own API key for richer analysis.

## Files to Build
- app/ai/llm_client.py
- app/ai/prompts.py
- app/ai/ai_feedback.py
- app/ui/settings_page.py
- app/config.py

## AI Features
- improved summary feedback
- rewrite suggestions
- bullet improvement suggestions
- recruiter-style concerns
- tailored recommendations by role level

## API Key Strategy
Use bring-your-own-key mode.

### Local Development
Use .env:
```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
```

### UI Mode
Allow user to paste:
- provider
- API key
- model

## Security Rule
Do not store user API keys permanently in v1.

Use session-only storage at first.

## Success Criteria
- App works with or without AI
- No cost to you for open-source users
- AI mode feels optional and additive

---

# Phase 9 - Optional Local AI Mode

## Goal
Offer a free local AI option.

## Suggested Tool
- Ollama

## Future Files
- app/ai/local_llm_client.py

## Suggested Environment Variables
```bash
USE_LOCAL_MODEL=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

## Why This Matters
This creates a 100 percent free path for advanced users.

## Success Criteria
- Users can choose:
  - no AI
  - OpenAI with own key
  - local AI with Ollama

---

# Phase 10 - GitHub Publishing and Open Source Readiness

## Goal
Publish a clean, credible open-source project.

## Required Files
- README.md
- LICENSE
- .env.example
- requirements.txt

## Recommended License
- MIT

## GitHub Checklist
- clear repo description
- clean README
- setup instructions
- screenshots
- sample output
- known limitations
- roadmap
- contribution guidance later

## Suggested Repo Description
Open-source ATS readiness and resume quality analyzer with free rule-based scoring and optional bring-your-own-AI support.

---

# Phase 11 - Future Productization

## Goal
Leave room to turn this into a product later.

## Future Product Features
- save analyses
- side-by-side resume versions
- rewrite assistant
- role-specific templates
- executive resume scoring
- team/recruiter mode
- subscription features
- hosted API-backed version

## Smart Monetization Path
Free:
- parsing checks
- ATS scoring
- recommendations

Paid later:
- AI rewrites
- saved history
- resume version tracking
- advanced recruiter-mode scoring
- multiple job analysis

---

## Scoring Categories in Detail

### 1. Resume Structure
Check for:
- clear contact information
- standard headings
- readable chronology
- section completeness

### 2. Parsing Safety
Check for:
- multi-column risk
- tables
- special symbols
- complex layouts
- text extraction problems

### 3. Keyword Relevance
Check for:
- title match
- skill overlap
- missing terms
- job-specific terminology

### 4. Achievement Quality
Check for:
- action verbs
- metrics
- business outcomes
- concise bullets

### 5. Recruiter Readability
Check for:
- title clarity
- location presence
- date formatting
- bullet consistency
- visual simplicity

---

## Output Example

A future result page should look like this:

- Overall ATS Readiness Score: 84
- Resume Structure: 90
- Parsing Safety: 72
- Keyword Match: 88
- Achievement Quality: 80
- Recruiter Readability: 85

Top Strengths:
- strong quantified impact
- good title alignment
- clear experience section

Top Risks:
- two-column parsing risk
- missing role locations
- skills section too broad

Top Recommendations:
- add role locations
- simplify skills into categories
- replace special symbols
- add 5 missing keywords from the JD

---

## Development Rules

To keep the project manageable:

1. Build one phase at a time
2. Make each phase runnable before moving on
3. Add tests for each core module
4. Keep README updated as the project grows
5. Avoid overbuilding v1
6. Document assumptions clearly
7. Use deterministic rules before AI whenever possible

---

## Initial Setup Instructions

### 1. Create the project
```bash
mkdir ats-insight
cd ats-insight
```

### 2. Create virtual environment
```bash
python -m venv .venv
```

### 3. Activate it

#### macOS/Linux
```bash
source .venv/bin/activate
```

#### Windows PowerShell
```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install packages
```bash
pip install -r requirements.txt
```

### 5. Run Streamlit later
```bash
streamlit run app/main.py
```

---

## Example .env.example

```bash
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
USE_LOCAL_MODEL=false
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

---

## Example requirements.txt

```txt
streamlit
pdfplumber
python-docx
pydantic
python-dotenv
openai
pytest
```

---

## Suggested GitHub Milestones

### Milestone 1
Project skeleton + parser

### Milestone 2
Section extraction + formatting checks

### Milestone 3
Keyword matching + scoring engine

### Milestone 4
Streamlit UI MVP

### Milestone 5
Optional AI mode

### Milestone 6
Local AI mode

---

## Suggested Launch Messaging

When this is ready, a good public message could be:

I kept seeing expensive ATS services everywhere, so I started building an open-source alternative that helps people understand ATS readiness, resume parsing risks, and job-description alignment in a more transparent way.

---

## Current Build Plan Summary

Build in this order:

1. Setup project
2. Resume parser
3. Section detection
4. Formatting checks
5. Keyword matcher
6. Scoring engine
7. Recommendations
8. Streamlit UI
9. Optional AI mode
10. Optional local AI mode
11. GitHub polish
12. Product validation

---

## Contributing

Contributions can be added later. For now, keep the project simple and focused until the MVP is stable.

---

## Final Note

The purpose of ATS Insight is to give job seekers a practical, transparent, and affordable way to evaluate their resumes.

The first goal is usefulness.  
The second goal is credibility.  
The third goal is product potential.

Start simple. Build phase by phase. Keep each release stable before adding more.
