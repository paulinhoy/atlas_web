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
from services.formatters import fmt_int_br, fmt_bilhoes_br
from streamlit_sortables import sort_items

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
                font-size: 28px;
                font-weight: 700;
                letter-spacing: -0.5px;
                margin: 0;
                color: #ffffff;
            }
            .header-subtitle {
                font-size: 26px;
                color: #d1e3f8;
                margin-top: 0.3rem;
                font-weight: 300;
                line-height: 1.3;
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
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                color: #64748b;
                letter-spacing: 0.5px;
            }
            .kpi-value {
                font-size: 28px;
                font-weight: 700;
                color: #0f172a;
                margin-top: 0.2rem;
            }
            .kpi-subtext {
                font-size: 12px;
                color: #94a3b8;
                margin-top: 0.2rem;
            }

            /* Título de seção com sublinhado padrão Atlas */
            .section-title {
                font-size: 20px;
                font-weight: 700;
                color: #0b2545;
                margin: 1.5rem 0 0.8rem 0;
                padding-bottom: 0.35rem;
                border-bottom: 2px solid #0b2545;
            }

            /* Tabela de Empreendimentos no padrão visual do Atlas */
            .home-atlas-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
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
                padding: 0.75rem 0.85rem;
                text-align: center;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.25px;
                white-space: nowrap;
                border: none;
            }
            .home-atlas-table tbody td {
                padding: 0.55rem 0.75rem;
                text-align: center;
                border-bottom: 1px solid #eef2f7;
                color: #334155;
                font-size: 12px;
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
                font-size: 12px;
            }
            .home-atlas-table .emp-link {
                color: #0b2545;
                text-decoration: none;
                font-weight: 600;
                font-size: 12px;
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
                font-size: 12px;
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
                padding: 0.20rem 0.50rem;
                border-radius: 12px;
                font-size: 11px;
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
            .home-atlas-table .badge-priv {
                background: #f5f3ff;
                color: #6d28d9;
                border: 1px solid #ddd6fe;
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
                font-size: 20px;
                font-weight: 700;
                color: #0b2545;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .filter-panel-subtitle {
                font-size: 14px;
                color: #64748b;
            }

            /* Customização profunda dos Inputs e Dropdowns Streamlit */
            div[data-testid="stTextInput"] label,
            div[data-testid="stSelectbox"] label {
                font-size: 13px !important;
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
                font-size: 14px !important;
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
                font-size: 14px !important;
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
                font-size: 14px !important;
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
                font-size: 14px !important;
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

            /* ---- Botão Flutuante do Chatbot (Floating Action Pill) ---- */
            .atlas-floating-chat-btn {
                position: fixed;
                bottom: 24px;
                right: 24px;
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
            .atlas-floating-chat-btn:hover {
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


def render_chatbot_button():
    """Botão flutuante para acessar o assistente virtual."""
    st.markdown(
        """
        <a href="?page=chatbot" target="_self" class="atlas-floating-chat-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span>Assistente Virtual</span>
        </a>
        """,
        unsafe_allow_html=True,
    )


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
    top_setor = df["setor"].mode()[0] if "setor" in df.columns and not df.empty else "-"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Empreendimentos Priorizados</div>
                <div class="kpi-value">{fmt_int_br(total_emp)}</div>
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
                <div class="kpi-value">{fmt_int_br(alto_impacto)}</div>
                <div class="kpi-subtext">{pct_alto:.1f}% da carteira</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        capex_map = data_loader.get_mapa_capex_custo_economico()
        if "id_empreendimento" in df.columns and not df.empty:
            eids = pd.to_numeric(df["id_empreendimento"], errors="coerce").dropna().astype(int)
            total_capex = float(eids.map(capex_map).fillna(0).sum())
            inv_formatado = fmt_bilhoes_br(total_capex)
        else:
            inv_formatado = "-"

        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Investimento Total</div>
                <div class="kpi-value">{inv_formatado}</div>
                <div class="kpi-subtext">CAPEX</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO DECLARATIVO DE COLUNAS DA TABELA (DESACOPLADO)
# Permite adicionar, remover ou reordenar colunas de forma centralizada e independente.
# ─────────────────────────────────────────────────────────────────────────────

def _render_badge_impacto(val) -> str:
    raw = str(val or "-")
    safe = html_mod.escape(raw)
    raw_lower = raw.lower()
    if "alto" in raw_lower:
        return f'<span class="badge badge-high">{safe}</span>'
    elif "médio" in raw_lower or "medio" in raw_lower:
        return f'<span class="badge badge-med">{safe}</span>'
    elif "baixo" in raw_lower:
        return f'<span class="badge badge-low">{safe}</span>'
    return f'<span class="badge badge-neutral">{safe}</span>'


def _render_badge_esfera(val) -> str:
    raw = str(val or "-")
    safe = html_mod.escape(raw)
    raw_lower = raw.lower()
    if "federal" in raw_lower:
        return f'<span class="badge badge-fed">{safe}</span>'
    elif "estadual" in raw_lower:
        return f'<span class="badge badge-est">{safe}</span>'
    elif "municipal" in raw_lower:
        return f'<span class="badge badge-mun">{safe}</span>'
    elif "privad" in raw_lower:
        return f'<span class="badge badge-priv">{safe}</span>'
    return f'<span class="badge badge-neutral">{safe}</span>'


def _render_badge_viabilidade(val) -> str:
    raw = str(val or "-")
    safe = html_mod.escape(raw)
    raw_lower = raw.lower()
    if "alta" in raw_lower:
        return f'<span class="badge badge-high">{safe}</span>'
    elif "média" in raw_lower or "media" in raw_lower:
        return f'<span class="badge badge-med">{safe}</span>'
    elif "baixa" in raw_lower:
        return f'<span class="badge badge-low">{safe}</span>'
    return f'<span class="badge badge-neutral">{safe}</span>'


def _fmt_ic(val) -> str:
    if pd.notnull(val) and isinstance(val, (int, float)):
        return f"{float(val):.4f}".replace(".", ",")
    return "-"


AVAILABLE_COLUMNS = {
    "id": {
        "label": "ID",
        "th_class": "tc",
        "th_style": "width: 60px;",
        "td_class": "tc font-bold",
        "render": lambda r: str(int(r["id_empreendimento"])),
    },
    "nome": {
        "label": "Nome do Empreendimento",
        "th_class": "tl",
        "th_style": "text-align: left; width: 28%;",
        "td_class": "tl",
        "render": lambda r: f'<a href="?id={int(r["id_empreendimento"])}" target="_self" class="emp-link">{html_mod.escape(str(r.get("nome_empreendimento") or "-"))}</a>',
    },
    "setor": {
        "label": "Setor",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: html_mod.escape(str(r.get("setor") or "-")),
    },
    "esfera": {
        "label": "Esfera",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: _render_badge_esfera(r.get("esfera_acao")),
    },
    "status": {
        "label": "Status",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: html_mod.escape(str(r.get("descr_status_empreendimento") or "-")),
    },
    "viabilidade": {
        "label": "Viabilidade",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: _render_badge_viabilidade(r.get("viabilidade")),
    },
    "vocacao": {
        "label": "Vocação",
        "th_class": "tl",
        "th_style": "text-align: left;",
        "td_class": "tl",
        "render": lambda r: html_mod.escape(str(r.get("vocacao") or "-")),
    },
    "origem_ajustada": {
        "label": "Origem",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: f'<span class="badge badge-neutral">{html_mod.escape(str(r.get("origem_ajustada") or "-"))}</span>',
    },
    "fonte_financiamento": {
        "label": "Financiamento",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: html_mod.escape(str(r.get("fonte_financiamento") or "-")),
    },
    "responsavel_gestao": {
        "label": "Responsável",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: html_mod.escape(str(r.get("responsavel_gestao_infraestrutura") or "-")),
    },
    "ic": {
        "label": "Índice (IC)",
        "th_class": "tr",
        "th_style": "text-align: right;",
        "td_class": "tr font-mono",
        "render": lambda r: _fmt_ic(r.get("ic_3_pond")),
    },
    "impacto": {
        "label": "Impacto",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: _render_badge_impacto(r.get("impacto_avaliado_3_pond_cenario")),
    },
    "acao": {
        "label": "Ação",
        "th_class": "tc",
        "th_style": "width: 105px;",
        "td_class": "tc",
        "render": lambda r: f'<a href="?id={int(r["id_empreendimento"])}" target="_self" class="btn-action">Ver Atlas</a>',
    },
}

# Colunas exibidas por padrão na tabela (altere aqui para ligar/desligar colunas via código)
DEFAULT_ACTIVE_COLUMNS = [
    "id",
    "nome",
    "setor",
    "esfera",
    "status",
    "viabilidade",
    "ic",
    "impacto",
    "acao",
]


def render_table_html(df_page: pd.DataFrame, active_columns: list = None):
    """Renderiza a tabela de empreendimentos estilizada no padrão visual do Atlas com colunas desacopladas."""
    if not active_columns:
        active_columns = DEFAULT_ACTIVE_COLUMNS

    cols_to_render = [c for c in active_columns if c in AVAILABLE_COLUMNS]

    # Cabeçalho da tabela
    ths_html = ""
    for col_id in cols_to_render:
        cfg = AVAILABLE_COLUMNS[col_id]
        th_class = cfg.get("th_class", "tc")
        th_style = cfg.get("th_style", "")
        style_attr = f' style="{th_style}"' if th_style else ""
        ths_html += f'<th class="{th_class}"{style_attr}>{cfg["label"]}</th>'

    # Linhas da tabela
    rows_html = ""
    for _, r in df_page.iterrows():
        id_emp = int(r["id_empreendimento"])
        tds_html = ""
        for col_id in cols_to_render:
            cfg = AVAILABLE_COLUMNS[col_id]
            td_class = cfg.get("td_class", "tc")
            content = cfg["render"](r)
            tds_html += f'<td class="{td_class}">{content}</td>'

        rows_html += (
            f'<tr onclick="window.location.href=\'?id={id_emp}\'">'
            f'{tds_html}'
            '</tr>'
        )

    table_html = (
        '<table class="home-atlas-table">'
        f'<thead><tr>{ths_html}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


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
            f"Mostrando <b>{fmt_int_br(start_idx + 1)}–{fmt_int_br(end_idx)}</b> de <b>{fmt_int_br(total_filtrado)}</b> empreendimentos (Total: {fmt_int_br(total_emp)})"
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
    render_chatbot_button()
    render_header()

    df_base = data_loader.get_empreendimentos()

    if df_base.empty:
        st.error(
            "Nenhum dado encontrado em `data/processed/empreendimentos_priorizacao.parquet`.\n"
            "Execute o script `scripts/process_data.py` para processar a base de dados."
        )
        return

    # ── Mapeamento das Carteiras Metodológicas ──
    carteiras_map = {
        "Carteira Recomendada (1.044)": {
            "fonte": "cenario recomendado",
            "titulo": "Carteira Recomendada",
        },
        "Carteira Otimizada (1.059)": {
            "fonte": "cenario otimizado",
            "titulo": "Carteira Otimizada",
        },
        "Carteira Completa (1.682)": {
            "fonte": "priorizacao geral",
            "titulo": "Carteira Completa",
        },
    }
    lista_carteiras = list(carteiras_map.keys())

    if "home_carteira_selecionada" not in st.session_state or st.session_state["home_carteira_selecionada"] not in carteiras_map:
        st.session_state["home_carteira_selecionada"] = lista_carteiras[0]

    carteira_ativa = st.session_state["home_carteira_selecionada"]
    config_carteira = carteiras_map[carteira_ativa]

    # Filtra e ordena a base pela carteira selecionada
    if "fonte_priorizacao" in df_base.columns:
        df_emp = df_base[df_base["fonte_priorizacao"] == config_carteira["fonte"]].copy()
    else:
        df_emp = df_base.copy()

    if "ic_3_pond" in df_emp.columns:
        df_emp["ic_3_pond"] = pd.to_numeric(df_emp["ic_3_pond"], errors="coerce")
        df_emp = df_emp.sort_values(by="ic_3_pond", ascending=False).reset_index(drop=True)

    # Renderiza KPIs específicos da carteira ativa
    render_kpis(df_emp)

    # Painel de Filtros e Busca
    st.markdown(
        """
        <div class="filter-panel-header">
            <div class="filter-panel-title">
                Pesquisa e Filtros da Carteira
            </div>
            <div class="filter-panel-subtitle">
                Refine a listagem por carteira metodológica, busca textual, setor, esfera, classificação, viabilidade, origem ou vocação
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Linha 1 de Filtros: Busca textual, Setor, Esfera e Seletor de Carteira
    f_col1, f_col2, f_col3, f_col4 = st.columns([2.6, 1.4, 1.4, 2.0])

    with f_col1:
        busca = st.text_input(
            "Buscar por Nome ou Código ID:",
            placeholder="Ex: Ferrovia Centro-Atlântica, BR-381, 113...",
            key="busca_termo",
        )

    with f_col2:
        setores = ["Todos"] + sorted([str(x) for x in df_emp["setor"].dropna().unique() if str(x).strip()]) if "setor" in df_emp.columns else ["Todos"]
        filtro_setor = st.selectbox("Setor:", setores, key="filtro_setor")

    with f_col3:
        esferas = ["Todas"] + sorted([str(x) for x in df_emp["esfera_acao"].dropna().unique() if str(x).strip()]) if "esfera_acao" in df_emp.columns else ["Todas"]
        filtro_esfera = st.selectbox("Esfera:", esferas, key="filtro_esfera")

    with f_col4:
        cur_idx = lista_carteiras.index(carteira_ativa)
        carteira_escolhida = st.selectbox(
            "Carteira:",
            options=lista_carteiras,
            index=cur_idx,
            key="filtro_carteira_select",
        )
        if carteira_escolhida != carteira_ativa:
            st.session_state["home_carteira_selecionada"] = carteira_escolhida
            st.session_state["home_page"] = 1
            st.rerun()

    # Linha 2 de Filtros: Classificação (Impacto), Viabilidade, Origem Ajustada e Vocação
    col_impacto = "impacto_avaliado_3_pond_cenario"
    g_col1, g_col2, g_col3, g_col4 = st.columns([1.5, 1.5, 1.5, 2.9])

    with g_col1:
        impactos = ["Todos"] + sorted([str(x) for x in df_emp[col_impacto].dropna().unique() if str(x).strip()]) if col_impacto in df_emp.columns else ["Todos"]
        filtro_impacto = st.selectbox("Classificação:", impactos, key="filtro_impacto")

    with g_col2:
        viabilidades = ["Todas"] + sorted([str(x) for x in df_emp["viabilidade"].dropna().unique() if str(x).strip()]) if "viabilidade" in df_emp.columns else ["Todas"]
        filtro_viabilidade = st.selectbox("Viabilidade:", viabilidades, key="filtro_viabilidade")

    with g_col3:
        origens = ["Todas"] + sorted([str(x) for x in df_emp["origem_ajustada"].dropna().unique() if str(x).strip()]) if "origem_ajustada" in df_emp.columns else ["Todas"]
        filtro_origem = st.selectbox("Origem Ajustada:", origens, key="filtro_origem")

    with g_col4:
        vocacoes = ["Todas"] + sorted([str(x) for x in df_emp["vocacao"].dropna().unique() if str(x).strip()]) if "vocacao" in df_emp.columns else ["Todas"]
        filtro_vocacao = st.selectbox("Vocação:", vocacoes, key="filtro_vocacao")

    # Aplicação dos Filtros
    df_filtrado = df_emp.copy()

    if busca.strip():
        termo = busca.strip().lower()
        id_mask = df_filtrado["id_empreendimento"].astype(str).str.contains(termo, case=False, na=False)
        nome_mask = df_filtrado["nome_empreendimento"].astype(str).str.lower().str.contains(termo, na=False)
        df_filtrado = df_filtrado[id_mask | nome_mask]

    filtros_categoricos = [
        (filtro_setor, "setor", "Todos"),
        (filtro_esfera, "esfera_acao", "Todas"),
        (filtro_impacto, col_impacto, "Todos"),
        (filtro_viabilidade, "viabilidade", "Todas"),
        (filtro_origem, "origem_ajustada", "Todas"),
        (filtro_vocacao, "vocacao", "Todas"),
    ]

    for val, col, default_val in filtros_categoricos:
        if val != default_val and col in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[col] == val]

    # Ordenação defensiva estrita por ic_3_pond decrescente
    if "ic_3_pond" in df_filtrado.columns:
        df_filtrado["ic_3_pond"] = pd.to_numeric(df_filtrado["ic_3_pond"], errors="coerce")
        df_filtrado = df_filtrado.sort_values(by="ic_3_pond", ascending=False).reset_index(drop=True)

    total_filtrado = len(df_filtrado)

    st.markdown(f'<div class="section-title">Carteira de Empreendimentos Priorizados — {config_carteira["titulo"]}</div>', unsafe_allow_html=True)

    # ── Painel de Personalização e Ordenação das Colunas (Drag & Drop) ──
    if "home_colunas_ativas" not in st.session_state:
        st.session_state["home_colunas_ativas"] = list(DEFAULT_ACTIVE_COLUMNS)

    # Mapas de conversão label ↔ id (para streamlit-sortables que trabalha com strings)
    _label_to_id = {cfg["label"]: col_id for col_id, cfg in AVAILABLE_COLUMNS.items()}
    _id_to_label = {col_id: cfg["label"] for col_id, cfg in AVAILABLE_COLUMNS.items()}

    with st.expander("Personalizar Colunas Visíveis da Tabela", expanded=False):
        st.caption("Arraste os cards para reordenar as colunas ou mova entre os grupos para exibir/ocultar.")

        # Monta listas de labels para os dois containers
        active_ids = [c for c in st.session_state["home_colunas_ativas"] if c in AVAILABLE_COLUMNS]
        available_ids = [c for c in AVAILABLE_COLUMNS if c not in active_ids]

        sortable_items = [
            {"header": "📋 Colunas Visíveis na Tabela", "items": [_id_to_label[c] for c in active_ids]},
            {"header": "➕ Colunas Disponíveis (arraste para cima para adicionar)", "items": [_id_to_label[c] for c in available_ids]},
        ]

        custom_style = """
        .sortable-component {
            gap: 12px;
        }
        .sortable-container {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0;
        }
        .sortable-container-header {
            background: linear-gradient(135deg, #0b2545 0%, #134074 100%);
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            padding: 8px 14px;
            border-radius: 8px 8px 0 0;
        }
        .sortable-container-body {
            padding: 8px;
            min-height: 40px;
        }
        .sortable-item {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 500;
            color: #0b2545;
            cursor: grab;
            transition: all 0.15s ease;
        }
        .sortable-item:hover {
            background: #e0f2fe;
            border-color: #0284c7;
            box-shadow: 0 1px 3px rgba(2,132,199,0.15);
        }
        .sortable-item.dragging {
            opacity: 0.5;
        }
        """

        sorted_containers = sort_items(
            sortable_items,
            multi_containers=True,
            direction="horizontal",
            custom_style=custom_style,
            key="home_sortable_colunas",
        )

        # Converte labels de volta para IDs preservando a ordem do drag
        new_active_labels = sorted_containers[0]["items"]
        new_active_ids = [_label_to_id[lbl] for lbl in new_active_labels if lbl in _label_to_id]

        # Atualiza session_state se houve mudança
        if new_active_ids != st.session_state["home_colunas_ativas"]:
            st.session_state["home_colunas_ativas"] = new_active_ids if new_active_ids else list(DEFAULT_ACTIVE_COLUMNS)

        # Botão restaurar padrão
        if st.button("↺ Restaurar Padrão", key="btn_restaurar_colunas", help="Restaurar a configuração de colunas original recomendada"):
            st.session_state["home_colunas_ativas"] = list(DEFAULT_ACTIVE_COLUMNS)
            st.rerun()

    colunas_ativas = st.session_state.get("home_colunas_ativas", DEFAULT_ACTIVE_COLUMNS)
    if not colunas_ativas:
        colunas_ativas = DEFAULT_ACTIVE_COLUMNS

    if total_filtrado == 0:
        st.warning("Nenhum empreendimento encontrado para os filtros selecionados.")
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

    # 1. Fatia e renderiza a tabela estilizada com colunas desacopladas
    df_page = df_filtrado.iloc[start_idx:end_idx]
    render_table_html(df_page, active_columns=colunas_ativas)

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
