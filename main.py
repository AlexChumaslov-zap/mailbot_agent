from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.email_routes import router as email_router
from app.routes.search_routes import router as search_router
from app.routes.rag_routes import router as rag_router

app = FastAPI(title="Email Collector", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register routes
app.include_router(email_router)
app.include_router(search_router)
app.include_router(rag_router)
