"""
Serviço de carregamento de dados com cache do Streamlit.
Lê os arquivos .parquet da pasta data/processed/ com garantia de decodificação correta.

Estratégia de Cache:
    - Datasets PEQUENOS (< 2 MB): usam @st.cache_data (cópia por sessão, seguro contra mutação).
    - Datasets GRANDES (empreendimento_geo ~108 MB em disco / ~255 MB em RAM): usam
      @st.cache_resource (objeto ÚNICO compartilhado entre todas as sessões, sem cópias).

    ⚠️ REGRA DE OURO para dados carregados com @st.cache_resource:
       O DataFrame retornado é COMPARTILHADO entre todos os usuários do servidor.
       NUNCA faça mutações in-place (drop, atribuição de colunas, inplace=True).
       Se precisar modificar, use .copy() antes: df_local = df.copy()
"""

from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"


from services.formatters import fix_mojibake


@st.cache_data(show_spinner=False)
def load_parquet(filename: str) -> pd.DataFrame:
    """Carrega um arquivo parquet da pasta processed com cache e limpeza de caracteres.
    Utiliza @st.cache_data (cópia por sessão) — adequado para datasets pequenos."""
    file_path = PROCESSED_DIR / f"{filename}.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    
    df = pd.read_parquet(file_path)
    
    # Aplica limpeza defensiva nas colunas de texto (exceto geometrias WKT)
    for col in df.select_dtypes(include="object").columns:
        if col not in ("geom_ponto", "geom_linha"):
            df[col] = df[col].apply(fix_mojibake)
        
    return df


@st.cache_resource(show_spinner=False)
def _load_geo_shared() -> pd.DataFrame:
    """Carrega o parquet geoespacial (~108 MB) com @st.cache_resource.
    
    Retorna um objeto ÚNICO compartilhado entre todas as sessões — economiza ~255 MB
    de RAM por sessão simultânea comparado com @st.cache_data.

    ⚠️ O DataFrame retornado é READ-ONLY. Não faça mutações in-place.
       Consumidores: services/map_service.py (somente leitura confirmada).
    """
    file_path = PROCESSED_DIR / "empreendimento_geo.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    
    df = pd.read_parquet(file_path)
    
    # Aplica limpeza de Mojibake apenas nas colunas de texto (não nas geometrias WKT)
    for col in df.select_dtypes(include="object").columns:
        if col not in ("geom_ponto", "geom_linha"):
            df[col] = df[col].apply(fix_mojibake)
    
    return df


def get_empreendimentos(carteira: str = None) -> pd.DataFrame:
    """Retorna os empreendimentos priorizados, opcionalmente filtrados por carteira.
    
    Opções de carteira:
        - 'completa' ou 'priorizacao geral' -> Carteira Completa (todos os ~1.682 empreendimentos)
        - 'otimizada' ou 'cenario otimizado' -> Carteira Otimizada (~1.059 empreendimentos)
        - 'recomendada' ou 'cenario recomendado' -> Carteira Recomendada (~1.044 empreendimentos)
        - None -> Retorna a base completa com todas as fontes
    """
    df = load_parquet("empreendimentos_priorizacao")
    if df.empty:
        return df

    if carteira and "fonte_priorizacao" in df.columns:
        c_norm = str(carteira).strip().lower()
        if c_norm in ("completa", "priorizacao geral", "geral"):
            df = df[df["fonte_priorizacao"] == "priorizacao geral"]
        elif c_norm in ("otimizada", "cenario otimizado", "otimizado"):
            df = df[df["fonte_priorizacao"] == "cenario otimizado"]
        elif c_norm in ("recomendada", "cenario recomendado", "recomendado"):
            df = df[df["fonte_priorizacao"] == "cenario recomendado"]
        else:
            df = df[df["fonte_priorizacao"].str.lower() == c_norm]

    if "ic_3_pond" in df.columns:
        return df.sort_values(by="ic_3_pond", ascending=False).reset_index(drop=True)
    return df


