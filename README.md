# Email Collector

A lightweight FastAPI web application for collecting contact form submissions, with an AI-powered web search feature backed by Google Gemini.

## Features

- Submit contact entries with email, title, and message fields
- Email validation via Pydantic
- View all submitted entries in a list
- Data persisted to a local JSON file (`data.json`)
- Server-side rendered HTML with Jinja2 templates
- **AI Web Search** — ask any question and get an answer from Gemini 2.0 Flash with live Google Search grounding, including cited sources

## Project Structure

```
├── main.py                   # FastAPI app entry point
├── requirements.txt
├── .env                      # GEMINI_API_KEY (not committed)
├── data.json                 # Persistent storage (auto-created)
├── app/
│   ├── models/
│   │   └── email_model.py    # Pydantic models
│   ├── routes/
│   │   └── email_routes.py   # Route handlers for form submission
│   │   └── search_routes.py  # Route handlers for AI search
│   └── services/
│       └── email_service.py  # Read/write logic for data.json
│       └── gemini_service.py # Gemini API client with Google Search grounding
├── templates/
│   ├── base.html
│   ├── form.html             # Submission form
│   ├── list.html             # Entries list
│   └── search.html           # AI search form and results
└── static/
    └── style.css
```

## Setup

```bash
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the project root with your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

## Running

```bash
uvicorn main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## Endpoints

| Method | Path      | Description                                  |
|--------|-----------|----------------------------------------------|
| GET    | `/`       | Display the submission form                  |
| POST   | `/`       | Submit a new entry                           |
| GET    | `/emails` | List all submitted entries                   |
| GET    | `/search` | Display the AI web search form               |
| POST   | `/search` | Run a query through Gemini with web search   |
