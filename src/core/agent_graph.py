# src/core/agent_graph.py
"""LangGraph agent for financial analysis."""

from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.core.agent_tools import available_tools_list
from src.core.config import settings
from src.core.prompts import prompts


class AgentState(TypedDict):
    """State for the agent graph."""

    messages: Annotated[Sequence[BaseMessage], add_messages]


# Tool node
tool_node = ToolNode(available_tools_list)

# LLM configuration (parametri da config.py)
llm = ChatOllama(
    model=settings.LLM_MODEL_NAME,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=settings.LLM_TEMPERATURE,
    keep_alive=settings.LLM_KEEP_ALIVE,
    seed=settings.LLM_SEED,
    num_ctx=settings.LLM_NUM_CTX,
)

llm_with_tools = llm.bind_tools(available_tools_list)


async def call_model_node(state: AgentState) -> dict:
    """Call the LLM node."""
    print("--- GRAPH: Calling LLM ---")
    messages = state["messages"]
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


def should_continue_edge(state: AgentState) -> str:
    """Decide whether to continue to tools or end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    return "end_conversation"


# Build the graph
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model_node)
workflow.add_node("action", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue_edge,
    {"continue_to_tools": "action", "end_conversation": END},
)
workflow.add_edge("action", "agent")

# Compile without checkpointer first (will be added dynamically)
app = workflow.compile()

# Async checkpointer for PostgreSQL
_checkpointer = None
_checkpointer_cm = None


async def get_checkpointer() -> AsyncPostgresSaver:
    """Get or create the async Postgres checkpointer."""
    global _checkpointer, _checkpointer_cm
    if _checkpointer is None:
        _checkpointer_cm = AsyncPostgresSaver.from_conn_string(settings.CHECKPOINT_PG_DSN)
        _checkpointer = await _checkpointer_cm.__aenter__()
        await _checkpointer.setup()
    return _checkpointer


async def get_compiled_graph():
    """Get the compiled graph with checkpointer."""
    checkpointer = await get_checkpointer()
    return workflow.compile(checkpointer=checkpointer)


def format_history_to_langchain(messages: list[dict]) -> list[BaseMessage]:
    """Convert message dicts to LangChain message objects."""
    history = []
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")
        if role == "user":
            history.append(HumanMessage(content=content))
        elif role in ("assistant", "agent"):
            history.append(AIMessage(content=content, tool_calls=msg.get("tool_calls", [])))
    return history


async def get_agent_graph_response(
    user_query: str,
    chat_history: list[dict],
    thread_id: str | None = None,
) -> AIMessage:
    """Invoke the agent graph and return the response.

    Args:
        user_query: The user's question
        chat_history: Previous messages in the conversation
        thread_id: Optional thread ID for checkpointing. If provided,
                   the graph will use PostgreSQL checkpointing to save state.
    """
    formatted_history = format_history_to_langchain(chat_history)

    # Log per debug
    print(f"--- GRAPH: History contains {len(formatted_history)} messages ---")
    if formatted_history:
        # Mostra gli ultimi 3 messaggi per debug
        for msg in formatted_history[-3:]:
            preview = msg.content[:100] if len(msg.content) > 100 else msg.content
            print(f"    [{msg.__class__.__name__}]: {preview}...")

    messages = [
        SystemMessage(content=prompts.system_prompt),
        *formatted_history,
        HumanMessage(content=user_query),
    ]

    # Use checkpointed graph if thread_id is provided
    if thread_id:
        graph = await get_compiled_graph()
        config = {"configurable": {"thread_id": thread_id}}
        final_state = await graph.ainvoke({"messages": messages}, config=config)
    else:
        # Use non-checkpointed graph for simple invocations
        final_state = await app.ainvoke({"messages": messages})

    return final_state["messages"][-1]
