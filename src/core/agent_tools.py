# src/core/agent_tools.py
"""LangChain tools for the financial agent."""

import asyncio
import json
import uuid

from langchain.tools import tool

from src.core.logging import get_logger
from src.core.schemas import (
    CompanyProfileSchema,
    CompareStocksSchema,
    DividendAnalysisSchema,
    EarningsCalendarSchema,
    KBReadSchema,
    KBWriteSchema,
    StockAnalysisSchema,
    StockNewsSchema,
    StockPriceSchema,
    TechnicalIndicatorsSchema,
    WebSearchSchema,
)
from src.services.financial import (
    analyze_stock_sync,
    company_profile_sync,
    compare_stocks_sync,
    dividend_analysis_sync,
    earnings_calendar_sync,
    get_stock_price_sync,
    stock_news_sync,
    technical_indicators_sync,
)
from src.services.knowledge import google_search
from src.services.llm import OllamaService
from src.services.vector_store import VectorStoreService

logger = get_logger("tools")


@tool("web_search_tool", args_schema=WebSearchSchema)
async def web_search_tool(query: str) -> str:
    """
    Use this tool to search the web for up-to-date information, news, or events that cannot be found in the
    knowledge base or other tools. Use only if the user requests recent or time-sensitive data, or if you cannot
    answer from internal sources. Never invent information. Maximum 2 calls per user request. Always answer in
    the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "web_search_tool", "query": query})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, google_search, query, 1)
        logger.debug("Tool completed", extra={"tool_name": "web_search_tool"})
        return result
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "web_search_tool", "error": str(e)})
        return f"Search error: {str(e)}"


@tool("read_from_kb_tool", args_schema=KBReadSchema)
async def read_from_kb_tool(query: str) -> str:
    """
    Use this tool to retrieve conceptual, procedural, or stable information from the internal knowledge base.
    Always try this tool before using web search for general knowledge questions.
    Never invent information. Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "read_from_kb_tool", "query": query})
    try:
        ollama = OllamaService()
        vector_store = VectorStoreService()

        embedding = await ollama.create_embedding(query)
        if not embedding:
            return "Error: Could not create embedding."

        context = await vector_store.search(embedding, limit=1)
        logger.debug("Tool completed", extra={"tool_name": "read_from_kb_tool"})
        return context
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "read_from_kb_tool", "error": str(e)})
        return f"KB read error: {str(e)}"


@tool("write_to_kb_tool", args_schema=KBWriteSchema)
async def write_to_kb_tool(content: str) -> str:
    """
    Use this tool to save reusable definitions, guidelines, or stable information to the internal knowledge base.
    Never use it for time-sensitive data such as prices or news. Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "write_to_kb_tool", "content_length": len(content)})
    try:
        ollama = OllamaService()
        vector_store = VectorStoreService()

        embedding = await ollama.create_embedding(content)
        if not embedding:
            return "Error: Could not create embedding."

        point_id = uuid.uuid4().int & ((1 << 63) - 1)
        await vector_store.add_context(question_id=point_id, embedding=embedding, text=content)
        logger.debug("Tool completed", extra={"tool_name": "write_to_kb_tool", "point_id": point_id})
        return f"Information saved to KB (ID: {point_id})."
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "write_to_kb_tool", "error": str(e)})
        return f"KB write error: {str(e)}"


@tool("stock_scoring_tool", args_schema=StockAnalysisSchema)
async def stock_scoring_tool(ticker: str) -> str:
    """
    Use this tool to calculate a BUY/HOLD/SELL score for a stock using fundamental indicators (P/E, ROE, D/E, Beta,
    Dividend Yield, Growth, EV/EBITDA). Never invent or estimate scores. Always call this tool for stock ratings.
    Return the result as JSON. Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "stock_scoring_tool", "ticker": ticker})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, analyze_stock_sync, ticker)
        logger.debug("Tool completed", extra={"tool_name": "stock_scoring_tool", "ticker": ticker})
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "stock_scoring_tool", "ticker": ticker, "error": str(e)})
        return json.dumps(
            {"ticker": ticker, "error": f"Analysis error: {str(e)}"},
            ensure_ascii=False,
        )


