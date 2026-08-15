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
    # A URL (query params) é a fonte única da verdade para o roteamento
    query_id = st.query_params.get("id", None)

    if query_id and str(query_id).strip():
        selected_id = str(query_id).strip()
        st.session_state["selected_empreendimento_id"] = selected_id
        atlas.render(selected_id)
    else:
        st.session_state["selected_empreendimento_id"] = None
        if "id" in st.query_params:
            del st.query_params["id"]
        home.render()


if __name__ == "__main__":
    main()
