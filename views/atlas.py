"""
Tela do Atlas - Ficha Técnica e Detalhamento do Empreendimento Selecionado
Réplica fiel do layout do Atlas gerado pelo QGIS (Atlasref.jpeg).
"""

from pathlib import Path
import html as html_mod
import streamlit as st
import pandas as pd
from services import data_loader, map_service
from services.formatters import (
    fmt_brl,
    fmt_decimal_br,
    fmt_decimal_br_2,
    fmt_int_br,
    fmt_pct_br,
    fmt_mes_ano_br,
)

BASE_DIR = Path(__file__).resolve().parent.parent
LOGOS_DIR = BASE_DIR / "logos"


# ---------------------------------------------------------------------------
# Estilos CSS
# ---------------------------------------------------------------------------

def apply_atlas_styles():
    """Aplica estilos CSS para a ficha técnica do Atlas."""
    st.markdown(
        """
        <style>
            /* ---- Cabeçalho institucional ---- */
            .atlas-header {
                background: linear-gradient(135deg, #0b2545 0%, #133b63 100%);
                padding: 1.4rem 2rem;
                border-radius: 10px;
                color: #ffffff;
                margin-bottom: 1.2rem;
                box-shadow: 0 4px 14px rgba(0,0,0,0.10);
            }
            .atlas-header h2 {
                color: #ffffff;
                margin: 0;
                font-size: 28px;
                font-weight: 700;
                line-height: 1.3;
            }
            .atlas-header .sub {
                margin-top: 0.35rem;
                color: #c7d6ea;
                font-size: 24px;
                font-weight: 300;
                line-height: 1.3;
            }

            /* ---- Card de metadados ---- */
            .meta-card {
                background: #ffffff;
                border: 1px solid #dde3ec;
                border-radius: 10px;
                padding: 1.1rem 1.4rem;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                height: 520px;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }
            .meta-card .meta-row {
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
                padding: 0.30rem 0;
                border-bottom: 1px solid #eef1f6;
            }
            .meta-card .meta-row:last-child {
                border-bottom: none;
            }
            .meta-label {
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                color: #64748b;
                margin-bottom: 0.15rem;
            }
            .meta-value {
                font-size: 15px;
                color: #0f172a;
                font-weight: 500;
                line-height: 1.35;
            }

            /* ---- Espaço reservado para mapa ---- */
            .map-placeholder {
                background: #f0f4f8;
                border: 2px dashed #b0bec5;
                border-radius: 10px;
                min-height: 260px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #78909c;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
                padding: 1.5rem;
            }

            /* ---- Legenda ---- */
            .legenda-box {
                background: #ffffff;
                border: 1px solid #dde3ec;
                border-radius: 8px;
                padding: 0.9rem 1.1rem;
                margin-top: 0.6rem;
                box-shadow: 0 1px 4px rgba(0,0,0,0.03);
            }
            .legenda-title {
                font-size: 14px;
                font-weight: 700;
                color: #334155;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                letter-spacing: 0.4px;
            }
            .legenda-item {
                font-size: 13px;
                color: #475569;
                padding: 0.15rem 0;
                display: flex;
                align-items: center;
                gap: 0.45rem;
            }
            .legenda-icon {
                display: inline-block;
                width: 18px;
                height: 5px;
                border-radius: 2px;
            }
            .legenda-dot {
                display: inline-block;
                width: 9px;
                height: 9px;
                border-radius: 50%;
            }
            .legenda-square {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 2px;
            }

            /* ---- Seção / Título de tabela ---- */
            .section-title {
                font-size: 20px;
                font-weight: 700;
                color: #0b2545;
                margin: 1.5rem 0 0.5rem 0;
                padding-bottom: 0.3rem;
                border-bottom: 2px solid #0b2545;
            }

            /* ---- Tabelas HTML estilizadas ---- */
            .atlas-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
                margin-bottom: 0.8rem;
                box-shadow: 0 1px 4px rgba(0,0,0,0.04);
                border-radius: 6px;
                overflow: hidden;
            }
            .atlas-table thead th {
                background: #0b2545;
                color: #ffffff;
                padding: 0.65rem 0.75rem;
                text-align: center;
                font-weight: 600;
                font-size: 16px;
                letter-spacing: 0.2px;
                white-space: nowrap;
            }
            .atlas-table tbody td {
                padding: 0.5rem 0.7rem;
                text-align: center;
                border-bottom: 1px solid #e8ecf1;
                color: #334155;
                font-size: 12px;
                vertical-align: middle;
            }
            .atlas-table tbody tr:nth-child(even) {
                background: #f8fafc;
            }
            .atlas-table tbody tr:hover {
                background: #eef2f7;
            }
            .atlas-table td.text-left, .atlas-table .tl {
                text-align: left !important;
            }
            .atlas-table td.text-right, .atlas-table .tr {
                text-align: right !important;
            }
            .atlas-table .font-mono {
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 12px;
            }
            .atlas-table .font-bold {
                font-weight: 600;
            }
            /* ---- Botão Voltar Flutuante (Floating Action Pill) ---- */
            .atlas-floating-back-btn {
                position: fixed;
                bottom: 24px;
                left: 24px;
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
            .atlas-floating-back-btn:hover {
                background: linear-gradient(135deg, #133b63 0%, #1d4ed8 100%);
                color: #ffffff !important;
                border-color: #ffffff;
                transform: translateY(-2px);
                box-shadow: 0 6px 22px rgba(11, 37, 69, 0.45);
            }

            /* ---- Alinhamento Metadados ↔ Mapa (520px exatos em ambas as colunas) ---- */
            div[data-testid="stColumn"] iframe[title="streamlit_folium.folium_static"],
            div[data-testid="stColumn"] div[data-testid="stCustomComponentV1"] iframe,
            div[data-testid="stColumn"] iframe {
                border-radius: 10px !important;
                border: 1px solid #dde3ec !important;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
                height: 520px !important;
                min-height: 520px !important;
                box-sizing: border-box !important;
            }
            div[data-testid="stColumn"] div[data-testid="stCustomComponentV1"] {
                height: 520px !important;
                min-height: 520px !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Componentes Visuais
# ---------------------------------------------------------------------------

def render_back_button():
    """Botão flutuante de retorno para a lista de empreendimentos."""
    st.markdown(
        """
        <a href="?" target="_self" class="atlas-floating-back-btn">
            <span style="font-size: 1.1rem; line-height: 1;">←</span>
            <span>Voltar para a Lista</span>
        </a>
        """,
        unsafe_allow_html=True,
    )


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
    origem = row.get("origem_ajustada", "N/D")
    status = row.get("descr_status_empreendimento", "N/D")
    natureza = row.get("natureza_empreendimento", "N/D")
    grupo_mod = row.get("grupo_modelagem", "N/D")
    responsavel = row.get("responsavel_gestao_infraestrutura", "N/D")

    # Extensão total: soma das extensões das obras vinculadas
    extensao_total = df_obras["extensao_km"].sum() if not df_obras.empty and "extensao_km" in df_obras.columns else 0
    extensao_str = fmt_decimal_br_2(extensao_total) if extensao_total > 0 else "N/D"

    # Duração: mín data_inicio_obra — máx data_conclusao_obra
    duracao_str = "N/D"
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
        value_safe = html_mod.escape(str(value)) if value not in (None, "N/D") else str(value)
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
    """Tabela 1 — Resultados da Priorização."""
    estrategica = fmt_decimal_br(row.get("dimensao_estrategica"), 1)
    financeira = fmt_decimal_br(row.get("dimensao_financeira"), 5)
    socioeconomica = fmt_decimal_br(row.get("dimensao_socioeconomica_pond"), 5)
    comercial = fmt_decimal_br(row.get("dimensao_comercial"))
    gerencial = fmt_decimal_br(row.get("dimensao_gerencial"))
    ic = fmt_decimal_br(row.get("ic_3_pond"), 5)
    impacto = html_mod.escape(str(row.get("impacto_avaliado_3_pond_cenario") or "N/D"))

    st.markdown('<div class="section-title">Resultados da Priorização</div>', unsafe_allow_html=True)
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
    """Tabela 2 — Dados Financeiros."""
    df_fin = data_loader.get_dados_financeiro()
    if df_fin.empty:
        st.warning("Dados financeiros não disponíveis.")
        return

    rec = df_fin[df_fin["id_empreendimento"].astype(str) == str(empreendimento_id)]
    if rec.empty:
        st.info("Sem dados financeiros para este empreendimento.")
        return

    r = rec.iloc[0]
    capex = r.get("capex_empreendimento_atualizado")
    opex = r.get("opex_empreendimento_atualizado")
    receita = r.get("receita")
    mes_base = r.get("mes_atualizacao", "N/D")

    # Valor total = CAPEX + OPEX
    valor_total = None
    if pd.notna(capex) and pd.notna(opex):
        valor_total = float(capex) + float(opex)

    # TIRM e Viabilidade vêm da tabela principal de empreendimentos
    df_emp = data_loader.get_empreendimentos()
    emp_rec = df_emp[df_emp["id_empreendimento"].astype(str) == str(empreendimento_id)]
    tirm_val = None
    viabilidade = "N/D"
    if not emp_rec.empty:
        e = emp_rec.iloc[0]
        tirm_raw = e.get("tirm")
        if pd.notna(tirm_raw):
            tirm_val = float(tirm_raw) * 100
        viabilidade = html_mod.escape(str(e.get("viabilidade") or "N/D"))

    # Formatar mês base para exibição
    mes_display = fmt_mes_ano_br(mes_base)

    st.markdown(
        f'<div class="section-title">Dados Financeiros — Mês Base: {mes_display}</div>',
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
                    <td>{fmt_pct_br(tirm_val) if tirm_val is not None else "N/D"}</td>
                    <td>{viabilidade}</td>
                </tr>
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_tabela_alocacao(empreendimento_id):
    """Tabela 3 — Dados de Alocação 2055 por cenário."""
    df_aloc = data_loader.get_alocacao()
    if df_aloc.empty:
        st.warning("Dados de alocação não disponíveis.")
        return

    df_emp_aloc = df_aloc[df_aloc["id_empreendimento"].astype(str) == str(empreendimento_id)]
    if df_emp_aloc.empty:
        st.info("Sem dados de alocação para este empreendimento.")
        return

    st.markdown('<div class="section-title">Dados de Alocação 2055</div>', unsafe_allow_html=True)

    # Mapear colunas do parquet para o layout da tabela
    col_map = {
        "CGC": "flt_tkucgcfuturo",
        "CGNC": "flt_tkucgncfuturo",
        "GL": "flt_tkuglfuturo",
        "GSA": "flt_tkugsafuturo",
        "GSM": "flt_tkugsmfuturo",
        "OGSM": "flt_tkuogsmfuturo",
        "TKU Total": "flt_tkutotalfuturo",
    }

    rows_html = ""
    for _, r in df_emp_aloc.sort_values("id_cenario").iterrows():
        cenario = int(r["id_cenario"])
        cells = f"<td>{cenario}</td>"
        for display_name, col_name in col_map.items():
            val = r.get(col_name)
            cells += f'<td class="text-right">{fmt_int_br(val)}</td>'
        rows_html += f"<tr>{cells}</tr>"

    st.markdown(
        f"""
        <table class="atlas-table">
            <thead>
                <tr>
                    <th>Cenário</th>
                    <th>CGC</th>
                    <th>CGNC</th>
                    <th>GL</th>
                    <th>GSA</th>
                    <th>GSM</th>
                    <th>OGSM</th>
                    <th>TKU Total</th>
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
        descricao = html_mod.escape(str(obra.get("descricao_obra") or "N/D"))
        intervencao = html_mod.escape(str(obra.get("intervencao") or "N/D"))
        tipo_infra = html_mod.escape(str(obra.get("tipo_infraestrutura") or "N/D"))
        extensao = obra.get("extensao_km")
        valor_num = obra.get("valor_calculado")

        extensao_fmt = fmt_decimal_br_2(extensao) if pd.notna(extensao) else "N/D"
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
        '<div style="max-height: 520px; overflow-y: auto; border: 1px solid #e8ecf1; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.04); margin-bottom: 1.5rem;">'
        '<table class="atlas-table" style="margin-bottom: 0;">'
        '<thead><tr>'
        '<th style="text-align:left; position: sticky; top: 0; z-index: 2;">Descrição da Obra</th>'
        '<th style="position: sticky; top: 0; z-index: 2;">Intervenção</th>'
        '<th style="position: sticky; top: 0; z-index: 2;">Tipo da Infraestrutura</th>'
        '<th style="position: sticky; top: 0; z-index: 2;">Extensão (Km)</th>'
        '<th style="text-align:right; position: sticky; top: 0; z-index: 2;">Valor Obra (R$)</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
        '</div>'
    )
    st.markdown(table_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Função principal de renderização
# ---------------------------------------------------------------------------

def render(empreendimento_id):
    """Renderiza a página completa do Atlas para o empreendimento selecionado."""
    apply_atlas_styles()

    df_emp = data_loader.get_empreendimentos()

    if df_emp.empty:
        st.error("Base de empreendimentos não encontrada.")
        return

    # Busca o registro do empreendimento
    record = df_emp[df_emp["id_empreendimento"].astype(str) == str(empreendimento_id)]

    if record.empty:
        st.error(f"Empreendimento com ID '{empreendimento_id}' não foi encontrado.")
        render_back_button()
        return

    row = record.iloc[0]
    nome_emp = row.get("nome_empreendimento", "")
    setor = row.get("setor", "")
    esfera = row.get("esfera_acao", "")

    # Carregar obras vinculadas
    df_obras_all = data_loader.get_obras()
    df_obras = pd.DataFrame()
    if not df_obras_all.empty:
        df_obras = df_obras_all[
            df_obras_all["id_empreendimento"].astype(str) == str(empreendimento_id)
        ].copy()

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
    render_tabela_alocacao(empreendimento_id)

    # ── Tabela 4: Detalhamento das Obras ──
    render_tabela_obras(df_obras)
