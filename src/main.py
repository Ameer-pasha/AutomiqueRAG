from fastapi import FastAPI

from src.api import admin, chat, documents, health
from src.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.2.0")
app.include_router(health.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
