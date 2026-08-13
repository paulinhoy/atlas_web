"""
Atlas Web - Aplicação Principal
Gerencia o roteamento entre a Home (lista/busca) e o Atlas (ficha do empreendimento).
"""

import streamlit as st
from views import home, atlas

# Configurações gerais da página
st.set_page_config(
    page_title="Atlas de Empreendimentos",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main():
    # Inicializa estado da sessão se não existir
    if "selected_empreendimento_id" not in st.session_state:
        # Verifica se veio parâmetro na URL (ex: ?id=113)
        query_id = st.query_params.get("id", None)
        st.session_state["selected_empreendimento_id"] = query_id

    selected_id = st.session_state["selected_empreendimento_id"]

    # Roteamento entre telas
    if selected_id:
        atlas.render(selected_id)
    else:
        home.render()


if __name__ == "__main__":
    main()
