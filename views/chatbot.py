"""
views/chatbot.py - Tela do Assistente Virtual / Chatbot do Atlas
Interface isolada construída com componentes nativos do Streamlit para posterior evolução.
"""

import uuid
from pathlib import Path
import streamlit as st
from services import chatbot_service, chat_logger

BASE_DIR = Path(__file__).resolve().parent.parent
LOGOS_DIR = BASE_DIR / "logos"


def apply_chatbot_styles():
    """Aplica estilos CSS customizados para a tela do Chatbot."""
    st.markdown(
        """
        <style>
            /* Cabeçalho institucional */
            .chatbot-header {
                background: linear-gradient(135deg, #0b2545 0%, #133b63 100%);
                padding: 1.4rem 2rem;
                border-radius: 12px;
                color: #ffffff;
                margin-bottom: 1.2rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }
            .chatbot-header h2 {
                font-size: 28px;
                font-weight: 700;
                color: #ffffff;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 10px;
                line-height: 1.3;
            }
            .chatbot-header .sub {
                font-size: 24px;
                color: #d1e3f8;
                margin-top: 0.3rem;
                font-weight: 300;
                line-height: 1.3;
            }

            /* Barra de Conformidade e Ações */
            .chatbot-toolbar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                margin-bottom: 1.2rem;
                font-size: 13px;
                color: #64748b;
            }

            /* ---- 1. Ocultar avatares / ícones completamente ---- */
            div[data-testid="stChatMessageAvatar"],
            div[data-testid="chatAvatarIcon-user"],
            div[data-testid="chatAvatarIcon-assistant"] {
                display: none !important;
            }

            /* ---- 2. Balões de Mensagem ---- */
            div[data-testid="stChatMessage"] {
                display: block !important;
                padding: 1.0rem 1.4rem !important;
                border-radius: 12px !important;
                margin-top: 0.4rem !important;
                margin-bottom: 1.0rem !important;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
            }

            /* Reset dos espaçamentos internos do Markdown do Streamlit */
            div[data-testid="stChatMessageContent"],
            div[data-testid="stChatMessageContent"] > div,
            div[data-testid="stChatMessageContent"] .stMarkdown,
            div[data-testid="stChatMessageContent"] div[data-testid="stMarkdownContainer"] {
                padding: 0 !important;
                margin: 0 !important;
                width: 100% !important;
            }

            div[data-testid="stChatMessageContent"] p {
                margin: 0 !important;
                padding: 0 !important;
                font-size: 15px !important;
                line-height: 1.6 !important;
            }

            div[data-testid="stChatMessageContent"] p:not(:last-child) {
                margin-bottom: 0.6rem !important;
            }

            /* Balão do USUÁRIO -> Direita (compacto e estilizado) */
            div[data-testid="stChatMessage"]:has(div[data-testid*="user"]) {
                margin-left: auto !important;
                margin-right: 0 !important;
                width: fit-content !important;
                max-width: 75% !important;
                background: linear-gradient(135deg, #0b2545 0%, #133b63 100%) !important;
                color: #ffffff !important;
                border-radius: 16px !important;
                border-bottom-right-radius: 4px !important;
                border: none !important;
                text-align: left !important;
            }
            div[data-testid="stChatMessage"]:has(div[data-testid*="user"]) p,
            div[data-testid="stChatMessage"]:has(div[data-testid*="user"]) span,
            div[data-testid="stChatMessage"]:has(div[data-testid*="user"]) strong,
            div[data-testid="stChatMessage"]:has(div[data-testid*="user"]) em {
                color: #ffffff !important;
            }

            /* Balão do ASSISTENTE -> Esquerda (Tom Claro da Paleta PELT #BAD6D9 / #9BA0BF) */
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) {
                margin-right: 0 !important;
                margin-left: 0 !important;
                width: 100% !important;
                max-width: 100% !important;
                background: linear-gradient(135deg, rgba(186, 214, 217, 0.28) 0%, rgba(155, 160, 191, 0.16) 100%) !important;
                border: 1.5px solid #BAD6D9 !important;
                border-left: 5px solid #9BA0BF !important;
                color: #0b2545 !important;
                border-radius: 12px !important;
                box-shadow: 0 2px 8px rgba(155, 160, 191, 0.12) !important;
                text-align: left !important;
            }
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) p,
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) span,
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) strong,
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) em {
                color: #0b2545 !important;
            }

            /* Tabelas embutidas nas respostas do assistente */
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) table {
                font-size: 12px !important;
                border-collapse: collapse !important;
                width: 100% !important;
                margin: 0.8rem 0 !important;
                border-radius: 6px !important;
                overflow: hidden !important;
                background: #ffffff !important;
            }
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) th {
                font-size: 14px !important;
                font-weight: 600 !important;
                background: #0b2545 !important;
                color: #ffffff !important;
                padding: 6px 10px !important;
            }
            div[data-testid="stChatMessage"]:has(div[data-testid*="assistant"]) td {
                font-size: 12px !important;
                padding: 6px 10px !important;
                border-bottom: 1px solid #e2e8f0 !important;
            }

            /* ---- 3. Campo de Digitação Limpo e Sem Caixas Claras Internas ---- */
            div[data-testid="stBottomBlockContainer"] {
                background-color: transparent !important;
            }
            div[data-testid="stBottomBlockContainer"] > div {
                background-color: transparent !important;
            }

            div[data-testid="stChatInput"] {
                background-color: transparent !important;
                border: none !important;
                padding: 0 !important;
            }

            /* Zerar qualquer fundo ou contorno das caixas internas do BaseWeb */
            div[data-testid="stChatInput"] div[data-baseweb="base-input"],
            div[data-testid="stChatInput"] div[data-baseweb="textarea"],
            div[data-testid="stChatInput"] textarea {
                background-color: transparent !important;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                outline: none !important;
            }
            
            /* Cápsula externa única e limpa */
            div[data-testid="stChatInput"] > div {
                background-color: #ffffff !important;
                border: 1.5px solid #cbd5e1 !important;
                border-radius: 28px !important;
                box-shadow: 0 3px 12px rgba(0, 0, 0, 0.05) !important;
                transition: all 0.2s ease !important;
                padding: 0.35rem 0.50rem 0.35rem 1.25rem !important;
                display: flex !important;
                align-items: center !important;
            }
            div[data-testid="stChatInput"] > div:focus-within {
                border-color: #0b2545 !important;
                box-shadow: 0 0 0 3px rgba(186, 214, 217, 0.40), 0 4px 16px rgba(0, 0, 0, 0.08) !important;
            }

            div[data-testid="stChatInput"] textarea {
                color: #0f172a !important;
                font-size: 14px !important;
                line-height: 1.45 !important;
                padding: 0.30rem 0 !important;
                margin: 0 !important;
            }
            div[data-testid="stChatInput"] textarea::placeholder {
                color: #94a3b8 !important;
                font-weight: 400 !important;
            }

            /* Botão de Enviar */
            div[data-testid="stChatInput"] button {
                position: static !important;
                background: #0b2545 !important;
                color: #ffffff !important;
                border-radius: 50% !important;
                width: 32px !important;
                min-width: 32px !important;
                height: 32px !important;
                min-height: 32px !important;
                border: none !important;
                padding: 0 !important;
                margin: 0 4px 0 8px !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
                align-self: center !important;
                box-shadow: 0 2px 4px rgba(11, 37, 69, 0.2) !important;
            }
            div[data-testid="stChatInput"] button:hover:not(:disabled) {
                background: #133b63 !important;
                transform: scale(1.06) !important;
            }
            div[data-testid="stChatInput"] button:disabled {
                background: #e2e8f0 !important;
                cursor: not-allowed !important;
                box-shadow: none !important;
            }
            div[data-testid="stChatInput"] button svg {
                width: 16px !important;
                height: 16px !important;
                fill: #ffffff !important;
                color: #ffffff !important;
                margin: auto !important;
                display: block !important;
            }
            div[data-testid="stChatInput"] button:disabled svg {
                fill: #94a3b8 !important;
                color: #94a3b8 !important;
            }

            /* ---- 4. Botão Voltar Flutuante (Floating Action Pill) ---- */
            .atlas-floating-back-btn {
                position: fixed;
                bottom: 24px;
                left: 24px;
                z-index: 99999;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: linear-gradient(135deg, #0b2545 0%, #133b63 100%);
                color: #ffffff !important;
                padding: 0.65rem 1.30rem;
                border-radius: 30px;
                font-size: 14px;
                font-weight: 600;
                text-decoration: none !important;
                box-shadow: 0 4px 18px rgba(11, 37, 69, 0.35);
                border: 1.5px solid #BAD6D9;
                transition: all 0.2s ease;
                backdrop-filter: blur(8px);
            }
            .atlas-floating-back-btn:hover {
                background: linear-gradient(135deg, #133b63 0%, #1d4ed8 100%);
                color: #ffffff !important;
                border-color: #ffffff;
                transform: translateY(-2px);
                box-shadow: 0 6px 22px rgba(11, 37, 69, 0.45);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_back_button():
    """Botão flutuante idêntico ao do Atlas para retorno à lista de empreendimentos."""
    st.markdown(
        """
        <a href="?" target="_self" class="atlas-floating-back-btn">
            <span style="font-size: 1.1rem; line-height: 1;">←</span>
            <span>Voltar para a Lista</span>
        </a>
        """,
        unsafe_allow_html=True,
    )


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
    apply_chatbot_styles()

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

