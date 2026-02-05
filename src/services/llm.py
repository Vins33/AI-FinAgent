# src/services/llm.py
"""Ollama LLM service."""

import httpx

from src.core.config import settings


class OllamaService:
    """Service for interacting with Ollama API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.llm_model = settings.LLM_MODEL_NAME
        self.embedding_model = settings.EMBEDDING_MODEL_NAME

    async def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Make async request to Ollama API."""
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.base_url}/api/{endpoint}", json=payload
            )
            response.raise_for_status()
            return response.json()

    async def create_embedding(self, text: str) -> list[float]:
        """Create embedding for text."""
        payload = {"model": self.embedding_model, "prompt": text}
        response = await self._make_request("embeddings", payload)
        return response.get("embedding", [])

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate text from prompt."""
        payload = {
            "model": self.llm_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = await self._make_request("generate", payload)
        return response.get("response", "").strip()

    async def classify_question(self, question: str) -> str:
        """Classify a question into a category."""
        prompt = f"""
        Classify the following question into a single concise category (max 2 words).
        Examples: 'Italian Cuisine', 'Web Development', 'Fitness', 'Digital Marketing'.
        Question: "{question}"
        Category:
        """
        return await self.generate(prompt, temperature=0.2)
