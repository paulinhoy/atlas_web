"""
views/chatbot.py - Tela do Assistente Virtual / Chatbot do Atlas
Interface isolada construída com componentes nativos do Streamlit para posterior evolução.
"""

from pathlib import Path
import streamlit as st

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
                padding: 1.5rem 2rem;
                border-radius: 12px;
                color: #ffffff;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }
            .chatbot-header h2 {
                font-size: 1.6rem;
                font-weight: 700;
                color: #ffffff;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .chatbot-header .sub {
                font-size: 0.90rem;
                color: #d1e3f8;
                margin-top: 0.3rem;
                font-weight: 300;
            }

            /* ---- Botão Voltar Flutuante (Floating Action Pill) ---- */
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
                padding: 0.60rem 1.25rem;
                border-radius: 30px;
                font-size: 0.85rem;
                font-weight: 600;
                text-decoration: none !important;
                box-shadow: 0 4px 18px rgba(11, 37, 69, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.15);
                transition: all 0.2s ease;
                backdrop-filter: blur(8px);
            }
            .atlas-floating-back-btn:hover {
                background: linear-gradient(135deg, #133b63 0%, #1d4ed8 100%);
                color: #ffffff !important;
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
            <h2>💬 Assistente Virtual — Atlas de Empreendimentos</h2>
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

    # 2. Cabeçalho
    render_header()

    # 3. Inicialização do histórico na sessão
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": "Olá! Sou o assistente virtual do **Atlas de Empreendimentos (PELTMG)**. Como posso te ajudar hoje?",
            }
        ]

    # 4. Exibição das mensagens do histórico
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 5. Entrada do usuário com layout nativo simples
    if prompt := st.chat_input("Digite sua pergunta ou mensagem aqui..."):
        # Adiciona e renderiza mensagem do usuário
        st.session_state["chat_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Resposta mock inicial para teste de visual/fluxo
        bot_reply = (
            f"Recebi sua mensagem: *\"{prompt}\"*\n\n"
            "Esta é a versão inicial para validação de layout. Nas próximas etapas, conectaremos o assistente à base de dados de empreendimentos."
        )
        with st.chat_message("assistant"):
            st.markdown(bot_reply)

        st.session_state["chat_messages"].append({"role": "assistant", "content": bot_reply})
