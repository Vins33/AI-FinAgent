# Percorso file: pages/3_Chat_con_Agente_Graph.py

import asyncio

import nest_asyncio
import streamlit as st

from src.core.agent_graph import get_agent_graph_response

nest_asyncio.apply()
st.set_page_config(page_title="Agente LangGraph", layout="wide")
st.title("🤖 Chat con Agente (LangGraph)")
st.markdown("""
Questa chat è connessa a un agente LangGraph.
L'agente può decidere autonomamente se:
1.  **Cercare sul web** (tramite `web_search_tool`)
2.  **Leggere dalla Knowledge Base** (tramite `read_from_kb_tool`)
3.  **Scrivere nella Knowledge Base** (tramite `write_to_kb_tool`)
""")


if "agent_graph_messages" not in st.session_state:
    st.session_state.agent_graph_messages = []

for message in st.session_state.agent_graph_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Esempio: 'Cosa è successo oggi a Milano?'"):


    user_message = {"role": "user", "content": prompt}
    st.session_state.agent_graph_messages.append(user_message)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("L'Agente LangGraph sta elaborando... (Controlla il terminale per i log dei tool)"):
            history_for_agent = st.session_state.agent_graph_messages[:-1]

            try:
                final_response_message = asyncio.run(get_agent_graph_response(prompt, history_for_agent))

                response_text = final_response_message.content

                st.markdown(response_text)
                st.session_state.agent_graph_messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "tool_calls": final_response_message.tool_calls
                })

            except Exception as e:
                error_msg = f"Si è verificato un errore critico nel grafo: {str(e)}"
                st.error(error_msg)
                st.session_state.agent_graph_messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "tool_calls": []
                })
