# Percorso file: src/core/agent_graph.py
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.core.agent_tools import available_tools_list
from src.core.config import settings


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

tool_node = ToolNode(available_tools_list)

llm = ChatOllama(
    model=settings.LLM_MODEL_NAME,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0.1,
    keep_alive="4h",
    seed=42
)

llm_with_tools = llm.bind_tools(available_tools_list)

async def call_model_node(state: AgentState) -> dict:
    """Nodo 1: Il "Cervello". Chiama l'LLM (Invariato)"""
    print("--- GRAFO: Chiamo LLM ---")
    messages = state['messages']
    response_ai_message = await llm_with_tools.ainvoke(messages)
    return {"messages": [response_ai_message]}

def should_continue_edge(state: AgentState) -> str:
    """Edge Condizionale: Decide la prossima mossa (Invariato)."""
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    else:
        return "end_conversation"

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model_node)
workflow.add_node("action", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue_edge,
    {
        "continue_to_tools": "action",
        "end_conversation": END
    }
)

workflow.add_edge("action", "agent")

app = workflow.compile()


def format_st_history_to_langchain(st_messages: list[dict]) -> list:
    """Converte la history di Streamlit (dict) nel formato LangChain (oggetti BaseMessage)."""
    history = []
    for msg in st_messages:
        role = msg["role"]
        if role == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif role == "assistant":
            history.append(AIMessage(content=msg.get("content", ""), tool_calls=msg.get("tool_calls", [])))
    return history

async def get_agent_graph_response(user_query: str, chat_history: list[dict]) -> AIMessage:
    """
    Funzione principale che invoca il grafo LangGraph (Invariata).
    """
    formatted_history = format_st_history_to_langchain(chat_history)
    current_messages = formatted_history + [HumanMessage(content=user_query)]

    final_state = await app.ainvoke(
        {"messages": current_messages}
    )

    return final_state['messages'][-1]
