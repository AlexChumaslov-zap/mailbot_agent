# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Email Collector** — a FastAPI web app that collects contact form submissions (email, title, message) and persists them to a local `data.json` file. Also includes an AI-powered web search page backed by Google Gemini 2.0 Flash with Google Search grounding. Server-side rendered with Jinja2 templates.

## Development Commands

```bash
# Activate virtual environment (bash)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn main:app --reload
```

App available at http://localhost:8000. FastAPI auto-generates API docs at http://localhost:8000/docs.

## Environment Variables

| Variable        | Description                        |
|-----------------|------------------------------------|
| `GEMINI_API_KEY`| Google Gemini API key (in `.env`)  |

## Architecture

```
main.py                    # FastAPI app init, mounts /static, registers routes
app/
  models/email_model.py    # Pydantic models: EmailEntry (stored), EmailEntryCreate (incoming)
  services/email_service.py    # JSON file read/write; get_all_entries(), save_entry()
  services/gemini_service.py   # Gemini client; search_with_gemini(query) → {answer, sources}
  routes/email_routes.py   # GET / (form), POST / (submit), GET /emails (list)
  routes/search_routes.py  # GET /search (form), POST /search (query → Gemini)
templates/                 # Jinja2 HTML (base.html, form.html, list.html, search.html)
static/style.css           # App styling
data.json                  # Flat-file persistence (auto-created on first submission)
.env                       # Local secrets — not committed
```

**Email data flow:** Form POST → route handler → `EmailEntryCreate` validation → `save_entry()` appends UTC-timestamped `EmailEntry` to `data.json` → redirect to `/emails`.

**Search data flow:** Form POST → `search_with_gemini(query)` → Gemini 2.0 Flash with `google_search` tool → returns `answer` (str) and `sources` (list of `{title, uri}`) → rendered in `search.html`.

**No database, no auth, no tests.** Concurrent writes to `data.json` are not safe.
