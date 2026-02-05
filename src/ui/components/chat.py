# src/ui/components/chat.py
"""Chat UI components - WhatsApp-like style with rounded bubbles."""

from nicegui import ui


class ChatMessage:
    """A single chat message component - WhatsApp style bubble."""

    def __init__(self, role: str, content: str, is_dark: bool = True):
        self.role = role
        self.content = content
        self.is_dark = is_dark
        self._render()

    def _render(self):
        is_user = self.role == "user"

        # WhatsApp-like bubble styling
        if is_user:
            # User message: green bubble, aligned right
            bubble_bg = "bg-[#005c4b]" if self.is_dark else "bg-[#dcf8c6]"
            bubble_text = "text-white" if self.is_dark else "text-gray-800"
            align_class = "justify-end"
            rounded_class = "rounded-3xl rounded-tr-lg"
            margin_class = "ml-16"
        else:
            # Assistant message: dark/light bubble, aligned left
            bubble_bg = "bg-[#202c33]" if self.is_dark else "bg-white"
            bubble_text = "text-gray-100" if self.is_dark else "text-gray-800"
            align_class = "justify-start"
            rounded_class = "rounded-3xl rounded-tl-lg"
            margin_class = "mr-16"

        # Message row
        with ui.row().classes(f"w-full {align_class} px-4 py-1"):
            with ui.column().classes(f"{margin_class} max-w-[75%]"):
                # Bubble container
                with ui.element("div").classes(
                    f"{bubble_bg} {rounded_class} px-4 py-2 shadow-md border border-white/5"
                ):
                    # Avatar + content for assistant
                    if not is_user:
                        with ui.row().classes("items-center gap-2 mb-1"):
                            ui.icon("smart_toy").classes("text-purple-400 text-xs")
                            ui.label("Assistente").classes("text-purple-400 text-xs font-semibold")

                    # Message content
                    ui.markdown(self.content).classes(f"{bubble_text} text-sm leading-relaxed")

                    # Timestamp (optional, styled like WhatsApp)
                    # ui.label("10:30").classes("text-xs text-gray-400 text-right mt-1")


class ChatInput:
    """Chat input component - Floating centered style."""

    def __init__(self, on_send: callable, is_dark: bool = True):
        self.on_send = on_send
        self.is_dark = is_dark
        self.input_ref = None
        self.is_sending = False
        self._render()

    def _render(self):
        input_bg = "bg-[#2a3942]" if self.is_dark else "bg-white"
        text_class = "text-white" if self.is_dark else "text-gray-800"
        border_class = "border-[#3b4a54]" if self.is_dark else "border-gray-300"

        # Floating container centered at bottom
        with ui.element("div").classes("w-full flex justify-center px-4 pb-4 pt-2"):
            # Floating input bar - max width, centered
            with (
                ui.row()
                .classes(
                    f"{input_bg} w-full max-w-3xl rounded-3xl border {border_class} px-4 py-2 items-end gap-2 shadow-lg"
                )
                .style("min-height: 44px;")
            ):
                # Input field - auto-grows with content
                self.input_ref = (
                    ui.textarea(placeholder="Scrivi un messaggio...")
                    .classes(f"flex-grow {text_class} bg-transparent resize-none leading-normal")
                    .props("autogrow rows=1 borderless dense")
                    .style("max-height: 150px; min-height: 24px; padding: 4px 0;")
                    .on("keydown.enter.prevent", self._handle_send)
                )

                # Send button
                self.send_btn = (
                    ui.button(icon="send", on_click=self._handle_send)
                    .props("round dense")
                    .classes("bg-[#00a884] hover:bg-[#00c49a] text-white self-center")
                )

    async def _handle_send(self):
        if self.input_ref.value and not self.is_sending:
            self.is_sending = True
            self.send_btn.props("loading")
            message = self.input_ref.value
            self.input_ref.value = ""
            try:
                await self.on_send(message)
            finally:
                self.is_sending = False
                self.send_btn.props(remove="loading")

    def disable(self):
        self.input_ref.disable()
        self.send_btn.disable()

    def enable(self):
        self.input_ref.enable()
        self.send_btn.enable()


class ChatContainer:
    """Container for chat messages - WhatsApp style with background pattern."""

    # CSS for rounded markdown tables and global rounded corners
    TABLE_STYLE = """
    <style>
    /* Rounded tables in markdown */
    .nicegui-markdown table {
        border-collapse: separate !important;
        border-spacing: 0 !important;
        border-radius: 16px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        margin: 8px 0 !important;
    }
    .nicegui-markdown th {
        background: rgba(0,0,0,0.4) !important;
        padding: 12px 16px !important;
        font-weight: 600 !important;
    }
    .nicegui-markdown td {
        padding: 10px 16px !important;
        border-top: 1px solid rgba(255,255,255,0.08) !important;
    }
    .nicegui-markdown th:first-child { border-top-left-radius: 16px !important; }
    .nicegui-markdown th:last-child { border-top-right-radius: 16px !important; }
    .nicegui-markdown tr:last-child td:first-child { border-bottom-left-radius: 16px !important; }
    .nicegui-markdown tr:last-child td:last-child { border-bottom-right-radius: 16px !important; }

    /* Global rounded scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.2);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.3);
    }

    /* Round all Quasar inputs */
    .q-field--outlined .q-field__control {
        border-radius: 24px !important;
    }
    .q-textarea .q-field__control {
        border-radius: 20px !important;
    }

    /* Code blocks rounded */
    .nicegui-markdown pre {
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    .nicegui-markdown code {
        border-radius: 6px !important;
    }

    /* Blockquotes rounded */
    .nicegui-markdown blockquote {
        border-radius: 8px !important;
        border-left: 4px solid #00a884 !important;
        padding: 8px 16px !important;
        background: rgba(0,0,0,0.2) !important;
    }
    </style>
    """

    def __init__(self, is_dark: bool = True):
        self.is_dark = is_dark
        self.container = None
        self.scroll_area = None
        self._render()

    def _render(self):
        # WhatsApp-like chat background
        if self.is_dark:
            bg_style = (
                "background-color: #0b141a; "
                "background-image: url(\"data:image/svg+xml,%3Csvg width='60' height='60' "
                "viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' "
                "fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.02'%3E"
                "%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4z"
                "M6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\");"
            )
        else:
            bg_style = (
                "background-color: #efeae2; "
                "background-image: url(\"data:image/svg+xml,%3Csvg width='60' height='60' "
                "viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' "
                "fill-rule='evenodd'%3E%3Cg fill='%23000000' fill-opacity='0.03'%3E"
                "%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4z"
                "M6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\");"
            )

        # Inject table styles globally
        ui.add_head_html(self.TABLE_STYLE)

        self.scroll_area = ui.scroll_area().classes("w-full flex-grow").style(bg_style)
        with self.scroll_area:
            self.container = ui.column().classes("w-full py-4")

    def add_message(self, role: str, content: str):
        with self.container:
            ChatMessage(role, content, self.is_dark)

    def clear(self):
        self.container.clear()

    def scroll_to_bottom(self):
        """Scroll to bottom - sync version to avoid slot issues."""
        try:
            self.scroll_area.scroll_to(percent=1.0)
        except Exception:
            pass  # Ignore if element deleted
