"""
Tela do Atlas - Ficha Técnica e Detalhamento do Empreendimento Selecionado
Réplica fiel do layout do Atlas gerado pelo QGIS (Atlasref.jpeg).
"""

from pathlib import Path
import streamlit as st
import pandas as pd
from services import data_loader

BASE_DIR = Path(__file__).resolve().parent.parent
LOGOS_DIR = BASE_DIR / "logos"


# ---------------------------------------------------------------------------
# Formatação Brasileira
# ---------------------------------------------------------------------------

def fmt_brl(valor):
    """Formata valor monetário no padrão brasileiro: R$ 1.234.567,89"""
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return "N/D"
    negativo = valor < 0
    valor = abs(valor)
    inteiro = int(valor)
    centavos = round((valor - inteiro) * 100)
    parte_int = f"{inteiro:,}".replace(",", ".")
    resultado = f"R$ {parte_int},{centavos:02d}"
    return f"-{resultado}" if negativo else resultado


def fmt_decimal_br(valor, casas=4):
    """Formata número decimal no padrão brasileiro: 0,4031"""
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return "N/D"
    return f"{valor:.{casas}f}".replace(".", ",")


def fmt_decimal_br_2(valor):
    """Formata decimal com 2 casas: 1.234,56"""
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return "N/D"
    inteiro = int(abs(valor))
    frac = round((abs(valor) - inteiro) * 100)
    parte_int = f"{inteiro:,}".replace(",", ".")
    sinal = "-" if valor < 0 else ""
    return f"{sinal}{parte_int},{frac:02d}"


def fmt_int_br(valor):
    """Formata inteiro com separador de milhar brasileiro: 1.682"""
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        valor = int(float(valor))
    except (ValueError, TypeError):
        return "N/D"
    return f"{valor:,}".replace(",", ".")


