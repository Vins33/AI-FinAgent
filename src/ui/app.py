# src/ui/app.py
"""NiceGUI application entry point."""

from nicegui import app, ui

from src.services.database import init_db
from src.ui.pages.chat_page import ChatPage


async def startup():
    """Application startup tasks."""
    await init_db()


@ui.page("/")
async def index():
    """Main page route."""
    ui.dark_mode(False)

    # Page configuration
    ui.add_head_html(
        """
        <style>
            body { margin: 0; padding: 0; }
            .nicegui-content { height: 100vh; }
        </style>
        """
    )

    # Render chat page
    chat_page = ChatPage()
    await chat_page.render()


def create_app():
    """Create and configure the NiceGUI application."""
    app.on_startup(startup)
    return app


# For running directly
if __name__ in {"__main__", "__mp_main__"}:
    create_app()
    ui.run(
        title="Agente Finanziario",
        host="0.0.0.0",
        port=8080,
        reload=False,
        show=False,
    )
