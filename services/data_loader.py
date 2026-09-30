"""
Serviço de carregamento de dados com cache do Streamlit.
Lê os arquivos .parquet da pasta data/processed/ (gerados em UTF-8 e com id_empreendimento inteiro pelo ETL).

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


@st.cache_data(show_spinner=False)
def load_parquet(filename: str) -> pd.DataFrame:
    """Carrega um arquivo parquet da pasta processed com cache.
    Utiliza @st.cache_data (cópia por sessão) — adequado para datasets pequenos."""
    file_path = PROCESSED_DIR / f"{filename}.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


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
    return pd.read_parquet(file_path)


def filtrar_por_empreendimento(df: pd.DataFrame, empreendimento_id: int) -> pd.DataFrame:
    """Linhas do DataFrame que pertencem ao empreendimento (o ETL garante id_empreendimento inteiro)."""
    if df.empty or "id_empreendimento" not in df.columns:
        return df.iloc[0:0]
    return df[df["id_empreendimento"] == empreendimento_id]


# Carteiras na ordem de precedência da ficha: slug -> nome exibido
CARTEIRAS = {
    "recomendada": "Carteira Recomendada",
    "otimizada": "Carteira Otimizada",
    "analise": "Carteira de Análise",
}
# Nomes antigos ainda aceitos (links salvos e chatbot usam "completa")
_ALIAS_CARTEIRA = {"completa": "analise", "geral": "analise", "otimizado": "otimizada", "recomendado": "recomendada"}


def slug_carteira(texto: str) -> str:
    """Normaliza o nome da carteira para o slug atual ('completa' -> 'analise')."""
    slug = str(texto).strip().lower()
    return _ALIAS_CARTEIRA.get(slug, slug)


def get_empreendimentos(carteira: str = None) -> pd.DataFrame:
    """Empreendimentos de uma carteira ('recomendada', 'otimizada' ou 'analise'), ordenados pelo IC.
    Sem carteira, devolve as três juntas (coluna 'carteira')."""
    df = load_parquet("carteiras")
    if df.empty:
        return df

    if carteira:
        df = df[df["carteira"] == slug_carteira(carteira)]

    # Valor Total = CAPEX + OPEX; vazio quando o empreendimento não tem nenhum dos dois
    df = df.assign(valor_total=(df["capex"].fillna(0) + df["opex"].fillna(0)).where(df["capex"].notna() | df["opex"].notna()))
    return df.sort_values(by="ic_3_pond", ascending=False).reset_index(drop=True)


def get_empreendimento_resolvido(empreendimento_id) -> pd.Series | None:
    """Registro do empreendimento na primeira carteira em que aparece:
    Recomendada -> Otimizada -> de Análise. Notas vazias são completadas pela carteira seguinte.
    A chave 'fonte_dimensoes' identifica a carteira usada."""
    matches = filtrar_por_empreendimento(load_parquet("carteiras"), empreendimento_id)
    if matches.empty:
        return None

    por_carteira = [matches[matches["carteira"] == slug] for slug in CARTEIRAS]
    por_carteira = [p.iloc[0] for p in por_carteira if not p.empty]

    base = por_carteira[0].copy()
    dim_cols = [
        "dimensao_estrategica",
        "dimensao_financeira",
        "dimensao_socioeconomica_pond",
        "dimensao_comercial",
        "dimensao_gerencial",
        "ic_3_pond",
        "impacto_avaliado_3_pond_cenario",
    ]
    for col in dim_cols:
        if pd.isna(base.get(col)) or base.get(col) == "":
            base[col] = next((p[col] for p in por_carteira[1:] if pd.notna(p.get(col))), base.get(col))

    base["fonte_dimensoes"] = CARTEIRAS[base["carteira"]]
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

def get_demanda_pax_aero() -> pd.DataFrame:
    """Retorna os dados de capacidade e demanda anual de passageiros aeroviários."""
    return load_parquet("demanda_pax_aero_ano")


def get_demanda_pax_ferro() -> pd.DataFrame:
    """Retorna os dados de demanda anual de passageiros ferroviários."""
    return load_parquet("demanda_pax_ferro_ano")

#def get_demanda_pax_aero() -> pd.DataFrame:
#    """Retorna os dados de demanda anual de passageiros aéreos."""
#    return load_parquet("demanda_pax_aero_ano")

def get_demanda_duto() -> pd.DataFrame:
    """Retorna os dados de demanda e volume dutoviário."""
    return load_parquet("demanda_duto_ano")


def get_resumo_financeiro() -> pd.DataFrame:
    """Retorna os dados do resumo financeiro (cenários 10, 7 e outros)."""
    return load_parquet("resumo_financeiro")


def get_dados_financeiro_resolvido(empreendimento_id) -> dict:
    """Retorna os dados financeiros consolidados do empreendimento com a regra de precedência:
    1. Cenário Recomendado (id_cenario = 10 em resumo_financeiro)
    2. Cenário Otimizado (id_cenario = 7 em resumo_financeiro)
    3. Custo Econômico LP (dados_financeiro / vw_empreendimento_custo_economico_lp)
    
    Retorna um dicionário com:
        - capex: float | None
        - opex: float | None
        - valor_total: float | None (capex + opex)
        - receita: float | None
        - tirm_val: float | None (em percentual, ex: 7.76 para 7,76%)
        - viabilidade: str ("-" se ausente)
        - mes_base: str ("-" se ausente)
        - fonte_financeiro: str ("Cenário Recomendado", "Cenário Otimizado" ou "Custo Econômico LP")
    """
    # 1. Tenta buscar em resumo_financeiro (Cenário 10 ou 7)
    df_resumo = get_resumo_financeiro()
    r_sel = None
    fonte_fin = "Custo Econômico LP"
    
    rec_resumo = filtrar_por_empreendimento(df_resumo, empreendimento_id)
    if not rec_resumo.empty:
        cenarios_num = pd.to_numeric(rec_resumo["id_cenario"], errors="coerce")
        r10 = rec_resumo[cenarios_num == 10]
        r7 = rec_resumo[cenarios_num == 7]
        if not r10.empty:
            r_sel = r10.iloc[0]
            fonte_fin = "Cenário Recomendado"
        elif not r7.empty:
            r_sel = r7.iloc[0]
            fonte_fin = "Cenário Otimizado"
                
    # 2. Dados de Custo Econômico LP (para fallback ou mês base)
    rec_fin = filtrar_por_empreendimento(get_dados_financeiro(), empreendimento_id)
    rf = rec_fin.iloc[0] if not rec_fin.empty else {}
    mes_base = rf.get("mes_atualizacao", "-")
    
    # 3. Metadados complementares (Viabilidade e TIRM da priorização)
    emp_res = get_empreendimento_resolvido(empreendimento_id)
    viab = emp_res.get("viabilidade") if emp_res is not None and pd.notna(emp_res.get("viabilidade")) else "-"
    
    if r_sel is not None:
        capex = r_sel.get("capex")
        opex = r_sel.get("opex")
        receita = r_sel.get("receita_codemge")
        tirm_val = r_sel.get("tirm_codemge")
        # Se tirm_codemge for nulo no resumo, faz fallback para o tirm da priorização
        if pd.isna(tirm_val) and emp_res is not None and pd.notna(emp_res.get("tirm")):
            tirm_val = float(emp_res["tirm"]) * 100
    else:
        capex = rf.get("capex_empreendimento_atualizado")
        opex = rf.get("opex_empreendimento_atualizado")
        receita = rf.get("receita")
        tirm_raw = emp_res.get("tirm") if emp_res is not None else None
        tirm_val = float(tirm_raw) * 100 if pd.notna(tirm_raw) else None
        
    valor_total = float(capex) + float(opex) if pd.notna(capex) and pd.notna(opex) else None
    
    return {
        "id_empreendimento": empreendimento_id,
        "capex": capex if pd.notna(capex) else None,
        "opex": opex if pd.notna(opex) else None,
        "valor_total": valor_total,
        "receita": receita if pd.notna(receita) else None,
        "tirm_val": float(tirm_val) if pd.notna(tirm_val) else None,
        "viabilidade": viab if viab not in (None, "", "nan") else "-",
        "mes_base": mes_base if mes_base not in (None, "", "nan") else "-",
        "fonte_financeiro": fonte_fin,
    }
