"""
Tela Inicial (Home) - Painel Executivo e Busca de Empreendimentos Priorizados
Apresenta KPIs, filtros dinâmicos e tabela de empreendimentos estilizada no mesmo padrão visual do Atlas.
"""

import html as html_mod
import math
import unicodedata
import streamlit as st
import pandas as pd
from services import data_loader
from services.formatters import fmt_int_br, fmt_bilhoes_br, fmt_brl_compacto, fmt_decimal_br_2, fmt_pct_br
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
    alta_viabilidade = int((df["viabilidade"] == "Alta viabilidade").sum())
    alto_impacto = int((df["impacto_avaliado_3_pond_cenario"] == "Alto impacto").sum())

    def pct_carteira(qtd: int) -> str:
        return f"{fmt_pct_br(qtd / total_emp * 100 if total_emp else 0)} da carteira"

    cards = [
        ("Empreendimentos Priorizados", fmt_int_br(total_emp), "Carteira avaliada"),
        ("Alta Viabilidade", fmt_int_br(alta_viabilidade), pct_carteira(alta_viabilidade)),
        ("Alto Impacto", fmt_int_br(alto_impacto), pct_carteira(alto_impacto)),
        ("Investimento Total", fmt_bilhoes_br(df["capex"].sum()), "CAPEX"),
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


def _texto(val) -> str:
    """Texto escapado; vazio ou nulo vira '-'."""
    if val is None or (not isinstance(val, str) and pd.isna(val)) or str(val).strip() == "":
        return "-"
    return html_mod.escape(str(val))


def _fmt_ic(val) -> str:
    if pd.notnull(val) and isinstance(val, (int, float)):
        return f"{float(val):.4f}".replace(".", ",")
    return "-"


def _fmt_tirm(val) -> str:
    """TIRM vem como fração (0,0776) e é exibida em % (7,76%)."""
    return fmt_pct_br(val * 100, 2) if pd.notna(val) else "-"


def _fmt_periodo(r) -> str:
    inicio, fim = r.get("data_inicio"), r.get("data_conclusao")
    if pd.isna(inicio) or pd.isna(fim):
        return "-"
    return f"{int(inicio)}–{int(fim)}"


CHIPS_VISIVEIS = 3


def _render_chips(valores) -> str:
    """Colunas-lista: até 3 chips cinza + chip '+N' com os demais itens no tooltip (passe o mouse)."""
    itens = [str(v) for v in (valores if valores is not None else [])]
    if not itens:
        return "-"
    chips = "".join(f'<span class="chip">{html_mod.escape(v)}</span>' for v in itens[:CHIPS_VISIVEIS])
    resto = itens[CHIPS_VISIVEIS:]
    if resto:
        chips += f'<span class="chip chip-mais" title="{html_mod.escape(", ".join(resto))}">+{len(resto)}</span>'
    return f'<div class="chips">{chips}</div>'


def _col_texto(label: str, coluna: str, alinhamento: str = "tc") -> dict:
    return {"label": label, "th_class": alinhamento, "th_style": "", "td_class": alinhamento,
            "render": lambda r: _texto(r.get(coluna))}


def _col_valor(label: str, render) -> dict:
    return {"label": label, "th_class": "tr", "th_style": "text-align: right;", "td_class": "tr font-mono nowrap",
            "render": render}


def _col_chips(label: str, coluna: str) -> dict:
    return {"label": label, "th_class": "tl", "th_style": "text-align: left;", "td_class": "tl",
            "render": lambda r: _render_chips(r.get(coluna))}


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
        "render": lambda r: f'<a href="{estado_url.link_empreendimento(int(r["id_empreendimento"]))}" target="_self" class="emp-link">{_texto(r.get("nome_empreendimento"))}</a>',
    },
    "setor": _col_texto("Setor", "setor"),
    "origem_ajustada": {
        "label": "Origem",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: f'<span class="badge badge-neutral">{_texto(r.get("origem_ajustada"))}</span>',
    },
    "esfera": {
        "label": "Esfera",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: _render_badge("esfera", r.get("esfera_acao")),
    },
    "tirm": _col_valor("TIRM", lambda r: _fmt_tirm(r.get("tirm"))),
    "ic": _col_valor("Índice (IC)", lambda r: _fmt_ic(r.get("ic_3_pond"))),
    "impacto": {
        "label": "Impacto",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: _render_badge("impacto", r.get("impacto_avaliado_3_pond_cenario")),
    },
    # ── Colunas ocultas por padrão (disponíveis em "Personalizar Colunas") ──
    "status": _col_texto("Status", "descr_status_empreendimento"),
    "viabilidade": {
        "label": "Viabilidade",
        "th_class": "tc",
        "th_style": "",
        "td_class": "tc",
        "render": lambda r: _render_badge("viabilidade", r.get("viabilidade")),
    },
    "vocacao": _col_texto("Vocação", "vocacao", "tl"),
    "natureza": _col_texto("Natureza", "natureza_empreendimento"),
    "intervencao_principal": _col_texto("Intervenção Principal", "intervencao_principal", "tl"),
    "capex": _col_valor("CAPEX", lambda r: fmt_brl_compacto(r.get("capex"))),
    "opex": _col_valor("OPEX", lambda r: fmt_brl_compacto(r.get("opex"))),
    "valor_total": _col_valor("Valor Total", lambda r: fmt_brl_compacto(r.get("valor_total"))),
    "extensao": _col_valor("Extensão (km)", lambda r: fmt_decimal_br_2(r.get("extensao_km"))),
    "periodo": _col_valor("Período", _fmt_periodo),
    "fonte_financiamento": _col_texto("Financiamento", "fonte_financiamento"),
    "responsavel_gestao": _col_texto("Responsável", "responsavel_gestao_infraestrutura"),
    "provavel_responsavel": _col_texto("Provável Responsável", "provavel_responsavel"),
    "intervencoes": _col_chips("Intervenções", "intervencoes"),
    "tipos_infraestruturas": _col_chips("Tipos de Infraestrutura", "tipos_infraestruturas"),
    "municipios": _col_chips("Municípios", "municipios"),
    "regioes": _col_chips("Regiões Intermediárias", "regioes_intermediarias"),
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
    "origem_ajustada",
    "esfera",
    "tirm",
    "ic",
    "impacto",
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


