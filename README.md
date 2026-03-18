# Email Collector

A lightweight FastAPI web application for collecting and storing contact form submissions.

## Features

- Submit contact entries with email, phone, title, and message fields
- Email validation via Pydantic
- View all submitted entries in a list
- Data persisted to a local JSON file (`data.json`)
- Server-side rendered HTML with Jinja2 templates

## Project Structure

```
├── main.py                   # FastAPI app entry point
├── requirements.txt
├── data.json                 # Persistent storage (auto-created)
├── app/
│   ├── models/
│   │   └── email_model.py    # Pydantic models
│   ├── routes/
│   │   └── email_routes.py   # Route handlers
│   └── services/
│       └── email_service.py  # Read/write logic
├── templates/
│   ├── base.html
│   ├── form.html             # Submission form
│   └── list.html             # Entries list
└── static/
    └── style.css
```

## Setup

```bash
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
uvicorn main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## Endpoints

| Method | Path      | Description                  |
|--------|-----------|------------------------------|
| GET    | `/`       | Display the submission form  |
| POST   | `/`       | Submit a new entry           |
| GET    | `/emails` | List all submitted entries   |
