"""
Diagnóstico e correção definitiva de Mojibake / Encodings
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

FILE_MAPPING = {
    "mvw_8_calcula_impacto": "empreendimentos_priorizacao",
    "vw_empreendimento_custo_economico_lp": "dados_financeiro",
    "tbl_alocacaoempreendimento": "alocacao_empreendimento",
    "vw_obra": "obras_priorizacao",
    "vw_custo_economico": "custo_obra",
}


def fix_mojibake(text):
    """Corrige texto que foi duplamente codificado (UTF-8 lido como Latin1)."""
    if not isinstance(text, str):
        return text
    try:
        # Se tem padrão de Mojibake (ex: Ã§, Ã£, Ã¡, Âª, Ã©)
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa todas as colunas de texto de um DataFrame corrigindo Mojibake."""
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include="object").columns:
        df_clean[col] = df_clean[col].apply(fix_mojibake)
    return df_clean


def process_all():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = list(RAW_DIR.glob("*.csv"))

    for prefix, target_name in FILE_MAPPING.items():
        matches = [f for f in csv_files if f.name.startswith(prefix)]
        if prefix == "vw_custo_economico":
            matches = [f for f in matches if not f.name.startswith("vw_empreendimento_custo_economico")]

        if not matches:
            continue

        csv_file = sorted(matches)[-1]
        parquet_file = PROCESSED_DIR / f"{target_name}.parquet"

        # Lê o CSV
        try:
            df = pd.read_csv(csv_file, sep=";", encoding="utf-8", low_memory=False)
        except Exception:
            df = pd.read_csv(csv_file, sep=";", encoding="latin1", low_memory=False)

        df.columns = [c.strip().strip('"') for c in df.columns]
        
        # Aplica a correção de mojibake em todas as colunas
        df = clean_dataframe(df)

        df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
        print(f"[OK] {target_name}.parquet gerado e corrigido!")


if __name__ == "__main__":
    process_all()
