"""
Tela Inicial (Home) - Painel Executivo e Busca de Empreendimentos Priorizados
"""

from pathlib import Path
import streamlit as st
import pandas as pd
from services import data_loader

BASE_DIR = Path(__file__).resolve().parent.parent
LOGOS_DIR = BASE_DIR / "logos"


def apply_custom_styles():
    """Aplica estilos CSS customizados para uma interface limpa, profissional e institucional."""
    st.markdown(
        """
        <style>
            /* Fonte e layout base */
            .main-header {
                background: linear-gradient(135deg, #0d2847 0%, #153e6b 100%);
                padding: 1.8rem 2rem;
                border-radius: 12px;
                color: #ffffff;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }
            .header-title {
                font-size: 1.9rem;
                font-weight: 700;
                letter-spacing: -0.5px;
                margin: 0;
                color: #ffffff;
            }
            .header-subtitle {
                font-size: 0.95rem;
                color: #d1e3f8;
                margin-top: 0.4rem;
                font-weight: 300;
            }
            .kpi-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 1.2rem;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .kpi-title {
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                color: #64748b;
                letter-spacing: 0.5px;
            }
            .kpi-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: #0f172a;
                margin-top: 0.2rem;
            }
            .kpi-subtext {
                font-size: 0.75rem;
                color: #94a3b8;
                margin-top: 0.2rem;
            }
            .filter-container {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 1rem 1.2rem;
                margin-bottom: 1.2rem;
            }
            /* Destaque para o botão de ação */
            div[data-testid="stDataFrame"] {
                border-radius: 8px;
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header():
    """Renderiza o cabeçalho institucional com as logos."""
    logo_pelt_path = LOGOS_DIR / "logo_pelt_branco.png"
    logo_codemge_path = LOGOS_DIR / "logo codemge - branco.png"

    with st.container():
        st.markdown(
            """
            <div class="main-header">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                    <div>
                        <div class="header-title">PELTMG — Atlas de Empreendimentos</div>
                        <div class="header-subtitle">
                            Plano Estadual de Logística e Transportes de Minas Gerais • Consulta à Carteira Priorizada
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_kpis(df: pd.DataFrame):
    """Renderiza cartões com indicadores resumidos dos empreendimentos."""
    total_emp = len(df)
    total_setores = df["setor"].nunique() if "setor" in df.columns else 0

    # Contagem de alto impacto
    col_impacto = "impacto_avaliado_3_pond_cenario"
    alto_impacto = len(df[df[col_impacto] == "Alto impacto"]) if col_impacto in df.columns else 0

    # Setores mais representativos
    top_setor = df["setor"].mode()[0] if "setor" in df.columns and not df.empty else "N/A"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Empreendimentos Priorizados</div>
                <div class="kpi-value">{total_emp:,}</div>
                <div class="kpi-subtext">Carteira avaliada</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Setores Atendidos</div>
                <div class="kpi-value">{total_setores}</div>
                <div class="kpi-subtext">Principal: <b>{top_setor}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Alto Impacto</div>
                <div class="kpi-value">{alto_impacto}</div>
                <div class="kpi-subtext">{((alto_impacto / total_emp) * 100):.1f}% do total</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        # TIRM média dos que possuem taxa declarada
        tirm_valid = df["tirm"].dropna() if "tirm" in df.columns else pd.Series()
        tirm_media = f"{tirm_valid.mean() * 100:.1f}%" if not tirm_valid.empty else "N/D"
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">TIRM Média Declarada</div>
                <div class="kpi-value">{tirm_media}</div>
                <div class="kpi-subtext">{len(tirm_valid)} projetos com TIRM</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")


def render():
    """Função principal da tela Home."""
    apply_custom_styles()
    render_header()

    df_emp = data_loader.get_empreendimentos()

    if df_emp.empty:
        st.error(
            "Nenhum dado encontrado em `data/processed/empreendimentos_priorizacao.parquet`.\n"
            "Execute o script `scripts/process_data.py` para processar a base de dados."
        )
        return

    # Renderiza KPIs
    render_kpis(df_emp)

    # Painel de Filtros e Busca
    st.markdown("### 🔍 Pesquisa e Seleção de Empreendimento")
    st.caption("Filtre a carteira ou pesquise pelo nome/código e selecione a linha na tabela para abrir o Atlas detalhado.")

    f_col1, f_col2, f_col3, f_col4 = st.columns([2.5, 1.5, 1.5, 1.5])

    with f_col1:
        busca = st.text_input(
            "Buscar por Nome ou Código ID:",
            placeholder="Ex: Ferrovia Centro-Atlântica, BR-381, 113...",
            key="busca_termo",
        )

    with f_col2:
        setores = ["Todos"] + sorted(df_emp["setor"].dropna().unique().tolist()) if "setor" in df_emp.columns else ["Todos"]
        filtro_setor = st.selectbox("Setor:", setores, key="filtro_setor")

    with f_col3:
        esferas = ["Todas"] + sorted(df_emp["esfera_acao"].dropna().unique().tolist()) if "esfera_acao" in df_emp.columns else ["Todas"]
        filtro_esfera = st.selectbox("Esfera:", esferas, key="filtro_esfera")

    col_impacto = "impacto_avaliado_3_pond_cenario"
    with f_col4:
        impactos = ["Todos"] + sorted(df_emp[col_impacto].dropna().unique().tolist()) if col_impacto in df_emp.columns else ["Todos"]
        filtro_impacto = st.selectbox("Classificação:", impactos, key="filtro_impacto")

    # Aplicação dos Filtros
    df_filtrado = df_emp.copy()

    if busca.strip():
        termo = busca.strip().lower()
        id_mask = df_filtrado["id_empreendimento"].astype(str).str.contains(termo, case=False, na=False)
        nome_mask = df_filtrado["nome_empreendimento"].astype(str).str.lower().str.contains(termo, na=False)
        df_filtrado = df_filtrado[id_mask | nome_mask]

    if filtro_setor != "Todos" and "setor" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["setor"] == filtro_setor]

    if filtro_esfera != "Todas" and "esfera_acao" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["esfera_acao"] == filtro_esfera]

    if filtro_impacto != "Todos" and col_impacto in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado[col_impacto] == filtro_impacto]

    st.write("")

    # Colunas formatadas para exibição na tabela
    display_cols_map = {
        "id_empreendimento": "ID",
        "nome_empreendimento": "Nome do Empreendimento",
        "setor": "Setor",
        "esfera_acao": "Esfera",
        "descr_status_empreendimento": "Status",
        "ic_3_pond": "Índice (IC)",
        "impacto_avaliado_3_pond_cenario": "Impacto",
    }

    cols_disponiveis = [c for c in display_cols_map.keys() if c in df_filtrado.columns]
    df_exibicao = df_filtrado[cols_disponiveis].rename(columns=display_cols_map)

    # Formatação de casas decimais para o Índice
    if "Índice (IC)" in df_exibicao.columns:
        df_exibicao["Índice (IC)"] = df_exibicao["Índice (IC)"].apply(
            lambda x: f"{x:.4f}" if pd.notnull(x) and isinstance(x, (int, float)) else ""
        )

    # Seção com a tabela e contagem
    st.markdown(f"**Resultados encontrados:** `{len(df_exibicao)}` de `{len(df_emp)}` empreendimentos")

    # Instrução visual
    st.info("💡 **Dica:** Clique em qualquer linha da tabela para visualizar o **Atlas completo** do empreendimento.")

    event = st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        height=450,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Nome do Empreendimento": st.column_config.TextColumn("Nome do Empreendimento", width="large"),
            "Setor": st.column_config.TextColumn("Setor", width="medium"),
            "Esfera": st.column_config.TextColumn("Esfera", width="small"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
            "Índice (IC)": st.column_config.TextColumn("Índice (IC)", width="small"),
            "Impacto": st.column_config.TextColumn("Impacto", width="small"),
        },
    )

    # Captura a seleção da linha
    selected_rows = event.selection.get("rows", [])
    if selected_rows:
        selected_index = selected_rows[0]
        selected_row_data = df_filtrado.iloc[selected_index]
        selected_id = int(selected_row_data["id_empreendimento"])

        # Define o estado e redireciona para o Atlas
        st.session_state["selected_empreendimento_id"] = selected_id
        st.query_params["id"] = str(selected_id)
        st.rerun()
