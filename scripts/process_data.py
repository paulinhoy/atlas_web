"""
Script de processamento e conversão de dados: CSV -> Parquet.
Mapeia os nomes brutos do banco de dados (PostGIS) para nomes padronizados em Parquet
lendo os CSVs em UTF-8 (padrão de exportação do banco) e pré-calculando o custo máximo de obras:
- <schema>_vw_dadosgerais_plataformaonline_* (3 carteiras) -> carteiras.parquet
- vw_empreendimento_custo_economico_* -> dados_financeiro.parquet
- tbl_alocacaoempreendimento_* -> alocacao_empreendimento.parquet
- vw_obra_* -> obras_priorizacao.parquet (com coluna 'valor_calculado' pré-calculada)
- vw_custo_economico_* -> custo_obra.parquet
"""

import csv
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Mapeamento de nome do arquivo parquet padronizado -> lista priorizada de prefixos brutos
TARGET_FILES = {
    # Carteiras (view vw_dadosgerais_plataformaonline de cada schema); juntadas em carteiras.parquet
    "carteira_recomendada": ["cenario_recomendado_2_vw_dadosgerais"],
    "carteira_otimizada": ["cenario_recomendado_1_vw_dadosgerais"],
    "carteira_analise": ["priorizacao_peltlp_vw_dadosgerais"],
    "natureza_legado": ["natureza_empreendimento_legado"],
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

# Colunas que chegam do banco como array PostgreSQL ("{Araporã,Prata}") e viram listas
COLUNAS_LISTA = ["intervencoes", "tipos_infraestruturas", "municipios", "regioes_intermediarias"]

# PENDENTE: a view vw_dadosgerais_plataformaonline não traz natureza_empreendimento nem
# id_grupo_modelagem, usados na tabela de Alocação da ficha. Até a view ser revisada:
# - a natureza vem de data/raw/natureza_empreendimento_legado.csv (extraída da tabela antiga);
# - o id do grupo de modelagem é deduzido do nome do grupo por este dicionário.
ID_GRUPO_MODELAGEM = {
    "Caso geral - infraestruturas lineares": 1,
    "Caso geral - infraestruturas pontuais": 2,
    "Terminais de passageiros": 3,
    "Empreendimentos rodoviários de execução pública - Infraestruturas lineares": 4,
    "Conservação rodoviária": 5,
    "Recuperação rodoviária": 6,
    "Empreendimentos rodoviários de execução pública - Infraestruturas pontuais": 8,
    "Caso geral - transporte ferroviário de pessoas": 9,
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


def array_pg_para_lista(valor) -> list:
    """'{Araporã,"Monte Alegre de Minas"}' -> ['Araporã', 'Monte Alegre de Minas']."""
    if not isinstance(valor, str) or not valor.strip("{} "):
        return []
    itens = next(csv.reader([valor.strip()[1:-1]], quotechar='"', escapechar="\\"))
    return [i.strip() for i in itens if i.strip()]


def montar_carteiras(processed_dfs: dict) -> pd.DataFrame | None:
    """Junta as 3 carteiras numa tabela só (coluna 'carteira'), converte as colunas-lista e
    completa natureza/id_grupo_modelagem, que a view ainda não traz."""
    partes = []
    for slug in ("recomendada", "otimizada", "analise"):
        df = processed_dfs.pop(f"carteira_{slug}", None)
        if df is None:
            print(f"[AVISO] Carteira '{slug}' nao encontrada em data/raw/.")
            continue
        partes.append(df.assign(carteira=slug))
    natureza = processed_dfs.pop("natureza_legado", None)
    if not partes:
        return None

    df = pd.concat(partes, ignore_index=True)
    for col in COLUNAS_LISTA:
        if col in df.columns:
            df[col] = df[col].map(array_pg_para_lista)

    if natureza is not None:
        df = df.merge(natureza[["id_empreendimento", "natureza_empreendimento"]], on="id_empreendimento", how="left")
        sem_natureza = df.loc[df["natureza_empreendimento"].isna(), "id_empreendimento"].unique()
        if len(sem_natureza):
            print(f"[AVISO] {len(sem_natureza)} empreendimentos sem natureza no arquivo legado: {list(sem_natureza)[:20]}")
    else:
        print("[AVISO] natureza_empreendimento_legado.csv nao encontrado: natureza ficara vazia.")

    df["id_grupo_modelagem"] = df["grupo_modelagem"].map(ID_GRUPO_MODELAGEM).astype("Int64")
    grupos_novos = set(df.loc[df["id_grupo_modelagem"].isna(), "grupo_modelagem"].dropna())
    if grupos_novos:
        print(f"[AVISO] grupo_modelagem sem id conhecido (atualize ID_GRUPO_MODELAGEM): {grupos_novos}")

    print(f"[CARTEIRAS] {df['carteira'].value_counts().to_dict()}")
    return df


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

    carteiras = montar_carteiras(processed_dfs)
    if carteiras is not None:
        processed_dfs["carteiras"] = carteiras

    # Salva todos os DataFrames em Parquet
    for target_name, df in processed_dfs.items():
        parquet_file = PROCESSED_DIR / f"{target_name}.parquet"
        df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
        print(f"[SALVO] {parquet_file.name} ({len(df):,} linhas)")

    print(f"\n--- Concluido: {processed_count}/{len(TARGET_FILES)} arquivos processados e salvos com sucesso! ---")


if __name__ == "__main__":
    convert_csv_to_parquet()
