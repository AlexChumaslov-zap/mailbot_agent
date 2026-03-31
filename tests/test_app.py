from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.models.email_model import EmailEntry, EmailEntryCreate


@pytest.fixture
def client():
    """Create a test client with RAG import patched out to avoid needing FAISS + docs."""
    with patch("app.services.gemini_service.retrieve"):
        from main import app
        yield TestClient(app)


# ── Model validation ──────────────────────────────────────────────────

def test_email_entry_create_valid():
    entry = EmailEntryCreate(email="user@example.com", title="Hi", message="Hello")
    assert entry.email == "user@example.com"
    assert entry.title == "Hi"


def test_email_entry_create_invalid_email():
    with pytest.raises(Exception):
        EmailEntryCreate(email="not-an-email", title="Hi", message="Hello")


def test_email_entry_strips_whitespace():
    entry = EmailEntryCreate(email="user@example.com", title="  Hi  ", message="  Msg  ")
    assert entry.title == "Hi"
    assert entry.message == "Msg"


# ── Route smoke tests ────────────────────────────────────────────────

def test_get_form(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "form" in response.text.lower() or "email" in response.text.lower()


def test_get_search_page(client):
    response = client.get("/search")
    assert response.status_code == 200


def test_get_rag_page(client):
    response = client.get("/rag")
    assert response.status_code == 200


def test_get_emails_page(client):
    with patch("app.services.email_service.get_all_entries", return_value=[]):
        response = client.get("/emails")
    assert response.status_code == 200


def test_submit_valid_email(client):
    with patch("app.services.email_service.save_entry"):
        response = client.post(
            "/",
            data={"email": "test@example.com", "title": "Test", "message": "Hello"},
            follow_redirects=False,
        )
    assert response.status_code == 303
    assert response.headers["location"] == "/emails"


def test_submit_invalid_email(client):
    response = client.post(
        "/",
        data={"email": "bad", "title": "Test", "message": "Hello"},
    )
    assert response.status_code == 422
