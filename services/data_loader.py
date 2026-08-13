"""
Serviço de carregamento de dados com cache do Streamlit.
Lê os arquivos .parquet da pasta data/processed/.
"""

from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"


@st.cache_data(show_spinner=False)
def load_parquet(filename: str) -> pd.DataFrame:
    """Carrega um arquivo parquet da pasta processed com cache."""
    file_path = PROCESSED_DIR / f"{filename}.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


def get_empreendimentos() -> pd.DataFrame:
    return load_parquet("empreendimentos_priorizacao")


def get_obras() -> pd.DataFrame:
    return load_parquet("obras_priorizacao")


def get_dados_financeiro() -> pd.DataFrame:
    return load_parquet("dados_financeiro")


def get_custo_obra() -> pd.DataFrame:
    return load_parquet("custo_obra")


def get_alocacao() -> pd.DataFrame:
    return load_parquet("alocacao_empreendimento")
