# src/core/agent_tools.py
"""LangChain tools for the financial agent."""

import asyncio
import json
import uuid

from langchain.tools import tool
from pydantic import BaseModel, Field

from src.services.financial import StockAnalysisSchema, analyze_stock_sync
from src.services.knowledge import google_search
from src.services.llm import OllamaService
from src.services.vector_store import VectorStoreService


class WebSearchSchema(BaseModel):
    """Schema for web search tool."""

    query: str = Field(description="The search query to send to Google.")


class KBReadSchema(BaseModel):
    """Schema for KB read tool."""

    query: str = Field(description="The query to search in the knowledge base.")


class KBWriteSchema(BaseModel):
    """Schema for KB write tool."""

    content: str = Field(description="The content to save to the knowledge base.")


@tool("web_search_tool", args_schema=WebSearchSchema)
async def web_search_tool(query: str) -> str:
    """
    Search for updated information on the web via Google.
    Use this for recent news, events, or time-sensitive data.
    Maximum 2 calls per request.
    """
    print(f"--- TOOL: web_search_tool (Query: {query}) ---")
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, google_search, query, 1)
        return result
    except Exception as e:
        return f"Search error: {str(e)}"


@tool("read_from_kb_tool", args_schema=KBReadSchema)
async def read_from_kb_tool(query: str) -> str:
    """
    Read information from the internal knowledge base.
    Use this for conceptual, procedural, or stable information.
    """
    print(f"--- TOOL: read_from_kb_tool (Query: {query}) ---")
    try:
        ollama = OllamaService()
        vector_store = VectorStoreService()

        embedding = await ollama.create_embedding(query)
        if not embedding:
            return "Error: Could not create embedding."

        context = await vector_store.search(embedding, limit=1)
        return context
    except Exception as e:
        return f"KB read error: {str(e)}"


@tool("write_to_kb_tool", args_schema=KBWriteSchema)
async def write_to_kb_tool(content: str) -> str:
    """
    Save information to the internal knowledge base.
    Use for reusable definitions, guidelines, or stable information.
    Do NOT save time-sensitive data like prices or news.
    """
    print(f"--- TOOL: write_to_kb_tool (Content: {content[:30]}...) ---")
    try:
        ollama = OllamaService()
        vector_store = VectorStoreService()

        embedding = await ollama.create_embedding(content)
        if not embedding:
            return "Error: Could not create embedding."

        point_id = uuid.uuid4().int & ((1 << 63) - 1)
        await vector_store.add_context(
            question_id=point_id, embedding=embedding, text=content
        )
        return f"Information saved to KB (ID: {point_id})."
    except Exception as e:
        return f"KB write error: {str(e)}"


@tool("stock_scoring_tool", args_schema=StockAnalysisSchema)
async def stock_scoring_tool(ticker: str) -> str:
    """
    Calculate a stock score (BUY/HOLD/SELL) using fundamental indicators.
    Metrics: P/E, ROE, D/E, Beta, Dividend Yield, Growth, EV/EBITDA.
    Returns JSON with metrics, score, and decision.
    """
    print(f"--- TOOL: stock_scoring_tool (Ticker: {ticker}) ---")
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, analyze_stock_sync, ticker)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps(
            {"ticker": ticker, "error": f"Analysis error: {str(e)}"},
            ensure_ascii=False,
        )


available_tools_list = [
    web_search_tool,
    read_from_kb_tool,
    write_to_kb_tool,
    stock_scoring_tool,
]
