"""
Tela do Atlas - Ficha Técnica e Detalhamento do Empreendimento Selecionado
"""

import streamlit as st
from services import data_loader


def render(empreendimento_id):
    # Botão para voltar à tela inicial
    col_nav, _ = st.columns([1, 5])
    with col_nav:
        if st.button("⬅ Voltar para a Lista"):
            st.session_state["selected_empreendimento_id"] = None
            if "id" in st.query_params:
                del st.query_params["id"]
            st.rerun()

    df_emp = data_loader.get_empreendimentos()
    if df_emp.empty:
        st.error("Dados de empreendimentos não encontrados.")
        return

    # Localiza o empreendimento pelo ID
    id_col = "id_empreendimento" if "id_empreendimento" in df_emp.columns else df_emp.columns[0]
    emp_record = df_emp[df_emp[id_col].astype(str) == str(empreendimento_id)]

    if emp_record.empty:
        st.error(f"Empreendimento com ID '{empreendimento_id}' não foi encontrado.")
        return

    emp_data = emp_record.iloc[0]
    nome_emp = emp_data.get("nome_empreendimento", f"Empreendimento {empreendimento_id}")

    # Cabeçalho
    st.title(f"{empreendimento_id} - {nome_emp}")
    st.divider()

    st.info("Estrutura do Atlas pronta. Quando os dados forem carregados, preencheremos o Mapa, Indicadores e Tabelas aqui.")