def fmt_pct_br(valor):
    """Formata porcentagem no padrão brasileiro: 19,9%"""
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return "N/D"
    return f"{valor:.1f}".replace(".", ",") + "%"


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
                font-size: 1.45rem;
                font-weight: 700;
                line-height: 1.3;
            }
            .atlas-header .sub {
                margin-top: 0.35rem;
                color: #c7d6ea;
                font-size: 0.9rem;
            }

            /* ---- Card de metadados ---- */
            .meta-card {
                background: #ffffff;
                border: 1px solid #dde3ec;
                border-radius: 10px;
                padding: 1.3rem 1.5rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                height: 100%;
            }
            .meta-card .meta-row {
                padding: 0.5rem 0;
                border-bottom: 1px solid #eef1f6;
            }
            .meta-card .meta-row:last-child {
                border-bottom: none;
            }
            .meta-label {
                font-size: 0.73rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.6px;
                color: #64748b;
                margin-bottom: 0.1rem;
            }
            .meta-value {
                font-size: 0.92rem;
                color: #0f172a;
                font-weight: 500;
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
                font-size: 1rem;
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
                font-size: 0.78rem;
                font-weight: 700;
                color: #334155;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                letter-spacing: 0.4px;
            }
            .legenda-item {
                font-size: 0.78rem;
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
                font-size: 0.95rem;
                font-weight: 700;
                color: #1e293b;
                margin: 1.5rem 0 0.5rem 0;
                padding-bottom: 0.3rem;
                border-bottom: 2px solid #0b2545;
            }

            /* ---- Tabelas HTML estilizadas ---- */
            .atlas-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 0.82rem;
                margin-bottom: 0.8rem;
                box-shadow: 0 1px 4px rgba(0,0,0,0.04);
                border-radius: 6px;
                overflow: hidden;
            }
            .atlas-table thead th {
                background: #0b2545;
                color: #ffffff;
                padding: 0.55rem 0.7rem;
                text-align: center;
                font-weight: 600;
                font-size: 0.78rem;
                letter-spacing: 0.2px;
                white-space: nowrap;
            }
            .atlas-table tbody td {
                padding: 0.5rem 0.7rem;
                text-align: center;
                border-bottom: 1px solid #e8ecf1;
                color: #334155;
                vertical-align: middle;
            }
            .atlas-table tbody tr:nth-child(even) {
                background: #f8fafc;
            }
            .atlas-table tbody tr:hover {
                background: #eef2f7;
            }
            .atlas-table td.text-left {
                text-align: left;
            }
            .atlas-table td.text-right {
                text-align: right;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Componentes Visuais
# ---------------------------------------------------------------------------

def render_back_button():
    """Botão de retorno para a lista de empreendimentos."""
    if st.button("⬅ Voltar para a Lista de Empreendimentos", use_container_width=False):
        st.session_state["selected_empreendimento_id"] = None
        if "id" in st.query_params:
            del st.query_params["id"]
        st.rerun()


def render_header(empreendimento_id, nome_emp, setor, esfera):
    """Cabeçalho institucional com título e badges de setor/esfera."""
    st.markdown(
        f"""
        <div class="atlas-header">
            <h2>{empreendimento_id} - {nome_emp}</h2>
            <div class="sub">
                <b>Setor:</b> {setor} &nbsp;|&nbsp; <b>Esfera:</b> {esfera}
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

    rows_html = ""
    for label, value in campos:
        rows_html += f"""
            <div class="meta-row">
                <div class="meta-label">{label}</div>
                <div class="meta-value">{value}</div>
            </div>
        """

    st.markdown(
        f'<div class="meta-card">{rows_html}</div>',
        unsafe_allow_html=True,
    )


def render_map_placeholder():
    """Espaço reservado para o mapa geoespacial e legenda de intervenções."""
    # Placeholder do mapa
    st.markdown(
        """
        <div class="map-placeholder">
            🗺️ Visualização geoespacial será integrada em etapa futura<br>
            <span style="font-size: 0.82rem; color: #90a4ae;">(GeoPandas / Folium)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Legenda fiel ao QGIS
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
    impacto = row.get("impacto_avaliado_3_pond_cenario", "N/D")

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
        viabilidade = e.get("viabilidade", "N/D")

    # Formatar mês base para exibição
    mes_display = "N/D"
    if pd.notna(mes_base) and mes_base != "N/D":
        try:
            dt = pd.to_datetime(mes_base)
            meses_pt = {
                1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
                7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
            }
            mes_display = f"{meses_pt.get(dt.month, '')}/{str(dt.year)[2:]}"
        except Exception:
            mes_display = str(mes_base)

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


def render_tabela_obras(empreendimento_id, df_obras):
    """Tabela 4 — Detalhamento de todas as obras vinculadas ao empreendimento.
    O valor de cada obra é o MAIOR valor_adotado entre todos os cenários (CAPEX).
    """
    if df_obras.empty:
        st.info("Nenhuma obra vinculada a este empreendimento.")
        return

    # Buscar custos por obra — somar CAPEX+OPEX por cenário e pegar o maior entre cenários
    df_custo = data_loader.get_custo_obra()
    valor_por_obra = {}
    if not df_custo.empty:
        custos_emp = df_custo[df_custo["id_empreendimento"].astype(str) == str(empreendimento_id)]
        if not custos_emp.empty:
            # Soma todos os tipos de custo (CAPEX+OPEX) por obra/cenário
            soma_por_cenario = (
                custos_emp.groupby(["id_obra", "id_cenario"])["valor_adotado"]
                .sum()
                .reset_index()
            )
            # Pega o maior valor entre os cenários para cada obra
            valor_por_obra = (
                soma_por_cenario.groupby("id_obra")["valor_adotado"]
                .max()
                .to_dict()
            )

    st.markdown('<div class="section-title">Detalhamento das Obras</div>', unsafe_allow_html=True)

    rows_html = ""
    for _, obra in df_obras.iterrows():
        id_obra = obra.get("id_obra")
        descricao = obra.get("descricao_obra", "N/D")
        intervencao = obra.get("intervencao", "N/D")
        tipo_infra = obra.get("tipo_infraestrutura", "N/D")
        extensao = obra.get("extensao_km")
        valor_obra = valor_por_obra.get(id_obra)

        extensao_fmt = fmt_decimal_br_2(extensao) if pd.notna(extensao) else "N/D"
        valor_fmt = fmt_brl(valor_obra)

        rows_html += f"""
            <tr>
                <td class="text-left">{descricao}</td>
                <td>{intervencao}</td>
                <td>{tipo_infra}</td>
                <td class="text-right">{extensao_fmt}</td>
                <td class="text-right">{valor_fmt}</td>
            </tr>
        """

    st.markdown(
        f"""
        <table class="atlas-table">
            <thead>
                <tr>
                    <th style="text-align: left;">Descrição da Obra</th>
                    <th>Intervenção</th>
                    <th>Tipo da Infraestrutura</th>
                    <th>Extensão (Km)</th>
                    <th>Valor Obra (R$)</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


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

    # ── Seção Superior: Metadados + Mapa ──
    col_meta, col_map = st.columns([2, 3])

    with col_meta:
        render_metadados(row, df_obras)

    with col_map:
        render_map_placeholder()

    # ── Tabela 1: Resultados da Priorização ──
    render_tabela_priorizacao(row)

    # ── Tabela 2: Dados Financeiros ──
    render_tabela_financeiros(empreendimento_id)

    # ── Tabela 3: Dados de Alocação 2055 ──
    render_tabela_alocacao(empreendimento_id)

    # ── Tabela 4: Detalhamento das Obras ──
    render_tabela_obras(empreendimento_id, df_obras)
