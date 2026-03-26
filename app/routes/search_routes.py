from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services import gemini_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Render the search form."""
    return templates.TemplateResponse("search.html", {"request": request})


@router.post("/search", response_class=HTMLResponse)
async def search_query(request: Request, query: str = Form(...)):
    """Send query to Gemini with web search and render results."""
    try:
        result = gemini_service.search_with_gemini(query)
        return templates.TemplateResponse("search.html", {
            "request": request,
            "query": query,
            "answer": result["answer"],
            "sources": result["sources"],
        })
    except RuntimeError as e:
        return templates.TemplateResponse("search.html", {
            "request": request,
            "query": query,
            "error": str(e),
        }, status_code=503)
