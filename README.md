# Financial Document Analyzer

A multi-agent financial document analysis system built with **CrewAI** and **FastAPI**. Upload a financial PDF (annual reports, 10-K filings, earnings statements) and get comprehensive analysis including document verification, financial metrics extraction, investment recommendations, and risk assessment.

## Architecture

The system uses 4 specialized AI agents working sequentially:

1. **Document Verifier** — Validates the uploaded file is a legitimate financial document and extracts metadata.
2. **Senior Financial Analyst** — Extracts key financial metrics (revenue, net income, EBITDA, cash flow) and answers the user's query.
3. **Investment Strategy Advisor** — Provides data-driven investment recommendations for different risk profiles.
4. **Risk Assessment Specialist** — Evaluates liquidity, leverage, market, and operational risks with a structured risk rating.

---

## 🐳 Quick Start (Docker — Recommended)

```bash
# 1. Copy .env.sample and add your API key
cp .env.sample .env
# Edit .env and set your LLM_API_KEY

# 2. Run everything
docker compose up --build
```
This starts **Redis + FastAPI + Celery worker** — all in one command. API available at `http://localhost:8000`.

---

## Setup & Installation (Manual)

### Prerequisites
- Python 3.10+
- A Cerebras API key (or Gemini API key — see LLM config below)
- **[For async mode]** Redis server ([Download Redis](https://redis.io/downloads/))

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/DevSujal/financial-document-analyzer-debug
cd financial-document-analyzer-debug

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install python-multipart celery redis

# 4. Configure environment variables
# Create a .env file in the project root:
echo CEREBRAS_API_KEY=your_api_key_here > .env
# Optional: set Redis URL (defaults to redis://localhost:6379/0)
echo REDIS_URL=redis://localhost:6379/0 >> .env
```

### LLM Configuration

The project uses **LiteLLM** under the hood (via CrewAI), so you can use any supported provider. Edit `agents.py`:

```python
# Cerebras (default)
llm = LLM(model="cerebras/gpt-oss-120b", api_key=os.getenv("CEREBRAS_API_KEY"))

# Google Gemini
llm = LLM(model="gemini/gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

# OpenAI
llm = LLM(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
```

---

## Running the Application (Manual)

### Basic Mode (synchronous)
```bash
python main.py
```
The server starts at `http://localhost:8000`.

### With Celery Queue Worker (async mode)
```bash
# Terminal 1: Start Redis server
redis-server

# Terminal 2: Start Celery worker
celery -A celery_worker.celery_app worker --loglevel=info --pool=solo

# Terminal 3: Start FastAPI server
python main.py
```

---

## API Documentation

### `GET /`
Health check endpoint.

**Response:**
```json
{ "message": "Financial Document Analyzer API is running" }
```

### `POST /analyze`
Upload a financial PDF and get a comprehensive analysis (synchronous — waits for result).

**Request (form-data):**

| Field   | Type   | Required | Description |
|---------|--------|----------|-------------|
| `file`  | File   | Yes      | PDF financial document to analyze |
| `query` | String | No       | Analysis query (default: "Analyze this financial document for investment insights") |

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@TSLA-Q2-2025-Update.pdf" \
  -F "query=What are the key revenue trends?"
```

**Success Response (200):**
```json
{
  "status": "success",
  "job_id": "abc-123-def",
  "query": "What are the key revenue trends?",
  "analysis": "Full multi-agent analysis output...",
  "file_processed": "TSLA-Q2-2025-Update.pdf"
}
```

### `POST /analyze/async` ⚡ (Bonus — Queue Worker)
Submit a document for async analysis via Celery. Returns immediately with a `job_id`.

**Request:** Same as `POST /analyze`

**Response (200):**
```json
{
  "status": "queued",
  "job_id": "abc-123-def",
  "message": "Analysis job submitted. Use GET /status/{job_id} to check progress."
}
```

### `GET /status/{job_id}` (Bonus — Queue Worker)
Poll for the status of an async analysis job.

**Response:**
```json
{
  "job_id": "abc-123-def",
  "filename": "TSLA-Q2-2025-Update.pdf",
  "query": "What are the key revenue trends?",
  "status": "completed",
  "result": "Full analysis output...",
  "error": null,
  "created_at": "2026-02-26 19:30:00",
  "completed_at": "2026-02-26 19:32:00"
}
```

### `GET /analyses` (Bonus — Database)
List all past analysis results.

**Response:**
```json
{
  "analyses": [
    {
      "job_id": "abc-123-def",
      "filename": "TSLA-Q2-2025-Update.pdf",
      "query": "...",
      "status": "completed",
      "created_at": "2026-02-26 19:30:00",
      "completed_at": "2026-02-26 19:32:00"
    }
  ]
}
```

### `GET /analyses/{job_id}` (Bonus — Database)
Get the full detail of a specific past analysis, including the complete result.

---

## Bonus Features

### 🔄 Queue Worker Model (Celery + Redis)
Long-running CrewAI analysis is offloaded to a Celery worker via Redis message broker. This allows:
- **Non-blocking requests** — `POST /analyze/async` returns immediately
- **Concurrent processing** — Multiple analysis jobs can run in parallel
- **Job tracking** — Poll `GET /status/{job_id}` for progress updates

**Files:** `celery_worker.py`

### 🗄️ Database Integration (SQLite + SQLAlchemy)
All analysis results (both sync and async) are persisted in a SQLite database (`analysis_results.db`). This enables:
- **Result history** — Browse past analyses via `GET /analyses`
- **Job persistence** — Results survive server restarts
- **Status tracking** — Every job goes through `pending → processing → completed/failed`

**Files:** `database.py`

---

## Bugs Found & Fixed

### Deterministic Bugs

#### Bug 1: Invalid Tool Import in `tools.py`
- **Error:** `ValidationError: Input should be a valid dictionary or instance of BaseTool`
- **Cause:** Imported non-existent `tools` from `crewai_tools`. Custom tool functions were plain methods, not CrewAI tools.
- **Fix:** Added `@tool` decorator, proper imports (`from crewai.tools import tool`, `PyPDFLoader`), type hints, and changed `async def` to `def`.

#### Bug 2: Missing Docstrings on Tool Functions in `tools.py`
- **Error:** `ValueError: Function must have a docstring`
- **Cause:** CrewAI's `@tool` decorator requires docstrings. Two functions were missing them.
- **Fix:** Added descriptive docstrings to `analyze_investment_tool` and `create_risk_assessment_tool`.

#### Bug 3: Missing `python-multipart` Dependency
- **Error:** `RuntimeError: Form data requires "python-multipart" to be installed.`
- **Cause:** FastAPI `File()` and `Form()` need this package but it was missing.
- **Fix:** Installed via `pip install python-multipart`.

#### Bug 4: Uvicorn `reload` Requires Import String in `main.py`
- **Error:** `WARNING: You must pass the application as an import string to enable 'reload'`
- **Cause:** `uvicorn.run(app, ..., reload=True)` passed the app object directly.
- **Fix:** Changed to `uvicorn.run("main:app", ...)`.

#### Bug 5: Typo `tool=` Instead of `tools=` in `agents.py`
- **Error:** Agent silently ignores the tools list.
- **Cause:** Used singular `tool=` instead of `tools=`.
- **Fix:** Renamed to `tools=`.

#### Bug 6: Function Name Shadowing in `main.py`
- **Error:** `500 Internal Server Error: 'function' object has no attribute 'get'`
- **Cause:** FastAPI route handler `analyze_financial_document` overwrote the imported CrewAI Task with the same name.
- **Fix:** Renamed route handler to `analyze_document_endpoint`.

#### Bug 7: Uploaded File Path Not Passed to CrewAI Task
- **Error:** `File path data/sample.pdf is not a valid file or url`
- **Cause:** `run_crew()` didn't forward `file_path` to crew inputs, and task descriptions lacked `{file_path}`.
- **Fix:** Added `file_path` to `kickoff()` inputs and task descriptions.

---

### Inefficient Prompts

#### Bug 8: Unprofessional Agent Prompts in `agents.py`
- **Problem:** All agent backstories encouraged hallucination, making up facts, ignoring user queries, and giving irresponsible financial advice.
- **Fix:** Rewrote all 4 agent prompts (financial_analyst, verifier, investment_advisor, risk_assessor) to be professional, data-driven, and ethically responsible.

#### Bug 9: Harmful Task Descriptions in `task.py`
- **Problem:** Task descriptions instructed agents to make up URLs, contradict themselves, ignore queries, and recommend scam investments.
- **Fix:** Rewrote all 4 task descriptions and expected outputs to produce structured, accurate financial analysis.

#### Bug 10: Wrong Agent Assigned to Verification Task
- **Problem:** `verification` task used `financial_analyst` agent instead of the `verifier` agent.
- **Fix:** Assigned correct agents: `verification` → `verifier`, `investment_analysis` → `investment_advisor`, `risk_assessment` → `risk_assessor`.

#### Bug 11: Only 1 Task Used in the Crew
- **Problem:** `main.py` only imported and used `analyze_financial_document`. The other 3 tasks (`verification`, `investment_analysis`, `risk_assessment`) were defined but never wired into the Crew.
- **Fix:** Imported all 4 agents and 4 tasks, and added all of them to the Crew running in sequential order.

#### Bug 12: `max_iter=1` and `max_rpm=1` Throttled Agents
- **Problem:** All agents had `max_iter=1` (only 1 reasoning step) and `max_rpm=1` (1 request per minute), severely limiting their ability to perform multi-step analysis.
- **Fix:** Increased to `max_iter=5` and `max_rpm=10` for proper multi-step reasoning.

---

## Files Modified / Added

| File | Changes |
|---|---|
| `tools.py` | Fixed imports, added `@tool` decorators, docstrings, type hints, `PyPDFLoader` import |
| `agents.py` | Rewrote all agent prompts, fixed `tool=` → `tools=`, increased `max_iter`/`max_rpm` |
| `task.py` | Rewrote all task prompts, fixed agent assignments, added `{file_path}` placeholder |
| `main.py` | Wired all 4 agents/tasks, added async endpoint, DB integration, job status endpoints |
| `database.py` | **[NEW]** SQLAlchemy models and helpers for SQLite analysis storage |
| `celery_worker.py` | **[NEW]** Celery app config and async analysis task with Redis broker |
