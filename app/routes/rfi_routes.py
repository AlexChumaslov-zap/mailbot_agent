from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.database import get_all_rfis, get_rfi_by_id

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/rfi-emails", response_class=HTMLResponse)
async def list_rfi_emails(request: Request):
    """Render the list of all captured RFI emails."""
    rfis = get_all_rfis()
    return templates.TemplateResponse("rfi_list.html", {"request": request, "rfis": rfis})


@router.get("/rfi-emails/{rfi_id}", response_class=HTMLResponse)
async def view_rfi_email(request: Request, rfi_id: int):
    """Render a single RFI email with its attachments."""
    rfi = get_rfi_by_id(rfi_id)
    if rfi is None:
        return HTMLResponse("RFI email not found", status_code=404)
    return templates.TemplateResponse("rfi_detail.html", {"request": request, "rfi": rfi})
