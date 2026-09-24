"""
views/chatbot.py - Tela do Assistente Virtual / Chatbot do Atlas
Interface isolada construída com componentes nativos do Streamlit para posterior evolução.
"""

import uuid
import streamlit as st
from services import chatbot_service, chat_logger
from views.ui import inject_css, render_back_button


def render_header():
    """Renderiza o cabeçalho do assistente virtual."""
    st.markdown(
        """
        <div class="chatbot-header">
            <h2>Assistente Virtual — Atlas de Empreendimentos</h2>
            <div class="sub">
                Tire dúvidas sobre os empreendimentos priorizados, custos e cenários do PELTMG
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render():
    """Função principal de renderização da tela do Chatbot."""
    inject_css("chatbot")

    # 1. Botão flutuante de retorno
    render_back_button()

    # 2. Cabeçalho institucional
    render_header()

    # 3. Inicialização de sessão única para logs
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())[:8]

    # 4. Inicialização do histórico de mensagens
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Sou o assistente virtual do **Atlas de Empreendimentos (PELTMG)**. "
                    "Posso consultar dados de priorização, valores financeiros, custos de obras e estatísticas da carteira. "
                    "Como posso te ajudar hoje?"
                ),
            }
        ]

    # 5. Exibição das mensagens do histórico
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 6. Entrada de mensagem do usuário
    if prompt := st.chat_input("Digite sua pergunta sobre os empreendimentos do PELTMG..."):
        # Adiciona e exibe mensagem do usuário
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Registra mensagem do usuário no log diário
        chat_logger.log_message(
            session_id=st.session_state["session_id"],
            role="user",
            content=prompt,
        )

        # Gera resposta via chatbot_service com spinner
        with st.chat_message("assistant"):
            with st.spinner("Consultando dados do Atlas..."):
                bot_reply = chatbot_service.generate_response(
                    user_prompt=prompt,
                    session_id=st.session_state["session_id"],
                    chat_history=st.session_state["chat_messages"][:-1],
                )
                st.markdown(bot_reply)

        # Adiciona resposta no histórico da sessão
        st.session_state["chat_messages"].append({"role": "assistant", "content": bot_reply})

