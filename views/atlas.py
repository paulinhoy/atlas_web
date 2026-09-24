"""
Tela do Atlas - Ficha Técnica e Detalhamento do Empreendimento Selecionado
Réplica fiel do layout do Atlas gerado pelo QGIS (Atlasref.jpeg).
"""

import html as html_mod
import streamlit as st
import pandas as pd
from services import data_loader, map_service
from views.ui import inject_css, render_back_button
from services.formatters import (
    fmt_brl,
    fmt_decimal_br,
    fmt_decimal_br_2,
    fmt_int_br,
    fmt_pct_br,
    fmt_mes_ano_br,
)

# ---------------------------------------------------------------------------
# Componentes Visuais
# ---------------------------------------------------------------------------

def render_header(empreendimento_id, nome_emp, setor, esfera):
    """Cabeçalho institucional com título e badges de setor/esfera."""
    nome_safe = html_mod.escape(str(nome_emp))
    setor_safe = html_mod.escape(str(setor))
    esfera_safe = html_mod.escape(str(esfera))
    st.markdown(
        f"""
        <div class="atlas-header">
            <h2>{empreendimento_id} - {nome_safe}</h2>
            <div class="sub">
                <b>Setor:</b> {setor_safe} &nbsp;|&nbsp; <b>Esfera:</b> {esfera_safe}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metadados(row, df_obras):
    """Painel esquerdo com ficha técnica de metadados do empreendimento."""
    origem = row.get("origem_ajustada", "-")
    status = row.get("descr_status_empreendimento", "-")
    natureza = row.get("natureza_empreendimento", "-")
    grupo_mod = row.get("grupo_modelagem", "-")
    responsavel = row.get("responsavel_gestao_infraestrutura", "-")

    # Extensão total: soma das extensões das obras vinculadas
    extensao_total = df_obras["extensao_km"].sum() if not df_obras.empty and "extensao_km" in df_obras.columns else 0
    extensao_str = fmt_decimal_br_2(extensao_total) if extensao_total > 0 else "-"

    # Duração: mín data_inicio_obra — máx data_conclusao_obra
    duracao_str = "-"
    if not df_obras.empty:
        col_ini = "data_inicio_obra"
        col_fim = "data_conclusao_obra"
        if col_ini in df_obras.columns and col_fim in df_obras.columns:
            inicio = df_obras[col_ini].dropna()
            fim = df_obras[col_fim].dropna()
            if not inicio.empty and not fim.empty:
                ano_ini = int(inicio.min())
                ano_fim = int(fim.max())
                duracao_str = f"{ano_ini} – {ano_fim}"

    campos = [
        ("Origem", origem),
        ("Status", status),
        ("Natureza", natureza),
        ("Extensão (Km)", extensao_str),
        ("Grupo de Modelagem", grupo_mod),
        ("Resp. atual da infraestrutura", responsavel),
        ("Duração", duracao_str),
    ]

    meta_html = '<div class="meta-card">'
    for i, (label, value) in enumerate(campos):
        label_safe = html_mod.escape(str(label))
        value_safe = html_mod.escape(str(value)) if value not in (None, "-", "N/D") else str(value)
        meta_html += (
            '<div class="meta-row">'
            f'<div class="meta-label">{label_safe}</div>'
            f'<div class="meta-value">{value_safe}</div>'
            '</div>'
        )
    meta_html += '</div>'
    st.markdown(meta_html, unsafe_allow_html=True)


def render_map_section(empreendimento_id):
    """Renderiza a visualização geoespacial interativa com altura alinhada ao painel de metadados."""
    # Renderiza o mapa interativo via serviço modular
    map_service.render_map(empreendimento_id)


def render_legenda_qgis():
    """
    [CÓDIGO PRESERVADO] Legenda do QGIS das camadas socioambientais e intervenções.
    Pode ser reativada a qualquer momento chamando render_legenda_qgis() abaixo do mapa.
    """
    st.markdown(
        """
        <div class="legenda-box">
            <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 160px;">
                    <div class="legenda-title">Camadas Socioambientais</div>
                    <div class="legenda-item"><span class="legenda-square" style="background: #d4e8d0; border: 1px solid #a8c8a0;"></span> Áreas Quilombolas INCRA</div>
                    <div class="legenda-item"><span class="legenda-square" style="background: #c8a882; border: 1px solid #a08060;"></span> Terras Indígenas FUNAI</div>
                    <div class="legenda-item"><span class="legenda-square" style="background: #a0c4b8; border: 1px solid #70a090;"></span> Unidades Conservação ANA</div>
                    <div class="legenda-item"><span class="legenda-square" style="background: #6b8ea0; border: 1px solid #4a7080;"></span> Áreas Urbanizadas IBGE</div>
                </div>
                <div style="flex: 1; min-width: 140px;">
                    <div class="legenda-title">Intervenções Lineares</div>
                    <div class="legenda-item"><span class="legenda-icon" style="background: #1a5276;"></span> Implantação</div>
                    <div class="legenda-item"><span class="legenda-icon" style="background: #1a3c5e; height: 7px;"></span> Ampliação</div>
                    <div class="legenda-item"><span class="legenda-icon" style="background: #5b7d9a;"></span> Manutenção</div>
                    <div class="legenda-item"><span class="legenda-icon" style="background: #8faabe;"></span> Operação</div>
                </div>
                <div style="flex: 1; min-width: 140px;">
                    <div class="legenda-title">Intervenções Pontuais</div>
                    <div class="legenda-item"><span class="legenda-dot" style="background: #1a5276;"></span> Implantação</div>
                    <div class="legenda-item"><span class="legenda-dot" style="background: #1a3c5e;"></span> Ampliação</div>
                    <div class="legenda-item"><span class="legenda-dot" style="background: #5b7d9a;"></span> Manutenção</div>
                    <div class="legenda-item"><span class="legenda-dot" style="background: #8faabe;"></span> Operação</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tabelas de Dados
# ---------------------------------------------------------------------------

def render_tabela_priorizacao(row):
    """Tabela 1 — Resultados da Priorização (com resolução hierárquica e badge da fonte)."""
    # Garante que as notas venham da resolução hierárquica: Recomendado -> Otimizado -> Geral
    emp_id = row.get("id_empreendimento")
    if "fonte_dimensoes" not in row and emp_id is not None:
        resolved = data_loader.get_empreendimento_resolvido(emp_id)
        if resolved is not None:
            row = resolved

    estrategica = fmt_decimal_br(row.get("dimensao_estrategica"), 1)
    financeira = fmt_decimal_br(row.get("dimensao_financeira"), 5)
    socioeconomica = fmt_decimal_br(row.get("dimensao_socioeconomica_pond"), 5)
    comercial = fmt_decimal_br(row.get("dimensao_comercial"))
    gerencial = fmt_decimal_br(row.get("dimensao_gerencial"))
    ic = fmt_decimal_br(row.get("ic_3_pond"), 5)
    impacto = html_mod.escape(str(row.get("impacto_avaliado_3_pond_cenario") or "-"))

    fonte = html_mod.escape(str(row.get("fonte_dimensoes") or "Priorização Geral"))
    badge_html = f'<span class="fonte-badge">Fonte: {fonte}</span>'

    st.markdown(
        f'<div class="section-title section-title--badge">'
        f'<span>Resultados da Priorização</span>'
        f'{badge_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <table class="atlas-table">
            <thead>
                <tr>
                    <th>Estratégica</th>
                    <th>Financeira</th>
                    <th>Socioeconômica</th>
                    <th>Comercial</th>
                    <th>Gerencial</th>
                    <th>Índice de Classificação</th>
                    <th>Impacto</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>{estrategica}</td>
                    <td>{financeira}</td>
                    <td>{socioeconomica}</td>
                    <td>{comercial}</td>
                    <td>{gerencial}</td>
                    <td>{ic}</td>
                    <td>{impacto}</td>
                </tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_tabela_financeiros(empreendimento_id):
    """Tabela 2 — Dados Financeiros consolidados com precedência (Cenário 10 ➔ Cenário 7 ➔ Custo Econômico LP)."""
    fin = data_loader.get_dados_financeiro_resolvido(empreendimento_id)
    if not fin:
        st.warning("Dados financeiros não disponíveis.")
        return

    capex = fin.get("capex")
    opex = fin.get("opex")
    valor_total = fin.get("valor_total")
    receita = fin.get("receita")
    tirm_val = fin.get("tirm_val")
    viabilidade = html_mod.escape(str(fin.get("viabilidade") or "-"))
    mes_base = fin.get("mes_base", "-")
    fonte_fin = html_mod.escape(str(fin.get("fonte_financeiro") or "Custo Econômico LP"))

    # Formatar mês base para exibição
    mes_display = fmt_mes_ano_br(mes_base) if mes_base != "-" else "-"
    badge_html = f'<span class="fonte-badge">Fonte: {fonte_fin}</span>'

    st.markdown(
        f'<div class="section-title section-title--badge">'
        f'<span>Dados Financeiros — Mês Base: {mes_display}</span>'
        f'{badge_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <table class="atlas-table">
            <thead>
                <tr>
                    <th>CAPEX (R$)</th>
                    <th>OPEX (R$)</th>
                    <th>Valor Total (R$)</th>
                    <th>Receita Total (R$)</th>
                    <th>TIRM (%)</th>
                    <th>Viabilidade</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="text-right">{fmt_brl(capex)}</td>
                    <td class="text-right">{fmt_brl(opex)}</td>
                    <td class="text-right">{fmt_brl(valor_total)}</td>
                    <td class="text-right">{fmt_brl(receita)}</td>
                    <td>{fmt_pct_br(tirm_val) if tirm_val is not None else "-"}</td>
                    <td>{viabilidade}</td>
                </tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_tabela_alocacao(empreendimento_id, row):
    """
    Tabela 3 - Dados de Alocação 2055 com roteamento dinâmico por setor, grupo e natureza.
    """
    # 1. Extração segura dos parâmetros de controle
    try:
        id_setor = int(row.get("id_setor")) if pd.notna(row.get("id_setor")) else None
    except (ValueError, TypeError):
        id_setor = None

    try:
        id_grupo = int(row.get("id_grupo_modelagem")) if pd.notna(row.get("id_grupo_modelagem")) else None
    except (ValueError, TypeError):
        id_grupo = None

    natureza = str(row.get("natureza_empreendimento") or "").strip()
    is_pax = natureza.lower() == "transporte de pessoas"

    # 4. Se for id_setor = 4: Não exibimos dados de alocação
    if id_setor == 4:
        return

    # 2. Definição da fonte de dados e do mapeamento de colunas
    df_fonte = pd.DataFrame()
    col_map = {}
    tem_cenario = True

    # -------------------------------------------------------------------------
    # CONDIÇÃO 1: Rodoviário (id_setor = 1)
    # -------------------------------------------------------------------------
    if id_setor == 1:
        df_fonte = data_loader.get_alocacao()
        col_map = {
            "Cenário": "id_cenario",
            "Carga": "flt_vehcargafuturo",
            "Ônibus": "flt_vehonibusfuturo",
            "Automóvel": "flt_vehautofuturo",
            "Total Veículos": "flt_vehtotalfuturo",
            "TKU Total": "flt_tkutotalfuturo",
        }

    # -------------------------------------------------------------------------
    # CONDIÇÃO 2.2: Ferroviário Passageiro (id_setor = 2 e Transporte de Pessoas)
    # -------------------------------------------------------------------------
    elif id_setor == 2 and is_pax:
        df_fonte = data_loader.get_demanda_pax_ferro()
        tem_cenario = "id_cenario" in df_fonte.columns if not df_fonte.empty else False
        col_map = {}
        if tem_cenario:
            col_map["Cenário"] = "id_cenario"
        col_map["Demanda Anual (Passageiros/Ano)"] = "demanda_ano"

    # -------------------------------------------------------------------------
    # CONDIÇÃO 2: Ferroviário TON (id_setor = 2, Cargas, id_grupo_modelagem = 2)
    # -------------------------------------------------------------------------
    elif id_setor == 2 and not is_pax and id_grupo == 2:
        df_fonte = data_loader.get_alocacao()
        col_map = {
            "Cenário": "id_cenario",
            "CGC": "flt_toncgcfuturo",
            "CGNC": "flt_toncgncfuturo",
            "GL": "flt_tonglfuturo",
            "GSA": "flt_tongsafuturo",
            "GSM": "flt_tongsmfuturo",
            "OGSM": "flt_tonogsmfuturo",
            "TON Total": "flt_tontotalfuturo",
        }

    # -------------------------------------------------------------------------
    # CONDIÇÃO 2.1: Ferroviário TKU (id_setor = 2, Cargas, id_grupo_modelagem = 1)
    # -------------------------------------------------------------------------
    elif id_setor == 2 and not is_pax and id_grupo == 1:
        df_fonte = data_loader.get_alocacao()
        col_map = {
            "Cenário": "id_cenario",
            "CGC": "flt_tkucgcfuturo",
            "CGNC": "flt_tkucgncfuturo",
            "GL": "flt_tkuglfuturo",
            "GSA": "flt_tkugsafuturo",
            "GSM": "flt_tkugsmfuturo",
            "OGSM": "flt_tkuogsmfuturo",
            "TKU Total": "flt_tkutotalfuturo",
        }

    # -------------------------------------------------------------------------
    # CONDIÇÃO 3: Hidroviário / Portuário (id_setor = 3)
    # -------------------------------------------------------------------------
    elif id_setor == 3:
        df_fonte = data_loader.get_alocacao()
        col_map = {
            "Cenário": "id_cenario",
            "CGC": "flt_toncgcfuturo",
            "CGNC": "flt_toncgncfuturo",
            "GL": "flt_tonglfuturo",
            "GSA": "flt_tongsafuturo",
            "GSM": "flt_tongsmfuturo",
            "OGSM": "flt_tonogsmfuturo",
            "TON Total": "flt_tontotalfuturo",
        }

    # -------------------------------------------------------------------------
    # CONDIÇÃO 5: Aeroviário (id_setor = 5)
    # -------------------------------------------------------------------------
    elif id_setor == 5:
        df_fonte = data_loader.get_demanda_pax_aero()
        tem_cenario = "id_cenario" in df_fonte.columns if not df_fonte.empty else False
        col_map = {}
        if tem_cenario:
            col_map["Cenário"] = "id_cenario"
        col_map["Demanda (Passageiros/Ano)"] = "demanda_pax_ano"

    # -------------------------------------------------------------------------
    # CONDIÇÃO 6: Dutoviário (id_setor = 6)
    # -------------------------------------------------------------------------
    elif id_setor == 6:
        df_fonte = data_loader.get_demanda_duto()
        tem_cenario = "id_cenario" in df_fonte.columns if not df_fonte.empty else False
        col_map = {}
        if tem_cenario:
            col_map["Cenário"] = "id_cenario"
        col_map["Tonelada Total"] = "volume_2055"
        col_map["TKU Total"] = "tku"

    # Fallback padrão caso não caia em nenhuma regra explícita
    else:
        df_fonte = data_loader.get_alocacao()
        col_map = {
            "Cenário": "id_cenario",
            "CGC": "flt_tkucgcfuturo",
            "CGNC": "flt_tkucgncfuturo",
            "GL": "flt_tkuglfuturo",
            "GSA": "flt_tkugsafuturo",
            "GSM": "flt_tkugsmfuturo",
            "OGSM": "flt_tkuogsmfuturo",
            "TKU Total": "flt_tkutotalfuturo",
        }

    # 3. Validação dos dados
    if df_fonte.empty or "id_empreendimento" not in df_fonte.columns:
        st.info("Sem dados de alocação para este empreendimento.")
        return

    df_emp_aloc = data_loader.filtrar_por_empreendimento(df_fonte, empreendimento_id)

    # 4. Filtro defensivo: inclui cenários 1 a 4, 7 (Otimizado) e 10 (Recomendado)
    if "id_cenario" in df_emp_aloc.columns:
        cenario_num = pd.to_numeric(df_emp_aloc["id_cenario"], errors="coerce")
        df_emp_aloc = df_emp_aloc[cenario_num.isin([1, 2, 3, 4, 7, 10])].sort_values("id_cenario")

    if df_emp_aloc.empty:
        st.info("Sem dados de alocação para este empreendimento.")
        return

    # 5. Renderização do Título e Tabela HTML
    st.markdown('<div class="section-title">Dados de Alocação 2055</div>', unsafe_allow_html=True)

    # Montagem do cabeçalho <th> com escape HTML defensivo
    ths_html = "".join([f"<th>{html_mod.escape(header)}</th>" for header in col_map.keys()])

    # Montagem das linhas <tr>
    rows_html = ""
    for _, r in df_emp_aloc.iterrows():
        cells = ""
        for header, col_name in col_map.items():
            val = r.get(col_name)
            if header == "Cenário":
                if pd.notna(val):
                    v_int = int(val)
                    if v_int == 7:
                        val_fmt = "7 (Otimizado)"
                    elif v_int == 10:
                        val_fmt = "10 (Recomendado)"
                    else:
                        val_fmt = str(v_int)
                else:
                    val_fmt = "-"
                cells += f"<td>{html_mod.escape(val_fmt)}</td>"
            else:
                val_fmt = html_mod.escape(fmt_int_br(val)) if pd.notna(val) else "-"
                cells += f'<td class="text-right">{val_fmt}</td>'
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(
        f"""
        <table class="atlas-table">
            <thead>
                <tr>
                    {ths_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_tabela_obras(df_obras):
    """Tabela 4 — Detalhamento de todas as obras vinculadas ao empreendimento.
    Ordenadas pelo valor da obra em ordem decrescente (do maior para o menor).
    O valor da intervenção é pré-calculado no pipeline ETL pelo cenário mais caro.
    """
    if df_obras.empty:
        st.info("Nenhuma obra vinculada a este empreendimento.")
        return

    # Cria cópia para ordenação defensiva
    df_obras_sorted = df_obras.copy()

    # Utiliza valor pré-calculado no ETL com fallback defensivo para valor_global
    if "valor_calculado" not in df_obras_sorted.columns:
        df_obras_sorted["valor_calculado"] = pd.to_numeric(
            df_obras_sorted.get("valor_global", 0), errors="coerce"
        ).fillna(0.0)

    # Ordena as obras pelo valor calculado em ordem decrescente
    df_obras_sorted = df_obras_sorted.sort_values(by="valor_calculado", ascending=False)

    st.markdown('<div class="section-title">Detalhamento das Obras</div>', unsafe_allow_html=True)

    rows_html = ""
    for _, obra in df_obras_sorted.iterrows():
        id_obra = obra.get("id_obra")
        descricao = html_mod.escape(str(obra.get("descricao_obra") or "-"))
        intervencao = html_mod.escape(str(obra.get("intervencao") or "-"))
        tipo_infra = html_mod.escape(str(obra.get("tipo_infraestrutura") or "-"))
        extensao = obra.get("extensao_km")
        valor_num = obra.get("valor_calculado")

        extensao_fmt = fmt_decimal_br_2(extensao) if pd.notna(extensao) else "-"
        valor_fmt = fmt_brl(valor_num)

        rows_html += (
            '<tr>'
            f'<td class="tl">{descricao}</td>'
            f'<td>{intervencao}</td>'
            f'<td>{tipo_infra}</td>'
            f'<td class="tr">{extensao_fmt}</td>'
            f'<td class="tr font-mono font-bold">{valor_fmt}</td>'
            '</tr>'
        )

    table_html = (
        '<div class="obras-scroll">'
        '<table class="atlas-table">'
        '<thead><tr>'
        '<th class="tl">Descrição da Obra</th>'
        '<th>Intervenção</th>'
        '<th>Tipo da Infraestrutura</th>'
        '<th>Extensão (Km)</th>'
        '<th class="tr">Valor Obra (R$)</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Função principal de renderização
# ---------------------------------------------------------------------------

def render(empreendimento_id: int | None):
    """Renderiza a página completa do Atlas; None indica um ID inválido vindo da URL."""
    inject_css("atlas")

    df_emp = data_loader.get_empreendimentos()

    if df_emp.empty:
        st.error("Base de empreendimentos não encontrada.")
        return

    # Busca o registro do empreendimento com notas resolvidas (Recomendado -> Otimizado -> Geral)
    row = data_loader.get_empreendimento_resolvido(empreendimento_id) if empreendimento_id is not None else None

    if row is None or (isinstance(row, pd.Series) and row.empty):
        if empreendimento_id is None:
            st.error("Empreendimento não encontrado: o ID informado na URL não é um número válido.")
        else:
            st.error(f"Empreendimento com ID '{empreendimento_id}' não foi encontrado.")
        render_back_button()
        return

    nome_emp = row.get("nome_empreendimento", "")
    setor = row.get("setor", "")
    esfera = row.get("esfera_acao", "")

    df_obras = data_loader.filtrar_por_empreendimento(data_loader.get_obras(), empreendimento_id)

    # ── Botão Voltar ──
    render_back_button()

    # ── Cabeçalho Institucional ──
    render_header(empreendimento_id, nome_emp, setor, esfera)

    # ── Seção Superior: Metadados + Mapa (alturas equalizadas via CSS) ──
    col_meta, col_map = st.columns([2, 3])

    with col_meta:
        render_metadados(row, df_obras)

    with col_map:
        render_map_section(empreendimento_id)

    # ── Tabela 1: Resultados da Priorização ──
    render_tabela_priorizacao(row)

    # ── Tabela 2: Dados Financeiros ──
    render_tabela_financeiros(empreendimento_id)

    # ── Tabela 3: Dados de Alocação 2055 ──
    render_tabela_alocacao(empreendimento_id, row)

    # ── Tabela 4: Detalhamento das Obras ──
    render_tabela_obras(df_obras)
