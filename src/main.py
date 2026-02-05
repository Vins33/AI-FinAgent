# src/main.py
"""Application entry point - FastAPI backend with NiceGUI frontend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from nicegui import ui

from src.api.endpoints import router
from src.services.database import async_engine, init_db
from src.services.models import Base
from src.ui.pages.chat_page import ChatPage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("Starting application...")
    await init_db()
    print("Database initialized.")
    yield
    print("Shutting down...")


# Create FastAPI app
fastapi_app = FastAPI(
    title="Financial Agent API",
    description="API for financial agent with LangGraph.",
    version="2.0.0",
    lifespan=lifespan,
)

fastapi_app.include_router(router, prefix="/api", tags=["API"])


@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# NiceGUI pages
@ui.page("/")
async def index():
    """Main chat page."""
    # Enable dark mode for ChatGPT-like appearance
    ui.dark_mode(True)
    ui.add_head_html(
        """
        <style>
            body { margin: 0; padding: 0; background-color: #343541; }
            .nicegui-content { height: 100vh; }
            .q-textarea .q-field__control { background: transparent !important; }
            .q-textarea textarea { color: white !important; }
            .q-textarea .q-placeholder { color: #8e8ea0 !important; }
        </style>
        """
    )
    chat_page = ChatPage(is_dark=True)
    await chat_page.render()


# Initialize NiceGUI with FastAPI
ui.run_with(
    fastapi_app,
    title="Agente Finanziario",
    storage_secret="financial-agent-secret",
)
