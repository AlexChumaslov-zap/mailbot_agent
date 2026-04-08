import os
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.email_routes import router as email_router
from app.routes.search_routes import router as search_router
from app.routes.rag_routes import router as rag_router
from app.routes.rfi_routes import router as rfi_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app):
    """Initialize database, start IMAP listener, and download resources from S3 on startup."""
    from app.services.database import init_db
    init_db()

    if os.getenv("S3_BUCKET"):
        from app.services.s3_service import download_dir
        download_dir("docs/", "docs")

    # Start IMAP IDLE listener in a daemon thread
    if os.getenv("IMAP_EMAIL"):
        from app.services.imap_service import idle_loop
        imap_thread = threading.Thread(target=idle_loop, daemon=True, name="imap-idle")
        imap_thread.start()
        logging.getLogger(__name__).info("IMAP IDLE listener started")

    yield


app = FastAPI(title="Email Collector", version="1.0.0", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routes
app.include_router(email_router)
app.include_router(search_router)
app.include_router(rag_router)
app.include_router(rfi_router)
