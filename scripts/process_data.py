"""
Script de processamento e conversão de dados: CSV -> Parquet.
Mapeia os nomes brutos do banco de dados (PostGIS) para nomes padronizados em Parquet
com correção automática de codificação dupla (Mojibake):
- mvw_8_calcula_impacto_* -> empreendimentos_priorizacao.parquet
- vw_empreendimento_custo_economico_* -> dados_financeiro.parquet
- tbl_alocacaoempreendimento_* -> alocacao_empreendimento.parquet
- vw_obra_* -> obras_priorizacao.parquet
- vw_custo_economico_* -> custo_obra.parquet
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Mapeamento de prefixo de arquivo bruto -> nome do arquivo parquet padronizado
FILE_MAPPING = {
    "mvw_8_calcula_impacto": "empreendimentos_priorizacao",
    "vw_empreendimento_custo_economico_lp": "dados_financeiro",
    "tbl_alocacaoempreendimento": "alocacao_empreendimento",
    "vw_obra": "obras_priorizacao",
    "vw_custo_economico": "custo_obra",
}


def fix_mojibake(text):
    """
    Corrige strings que sofreram double-encoding (ex: UTF-8 lido como Latin1 gerando 'Ã§Ã£o').
    Converte 'ConservaÃ§Ã£o' -> 'Conservação'.
    """
    if not isinstance(text, str):
        return text
    # Se contém sequências típicas de double encoding UTF-8 em Latin1
    if any(m in text for m in ["Ã", "Â", "â", "©"]):
        try:
            return text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica a correção de caracteres em todas as colunas de texto."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(fix_mojibake)
    return df


def convert_csv_to_parquet():
    """Converte os CSVs brutos em Parquet otimizado com encoding 100% corrigido."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("--- Iniciando Conversao de CSV para Parquet com correcao de texto ---")
    print(f"Origem dos dados brutos: {RAW_DIR}")
    print(f"Destino dos dados processados: {PROCESSED_DIR}\n")

    csv_files = list(RAW_DIR.glob("*.csv"))

    if not csv_files:
        print("[AVISO] Nenhum arquivo .csv encontrado em data/raw/.")
        return

    processed_count = 0

    for prefix, target_name in FILE_MAPPING.items():
        matches = [f for f in csv_files if f.name.startswith(prefix)]
        
        if prefix == "vw_custo_economico":
            matches = [f for f in matches if not f.name.startswith("vw_empreendimento_custo_economico")]

        if not matches:
            print(f"[NAO ENCONTRADO] Arquivo com prefixo '{prefix}' nao localizado.")
            continue

        csv_file = sorted(matches)[-1]
        parquet_file = PROCESSED_DIR / f"{target_name}.parquet"

        try:
            # Leitura do CSV
            try:
                df = pd.read_csv(csv_file, sep=";", encoding="latin1", low_memory=False)
            except Exception:
                df = pd.read_csv(csv_file, sep=";", encoding="utf-8", low_memory=False)

            # Limpeza das colunas
            df.columns = [c.strip().strip('"') for c in df.columns]

            # Correção de caracteres e acentuação
            df = clean_dataframe(df)

            # Salva em Parquet
            df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
            print(f"[OK] {csv_file.name} -> {target_name}.parquet ({len(df):,} linhas)")
            processed_count += 1
        except Exception as e:
            print(f"[ERRO] Falha ao processar {csv_file.name}: {e}")

    print(f"\n--- Concluido: {processed_count}/{len(FILE_MAPPING)} arquivos processados com sucesso! ---")


if __name__ == "__main__":
    convert_csv_to_parquet()
