# src/core/prompts.py
"""Modulo per il caricamento e gestione dei prompt."""

from functools import lru_cache
from pathlib import Path

import yaml

PROMPTS_FILE = Path(__file__).parent / "prompts.yaml"


@lru_cache(maxsize=1)
def load_prompts() -> dict:
    """Carica i prompt dal file YAML.

    Returns:
        dict: Dizionario con tutti i prompt configurati.

    Raises:
        FileNotFoundError: Se il file prompts.yaml non esiste.
        yaml.YAMLError: Se il file YAML non è valido.
    """
    if not PROMPTS_FILE.exists():
        raise FileNotFoundError(f"File prompts non trovato: {PROMPTS_FILE}")

    with open(PROMPTS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


class Prompts:
    """Classe per accedere ai prompt in modo strutturato."""

    def __init__(self):
        self._prompts = load_prompts()

    @property
    def agent(self) -> dict:
        """Prompt relativi all'agente."""
        return self._prompts.get("agent", {})

    @property
    def tools(self) -> dict:
        """Prompt relativi agli strumenti."""
        return self._prompts.get("tools", {})

    @property
    def ui(self) -> dict:
        """Messaggi dell'interfaccia utente."""
        return self._prompts.get("ui", {})

    # --- Agent Prompts ---

    @property
    def system_prompt(self) -> str:
        """Prompt di sistema principale dell'agente."""
        return self.agent.get("system_prompt", "")

    @property
    def title_generation_prompt(self) -> str:
        """Prompt per generare il titolo della conversazione."""
        return self.agent.get("title_generation_prompt", "")

    @property
    def error_prompt(self) -> str:
        """Prompt per messaggi di errore."""
        return self.agent.get("error_prompt", "")

    # --- Tool Prompts ---

    @property
    def stock_scoring_prompt(self) -> str:
        """Prompt per lo scoring delle azioni."""
        return self.tools.get("stock_scoring_prompt", "")

    @property
    def web_search_context_prompt(self) -> str:
        """Prompt per contestualizzare risultati web."""
        return self.tools.get("web_search_context_prompt", "")

    @property
    def kb_write_prompt(self) -> str:
        """Prompt per scrivere nella knowledge base."""
        return self.tools.get("kb_write_prompt", "")

    # --- UI Messages ---

    @property
    def welcome_message(self) -> str:
        """Messaggio di benvenuto."""
        return self.ui.get("welcome_message", "")

    @property
    def loading_message(self) -> str:
        """Messaggio di caricamento."""
        return self.ui.get("loading_message", "")

    @property
    def empty_conversation_message(self) -> str:
        """Messaggio per conversazione vuota."""
        return self.ui.get("empty_conversation_message", "")

    @property
    def disclaimer(self) -> str:
        """Disclaimer dell'interfaccia."""
        return self.ui.get("disclaimer", "")

    def format(self, prompt_name: str, **kwargs) -> str:
        """Formatta un prompt con i parametri forniti.

        Args:
            prompt_name: Nome del prompt (es. "error_prompt", "stock_scoring_prompt")
            **kwargs: Parametri da sostituire nel prompt

        Returns:
            str: Prompt formattato
        """
        prompt = getattr(self, prompt_name, "")
        if prompt and kwargs:
            return prompt.format(**kwargs)
        return prompt


# Singleton per accesso globale
prompts = Prompts()
