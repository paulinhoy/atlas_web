"""
Tela Inicial (Home) - Painel Executivo e Busca de Empreendimentos Priorizados
Apresenta KPIs, filtros dinâmicos e tabela de empreendimentos estilizada no mesmo padrão visual do Atlas.
"""

import html as html_mod
import math
import streamlit as st
import pandas as pd
from services import data_loader
from services.formatters import fmt_int_br, fmt_bilhoes_br
from streamlit_sortables import sort_items
from views import estado_url
from views.ui import inject_css, read_css, render_navbar


def render_chatbot_button(container):
    """Botão flutuante para acessar o assistente virtual (leva o estado atual da Home)."""
    container.markdown(
        f"""
        <a href="{estado_url.link_chatbot()}" target="_self" class="atlas-floating-chat-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
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
            <div class="main-header-row">
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
    pct_alto = (alto_impacto / total_emp) * 100 if total_emp > 0 else 0

    capex_map = data_loader.get_mapa_capex_custo_economico()
    if "id_empreendimento" in df.columns and not df.empty:
        inv_formatado = fmt_bilhoes_br(float(df["id_empreendimento"].map(capex_map).fillna(0).sum()))
    else:
        inv_formatado = "-"

    cards = [
        ("Empreendimentos Priorizados", fmt_int_br(total_emp), "Carteira avaliada"),
        ("Setores Atendidos", total_setores, f"Principal: <b>{top_setor}</b>"),
        ("Alto Impacto", fmt_int_br(alto_impacto), f"{pct_alto:.1f}% da carteira"),
        ("Investimento Total", inv_formatado, "CAPEX"),
    ]
    for col, (titulo, valor, subtexto) in zip(st.columns(4), cards):
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-title">{titulo}</div>'
            f'<div class="kpi-value">{valor}</div><div class="kpi-subtext">{subtexto}</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")


# ─────────────────────────────────────────────────────────────────────────────
# REGISTRO DECLARATIVO DE COLUNAS DA TABELA (DESACOPLADO)
# Permite adicionar, remover ou reordenar colunas de forma centralizada e independente.
# ─────────────────────────────────────────────────────────────────────────────

BADGE_RULES = {
    "impacto": [(("alto",), "badge-high"), (("médio", "medio"), "badge-med"), (("baixo",), "badge-low")],
    "esfera": [(("federal",), "badge-fed"), (("estadual",), "badge-est"), (("municipal",), "badge-mun"), (("privad",), "badge-priv")],
    "viabilidade": [(("alta",), "badge-high"), (("média", "media"), "badge-med"), (("baixa",), "badge-low")],
}


def _render_badge(tipo: str, val) -> str:
    """Badge colorido: a classe é escolhida pelo primeiro trecho de texto encontrado no valor."""
    raw = str(val or "-")
    raw_lower = raw.lower()
    css = next((c for termos, c in BADGE_RULES[tipo] if any(t in raw_lower for t in termos)), "badge-neutral")
    return f'<span class="badge {css}">{html_mod.escape(raw)}</span>'


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
        "render": lambda r: f'<a href="{estado_url.link_empreendimento(int(r["id_empreendimento"]))}" target="_self" class="emp-link">{html_mod.escape(str(r.get("nome_empreendimento") or "-"))}</a>',
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
        "render": lambda r: _render_badge("esfera", r.get("esfera_acao")),
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
        "render": lambda r: _render_badge("viabilidade", r.get("viabilidade")),
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
        "render": lambda r: _render_badge("impacto", r.get("impacto_avaliado_3_pond_cenario")),
    },
    "acao": {
        "label": "Ação",
        "th_class": "tc",
        "th_style": "width: 105px;",
        "td_class": "tc",
        "render": lambda r: f'<a href="{estado_url.link_empreendimento(int(r["id_empreendimento"]))}" target="_self" class="btn-action">Ver Atlas</a>',
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

PAGE_SIZE_OPTIONS = [15, 25, 50, 100]


def _inteiro_positivo(texto: str) -> int:
    valor = int(texto)
    if valor < 1:
        raise ValueError(texto)
    return valor


LABEL_TO_ID = {cfg["label"]: col_id for col_id, cfg in AVAILABLE_COLUMNS.items()}
ID_TO_LABEL = {col_id: cfg["label"] for col_id, cfg in AVAILABLE_COLUMNS.items()}


if hasattr(st, "dialog"):
    _dialog_decorator = st.dialog("Personalizar Colunas da Tabela", width="large")
elif hasattr(st, "experimental_dialog"):
    _dialog_decorator = st.experimental_dialog("Personalizar Colunas da Tabela", width="large")
else:
    def _dialog_decorator(f):
        return f


@_dialog_decorator
def modal_personalizar_colunas():
    """Modal interativo para ordenação e seleção de colunas via drag-and-drop."""
    st.markdown(
        "<div class='modal-hint'>"
        "Arraste os cards para reordenar as colunas na tabela ou mova entre os blocos para exibir/ocultar."
        "</div>",
        unsafe_allow_html=True,
    )

    active_ids = [c for c in st.session_state.get("home_colunas_ativas", DEFAULT_ACTIVE_COLUMNS) if c in AVAILABLE_COLUMNS]
    available_ids = [c for c in AVAILABLE_COLUMNS if c not in active_ids]

    sortable_items = [
        {"header": "Colunas Visíveis na Tabela", "items": [ID_TO_LABEL[c] for c in active_ids]},
        {"header": "Colunas Ocultas (arraste para cima para incluir)", "items": [ID_TO_LABEL[c] for c in available_ids]},
    ]


    ver = st.session_state.get("sortable_modal_ver", 0)
    sorted_containers = sort_items(
        sortable_items,
        multi_containers=True,
        direction="horizontal",
        custom_style=read_css("sortable_modal"),
        key=f"home_sortable_colunas_modal_{ver}",
    )

    # Converte labels de volta para IDs preservando a ordem do drag
    new_active_labels = sorted_containers[0]["items"]
    new_active_ids = [LABEL_TO_ID[lbl] for lbl in new_active_labels if lbl in LABEL_TO_ID]

    if new_active_ids:
        st.session_state["home_colunas_ativas"] = new_active_ids

    st.markdown('<div class="divider-light"></div>', unsafe_allow_html=True)
    c_rst, c_done = st.columns([1.5, 1], vertical_alignment="center")
    with c_rst:
        if st.button("↺ Restaurar padrão", key="btn_restaurar_colunas", help="Restaurar a configuração de colunas original recomendada"):
            st.session_state["home_colunas_ativas"] = list(DEFAULT_ACTIVE_COLUMNS)
            st.session_state["sortable_modal_ver"] = ver + 1
            st.rerun()
    with c_done:
        if st.button("Salvar e Fechar", key="btn_fechar_modal_colunas", type="primary", use_container_width=True):
            st.rerun()


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
            f'<tr onclick="window.location.href=\'{estado_url.link_empreendimento(id_emp)}\'">'
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
            f"<div class='pagination-info'>"
            f"Mostrando <b>{fmt_int_br(start_idx + 1)}–{fmt_int_br(end_idx)}</b> de <b>{fmt_int_br(total_filtrado)}</b> empreendimentos (Total: {fmt_int_br(total_emp)})"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c_size:
        c_lbl, c_sel = st.columns([1.1, 1.2])
        with c_lbl:
            st.markdown("<div class='pagination-info pagination-size-label'>Itens por pág.:</div>", unsafe_allow_html=True)
        with c_sel:
            cur_size_idx = PAGE_SIZE_OPTIONS.index(page_size) if page_size in PAGE_SIZE_OPTIONS else 1
            novo_size = st.selectbox(
                "Itens por página:",
                options=PAGE_SIZE_OPTIONS,
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
                    "<div class='pagination-ellipsis'>…</div>",
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
    inject_css("home")
    barra_nav = st.empty()  # barra e botão do chatbot são preenchidos depois que o estado atual é gravado na URL
    botao_chatbot = st.empty()
    render_header()

    df_base = data_loader.get_empreendimentos()

    if df_base.empty:
        st.error(
            "Nenhum dado encontrado em `data/processed/empreendimentos_priorizacao.parquet`.\n"
            "Execute o script `scripts/process_data.py` para processar a base de dados."
        )
        render_navbar("home", barra_nav)
        render_chatbot_button(botao_chatbot)
        return

    # ── Mapeamento das Carteiras Metodológicas ──
    carteiras_map = {
        "Carteira Recomendada (1.044)": {
            "slug": "recomendada",
            "fonte": "cenario recomendado",
            "titulo": "Carteira Recomendada",
        },
        "Carteira Otimizada (1.059)": {
            "slug": "otimizada",
            "fonte": "cenario otimizado",
            "titulo": "Carteira Otimizada",
        },
        "Carteira Completa (1.682)": {
            "slug": "completa",
            "fonte": "priorizacao geral",
            "titulo": "Carteira Completa",
        },
    }
    lista_carteiras = list(carteiras_map.keys())
    label_por_slug = {cfg["slug"]: label for label, cfg in carteiras_map.items()}

    if estado_url.inicio_da_sessao():
        slug_url = estado_url.ler("carteira", label_por_slug)
        if slug_url:
            st.session_state["home_carteira_selecionada"] = label_por_slug[slug_url]

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
        estado_url.semear_widget("busca_termo", "q")
        busca = st.text_input(
            "Buscar por Nome ou Código ID:",
            placeholder="Ex: Ferrovia Centro-Atlântica, BR-381, 113...",
            key="busca_termo",
        )

    with f_col2:
        setores = ["Todos"] + sorted([str(x) for x in df_emp["setor"].dropna().unique() if str(x).strip()]) if "setor" in df_emp.columns else ["Todos"]
        estado_url.semear_widget("filtro_setor", "setor", setores)
        filtro_setor = st.selectbox("Setor:", setores, key="filtro_setor")

    with f_col3:
        esferas = ["Todas"] + sorted([str(x) for x in df_emp["esfera_acao"].dropna().unique() if str(x).strip()]) if "esfera_acao" in df_emp.columns else ["Todas"]
        estado_url.semear_widget("filtro_esfera", "esfera", esferas)
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
        estado_url.semear_widget("filtro_impacto", "classificacao", impactos)
        filtro_impacto = st.selectbox("Classificação:", impactos, key="filtro_impacto")

    with g_col2:
        viabilidades = ["Todas"] + sorted([str(x) for x in df_emp["viabilidade"].dropna().unique() if str(x).strip()]) if "viabilidade" in df_emp.columns else ["Todas"]
        estado_url.semear_widget("filtro_viabilidade", "viabilidade", viabilidades)
        filtro_viabilidade = st.selectbox("Viabilidade:", viabilidades, key="filtro_viabilidade")

    with g_col3:
        origens = ["Todas"] + sorted([str(x) for x in df_emp["origem_ajustada"].dropna().unique() if str(x).strip()]) if "origem_ajustada" in df_emp.columns else ["Todas"]
        estado_url.semear_widget("filtro_origem", "origem", origens)
        filtro_origem = st.selectbox("Origem Ajustada:", origens, key="filtro_origem")

    with g_col4:
        vocacoes = ["Todas"] + sorted([str(x) for x in df_emp["vocacao"].dropna().unique() if str(x).strip()]) if "vocacao" in df_emp.columns else ["Todas"]
        estado_url.semear_widget("filtro_vocacao", "vocacao", vocacoes)
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

    # ── Estado da tabela (colunas e paginação), lido da URL no início da sessão ──
    if "home_colunas_ativas" not in st.session_state:
        cols_url = estado_url.ler("cols", conversor=lambda t: [c for c in t.split(",") if c in AVAILABLE_COLUMNS])
        st.session_state["home_colunas_ativas"] = cols_url or list(DEFAULT_ACTIVE_COLUMNS)
    if "home_page" not in st.session_state:
        st.session_state["home_page"] = estado_url.ler("pg", conversor=_inteiro_positivo) or 1
    if "home_page_size" not in st.session_state:
        st.session_state["home_page_size"] = estado_url.ler("itens", PAGE_SIZE_OPTIONS, int) or 25

    # Qualquer mudança de filtro volta a listagem para a página 1
    assinatura = (carteira_ativa, busca.strip(), filtro_setor, filtro_esfera, filtro_impacto,
                  filtro_viabilidade, filtro_origem, filtro_vocacao)
    if st.session_state.get("_home_assinatura_filtros", assinatura) != assinatura:
        st.session_state["home_page"] = 1
    st.session_state["_home_assinatura_filtros"] = assinatura

    page_size = st.session_state["home_page_size"]
    total_pages = max(1, math.ceil(total_filtrado / page_size))
    if st.session_state["home_page"] > total_pages:
        st.session_state["home_page"] = 1

    colunas_ativas = st.session_state.get("home_colunas_ativas") or DEFAULT_ACTIVE_COLUMNS

    estado_url.gravar(
        {
            "carteira": config_carteira["slug"], "q": busca.strip(),
            "setor": filtro_setor, "esfera": filtro_esfera, "classificacao": filtro_impacto,
            "viabilidade": filtro_viabilidade, "origem": filtro_origem, "vocacao": filtro_vocacao,
            "pg": st.session_state["home_page"], "itens": page_size, "cols": ",".join(colunas_ativas),
        },
        padroes={
            "carteira": "recomendada", "setor": "Todos", "esfera": "Todas", "classificacao": "Todos",
            "viabilidade": "Todas", "origem": "Todas", "vocacao": "Todas",
            "pg": 1, "itens": 25, "cols": ",".join(DEFAULT_ACTIVE_COLUMNS),
        },
    )
    estado_url.marcar_sessao_iniciada()
    render_navbar("home", barra_nav)
    render_chatbot_button(botao_chatbot)

    # ── Cabeçalho da Tabela com Botão de Personalização Integrado ──

    col_hdr_title, col_hdr_btn = st.columns([0.76, 0.24], vertical_alignment="bottom")
    with col_hdr_title:
        st.markdown(
            f'<div class="carteira-header-title">'
            f'Carteira de Empreendimentos Priorizados — {config_carteira["titulo"]}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_hdr_btn:
        if st.button(
            "Personalizar Colunas",
            key="btn_abrir_modal_colunas",
            help="Personalizar ordem e visibilidade das colunas na tabela",
            use_container_width=True,
        ):
            modal_personalizar_colunas()

    st.markdown('<div class="divider-navy"></div>', unsafe_allow_html=True)

    if total_filtrado == 0:
        st.warning("Nenhum empreendimento encontrado para os filtros selecionados.")
        return

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