@tool("stock_price_tool", args_schema=StockPriceSchema)
async def stock_price_tool(ticker: str, period: str = "1mo") -> str:
    """
    Use this tool to get the current price, historical data, and trend for a stock. Always use this tool for price,
    percentage change, or trend questions. Never invent or estimate prices. If the user does not specify a period,
    use the default "1mo". Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "stock_price_tool", "ticker": ticker, "period": period})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, get_stock_price_sync, ticker, period)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "stock_price_tool", "error": str(e)})
        return json.dumps({"ticker": ticker, "error": str(e)}, ensure_ascii=False)


@tool("compare_stocks_tool", args_schema=CompareStocksSchema)
async def compare_stocks_tool(tickers: list[str]) -> str:
    """
    Use this tool to compare 2-5 stocks side by side on key metrics (P/E, ROE, Market Cap, Dividend Yield, Beta, etc.).
      Never invent or estimate comparison data. Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "compare_stocks_tool", "tickers": tickers})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, compare_stocks_sync, tickers)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "compare_stocks_tool", "error": str(e)})
        return json.dumps({"tickers": tickers, "error": str(e)}, ensure_ascii=False)


@tool("dividend_analysis_tool", args_schema=DividendAnalysisSchema)
async def dividend_analysis_tool(ticker: str) -> str:
    """
    Use this tool to analyze the dividend history and metrics for a stock (dividend yield, payout ratio,
    ex-dividend date,    YoY growth, history).
    Never invent or estimate dividend data. Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "dividend_analysis_tool", "ticker": ticker})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, dividend_analysis_sync, ticker)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "dividend_analysis_tool", "error": str(e)})
        return json.dumps({"ticker": ticker, "error": str(e)}, ensure_ascii=False)


@tool("company_profile_tool", args_schema=CompanyProfileSchema)
async def company_profile_tool(ticker: str) -> str:
    """
    Use this tool to retrieve the official company profile (sector, industry, country, employees, website, description).
    Always use this tool to verify or find a ticker from a company name. Never invent or guess company data.
    Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "company_profile_tool", "ticker": ticker})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, company_profile_sync, ticker)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "company_profile_tool", "error": str(e)})
        return json.dumps({"ticker": ticker, "error": str(e)}, ensure_ascii=False)


@tool("stock_news_tool", args_schema=StockNewsSchema)
async def stock_news_tool(ticker: str) -> str:
    """
    Use this tool to get the latest 5 news headlines for a stock from financial sources.
    Use for sentiment analysis or recent events. Never invent or summarize news from memory.
    Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "stock_news_tool", "ticker": ticker})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, stock_news_sync, ticker)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "stock_news_tool", "error": str(e)})
        return json.dumps({"ticker": ticker, "error": str(e)}, ensure_ascii=False)


@tool("technical_indicators_tool", args_schema=TechnicalIndicatorsSchema)
async def technical_indicators_tool(ticker: str, period: str = "3mo") -> str:
    """
    Use this tool to calculate technical indicators (SMA, RSI,
    volume analysis, support/resistance, RSI signal) for a stock.
    Never invent or estimate technical data. If the user does not specify a period, use the default "3mo".
    Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "technical_indicators_tool", "ticker": ticker, "period": period})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, technical_indicators_sync, ticker, period)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "technical_indicators_tool", "error": str(e)})
        return json.dumps({"ticker": ticker, "error": str(e)}, ensure_ascii=False)


@tool("earnings_calendar_tool", args_schema=EarningsCalendarSchema)
async def earnings_calendar_tool(ticker: str) -> str:
    """
    Use this tool to get the earnings calendar for a stock (next earnings date, EPS history, surprise %).
    Always use this tool for earnings-related questions. Never invent or estimate earnings data.
    Always answer in the user's language.
    """
    logger.info("Tool invoked", extra={"tool_name": "earnings_calendar_tool", "ticker": ticker})
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, earnings_calendar_sync, ticker)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        logger.error("Tool failed", extra={"tool_name": "earnings_calendar_tool", "error": str(e)})
        return json.dumps({"ticker": ticker, "error": str(e)}, ensure_ascii=False)


available_tools_list = [
    web_search_tool,
    read_from_kb_tool,
    write_to_kb_tool,
    stock_scoring_tool,
    stock_price_tool,
    compare_stocks_tool,
    dividend_analysis_tool,
    company_profile_tool,
    stock_news_tool,
    technical_indicators_tool,
    earnings_calendar_tool,
]
