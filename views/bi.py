"""
Painel de Indicadores & BI — explorar a carteira para encontrar empreendimentos.

Não é um ranking geral pelo IC: cada empreendimento é comparado com os seus pares (mesmo setor e mesmo
recorte) para mostrar em que ele vai bem. Os cálculos ficam em services/bi_service.py.
"""

import html as html_mod
import altair as alt
import pandas as pd
import streamlit as st
from services import bi_service as bi
from services import data_loader
from services.formatters import fmt_brl_compacto, fmt_decimal_br, fmt_int_br, fmt_pct_br
from views import estado_url
from views.home import CARTEIRAS_HOME
from views.ui import inject_css, render_navbar

TODOS_SETORES = "Todos os setores"

# Cores dos gráficos (configuração do Altair, que não lê o CSS da página); mesmas dos badges da Home
CORES_IMPACTO = {"Alto impacto": "#166534", "Médio impacto": "#d97706", "Baixo impacto": "#94a3b8"}
COR_NAVY = "#0b2545"
COR_CINZA = "#cbd5e1"


# ── Dados (cache por carteira + setor) ──────────────────────────────────────

@st.cache_data(show_spinner=False)
def _dados(carteira: str, setor: str) -> pd.DataFrame:
    df = bi.preparar(data_loader.get_empreendimentos(carteira))
    if setor == TODOS_SETORES:
        return df
    return df[df["setor"] == setor].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _perfil(carteira: str, setor: str, empreendimento_id: int) -> pd.DataFrame:
    return bi.perfil(_dados(carteira, setor), empreendimento_id)


# ── Formatação ──────────────────────────────────────────────────────────────

def _fmt_metrica(metrica_id: str, valor) -> str:
    if pd.isna(valor):
        return "-"
    if metrica_id == "tirm":
        return fmt_pct_br(valor * 100, 2)
    return fmt_decimal_br(valor, 4)


def _fmt_posicao(posicao, total) -> str:
    return f"{fmt_int_br(posicao)}º de {fmt_int_br(total)}"


def _classe_posicao(posicao, total) -> str:
    """Faixa de cor da posição: topo (destaque), primeiro quarto, meio, fim do grupo."""
    if posicao <= bi.limite_destaque(total):
        return "rk rk-topo"
    if posicao <= total * 0.25:
        return "rk rk-bom"
    if posicao <= total * 0.75:
        return "rk rk-meio"
    return "rk rk-fim"


def _link_emp(row) -> str:
    nome = html_mod.escape(str(row["nome_empreendimento"]))
    return f'<a href="{estado_url.link_empreendimento(int(row["id_empreendimento"]))}" target="_self" class="bi-emp-link">{nome}</a>'


def _badge_impacto(valor) -> str:
    texto = str(valor or "-")
    classe = {"Alto impacto": "bi-badge-alto", "Médio impacto": "bi-badge-medio"}.get(texto, "bi-badge-baixo")
    return f'<span class="bi-badge {classe}">{html_mod.escape(texto)}</span>'


def _tabela(cabecalhos: list, linhas: list, classe: str = "") -> str:
    """Tabela HTML no padrão do Atlas. `cabecalhos`: lista de (rótulo, classe de alinhamento)."""
    ths = "".join(f'<th class="{cls}">{html_mod.escape(rot)}</th>' for rot, cls in cabecalhos)
    trs = "".join("<tr>" + "".join(f'<td class="{cls}">{cel}</td>' for cel, (_, cls) in zip(linha, cabecalhos)) + "</tr>"
                  for linha in linhas)
    return f'<table class="atlas-table bi-table {classe}"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>'


def _titulo(texto: str, subtitulo: str = "") -> None:
    sub = f'<div class="bi-section-sub">{subtitulo}</div>' if subtitulo else ""
    st.markdown(f'<div class="bi-section-title">{html_mod.escape(texto)}</div>{sub}', unsafe_allow_html=True)


# ── Cabeçalho e números-resumo ──────────────────────────────────────────────

