import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.email_routes import router as email_router
from app.routes.search_routes import router as search_router
from app.routes.rag_routes import router as rag_router


@asynccontextmanager
async def lifespan(app):
    """Download docs and data from S3 on startup (only when S3_BUCKET is set)."""
    if os.getenv("S3_BUCKET"):
        from app.services.s3_service import download_dir, download_file
        download_dir("docs/", "docs")
        download_file("data.json", "data.json")
    yield


app = FastAPI(title="Email Collector", version="1.0.0", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routes
app.include_router(email_router)
app.include_router(search_router)
app.include_router(rag_router)
