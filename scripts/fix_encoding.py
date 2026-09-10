"""
Diagnóstico e correção definitiva de Mojibake / Encodings
"""

import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.formatters import fix_mojibake

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

TARGET_FILES = {
    "empreendimentos_priorizacao": ["priorizacao", "mvw_8_calcula_impacto"],
    "alocacao_empreendimento": ["alocacao_total", "tbl_alocacaoempreendimento"],
    "dados_financeiro": ["vw_empreendimento_custo_economico_lp"],
    "obras_priorizacao": ["vw_obra"],
    "custo_obra": ["vw_custo_economico"],
}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa todas as colunas de texto de um DataFrame corrigindo Mojibake."""
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include="object").columns:
        df_clean[col] = df_clean[col].apply(fix_mojibake)
    return df_clean


def process_all():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    csv_files = [f for f in RAW_DIR.glob("*.csv") if not f.name.startswith(".~lock") and not f.name.startswith(".")]

    for target_name, prefixes in TARGET_FILES.items():
        csv_file = None
        for prefix in prefixes:
            matches = [f for f in csv_files if f.name.startswith(prefix)]
            if prefix == "vw_custo_economico":
                matches = [f for f in matches if not f.name.startswith("vw_empreendimento_custo_economico")]
            if matches:
                csv_file = sorted(matches)[-1]
                break

        if not csv_file:
            continue

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