def _render_kpis(df: pd.DataFrame) -> None:
    presente = int((df["momento"] == "Presente").sum())
    alto = int((df["impacto_avaliado_3_pond_cenario"] == "Alto impacto").sum())
    cards = [
        ("Empreendimentos", fmt_int_br(len(df)), "na seleção"),
        ("Presente | Futuro", f"{fmt_int_br(presente)} | {fmt_int_br(len(df) - presente)}", "Contratado | Planejado"),
        ("CAPEX", fmt_brl_compacto(df["capex"].sum()), "soma da seleção"),
        ("Alto Impacto", fmt_int_br(alto), f"{fmt_pct_br(alto / len(df) * 100 if len(df) else 0)} da seleção"),
    ]
    for col, (titulo, valor, sub) in zip(st.columns(len(cards)), cards):
        col.markdown(
            f'<div class="bi-kpi"><div class="bi-kpi-title">{titulo}</div>'
            f'<div class="bi-kpi-value">{valor}</div><div class="bi-kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )


# ── Aba 1: Perfil do empreendimento ─────────────────────────────────────────

def _render_perfil(carteira: str, setor: str, df: pd.DataFrame, empreendimento_id: int) -> None:
    r = df[df["id_empreendimento"] == empreendimento_id]
    if r.empty:
        return
    r = r.iloc[0]
    st.markdown(
        f'<div class="bi-perfil-card"><div class="bi-perfil-nome">{_link_emp(r)}</div>'
        f'<div class="bi-perfil-meta">{html_mod.escape(str(r["intervencao_principal"]))} · {r["momento"]} '
        f'({html_mod.escape(str(r["descr_status_empreendimento"]))}) · {html_mod.escape(str(r["esfera_acao"]))} · '
        f'Investimento total {fmt_brl_compacto(r["valor_total"])} · TIRM {_fmt_metrica("tirm", r["tirm"])} · '
        f'IC {fmt_decimal_br(r["ic_3_pond"], 4)} — {_fmt_posicao(r["pos_ic_setor"], r["total_setor"])} no setor</div></div>',
        unsafe_allow_html=True,
    )
    p = _perfil(carteira, setor, empreendimento_id)
    if p.empty:
        return
    # Região: o empreendimento pode tocar várias; mostra a melhor posição
    p = p.sort_values("top_pct").drop_duplicates(["metrica", "recorte"])
    grupos = p.drop_duplicates("recorte").set_index("recorte")["grupo"]
    cab = [("Métrica", "tl"), ("Valor", "tr")]
    for rec in bi.RECORTES:
        rotulo = bi.RECORTES[rec][0]
        if rec in grupos and rec != "setor":
            rotulo = f"{rotulo}: {grupos[rec]}" if rec != "regiao" else f"{rotulo} (melhor)"
        cab.append((rotulo, "tc"))
    linhas = []
    for metrica_id, metrica in bi.METRICAS.items():
        m = p[p["metrica"] == metrica_id].set_index("recorte")
        linha = [html_mod.escape(metrica.rotulo), _fmt_metrica(metrica_id, r[metrica.coluna])]
        for rec in bi.RECORTES:
            if rec not in m.index:
                linha.append("-")
                continue
            x = m.loc[rec]
            onde = f'<div class="bi-cel-sub">{html_mod.escape(str(x["grupo"]))}</div>' if rec == "regiao" else ""
            linha.append(f'<span class="{_classe_posicao(x["posicao"], x["total"])}">{_fmt_posicao(x["posicao"], x["total"])}</span>{onde}')
        linhas.append(linha)
    st.markdown(_tabela(cab, linhas), unsafe_allow_html=True)
    st.markdown(
        '<div class="bi-legenda"><span class="rk rk-topo">topo do grupo</span><span class="rk rk-bom">primeiro quarto</span>'
        '<span class="rk rk-meio">meio</span><span class="rk rk-fim">último quarto</span>'
        '<span class="bi-legenda-txt">"-" = sem valor na métrica (ou nota zero)</span></div>',
        unsafe_allow_html=True,
    )


def _render_aba_perfil(carteira: str, setor: str, df: pd.DataFrame) -> None:
    _titulo("Avaliação específica do empreendimento",
            "Posição do empreendimento em cada métrica, em comparação com os empreendimentos do mesmo recorte.")
    nomes = df.set_index("id_empreendimento")["nome_empreendimento"]
    eid = st.selectbox("Empreendimento", nomes.index.tolist(), key="bi_perfil_emp",
                       format_func=lambda i: f"{nomes[i]} (ID {i})")
    _render_perfil(carteira, setor, df, int(eid))


# ── Aba 2: Matriz Impacto × Viabilidade ─────────────────────────────────────

def _selecionado(evento, nome: str) -> int | None:
    pontos = (evento.selection.get(nome) if evento and evento.selection else None) or []
    return int(pontos[0]["id_empreendimento"]) if pontos else None


# Eixos Y da matriz: (chave, coluna, título do eixo, título do gráfico)
EIXOS_Y = [
    ("ic", "ic_3_pond", "Índice (IC) — impacto", "Impacto (IC) × Viabilidade"),
    ("invest", "valor_total", "Investimento total (CAPEX + OPEX) — escala logarítmica", "Investimento total × Viabilidade"),
    ("socio", "dimensao_socioeconomica_pond", "Dimensão socioeconômica — nota", "Dimensão socioeconômica × Viabilidade"),
    ("estrat", "dimensao_estrategica", "Dimensão estratégica — nota", "Dimensão estratégica × Viabilidade"),
]


def _grafico_matriz(carteira: str, setor: str, df: pd.DataFrame, m: pd.DataFrame,
                    chave: str, coluna: str, titulo_y: str, titulo: str) -> None:
    """Gráfico da matriz: X = TIRM (igual em todos), Y = `coluna`. Clique no ponto abre o perfil."""
    m = m[m[coluna].notna()]
    if chave == "invest":
        m = m[m[coluna] > 0]  # escala logarítmica não comporta zero
    if m.empty:
        st.info("Nenhum empreendimento deste setor tem esse valor calculado.")
        return
    x_min, x_max = min(m["tirm_pct"].min(), -2) - 1, max(m["tirm_pct"].max(), 13) + 1
    y_max = m[coluna].max() * (1.5 if chave == "invest" else 1.12)

    ponto = alt.selection_point(name="ponto", fields=["id_empreendimento"])
    cortes = [bi.CORTE_PPP * 100, bi.CORTE_CONCESSAO * 100]
    escala_x = alt.Scale(domain=[x_min, x_max], nice=False)
    escala_y = (alt.Scale(type="log", domain=[m[coluna].min() / 1.5, y_max], nice=False) if chave == "invest"
                else alt.Scale(domain=[0, y_max], nice=False))
    eixo_y = (alt.Axis(labelExpr="datum.value >= 1e9 ? replace(format(datum.value / 1e9, '.1f'), '.', ',') + ' Bi'"
                                 " : replace(format(datum.value / 1e6, '.0f'), '.', ',') + ' Mi'")
              if chave == "invest" else alt.Axis())
    tooltip = [alt.Tooltip("nome_empreendimento:N", title="Empreendimento"),
               alt.Tooltip("tirm_pct:Q", title="TIRM (%)", format=".2f"),
               alt.Tooltip("ic_3_pond:Q", title="IC", format=".4f")]
    notas = {"socio": "Nota socioeconômica", "estrat": "Nota estratégica"}
    if chave in notas:
        tooltip.append(alt.Tooltip(f"{coluna}:Q", title=notas[chave], format=".4f"))
    tooltip.append(alt.Tooltip("valor_total_txt:N", title="Valor total"))

    pontos = alt.Chart(m).mark_circle(size=90, stroke="white", strokeWidth=0.8).encode(
        # Streamlit 1.36 não aceita clique em gráfico de camadas: as linhas de corte são a grade do eixo X
        x=alt.X("tirm_pct:Q", title="TIRM (%) — viabilidade", scale=escala_x,
                axis=alt.Axis(values=cortes, grid=True, gridColor=COR_NAVY, gridDash=[6, 4], gridWidth=1.5,
                              labelExpr="replace(format(datum.value, '.1f'), '.', ',') + '%'")),
        y=alt.Y(f"{coluna}:Q", title=titulo_y, scale=escala_y, axis=eixo_y),
        color=alt.Color("impacto_avaliado_3_pond_cenario:N", title="Impacto",
                        scale=alt.Scale(domain=list(CORES_IMPACTO), range=list(CORES_IMPACTO.values()))),
        opacity=alt.condition(ponto, alt.value(0.9), alt.value(0.25)),
        tooltip=tooltip,
    ).add_params(ponto)

    evento = st.altair_chart(pontos.properties(height=480), use_container_width=True,
                             on_select="rerun", key=f"bi_matriz_{chave}")  # chave por eixo: cada gráfico guarda a sua seleção
    eid = _selecionado(evento, "ponto")
    if eid is not None:
        _titulo("Empreendimento selecionado")
        _render_perfil(carteira, setor, df, eid)


def _render_matriz(carteira: str, setor: str, df: pd.DataFrame) -> None:
    _titulo(
        "Matriz Impacto × Viabilidade",
        "Eixo X: TIRM (viabilidade), com linhas tracejadas em 0% e 11,2%. Eixo Y à sua escolha: Índice (IC), "
        "investimento total (CAPEX + OPEX, escala logarítmica) ou nota da dimensão socioeconômica ou da estratégica. Só aparecem "
        "empreendimentos com TIRM. <b>Clique num ponto</b> para ver o perfil dele.",
    )
    m = df[df["tirm"].notna()].copy()
    if m.empty:
        st.info("Nenhum empreendimento deste setor tem TIRM calculada.")
        return
    m["tirm_pct"] = m["tirm"] * 100
    m["valor_total_txt"] = m["valor_total"].map(fmt_brl_compacto)
    rotulos = {chave: rot for chave, _, rot, _ in EIXOS_Y}
    nomes_curtos = {"ic": "Índice (IC)", "invest": "Investimento total", "socio": "Dimensão socioeconômica",
                    "estrat": "Dimensão estratégica"}
    escolha = st.radio("Eixo Y", list(rotulos), format_func=nomes_curtos.get, horizontal=True, key="bi_matriz_eixo_y")
    chave, coluna, titulo_y, titulo = next(e for e in EIXOS_Y if e[0] == escolha)
    _grafico_matriz(carteira, setor, df, m, chave, coluna, titulo_y, titulo)


# ── Aba 4: Eficiência do CAPEX ──────────────────────────────────────────────

def _render_eficiencia(carteira: str, setor: str, df: pd.DataFrame) -> None:
    _titulo(
        "Eficiência do investimento",
        "Compara CAPEX e IC entre empreendimentos da mesma intervenção principal. Em navy, a <b>fronteira de "
        "eficiência</b>: nenhum outro empreendimento do grupo tem IC maior gastando menos. <b>Clique num ponto</b> "
        "para ver o perfil.",
    )
    base = df[df["capex"] > 0].copy()
    if base.empty:
        st.info("Nenhum empreendimento deste setor tem CAPEX.")
        return
    tamanhos = base.groupby("intervencao_principal").size().sort_values(ascending=False)
    grupo = st.selectbox("Intervenção principal", tamanhos.index.tolist(), key="bi_efic_grupo",
                         format_func=lambda g: f"{g} ({fmt_int_br(tamanhos[g])})")
    g = base[base["intervencao_principal"] == grupo].copy()
    g["fronteira"] = bi.fronteira_eficiencia(g)
    g["serie"] = g["fronteira"].map({True: "Fronteira de eficiência", False: "Demais"})
    g["capex_txt"] = g["capex"].map(fmt_brl_compacto)

    ponto = alt.selection_point(name="ponto_efic", fields=["id_empreendimento"])
    escala_x = alt.Scale(type="log")
    enc_x = alt.X("capex:Q", title="CAPEX (R$, escala logarítmica)", scale=escala_x, axis=alt.Axis(format="~s"))
    enc_y = alt.Y("ic_3_pond:Q", title="Índice (IC)")
    pontos = alt.Chart(g).mark_circle(size=80, stroke="white", strokeWidth=0.8).encode(
        x=enc_x, y=enc_y,
        color=alt.Color("serie:N", title=None,
                        scale=alt.Scale(domain=["Fronteira de eficiência", "Demais"], range=[COR_NAVY, COR_CINZA])),
        opacity=alt.condition(ponto, alt.value(0.95), alt.value(0.3)),
        tooltip=[alt.Tooltip("nome_empreendimento:N", title="Empreendimento"),
                 alt.Tooltip("capex_txt:N", title="CAPEX"),
                 alt.Tooltip("ic_3_pond:Q", title="IC", format=".4f")],
    ).add_params(ponto)
    evento = st.altair_chart(pontos.properties(height=420), use_container_width=True,
                             on_select="rerun", key="bi_eficiencia")

    f = g[g["fronteira"]].sort_values("capex")
    cab = [("Empreendimento", "tl"), ("CAPEX", "tr"), ("Índice (IC)", "tr"),
           ("Posição no setor (IC)", "tc"), ("Momento", "tc")]
    linhas_tab = [[_link_emp(r), fmt_brl_compacto(r["capex"]), fmt_decimal_br(r["ic_3_pond"], 4),
                   _fmt_posicao(r["pos_ic_setor"], r["total_setor"]), r["momento"]]
                  for _, r in f.iterrows()]
    st.markdown(_tabela(cab, linhas_tab), unsafe_allow_html=True)
    sem_capex = int((df["capex"] <= 0).sum())
    if sem_capex:
        st.caption(f"{fmt_int_br(sem_capex)} empreendimento(s) do setor com CAPEX zero ficaram fora desta análise.")

    eid = _selecionado(evento, "ponto_efic")
    if eid is not None:
        _titulo("Empreendimento selecionado")
        _render_perfil(carteira, setor, df, eid)


# ── Aba 3: Presente × Futuro (composição por esfera) ────────────────────────

def _fmt_capex_grupo(qtd, capex, opex) -> str:
    """CAPEX do grupo; "-" quando há empreendimentos mas CAPEX e OPEX somam zero (sem modelagem financeira)."""
    if qtd > 0 and capex == 0 and opex == 0:
        return "-"
    return fmt_brl_compacto(capex)


def _render_composicao(df: pd.DataFrame) -> None:
    _titulo("Intervenção principal por esfera", "Quantidade de empreendimentos e investimento (CAPEX) por "
            "intervenção principal, separados pela esfera.")
    coluna = "esfera_acao"
    valores = sorted(df[coluna].dropna().unique())
    qtd = pd.crosstab(df["intervencao_principal"], df[coluna]).reindex(columns=valores, fill_value=0)
    capex, opex = (df.pivot_table(index="intervencao_principal", columns=coluna, values=v, aggfunc="sum",
                                  fill_value=0).reindex(columns=valores, fill_value=0) for v in ("capex", "opex"))
    ordem = qtd.sum(axis=1).sort_values(ascending=False).index
    cab = [("Intervenção principal", "tl")] + [(v, "tr") for v in valores] + [(f"{v} — CAPEX", "tr") for v in valores]
    linhas = [[html_mod.escape(str(i))] + [fmt_int_br(qtd.loc[i, v]) for v in valores]
              + [_fmt_capex_grupo(qtd.loc[i, v], capex.loc[i, v], opex.loc[i, v]) for v in valores] for i in ordem]
    linhas.append(["<b>Total</b>"] + [f"<b>{fmt_int_br(qtd[v].sum())}</b>" for v in valores]
                  + [f"<b>{_fmt_capex_grupo(qtd[v].sum(), capex[v].sum(), opex[v].sum())}</b>" for v in valores])
    st.markdown(_tabela(cab, linhas, "bi-table-pf"), unsafe_allow_html=True)
    st.caption('"-" no CAPEX: CAPEX e OPEX zerados ao mesmo tempo, ou seja, não foi possível fazer a modelagem '
               "financeira completa desses empreendimentos nos estudos.")


# ── Página ──────────────────────────────────────────────────────────────────

def render():
    inject_css("bi")
    navbar = st.empty()
    render_navbar("bi", container=navbar)  # conteúdo provisório: evita o "tranco" (erros_solucoes.md, caso 12)

    # Carteira é global: vem da URL (a mesma da Home) e volta para ela
    if estado_url.inicio_da_sessao() and "bi_carteira" not in st.session_state:
        rotulo_por_slug = {slug: rot for rot, slug in CARTEIRAS_HOME.items()}
        slug_url = estado_url.ler("carteira", rotulo_por_slug, data_loader.slug_carteira)
        st.session_state["bi_carteira"] = rotulo_por_slug.get(slug_url, "Recomendada")
        estado_url.marcar_sessao_iniciada()

    st.markdown(
        '<div class="bi-header"><div class="bi-header-title">Painel de Indicadores &amp; BI</div>'
        '<div class="bi-header-sub">Encontre empreendimentos comparando cada um com os seus pares — '
        'não só pelo IC geral, mas pelos recortes em que ele se destaca.</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2, _ = st.columns([1.3, 1.3, 4])
    c1.selectbox("Carteira", list(CARTEIRAS_HOME), key="bi_carteira")
    carteira = CARTEIRAS_HOME[st.session_state["bi_carteira"]]
    estado_url.gravar({"carteira": carteira}, {"carteira": "recomendada"})
    render_navbar("bi", container=navbar)

    todos = data_loader.get_empreendimentos(carteira)
    if todos.empty:
        st.warning("Nenhum dado encontrado em `data/processed/carteiras.parquet`.")
        return
    setores = [TODOS_SETORES] + todos["setor"].value_counts().index.tolist()
    if st.session_state.get("bi_setor") not in setores:
        st.session_state["bi_setor"] = TODOS_SETORES
    c2.selectbox("Setor", setores, key="bi_setor")
    setor = st.session_state["bi_setor"]

    df = _dados(carteira, setor)
    _render_kpis(df)

    # Aba "Eficiência do CAPEX" (_render_eficiencia) oculta por enquanto
    abas = st.tabs(["Perfil do empreendimento", "Impacto × Viabilidade", "Presente × Futuro"])
    with abas[0]:
        _render_aba_perfil(carteira, setor, df)
    with abas[1]:
        _render_matriz(carteira, setor, df)
    with abas[2]:
        _render_composicao(df)