def get_empreendimento_resolvido(empreendimento_id) -> pd.Series | None:
    """Retorna o registro do empreendimento com notas das dimensões resolvidas pela regra:
    1. Nota no Cenário Recomendado (se existir)
    2. Se não tiver, nota no Cenário Otimizado
    3. Se não tiver, nota na Priorização Geral
    
    Retorna uma pd.Series com os dados e a chave 'fonte_dimensoes' identificando a origem das notas.
    """
    df_all = load_parquet("empreendimentos_priorizacao")
    if df_all.empty:
        return None

    emp_id_num = pd.to_numeric(empreendimento_id, errors="coerce")
    if pd.notna(emp_id_num):
        matches = df_all[pd.to_numeric(df_all["id_empreendimento"], errors="coerce") == emp_id_num]
    else:
        matches = df_all[df_all["id_empreendimento"].astype(str) == str(empreendimento_id)]

    if matches.empty:
        return None

    p_rec = matches[matches["fonte_priorizacao"] == "cenario recomendado"]
    p_otim = matches[matches["fonte_priorizacao"] == "cenario otimizado"]
    p_geral = matches[matches["fonte_priorizacao"] == "priorizacao geral"]

    if not p_rec.empty:
        base = p_rec.iloc[0].copy()
        fonte_dimensoes = "Cenário Recomendado"
    elif not p_otim.empty:
        base = p_otim.iloc[0].copy()
        fonte_dimensoes = "Cenário Otimizado"
    elif not p_geral.empty:
        base = p_geral.iloc[0].copy()
        fonte_dimensoes = "Priorização Geral"
    else:
        base = matches.iloc[0].copy()
        fonte_dimensoes = "Priorização Geral"

    # Preenchimento defensivo dimensão por dimensão caso haja valores faltantes
    dim_cols = [
        "dimensao_estrategica",
        "dimensao_financeira",
        "dimensao_socioeconomica_pond",
        "dimensao_comercial",
        "dimensao_gerencial",
        "ic_1_pond",
        "ic_2_pond",
        "ic_3_pond",
        "impacto_avaliado_1_pond_cenario",
        "impacto_avaliado_2_pond_cenario",
        "impacto_avaliado_3_pond_cenario",
    ]
    for col in dim_cols:
        if col in base and (pd.isna(base[col]) or base[col] == ""):
            if not p_otim.empty and pd.notna(p_otim.iloc[0].get(col)):
                base[col] = p_otim.iloc[0][col]
            elif not p_geral.empty and pd.notna(p_geral.iloc[0].get(col)):
                base[col] = p_geral.iloc[0][col]

    base["fonte_dimensoes"] = fonte_dimensoes
    return base


def get_obras() -> pd.DataFrame:
    return load_parquet("obras_priorizacao")


def get_dados_financeiro() -> pd.DataFrame:
    return load_parquet("dados_financeiro")


def get_custo_obra() -> pd.DataFrame:
    return load_parquet("custo_obra")


def get_alocacao() -> pd.DataFrame:
    return load_parquet("alocacao_empreendimento")


def get_empreendimento_geo() -> pd.DataFrame:
    """Retorna o DataFrame geoespacial compartilhado (READ-ONLY via @st.cache_resource).
    Não mute o DataFrame retornado — use .copy() se precisar modificar."""
    return _load_geo_shared()

def get_demanda_pax_ferro() -> pd.DataFrame:
    """Retorna os dados de demanda anual de passageiros ferroviários."""
    return load_parquet("demanda_pax_ferro_ano")


def get_demanda_duto() -> pd.DataFrame:
    """Retorna os dados de demanda e volume dutoviário."""
    return load_parquet("demanda_duto_ano")


def get_demanda_pax_aero() -> pd.DataFrame:
    """Retorna os dados de demanda de passageiros aeroviários por ano/cenário."""
    return load_parquet("demanda_pax_aero_ano")


