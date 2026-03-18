from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from typing import Optional

from app.models.email_model import EmailEntryCreate
from app.services import email_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def show_form(request: Request, error: Optional[str] = None):
    """Render the email submission form."""
    return templates.TemplateResponse("form.html", {"request": request, "error": error})


@router.post("/", response_class=HTMLResponse)
async def submit_form(
    request: Request,
    email: str = Form(...),
    phone: str = Form(""),
    title: str = Form(""),
    message: str = Form(""),
):
    """
    Validate and save a new entry.
    On success: redirect to /emails.
    On validation error: re-render form with error message.
    """
    try:
        entry = EmailEntryCreate(email=email, phone=phone, title=title, message=message)
    except ValidationError as exc:
        # Extract the first human-readable error message
        first_error = exc.errors()[0]["msg"]
        return templates.TemplateResponse(
            "form.html",
            {"request": request, "error": first_error, "form_data": {
                "email": email, "phone": phone, "title": title, "message": message
            }},
            status_code=422,
        )

    email_service.save_entry(entry)
    return RedirectResponse(url="/emails", status_code=303)


@router.get("/emails", response_class=HTMLResponse)
async def list_emails(request: Request):
    """Render the list of all submitted entries."""
    entries = email_service.get_all_entries()
    return templates.TemplateResponse("list.html", {"request": request, "entries": entries})
