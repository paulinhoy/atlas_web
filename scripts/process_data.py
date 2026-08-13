"""
Script de processamento e conversão de dados: CSV -> Parquet.
Mapeia os nomes brutos do banco de dados (PostGIS) para nomes padronizados em Parquet:
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


def convert_csv_to_parquet():
    """Converte os CSVs brutos em Parquet otimizado."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("--- Iniciando Conversao de CSV para Parquet ---")
    print(f"Origem dos dados brutos: {RAW_DIR}")
    print(f"Destino dos dados processados: {PROCESSED_DIR}\n")

    # Lista todos os CSVs em data/raw/
    csv_files = list(RAW_DIR.glob("*.csv"))

    if not csv_files:
        print("[AVISO] Nenhum arquivo .csv encontrado em data/raw/.")
        return

    processed_count = 0

    for prefix, target_name in FILE_MAPPING.items():
        # Busca arquivo que começa com o prefixo (evitando colisões específicas)
        matches = [f for f in csv_files if f.name.startswith(prefix)]
        
        # Filtro especial para não confundir vw_custo_economico com vw_empreendimento_custo_economico
        if prefix == "vw_custo_economico":
            matches = [f for f in matches if not f.name.startswith("vw_empreendimento_custo_economico")]

        if not matches:
            print(f"[NAO ENCONTRADO] Arquivo com prefixo '{prefix}' nao localizado.")
            continue

        csv_file = sorted(matches)[-1]  # Pega o mais recente se houver múltiplos
        parquet_file = PROCESSED_DIR / f"{target_name}.parquet"

        try:
            # Leitura com separador ';' e encoding utf-8/latin1
            try:
                df = pd.read_csv(csv_file, sep=";", encoding="utf-8", low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(csv_file, sep=";", encoding="latin1", low_memory=False)

            # Limpeza básica de nomes de colunas
            df.columns = [c.strip().strip('"') for c in df.columns]

            # Salva em Parquet
            df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
            print(f"[OK] {csv_file.name} -> {target_name}.parquet ({len(df):,} linhas, {len(df.columns)} colunas)")
            processed_count += 1
        except Exception as e:
            print(f"[ERRO] Falha ao processar {csv_file.name}: {e}")

    print(f"\n--- Concluido: {processed_count}/{len(FILE_MAPPING)} arquivos processados com sucesso! ---")


if __name__ == "__main__":
    convert_csv_to_parquet()
