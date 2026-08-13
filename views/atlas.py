"""
Tela do Atlas - Ficha Técnica e Detalhamento do Empreendimento Selecionado
"""

from pathlib import Path
import streamlit as st
import pandas as pd
from services import data_loader

BASE_DIR = Path(__file__).resolve().parent.parent
LOGOS_DIR = BASE_DIR / "logos"


def render(empreendimento_id):
    """Renderiza a página de Atlas do empreendimento."""
    df_emp = data_loader.get_empreendimentos()

    if df_emp.empty:
        st.error("Base de empreendimentos não encontrada.")
        return

    # Busca o empreendimento selecionado
    record = df_emp[df_emp["id_empreendimento"].astype(str) == str(empreendimento_id)]

    if record.empty:
        st.error(f"Empreendimento com ID '{empreendimento_id}' não foi encontrado.")
        if st.button("⬅ Voltar para a Lista"):
            st.session_state["selected_empreendimento_id"] = None
            if "id" in st.query_params:
                del st.query_params["id"]
            st.rerun()
        return

    row = record.iloc[0]
    nome_emp = row.get("nome_empreendimento", "")
    setor = row.get("setor", "")
    esfera = row.get("esfera_acao", "")

    # Barra superior de navegação
    col_voltar, col_info = st.columns([1.5, 4.5])
    with col_voltar:
        if st.button("⬅ Voltar para a Lista de Empreendimentos", use_container_width=True):
            st.session_state["selected_empreendimento_id"] = None
            if "id" in st.query_params:
                del st.query_params["id"]
            st.rerun()

    # Cabeçalho da Ficha Técnica
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #0b2545 0%, #133b63 100%); padding: 1.5rem; border-radius: 10px; color: white; margin-top: 0.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                <div>
                    <h2 style="color: white; margin: 0; font-size: 1.6rem; font-weight: 700;">{empreendimento_id} - {nome_emp}</h2>
                    <div style="margin-top: 0.4rem; color: #cbd5e1; font-size: 0.95rem;">
                        <b>Setor:</b> {setor} &nbsp;|&nbsp; <b>Esfera:</b> {esfera}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.success(f"Conexão com a página do Atlas funcionando perfeitamente para o empreendimento **{empreendimento_id}**!")
    st.info("Na próxima etapa iremos montar o layout completo da ficha técnica (painel esquerdo de metadados, espaço do mapa, e as 4 tabelas de dados).")
