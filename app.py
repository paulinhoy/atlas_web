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
    # Sincroniza query params da URL com o estado da sessão
    query_id = st.query_params.get("id", None)
    if query_id:
        st.session_state["selected_empreendimento_id"] = query_id
    elif "selected_empreendimento_id" not in st.session_state:
        st.session_state["selected_empreendimento_id"] = None

    selected_id = st.session_state["selected_empreendimento_id"]

    # Roteamento entre telas
    if selected_id:
        atlas.render(selected_id)
    else:
        home.render()


if __name__ == "__main__":
    main()
