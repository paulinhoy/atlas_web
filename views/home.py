"""
Tela Inicial (Home) - Painel Executivo e Busca de Empreendimentos Priorizados
Apresenta KPIs, filtros dinâmicos e tabela de empreendimentos estilizada no mesmo padrão visual do Atlas.
"""

from pathlib import Path
import html as html_mod
import math
import streamlit as st
import pandas as pd
from services import data_loader

BASE_DIR = Path(__file__).resolve().parent.parent
LOGOS_DIR = BASE_DIR / "logos"


def apply_custom_styles():
    """Aplica estilos CSS customizados para a tela inicial."""
    st.markdown(
        """
        <style>
            /* Cabeçalho institucional */
            .main-header {
                background: linear-gradient(135deg, #0b2545 0%, #133b63 100%);
                padding: 1.5rem 2rem;
                border-radius: 12px;
                color: #ffffff;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            }
            .header-title {
                font-size: 1.8rem;
                font-weight: 700;
                letter-spacing: -0.5px;
                margin: 0;
                color: #ffffff;
            }
            .header-subtitle {
                font-size: 0.95rem;
                color: #d1e3f8;
                margin-top: 0.3rem;
                font-weight: 300;
            }

            /* Cartões de KPI */
            .kpi-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 1.1rem 1.2rem;
                box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .kpi-title {
                font-size: 0.78rem;
                font-weight: 600;
                text-transform: uppercase;
                color: #64748b;
                letter-spacing: 0.5px;
            }
            .kpi-value {
                font-size: 1.7rem;
                font-weight: 700;
                color: #0f172a;
                margin-top: 0.2rem;
            }
            .kpi-subtext {
                font-size: 0.75rem;
                color: #94a3b8;
                margin-top: 0.2rem;
            }

            /* Título de seção com sublinhado padrão Atlas */
            .section-title {
                font-size: 1.05rem;
                font-weight: 700;
                color: #1e293b;
                margin: 1.5rem 0 0.8rem 0;
                padding-bottom: 0.35rem;
                border-bottom: 2px solid #0b2545;
            }

            /* Tabela de Empreendimentos no padrão visual do Atlas */
            .home-atlas-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.84rem;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                background: #ffffff;
                border: 1px solid #e2e8f0;
                margin-top: 0.6rem;
                margin-bottom: 1.2rem;
            }
            .home-atlas-table thead th {
                background: #0b2545;
                color: #ffffff;
                padding: 0.70rem 0.80rem;
                text-align: center;
                font-weight: 600;
                font-size: 0.80rem;
                letter-spacing: 0.25px;
                white-space: nowrap;
                border: none;
            }
            .home-atlas-table tbody td {
                padding: 0.60rem 0.80rem;
                text-align: center;
                border-bottom: 1px solid #eef2f7;
                color: #334155;
                vertical-align: middle;
            }
            .home-atlas-table tbody tr {
                cursor: pointer;
                transition: background-color 0.15s ease;
            }
            .home-atlas-table tbody tr:nth-child(even) {
                background: #f8fafc;
            }
            .home-atlas-table tbody tr:hover {
                background: #edf4fb;
            }
            .home-atlas-table .tl {
                text-align: left;
            }
            .home-atlas-table .tc {
                text-align: center;
            }
            .home-atlas-table .tr {
                text-align: right;
            }
            .home-atlas-table .font-bold {
                font-weight: 600;
                color: #0b2545;
            }
            .home-atlas-table .font-mono {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 0.82rem;
            }
            .home-atlas-table .emp-link {
                color: #0b2545;
                text-decoration: none;
                font-weight: 600;
                display: block;
                transition: color 0.15s ease;
            }
            .home-atlas-table .emp-link:hover {
                color: #1d4ed8;
                text-decoration: underline;
            }
            .home-atlas-table .btn-action {
                display: inline-block;
                background: #0b2545;
                color: #ffffff !important;
                padding: 0.32rem 0.70rem;
                border-radius: 5px;
                font-size: 0.76rem;
                font-weight: 600;
                text-decoration: none !important;
                transition: background-color 0.15s ease, transform 0.1s ease;
                white-space: nowrap;
            }
            .home-atlas-table .btn-action:hover {
                background: #133b63;
                color: #ffffff !important;
                transform: translateX(2px);
            }
            .home-atlas-table .badge {
                display: inline-block;
                padding: 0.22rem 0.58rem;
                border-radius: 12px;
                font-size: 0.73rem;
                font-weight: 600;
                white-space: nowrap;
            }
            .home-atlas-table .badge-high {
                background: #dcfce7;
                color: #166534;
                border: 1px solid #bbf7d0;
            }
            .home-atlas-table .badge-med {
                background: #fef3c7;
                color: #92400e;
                border: 1px solid #fde68a;
            }
            .home-atlas-table .badge-low {
                background: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
            }
            .home-atlas-table .badge-neutral {
                background: #f1f5f9;
                color: #334155;
                border: 1px solid #e2e8f0;
            }
            .home-atlas-table .badge-fed {
                background: #e0f2fe;
                color: #0369a1;
                border: 1px solid #bae6fd;
            }
            .home-atlas-table .badge-est {
                background: #f0fdf4;
                color: #15803d;
                border: 1px solid #bbf7d0;
            }
            .home-atlas-table .badge-mun {
                background: #fef9c3;
                color: #a16207;
                border: 1px solid #fef08a;
            }
            /* Painel de Filtros e Busca */
            .filter-panel-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-top: 1.2rem;
                margin-bottom: 0.6rem;
                padding-bottom: 0.4rem;
                border-bottom: 1px solid #e2e8f0;
            }
            .filter-panel-title {
                font-size: 0.95rem;
                font-weight: 700;
                color: #0b2545;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .filter-panel-subtitle {
                font-size: 0.80rem;
                color: #64748b;
            }

            /* Customização profunda dos Inputs e Dropdowns Streamlit */
            div[data-testid="stTextInput"] label,
            div[data-testid="stSelectbox"] label {
                font-size: 0.74rem !important;
                font-weight: 700 !important;
                color: #475569 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.4px !important;
                margin-bottom: 0.25rem !important;
            }
            
            div[data-testid="stTextInput"] input {
                background-color: #f8fafc !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 8px !important;
                color: #0f172a !important;
                font-size: 0.86rem !important;
                padding: 0.48rem 0.8rem !important;
                box-shadow: none !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stTextInput"] input:hover {
                background-color: #ffffff !important;
                border-color: #94a3b8 !important;
            }
            div[data-testid="stTextInput"] input:focus {
                background-color: #ffffff !important;
                border-color: #0b2545 !important;
                box-shadow: 0 0 0 3px rgba(11, 37, 69, 0.12) !important;
            }

            div[data-testid="stSelectbox"] > div > div {
                background-color: #f8fafc !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 8px !important;
                color: #0f172a !important;
                font-size: 0.86rem !important;
                box-shadow: none !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stSelectbox"] > div > div:hover {
                background-color: #ffffff !important;
                border-color: #94a3b8 !important;
            }
            div[data-testid="stSelectbox"] > div > div[aria-expanded="true"] {
                background-color: #ffffff !important;
                border-color: #0b2545 !important;
                box-shadow: 0 0 0 3px rgba(11, 37, 69, 0.12) !important;
            }

            /* Controles de paginação numérica minimalista (estilo < 1 ... 5 [6] 7 ... 17 >) */
            div[data-testid="stHorizontalBlock"] button[kind="primary"] {
                background-color: #0b2545 !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 4px !important;
                min-width: 32px !important;
                max-width: 32px !important;
                height: 32px !important;
                min-height: 32px !important;
                padding: 0 !important;
                font-size: 0.90rem !important;
                font-weight: 700 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 auto !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15) !important;
            }

            div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
                background-color: transparent !important;
                color: #0f172a !important;
                border: none !important;
                border-radius: 4px !important;
                min-width: 32px !important;
                max-width: 32px !important;
                height: 32px !important;
                min-height: 32px !important;
                padding: 0 !important;
                font-size: 0.90rem !important;
                font-weight: 500 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin: 0 auto !important;
                box-shadow: none !important;
                transition: all 0.15s ease !important;
            }
            div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover:not(:disabled) {
                background-color: #f1f5f9 !important;
                color: #0b2545 !important;
            }
            div[data-testid="stHorizontalBlock"] button[kind="secondary"]:disabled {
                color: #cbd5e1 !important;
                background-color: transparent !important;
                cursor: not-allowed !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_br_int(val: int) -> str:
    """Formata inteiros com separador de milhar brasileiro (.)"""
    if pd.isna(val) or val is None:
        return "N/D"
    try:
        val = int(float(val))
    except (ValueError, TypeError):
        return "N/D"
    return f"{val:,}".replace(",", ".")


def render_header():
    """Renderiza o cabeçalho institucional."""
    st.markdown(
        """
        <div class="main-header">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
                <div>
                    <div class="header-title">PELTMG — Atlas de Empreendimentos</div>
                    <div class="header-subtitle">
                        Plano Estadual de Logística e Transportes de Minas Gerais • Carteira Priorizada
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(df: pd.DataFrame):
    """Renderiza cartões com indicadores resumidos dos empreendimentos no formato brasileiro."""
    total_emp = len(df)
    total_setores = df["setor"].nunique() if "setor" in df.columns else 0

    col_impacto = "impacto_avaliado_3_pond_cenario"
    alto_impacto = len(df[df[col_impacto] == "Alto impacto"]) if col_impacto in df.columns else 0
    top_setor = df["setor"].mode()[0] if "setor" in df.columns and not df.empty else "N/A"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Empreendimentos Priorizados</div>
                <div class="kpi-value">{format_br_int(total_emp)}</div>
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
        pct_alto = (alto_impacto / total_emp) * 100 if total_emp > 0 else 0
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Alto Impacto</div>
                <div class="kpi-value">{format_br_int(alto_impacto)}</div>
                <div class="kpi-subtext">{pct_alto:.1f}% da carteira</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        tirm_valid = df["tirm"].dropna() if "tirm" in df.columns else pd.Series()
        tirm_media = f"{tirm_valid.mean() * 100:.1f}%".replace(".", ",") if not tirm_valid.empty else "N/D"
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">TIRM Média Declarada</div>
                <div class="kpi-value">{tirm_media}</div>
                <div class="kpi-subtext">{format_br_int(len(tirm_valid))} projetos com TIRM</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")


def render_table_html(df_page: pd.DataFrame):
    """Renderiza a tabela de empreendimentos estilizada no padrão visual do Atlas com links funcionais."""
    rows_html = ""
    for _, r in df_page.iterrows():
        id_emp = int(r["id_empreendimento"])
        nome = html_mod.escape(str(r.get("nome_empreendimento") or "N/D"))
        setor = html_mod.escape(str(r.get("setor") or "N/D"))
        esfera = html_mod.escape(str(r.get("esfera_acao") or "N/D"))
        status = html_mod.escape(str(r.get("descr_status_empreendimento") or "N/D"))
        
        ic_val = r.get("ic_3_pond")
        ic_str = f"{ic_val:.4f}".replace(".", ",") if pd.notnull(ic_val) and isinstance(ic_val, (int, float)) else "N/D"
        
        impacto_raw = str(r.get("impacto_avaliado_3_pond_cenario") or "N/D")
        impacto_safe = html_mod.escape(impacto_raw)

        # Badges contextuais de impacto
        if "alto" in impacto_raw.lower():
            impacto_badge = f'<span class="badge badge-high">{impacto_safe}</span>'
        elif "médio" in impacto_raw.lower() or "medio" in impacto_raw.lower():
            impacto_badge = f'<span class="badge badge-med">{impacto_safe}</span>'
        elif "baixo" in impacto_raw.lower():
            impacto_badge = f'<span class="badge badge-low">{impacto_safe}</span>'
        else:
            impacto_badge = f'<span class="badge badge-neutral">{impacto_safe}</span>'

        # Badges contextuais de esfera
        esfera_lower = esfera.lower()
        if "federal" in esfera_lower:
            esfera_badge = f'<span class="badge badge-fed">{esfera}</span>'
        elif "estadual" in esfera_lower:
            esfera_badge = f'<span class="badge badge-est">{esfera}</span>'
        elif "municipal" in esfera_lower:
            esfera_badge = f'<span class="badge badge-mun">{esfera}</span>'
        elif "privad" in esfera_lower:
            esfera_badge = f'<span class="badge badge-priv">{esfera}</span>'
        else:
            esfera_badge = f'<span class="badge badge-neutral">{esfera}</span>'

        rows_html += (
            f'<tr onclick="window.location.href=\'?id={id_emp}\'">'
            f'<td class="tc font-bold">{id_emp}</td>'
            f'<td class="tl"><a href="?id={id_emp}" target="_self" class="emp-link">{nome}</a></td>'
            f'<td class="tc">{setor}</td>'
            f'<td class="tc">{esfera_badge}</td>'
            f'<td class="tc">{status}</td>'
            f'<td class="tr font-mono">{ic_str}</td>'
            f'<td class="tc">{impacto_badge}</td>'
            f'<td class="tc"><a href="?id={id_emp}" target="_self" class="btn-action">Ver Atlas ➔</a></td>'
            '</tr>'
        )

    table_html = (
        '<table class="home-atlas-table">'
        '<thead><tr>'
        '<th style="width: 60px;">ID</th>'
        '<th style="text-align: left; width: 35%;">Nome do Empreendimento</th>'
        '<th>Setor</th>'
        '<th>Esfera</th>'
        '<th>Status</th>'
        '<th style="text-align: right;">Índice (IC)</th>'
        '<th>Impacto</th>'
        '<th style="width: 110px;">Ação</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


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
    st.markdown(
        """
        <div class="filter-panel-header">
            <div class="filter-panel-title">
                <span>🔍</span> Pesquisa e Filtros da Carteira
            </div>
            <div class="filter-panel-subtitle">
                Refine a listagem por código, nome, setor, esfera governamental ou classificação
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    total_filtrado = len(df_filtrado)

    st.markdown('<div class="section-title">Carteira de Empreendimentos Priorizados</div>', unsafe_allow_html=True)

def render_pagination(
    current_page: int,
    total_pages: int,
    total_filtrado: int,
    start_idx: int,
    end_idx: int,
    total_emp: int,
    page_size: int,
):
    """Renderiza a paginação numérica minimalista no padrão da imagem (< 1 ... 5 [6] 7 ... 17 >)."""
    # 1. Informações de contagem e seletor de linhas por página
    c_info, c_size = st.columns([3.5, 1.5])
    with c_info:
        st.markdown(
            f"<div style='font-size: 0.85rem; color: #64748b; padding-top: 0.4rem;'>"
            f"Mostrando <b>{format_br_int(start_idx + 1)}–{format_br_int(end_idx)}</b> de <b>{format_br_int(total_filtrado)}</b> empreendimentos (Total: {format_br_int(total_emp)})"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c_size:
        c_lbl, c_sel = st.columns([1.1, 1.2])
        with c_lbl:
            st.markdown("<div style='text-align: right; font-size: 0.82rem; color: #64748b; padding-top: 0.4rem;'>Itens por pág.:</div>", unsafe_allow_html=True)
        with c_sel:
            size_options = [15, 25, 50, 100]
            cur_size_idx = size_options.index(page_size) if page_size in size_options else 1
            novo_size = st.selectbox(
                "Itens por página:",
                options=size_options,
                index=cur_size_idx,
                key="select_page_size",
                label_visibility="collapsed",
            )
            if novo_size != page_size:
                st.session_state["home_page_size"] = novo_size
                st.session_state["home_page"] = 1
                st.rerun()

    if total_pages <= 1:
        return

    st.write("")

    # 2. Monta os elementos numéricos da paginação
    if total_pages <= 7:
        items = list(range(1, total_pages + 1))
    elif current_page <= 4:
        items = [1, 2, 3, 4, 5, "...", total_pages]
    elif current_page >= total_pages - 3:
        items = [1, "...", total_pages - 4, total_pages - 3, total_pages - 2, total_pages - 1, total_pages]
    else:
        items = [1, "...", current_page - 1, current_page, current_page + 1, "...", total_pages]

    num_items = len(items)
    total_nav_cols = num_items + 2

    # Espaçadores proporcionais nas pontas para centralização
    spacer_width = max(1.0, (14 - total_nav_cols) / 2.0)
    col_weights = [spacer_width] + [1.0] * total_nav_cols + [spacer_width]
    cols = st.columns(col_weights)

    # Botão Anterior (<)
    with cols[1]:
        if st.button("‹", disabled=(current_page <= 1), key="btn_pg_prev", help="Página anterior"):
            st.session_state["home_page"] = current_page - 1
            st.rerun()

    # Itens de página e reticências
    for i, item in enumerate(items):
        with cols[2 + i]:
            if item == "...":
                st.markdown(
                    "<div style='text-align: center; color: #64748b; font-size: 0.95rem; line-height: 32px; font-weight: bold;'>…</div>",
                    unsafe_allow_html=True,
                )
            else:
                p_num = int(item)
                is_active = (p_num == current_page)
                btn_type = "primary" if is_active else "secondary"
                if st.button(str(p_num), key=f"btn_pg_{p_num}", type=btn_type):
                    if p_num != current_page:
                        st.session_state["home_page"] = p_num
                        st.rerun()

    # Botão Próximo (>)
    with cols[-2]:
        if st.button("›", disabled=(current_page >= total_pages), key="btn_pg_next", help="Próxima página"):
            st.session_state["home_page"] = current_page + 1
            st.rerun()


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
    st.markdown(
        """
        <div class="filter-panel-header">
            <div class="filter-panel-title">
                <span>🔍</span> Pesquisa e Filtros da Carteira
            </div>
            <div class="filter-panel-subtitle">
                Refine a listagem por código, nome, setor, esfera governamental ou classificação
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    total_filtrado = len(df_filtrado)

    st.markdown('<div class="section-title">Carteira de Empreendimentos Priorizados</div>', unsafe_allow_html=True)

    if total_filtrado == 0:
        st.warning("⚠️ Nenhum empreendimento encontrado para os filtros selecionados.")
        return

    # Inicializa estado da página e tamanho se necessário
    if "home_page" not in st.session_state:
        st.session_state["home_page"] = 1
    if "home_page_size" not in st.session_state:
        st.session_state["home_page_size"] = 25

    page_size = st.session_state["home_page_size"]
    total_pages = max(1, math.ceil(total_filtrado / page_size))
    
    # Corrige se a página atual ultrapassar o total de páginas após filtro
    if st.session_state["home_page"] > total_pages:
        st.session_state["home_page"] = 1

    current_page = st.session_state["home_page"]
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_filtrado)

    # 1. Fatia e renderiza a tabela estilizada
    df_page = df_filtrado.iloc[start_idx:end_idx]
    render_table_html(df_page)

    # 2. Barra de paginação numérica minimalista (< 1 ... 5 [6] 7 ... 17 >)
    render_pagination(
        current_page=current_page,
        total_pages=total_pages,
        total_filtrado=total_filtrado,
        start_idx=start_idx,
        end_idx=end_idx,
        total_emp=len(df_emp),
        page_size=page_size,
    )