# ─────────────────────────────────────────────────────────────────────────────
# FILTROS (declarativos): (parâmetro na URL, rótulo, coluna do DataFrame)
# A chave do widget é "filtro_<parâmetro>". Para incluir um filtro, basta uma linha aqui.
# ─────────────────────────────────────────────────────────────────────────────

CARTEIRAS_HOME = {"Recomendada": "recomendada", "Otimizada": "otimizada", "De análise": "analise"}

# Seleção múltipla sempre visível (duas linhas de 4)
FILTROS_PRINCIPAIS = [
    ("setor", "Setor", "setor"),
    ("status", "Status", "descr_status_empreendimento"),
    ("origem", "Origem", "origem_ajustada"),
    ("esfera", "Esfera", "esfera_acao"),
    ("impacto", "Impacto", "impacto_avaliado_3_pond_cenario"),
    ("viabilidade", "Viabilidade", "viabilidade"),
    ("vocacao", "Vocação", "vocacao"),
    ("intervencao", "Intervenção Principal", "intervencao_principal"),
]
# Seleção múltipla dentro de "Mais filtros"
FILTROS_MAIS = [
    ("natureza", "Natureza", "natureza_empreendimento"),
    ("municipio", "Município", "municipios"),
    ("regiao", "Região Intermediária", "regioes_intermediarias"),
    ("infraestrutura", "Tipo de Infraestrutura", "tipos_infraestruturas"),
]
# Sliders de faixa dentro de "Mais filtros"; os limites acompanham a carteira ativa
FILTROS_FAIXA = [
    ("capex", "CAPEX", "capex"),
    ("opex", "OPEX", "opex"),
    ("ic", "Índice (IC)", "ic_3_pond"),
]

# Colunas cujo valor é uma lista: o filtro casa se QUALQUER item estiver selecionado
COLUNAS_LISTA = {"intervencoes", "tipos_infraestruturas", "municipios", "regioes_intermediarias"}

# Degraus dos sliders de R$: a maioria dos valores é pequena, uma escala linear os esmagaria no início
DEGRAUS_REAIS = [0.0, 1e6, 5e6, 1e7, 5e7, 1e8, 5e8, 1e9, 5e9, 1e10, 5e10, 1e11, 5e11, 1e12]


