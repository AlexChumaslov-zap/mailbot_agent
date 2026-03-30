import asyncio

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services import gemini_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/rag", response_class=HTMLResponse)
async def rag_page(request: Request):
    return templates.TemplateResponse("rag.html", {"request": request})


@router.post("/rag", response_class=HTMLResponse)
async def rag_query(request: Request, query: str = Form(...)):
    try:
        result = await asyncio.to_thread(gemini_service.search_with_rag, query)
        return templates.TemplateResponse("rag.html", {
            "request": request,
            "query": query,
            "answer": result["answer"],
            "chunks": result["chunks"],
        })
    except RuntimeError as e:
        return templates.TemplateResponse("rag.html", {
            "request": request,
            "query": query,
            "error": str(e),
        }, status_code=503)
