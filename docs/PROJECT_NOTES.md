# SustainIQ — Project brief for Claude Code

AI-powered sustainability assessment tool for German SMEs. Companies enter
operational data and receive EU benchmarking, a CSRD/ESRS gap analysis,
AI recommendations, dashboards, and a PDF report.

This is a portfolio project for Werkstudent / internship applications at
sustainability and e-mobility companies in Germany. Code quality, clear
structure, and a clean Git history matter as much as features.

## About the developer
- Student, Sustainable Resources, Engineering and Management (Hochschule Magdeburg-Stendal)
- Comfortable with: Python, SQL, HTML, basic web development
- Still learning: React, API design, deployment
- Must be able to explain every part of this codebase in a job interview

## How to work with me (always follow)
1. Before writing code, explain in 3-5 sentences what you will build and why.
2. Work in small steps. One feature per task. Never create many files at once without asking.
3. Write clean, commented code. Comments explain *why*, not only *what*.
4. After each step, tell me exactly how to test it (commands + what I should see).
5. If something is complex, simplify it for my level and explain the concept in plain words.
6. Prefer free and open-source options.
7. Do not add a dependency without saying why it is needed.
8. After each completed step, update the "Progress" section at the bottom of this file.
9. After each working step, suggest a short Git commit message. Do not commit unless I say so.

## Tech stack
- Frontend: React + Vite + Tailwind CSS (utility classes, not inline styles)
- Charts: Recharts
- Backend: Python 3.11+, FastAPI, Pydantic v2
- AI: Anthropic Python SDK. The model name lives in `.env` as `CLAUDE_MODEL` (never hardcode it)
- Database: SQLite via SQLAlchemy (stores past assessments)
- PDF export: decide in Phase 2 (WeasyPrint or ReportLab)
- Tests: pytest for the backend
- Deployment: Vercel (frontend) + Render free tier (backend)

## Folder structure
```
sustainiq/
├── CLAUDE.md
├── README.md
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, routes, CORS
│   │   ├── config.py        # loads settings from .env
│   │   ├── models.py        # Pydantic request/response schemas
│   │   ├── benchmarks.py    # EU/Eurostat sector benchmark data, each with a source
│   │   ├── scoring.py       # per-FTE metrics, benchmark comparison, 0-100 score
│   │   ├── analyzer.py      # builds the prompt, calls Claude, parses the answer
│   │   └── database.py      # SQLite / SQLAlchemy (Phase 2)
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── components/      # form sections, charts, result cards
    │   ├── pages/           # AssessmentForm, Results
    │   ├── api/client.js    # every fetch call to the backend lives here
    │   └── App.jsx
    └── package.json
```

## Domain rules (sustainability)
- Input metrics: company name, sector, employees (FTE), energy (kWh/yr),
  renewable share (%), Scope 1+2 emissions (t CO2e/yr), waste (t/yr),
  recycling rate (%), water (m3/yr). Scope 3 comes later.
- Normalise per FTE before benchmarking.
- Sectors: manufacturing, logistics & transport, food & retail, construction, other.
- Every benchmark value has a `source` field (Eurostat table, UBA, SBTi, EU Taxonomy).
  Values that are estimates are marked `indicative: true` and shown as indicative in the UI.
  Never present an estimate as an official figure.
- Regulatory frame: CSRD, ESRS E1 (climate), E2 (pollution), E3 (water),
  E5 (resource use / circular economy), EU Taxonomy, German EnEfG.
  Funding references: KfW, BAFA.
- The score and benchmark comparison are calculated in Python (deterministic and testable).
  Claude only writes the summary, recommendations, CSRD gaps, and quick wins.
- Claude's answer must be structured JSON, validated with Pydantic before it reaches the frontend.

## Security
- Never commit `.env` or API keys. `.env` must be in `.gitignore` from the first commit.
- Validate every input with Pydantic (percentages 0-100, employees > 0, no negative values).
- CORS: localhost in development, the real frontend domain in production.

## Phases
- Phase 1 (MVP): input form, FastAPI `/analyse`, benchmarks, scoring, Claude analysis, results page
- Phase 2: Recharts benchmark charts, score gauge, PDF export, save assessments in SQLite
- Phase 3: CSRD checklist, progress tracking across assessments, deployment, README with screenshots

## Progress
(Claude Code updates this after each step)
- [x] Step 1: project scaffold, .gitignore, Git init
  - Python 3.11.9 installed (user scope, on PATH).
- [x] Step 2: backend venv, requirements.txt (fastapi, uvicorn), FastAPI app with GET /health
- [x] Step 3: config.py (pydantic-settings, loads .env), CORS limited to frontend origin
- [x] Step 4: models.py (AssessmentInput + Sector enum with validation), pytest setup, 18 tests passing
- [x] Step 5: benchmarks.py (5 sectors x 6 metrics, all indicative with source), 29 tests passing
  - TODO: verify values against real Eurostat/UBA downloads; switch to indicative=False only with exact table + year
- [x] Step 6: scoring.py (per-FTE metrics, linear 0-100 metric score, weighted overall score), MetricResult/ScoreResult schemas, 51 tests passing
- [x] Step 7: POST /analyse (validated input, returns ScoreResult, no Claude yet), API tests with TestClient + httpx2, 57 tests passing
- [x] Step 8: analyzer.py (Claude via anthropic SDK messages.parse, structured AIAnalysis output, friendly errors), /analyse returns AnalysisResponse (score always, AI text if available), 68 tests passing with fake client
  - TODO: live test with real ANTHROPIC_API_KEY + CLAUDE_MODEL in backend/.env
- [x] Step 9: frontend scaffold (Vite 8 + React 19, Tailwind CSS 4 via @tailwindcss/vite), demo files removed, start page
- [x] Step 10: api/client.js (analyseCompany, 422 -> field errors), FormField component, AssessmentForm page (9 fields, example data button), raw JSON result view (temporary)
