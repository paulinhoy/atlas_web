"""
Tela Inicial - Listagem e seleção de Empreendimentos
"""

import streamlit as st
from services import data_loader


def render():
    st.title("🗺️ Atlas de Empreendimentos")
    st.caption("Selecione um empreendimento na tabela abaixo para abrir sua Ficha Técnica.")

    df_emp = data_loader.get_empreendimentos()

    if df_emp.empty:
        st.warning(
            "Nenhum dado encontrado na pasta `data/processed/`. "
            "Coloque seus arquivos CSV na pasta `data/raw/` e execute o script `scripts/process_data.py`."
        )
        return

    st.subheader(f"Lista de Empreendimentos ({len(df_emp)} registros)")

    # Exibição simples com seleção
    cols_to_show = [col for col in ["id_empreendimento", "nome_empreendimento", "setor", "esfera", "status"] if col in df_emp.columns]
    if not cols_to_show:
        cols_to_show = df_emp.columns.tolist()

    event = st.dataframe(
        df_emp[cols_to_show],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Se o usuário selecionou uma linha na tabela
    selected_rows = event.selection.get("rows", [])
    if selected_rows:
        selected_index = selected_rows[0]
        selected_record = df_emp.iloc[selected_index]
        id_col = "id_empreendimento" if "id_empreendimento" in selected_record else df_emp.columns[0]
        selected_id = selected_record[id_col]

        st.session_state["selected_empreendimento_id"] = selected_id
        st.query_params["id"] = str(selected_id)
        st.rerun()
