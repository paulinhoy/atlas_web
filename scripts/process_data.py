"""
Script de processamento e conversão de dados: CSV -> Parquet.
Mapeia os nomes brutos do banco de dados (PostGIS) para nomes padronizados em Parquet
lendo os CSVs em UTF-8 (padrão de exportação do banco) e pré-calculando o custo máximo de obras:
- mvw_8_calcula_impacto_* -> empreendimentos_priorizacao.parquet
- vw_empreendimento_custo_economico_* -> dados_financeiro.parquet
- tbl_alocacaoempreendimento_* -> alocacao_empreendimento.parquet
- vw_obra_* -> obras_priorizacao.parquet (com coluna 'valor_calculado' pré-calculada)
- vw_custo_economico_* -> custo_obra.parquet
"""

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Mapeamento de nome do arquivo parquet padronizado -> lista priorizada de prefixos brutos
TARGET_FILES = {
    # Tabelas de Priorização e Alocação (prioriza novos arquivos e mantém retrocompatibilidade)
    "empreendimentos_priorizacao": ["priorizacao", "mvw_8_calcula_impacto"],
    "alocacao_empreendimento": ["alocacao_total", "tbl_alocacaoempreendimento"],
    "dados_financeiro": ["vw_empreendimento_custo_economico_lp"],
    "obras_priorizacao": ["vw_obra"],
    "custo_obra": ["vw_custo_economico"],
    # Novas tabelas de alocação/demanda
    "resumo_financeiro": ["resumo_financeiro"],
    "demanda_pax_aero_ano": ["capacidade_satur_aero_cenarios"],
    "demanda_duto_ano": ["demanda_duto"],
    "demanda_pax_ferro_ano": ["demanda_ferro_passageiro"],
}


# Sequências típicas de UTF-8 lido como Latin-1 ("ç" -> "Ã§", "ã" -> "Ã£", "–" -> "â€“")
MOJIBAKE_PATTERN = r"Ã[-¿]|â€"


def read_csv_bruto(csv_file: Path) -> pd.DataFrame:
    """Lê o CSV em UTF-8; Latin-1 fica só como reserva (UTF-8 falha de verdade, Latin-1 nunca falha)."""
    try:
        return pd.read_csv(csv_file, sep=";", encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        print(f"[AVISO] {csv_file.name} nao esta em UTF-8; lido como Latin-1.")
        return pd.read_csv(csv_file, sep=";", encoding="latin1", low_memory=False)


def avisar_acentuacao_suspeita(df: pd.DataFrame, nome: str) -> None:
    """Alerta (sem alterar) quando o texto parece ter acentuação corrompida na origem."""
    for col in df.select_dtypes(include="object").columns:
        suspeitos = df[col].astype(str).str.contains(MOJIBAKE_PATTERN, regex=True, na=False).sum()
        if suspeitos:
            print(f"[AVISO] {nome}.{col}: {suspeitos} valores com possivel acentuacao corrompida (ex.: 'Ã§').")


def convert_csv_to_parquet():
    """Converte os CSVs brutos (UTF-8) em Parquet otimizado com métricas pré-calculadas."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("--- Iniciando Conversao de CSV para Parquet ---")
    print(f"Origem dos dados brutos: {RAW_DIR}")
    print(f"Destino dos dados processados: {PROCESSED_DIR}\n")

    # Ignora arquivos temporários e de lock (ex: .~lock.*)
    csv_files = [f for f in RAW_DIR.glob("*.csv") if not f.name.startswith(".~lock") and not f.name.startswith(".")]

    if not csv_files:
        print("[AVISO] Nenhum arquivo .csv encontrado em data/raw/.")
        return

    processed_dfs = {}
    processed_count = 0

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
            print(f"[NAO ENCONTRADO] Arquivo para '{target_name}' (prefixos: {prefixes}) nao localizado.")
            continue

        try:
            df = read_csv_bruto(csv_file)
            df.columns = [c.strip().strip('"') for c in df.columns]
            avisar_acentuacao_suspeita(df, target_name)

            # Inteiro que aceita vazio: as views comparam o ID direto, sem conversões
            if "id_empreendimento" in df.columns:
                df["id_empreendimento"] = pd.to_numeric(df["id_empreendimento"]).astype("Int64")

            if target_name == "resumo_financeiro" and "id_empreendimento" in df.columns and "id_cenario" in df.columns:
                df = df.drop_duplicates(subset=["id_empreendimento", "id_cenario"]).reset_index(drop=True)

            processed_dfs[target_name] = df
            processed_count += 1
            print(f"[LIDO] {csv_file.name} -> {target_name} ({len(df):,} linhas)")

        except Exception as e:
            print(f"[ERRO] Falha ao processar {csv_file.name}: {e}")

    # Pré-cálculo inteligente de custos de obras (Opção 3 do Diagnóstico)
    # Calcula a soma por cenário e seleciona o maior custo entre cenários uma única vez no ETL
    if "obras_priorizacao" in processed_dfs and "custo_obra" in processed_dfs:
        df_obra = processed_dfs["obras_priorizacao"]
        df_custo = processed_dfs["custo_obra"]

        if "valor_adotado" in df_custo.columns and "id_obra" in df_custo.columns and "id_cenario" in df_custo.columns:
            soma_por_cenario = df_custo.groupby(["id_obra", "id_cenario"])["valor_adotado"].sum().reset_index()
            max_por_obra = soma_por_cenario.groupby("id_obra")["valor_adotado"].max()

            val_series = df_obra["id_obra"].map(max_por_obra)
            if "valor_global" in df_obra.columns:
                val_series = val_series.combine_first(pd.to_numeric(df_obra["valor_global"], errors="coerce"))
            df_obra["valor_calculado"] = val_series.fillna(0.0)
            print("[OTIMIZACAO ETL] Coluna 'valor_calculado' pre-calculada com sucesso em obras_priorizacao!")

    # Salva todos os DataFrames em Parquet
    for target_name, df in processed_dfs.items():
        parquet_file = PROCESSED_DIR / f"{target_name}.parquet"
        df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
        print(f"[SALVO] {parquet_file.name} ({len(df):,} linhas)")

    print(f"\n--- Concluido: {processed_count}/{len(TARGET_FILES)} arquivos processados e salvos com sucesso! ---")


if __name__ == "__main__":
    convert_csv_to_parquet()
