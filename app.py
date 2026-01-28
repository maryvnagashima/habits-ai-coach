import streamlit as st
from agent import process_action, ask_llm, load_session, save_session, WORKSPACE

st.set_page_config(page_title="AgentLocal", layout="wide")
st.title("🤖 AgentLocal – Seu colega de trabalho offline")
st.caption(f"Trabalhando em: {WORKSPACE}")

if "history" not in st.session_state:
    session_data = load_session()
    st.session_state.history = session_data.get("history", [])

# Exibir histórico
for msg in st.session_state.history:
    if msg.startswith("Usuário:"):
        with st.chat_message("user"):
            st.write(msg.replace("Usuário: ", ""))
    else:
        with st.chat_message("assistant"):
            st.write(msg.replace("Agente: ", ""))

# Entrada do usuário
if prompt := st.chat_input("Descreva uma tarefa (ex: crie um arquivo README.md com instruções)"):
    # Adicionar mensagem do usuário
    st.session_state.history.append(f"Usuário: {prompt}")
    with st.chat_message("user"):
        st.write(prompt)

    # Processar com agente
    with st.chat_message("assistant"):
        with st.spinner("Pensando e agindo..."):
            context = "\n".join(st.session_state.history[-6:])
            raw_response = ask_llm(prompt, context)
            result = process_action(raw_response)
            st.write(result)
            st.session_state.history.append(f"Agente: {result}")
            save_session({"history": st.session_state.history})