# src/services/knowledge.py
"""Knowledge retrieval service using SerpAPI."""

from serpapi import SerpApiClient

from src.core.config import settings


def google_search(query: str, num_results: int = 1) -> str:
    """
    Perform Google search using SerpAPI.
    Returns concatenated snippets from organic results.
    """
    try:
        params = {
            "q": query,
            "api_key": settings.SERPAPI_API_KEY,
            "engine": "google",
            "gl": "it",
            "hl": "it",
        }
        client = SerpApiClient(params)
        results = client.get_dict()

        organic_results = results.get("organic_results", [])
        snippets = [
            item.get("snippet", "")
            for item in organic_results[:num_results]
            if "snippet" in item
        ]

        if not snippets:
            return "No useful results found."

        return " ".join(snippets).replace("\n", " ")

    except Exception as e:
        print(f"SerpAPI search error: {e}")
        return "No information found due to an error."