def _chave_ordem(texto: str) -> str:
    """Ordena ignorando acentos ('Águas' junto de 'Aguanil', não depois de 'Z')."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def _opcoes(df: pd.DataFrame, coluna: str) -> list:
    valores = df[coluna].explode() if coluna in COLUNAS_LISTA else df[coluna]
    return sorted({str(v) for v in valores.dropna() if str(v).strip()}, key=_chave_ordem)


def _degraus_reais(maximo: float) -> list:
    """Degraus até o primeiro que cobre o máximo da carteira (ex.: máximo 60 bi -> ... 50 bi, 100 bi)."""
    teto = next((d for d in DEGRAUS_REAIS if d >= maximo), DEGRAUS_REAIS[-1])
    return [d for d in DEGRAUS_REAIS if d <= teto] if teto > 0 else DEGRAUS_REAIS[:2]


def _degraus_ic(serie: pd.Series) -> list:
    """Passos de 0,01 cobrindo o menor e o maior IC da carteira."""
    inicio, fim = math.floor(serie.min() * 100), math.ceil(serie.max() * 100)
    return [round(v / 100, 2) for v in range(inicio, max(fim, inicio + 1) + 1)]


def _fmt_ic_faixa(val) -> str:
    return f"{val:.2f}".replace(".", ",")


def _preparar_lista(param: str, opcoes: list) -> list:
    """Estado do multiselect: semeado pela URL no início da sessão e sempre restrito às opções atuais
    (as opções mudam com a carteira; um valor fora delas derruba o widget)."""
    chave = f"filtro_{param}"
    if estado_url.inicio_da_sessao() and chave not in st.session_state:
        st.session_state[chave] = estado_url.ler_lista(param, opcoes)
    st.session_state[chave] = [v for v in st.session_state.get(chave, []) if v in opcoes]
    return st.session_state[chave]


def _preparar_faixa(param: str, opcoes: list) -> tuple:
    """Estado do slider de faixa; volta à faixa completa se o valor não existir nos degraus atuais."""
    chave = f"filtro_{param}"
    padrao = (opcoes[0], opcoes[-1])
    if estado_url.inicio_da_sessao() and chave not in st.session_state:
        st.session_state[chave] = estado_url.ler_faixa(param, opcoes) or padrao
    atual = tuple(st.session_state.get(chave, padrao))
    # Faixa completa da carteira anterior continua "completa" na nova (os limites mudam com a carteira)
    padrao_anterior = st.session_state.get(f"_{chave}_padrao", padrao)
    if len(atual) != 2 or not all(v in opcoes for v in atual) or atual == padrao_anterior:
        atual = padrao
    st.session_state[f"_{chave}_padrao"] = padrao
    st.session_state[chave] = atual
    return atual


def _limpar_filtros():
    """Callback do botão "Limpar filtros" (mantém a carteira escolhida)."""
    for param, _, _ in FILTROS_PRINCIPAIS + FILTROS_MAIS:
        st.session_state[f"filtro_{param}"] = []
    for param, _, _ in FILTROS_FAIXA:
        st.session_state.pop(f"filtro_{param}", None)
    st.session_state["busca_termo"] = ""


def _aplicar_filtros(df: pd.DataFrame, busca: str, selecoes: dict, faixas: dict, opcoes_faixa: dict) -> pd.DataFrame:
    if busca:
        termo = busca.lower()
        id_mask = df["id_empreendimento"].astype(str).str.contains(termo, regex=False, na=False)
        nome_mask = df["nome_empreendimento"].astype(str).str.lower().str.contains(termo, regex=False, na=False)
        df = df[id_mask | nome_mask]

    for param, _, coluna in FILTROS_PRINCIPAIS + FILTROS_MAIS:
        escolhidos = set(selecoes[param])
        if not escolhidos:
            continue
        if coluna in COLUNAS_LISTA:
            df = df[df[coluna].map(lambda itens: not escolhidos.isdisjoint(itens))]
        else:
            df = df[df[coluna].astype(str).isin(escolhidos)]

    for param, _, coluna in FILTROS_FAIXA:
        minimo, maximo = faixas[param]
        if (minimo, maximo) != (opcoes_faixa[param][0], opcoes_faixa[param][-1]):
            df = df[df[coluna].between(minimo, maximo)]
    return df


def render():
    """Função principal da tela Home."""
    inject_css("home")
    barra_nav = st.empty()  # barra e botão do chatbot são preenchidos depois que o estado atual é gravado na URL
    botao_chatbot = st.empty()
    render_header()

    # ── Carteira ativa (URL -> sessão no início; aceita o nome antigo "completa") ──
    rotulo_por_slug = {slug: rotulo for rotulo, slug in CARTEIRAS_HOME.items()}
    if estado_url.inicio_da_sessao():
        slug_url = estado_url.ler("carteira", rotulo_por_slug, data_loader.slug_carteira)
        if slug_url:
            st.session_state["filtro_carteira"] = rotulo_por_slug[slug_url]
    if st.session_state.get("filtro_carteira") not in CARTEIRAS_HOME:
        st.session_state["filtro_carteira"] = "Recomendada"
    slug_carteira = CARTEIRAS_HOME[st.session_state["filtro_carteira"]]

    df_emp = data_loader.get_empreendimentos(slug_carteira)

    if df_emp.empty:
        st.error(
            "Nenhum dado encontrado em `data/processed/carteiras.parquet`.\n"
            "Execute o script `scripts/process_data.py` para processar a base de dados."
        )
        render_navbar("home", barra_nav)
        render_chatbot_button(botao_chatbot)
        return

    # Renderiza KPIs específicos da carteira ativa
    render_kpis(df_emp)

    # ── Estado dos filtros (antes dos widgets: opções dependem da carteira) ──
    opcoes_lista = {param: _opcoes(df_emp, coluna) for param, _, coluna in FILTROS_PRINCIPAIS + FILTROS_MAIS}
    opcoes_faixa = {
        "capex": _degraus_reais(df_emp["capex"].max()),
        "opex": _degraus_reais(df_emp["opex"].max()),
        "ic": _degraus_ic(df_emp["ic_3_pond"]),
    }
    selecoes = {param: _preparar_lista(param, opcoes) for param, opcoes in opcoes_lista.items()}
    faixas = {param: _preparar_faixa(param, opcoes) for param, opcoes in opcoes_faixa.items()}
    estado_url.semear_widget("busca_termo", "q")

    # "Mais filtros" abre sozinho só se o link já vier com algum desses filtros ativo
    if "_home_mais_filtros_aberto" not in st.session_state:
        st.session_state["_home_mais_filtros_aberto"] = (
            any(selecoes[p] for p, _, _ in FILTROS_MAIS)
            or any(faixas[p] != (opcoes_faixa[p][0], opcoes_faixa[p][-1]) for p, _, _ in FILTROS_FAIXA)
        )

    # Painel de Filtros e Busca
    st.markdown(
        """
        <div class="filter-panel-header">
            <div class="filter-panel-title">
                Pesquisa e Filtros da Carteira
            </div>
            <div class="filter-panel-subtitle">
                Escolha a carteira e refine a listagem; filtro vazio considera todos
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_carteira, c_busca = st.columns([1.4, 5.4], vertical_alignment="bottom")
    c_carteira.selectbox("Carteira", list(CARTEIRAS_HOME), key="filtro_carteira")
    busca = c_busca.text_input(
        "Buscar por Nome ou Código ID",
        placeholder="Ex: Ferrovia Centro-Atlântica, BR-381, 113...",
        key="busca_termo",
    ).strip()

    for linha in (FILTROS_PRINCIPAIS[:4], FILTROS_PRINCIPAIS[4:]):
        for coluna_ui, (param, rotulo, _) in zip(st.columns(4), linha):
            coluna_ui.multiselect(rotulo, opcoes_lista[param], key=f"filtro_{param}", placeholder="Todos")

    with st.expander("Mais filtros", expanded=st.session_state["_home_mais_filtros_aberto"]):
        for coluna_ui, (param, rotulo, _) in zip(st.columns(4), FILTROS_MAIS):
            coluna_ui.multiselect(rotulo, opcoes_lista[param], key=f"filtro_{param}", placeholder="Todos")
        for coluna_ui, (param, rotulo, _) in zip(st.columns(3), FILTROS_FAIXA):
            opcoes = opcoes_faixa[param]
            # value= em tupla é o que faz o select_slider ter duas alças (faixa); o valor atual vem da sessão
            faixas[param] = coluna_ui.select_slider(
                rotulo,
                options=opcoes,
                value=(opcoes[0], opcoes[-1]),
                key=f"filtro_{param}",
                format_func=_fmt_ic_faixa if param == "ic" else fmt_brl_compacto,
            )

    df_filtrado = _aplicar_filtros(df_emp, busca, selecoes, faixas, opcoes_faixa).reset_index(drop=True)
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
    assinatura = (slug_carteira, busca, tuple(tuple(v) for v in selecoes.values()), tuple(faixas.values()))
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
            "carteira": slug_carteira, "q": busca,
            **{param: estado_url.texto_lista(valores) for param, valores in selecoes.items()},
            **{param: estado_url.texto_faixa(faixas[param], (op[0], op[-1])) for param, op in opcoes_faixa.items()},
            "pg": st.session_state["home_page"], "itens": page_size, "cols": ",".join(colunas_ativas),
        },
        padroes={"carteira": "recomendada", "pg": 1, "itens": 25, "cols": ",".join(DEFAULT_ACTIVE_COLUMNS)},
    )
    estado_url.marcar_sessao_iniciada()
    render_navbar("home", barra_nav)
    render_chatbot_button(botao_chatbot)

    # ── Cabeçalho da Tabela: título | botão redondo "Limpar filtros" | "Personalizar Colunas" ──
    # A ordem das colunas importa: o CSS identifica cada botão pela posição (home.css)

    col_hdr_title, col_hdr_limpar, col_hdr_btn = st.columns([0.80, 0.045, 0.155], vertical_alignment="bottom")
    with col_hdr_title:
        st.markdown(
            f'<div class="carteira-header-title">'
            f'Carteira de Empreendimentos Priorizados — {data_loader.CARTEIRAS[slug_carteira]}'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col_hdr_limpar:
        # O texto fica escondido pelo CSS (aparece só a vassoura); a dica aparece ao passar o mouse
        st.button("Limpar filtros", key="btn_limpar_filtros", on_click=_limpar_filtros, help="Limpar filtros")
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
