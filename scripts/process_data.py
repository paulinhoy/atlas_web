"""
Script de processamento e conversão de dados: CSV -> Parquet.
Mapeia os nomes brutos do banco de dados (PostGIS) para nomes padronizados em Parquet
lendo os CSVs em UTF-8 (padrão de exportação do banco) e pré-calculando o custo máximo de obras:
- <schema>_vw_dadosgerais_plataformaonline (3 carteiras) -> carteiras.parquet
- <schema>_vw_custo_economico (carteira, cenario_recomendado_1 e _2) -> custo_obra.parquet
- <schema>_vw_financeiro_completo (cenario_recomendado_1 e _2) -> financeiro_completo.parquet
- carteira_vw_empreendimento_custo_economico_lp -> dados_financeiro.parquet
- cenario_recomendado_2_alocacao_geral -> alocacao_empreendimento.parquet
- carteira_vw_obra -> obras_priorizacao.parquet (com 'valor_calculado', 'cenario_valor' e 'origem_valor' pré-calculados)

Os CSVs podem estar em data/raw/ ou em subpastas dela (ex.: uma pasta por rodada de atualização).
"""

import csv
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Mapeamento de nome do arquivo parquet padronizado -> lista priorizada de prefixos brutos.
# Vale o primeiro prefixo que tiver arquivo; se vários arquivos casarem, vence o modificado por último.
TARGET_FILES = {
    # Carteiras (view vw_dadosgerais_plataformaonline de cada schema); juntadas em carteiras.parquet
    "carteira_recomendada": ["cenario_recomendado_2_vw_dadosgerais"],
    "carteira_otimizada": ["cenario_recomendado_1_vw_dadosgerais"],
    "carteira_analise": ["priorizacao_peltlp_vw_dadosgerais"],
    # Alocação compilada (cenários 1-4, 8 Otimizado e 10 Recomendado); os antigos (cenário 7) ficam de reserva
    "alocacao_empreendimento": ["cenario_recomendado_2_alocacao_geral", "alocacao_total", "tbl_alocacaoempreendimento"],
    "dados_financeiro": ["carteira_vw_empreendimento_custo_economico_lp", "vw_empreendimento_custo_economico_lp"],
    "obras_priorizacao": ["carteira_vw_obra", "vw_obra"],
    # Tabelas de alocação/demanda
    "demanda_pax_aero_ano": ["capacidade_satur_aero_cenarios"],
    "demanda_duto_ano": ["demanda_duto"],
    "demanda_pax_ferro_ano": ["demanda_ferro_passageiro"],
}

# Tabelas montadas com um arquivo por schema: (prefixo, id_cenario do schema).
# None mantém o id_cenario do arquivo (cenários oficiais 1 a 4). O número vem do schema porque o
# arquivo do Otimizado ainda chega com id_cenario = 7 (numeração antiga) e o financeiro não traz cenário.
TARGET_POR_CENARIO = {
    "custo_obra": [
        ("carteira_vw_custo_economico", None),
        ("cenario_recomendado_1_vw_custo_economico", 8),   # Otimizado
        ("cenario_recomendado_2_vw_custo_economico", 10),  # Recomendado
    ],
    "financeiro_completo": [
        ("cenario_recomendado_1_vw_financeiro_completo", 8),
        ("cenario_recomendado_2_vw_financeiro_completo", 10),
    ],
}

# Cenário adotado para o valor da obra: Recomendado (10) se existir; senão Otimizado (8);
# senão o mais caro entre os cenários da carteira de análise (1 a 4)
PRIORIDADE_CENARIO_OBRA = {10: 2, 8: 1}

# Origem do valor da obra (coluna 'origem_valor' de obras_priorizacao) a partir do tipo_custo da vw_custo_economico
ORIGEM_VALOR_OBRA = {"estimativa": "Estimado", "obra": "Declarado", "empreendimento": "Declarado"}

# Colunas que chegam do banco como array PostgreSQL ("{Araporã,Prata}") e viram listas
COLUNAS_LISTA = ["intervencoes", "tipos_infraestruturas", "municipios", "regioes_intermediarias"]

# A view vw_dadosgerais_plataformaonline traz natureza_empreendimento e o nome do grupo de modelagem,
# mas não o id do grupo, usado na tabela de Alocação da ficha: o id é deduzido do nome por este dicionário.
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


def escolher_arquivo(csv_files: list, prefixo: str) -> Path | None:
    """Arquivo cujo nome começa com `prefixo`; havendo vários, o modificado por último."""
    matches = [f for f in csv_files if f.name.startswith(prefixo)]
    return max(matches, key=lambda f: (f.stat().st_mtime, f.name)) if matches else None


def ler_arquivo(csv_file: Path, target_name: str) -> pd.DataFrame:
    """Lê o CSV, limpa o cabeçalho, avisa acentuação suspeita e converte o id_empreendimento."""
    df = read_csv_bruto(csv_file)
    df.columns = [c.strip().strip('"') for c in df.columns]
    avisar_acentuacao_suspeita(df, target_name)
    # Inteiro que aceita vazio: as views comparam o ID direto, sem conversões
    if "id_empreendimento" in df.columns:
        df["id_empreendimento"] = pd.to_numeric(df["id_empreendimento"]).astype("Int64")
    return df


def montar_por_cenario(csv_files: list, target_name: str, fontes: list) -> pd.DataFrame | None:
    """Junta um arquivo por schema numa tabela só, com o id_cenario de cada schema.
    Linhas repetidas por inteiro (mesma linha exportada duas vezes) são removidas."""
    partes = []
    for prefixo, cenario in fontes:
        csv_file = escolher_arquivo(csv_files, prefixo)
        if csv_file is None:
            print(f"[NAO ENCONTRADO] {prefixo} (parte de '{target_name}')")
            continue
        df = ler_arquivo(csv_file, target_name)
        if cenario is not None:
            df["id_cenario"] = cenario
        partes.append(df)
        print(f"[LIDO] {csv_file.relative_to(RAW_DIR)} -> {target_name} ({len(df):,} linhas, cenarios {sorted(df['id_cenario'].unique().tolist())})")
    if not partes:
        return None
    df = pd.concat(partes, ignore_index=True)
    repetidas = int(df.duplicated().sum())
    if repetidas:
        print(f"[AVISO] {target_name}: {repetidas} linha(s) repetida(s) por inteiro removida(s).")
        df = df.drop_duplicates().reset_index(drop=True)
    return df


def montar_carteiras(processed_dfs: dict) -> pd.DataFrame | None:
    """Junta as 3 carteiras numa tabela só (coluna 'carteira'), converte as colunas-lista e
    deduz o id_grupo_modelagem do nome do grupo (a view não traz o id)."""
    partes = []
    for slug in ("recomendada", "otimizada", "analise"):
        df = processed_dfs.pop(f"carteira_{slug}", None)
        if df is None:
            print(f"[AVISO] Carteira '{slug}' nao encontrada em data/raw/.")
            continue
        partes.append(df.assign(carteira=slug))
    if not partes:
        return None

    df = pd.concat(partes, ignore_index=True)
    for col in COLUNAS_LISTA:
        if col in df.columns:
            df[col] = df[col].map(array_pg_para_lista)

    if "natureza_empreendimento" not in df.columns:
        print("[AVISO] a view nao trouxe natureza_empreendimento: a tabela de Alocacao da ficha depende dela.")
    else:
        sem_natureza = df.loc[df["natureza_empreendimento"].isna(), "id_empreendimento"].unique()
        if len(sem_natureza):
            print(f"[AVISO] {len(sem_natureza)} empreendimentos sem natureza: {list(sem_natureza)[:20]}")

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

    # data/raw/ e subpastas; ignora arquivos temporários e de lock (ex: .~lock.*)
    csv_files = [f for f in RAW_DIR.rglob("*.csv") if not f.name.startswith(".")]

    if not csv_files:
        print("[AVISO] Nenhum arquivo .csv encontrado em data/raw/.")
        return

    processed_dfs = {}
    processed_count = 0

    for target_name, prefixes in TARGET_FILES.items():
        csv_file = next((f for f in (escolher_arquivo(csv_files, p) for p in prefixes) if f), None)
        if not csv_file:
            print(f"[NAO ENCONTRADO] Arquivo para '{target_name}' (prefixos: {prefixes}) nao localizado.")
            continue
        try:
            processed_dfs[target_name] = ler_arquivo(csv_file, target_name)
            processed_count += 1
            print(f"[LIDO] {csv_file.relative_to(RAW_DIR)} -> {target_name} ({len(processed_dfs[target_name]):,} linhas)")
        except Exception as e:
            print(f"[ERRO] Falha ao processar {csv_file.name}: {e}")

    for target_name, fontes in TARGET_POR_CENARIO.items():
        try:
            df = montar_por_cenario(csv_files, target_name, fontes)
        except Exception as e:
            print(f"[ERRO] Falha ao montar {target_name}: {e}")
            continue
        if df is not None:
            processed_dfs[target_name] = df
            processed_count += 1

    # Valor da obra: soma dos custos de cada cenário e escolha do cenário por PRIORIDADE_CENARIO_OBRA
    if "obras_priorizacao" in processed_dfs and "custo_obra" in processed_dfs:
        df_obra = processed_dfs["obras_priorizacao"]
        df_custo = processed_dfs["custo_obra"]

        if {"valor_adotado", "id_obra", "id_cenario"} <= set(df_custo.columns):
            soma = df_custo.groupby(["id_obra", "id_cenario"])["valor_adotado"].sum().reset_index()
            soma["prioridade"] = soma["id_cenario"].map(PRIORIDADE_CENARIO_OBRA).fillna(0)
            adotado = (soma.sort_values(["prioridade", "valor_adotado"], ascending=False)
                           .drop_duplicates("id_obra").set_index("id_obra"))

            val_series = df_obra["id_obra"].map(adotado["valor_adotado"])
            if "valor_global" in df_obra.columns:
                val_series = val_series.combine_first(pd.to_numeric(df_obra["valor_global"], errors="coerce"))
            df_obra["valor_calculado"] = val_series.fillna(0.0)
            df_obra["cenario_valor"] = df_obra["id_obra"].map(adotado["id_cenario"]).astype("Int64")
            print(f"[OBRAS] valor por cenario adotado: {df_obra['cenario_valor'].value_counts().sort_index().to_dict()}")

            # Origem do valor: tipo_custo das linhas do cenário adotado (obra sem custo fica vazia)
            if "tipo_custo" in df_custo.columns:
                chave = df_custo["id_obra"].astype(str) + "|" + df_custo["id_cenario"].astype(str)
                escolhidas = set(adotado.index.astype(str) + "|" + adotado["id_cenario"].astype(str))
                linhas = df_custo[chave.isin(escolhidas)]
                origem = linhas["tipo_custo"].str.strip().str.lower().map(ORIGEM_VALOR_OBRA)
                por_obra = origem.groupby(linhas["id_obra"]).agg(lambda s: set(s.dropna()))
                mistas = por_obra[por_obra.map(len) > 1]
                if not mistas.empty:
                    print(f"[AVISO] {len(mistas)} obra(s) com custo estimado e declarado ao mesmo tempo: marcadas como Estimado")
                por_obra = por_obra.map(lambda s: "Estimado" if "Estimado" in s else next(iter(s), None))
                df_obra["origem_valor"] = df_obra["id_obra"].map(por_obra)
                desconhecidos = set(df_custo["tipo_custo"].dropna().str.strip().str.lower()) - set(ORIGEM_VALOR_OBRA)
                if desconhecidos:
                    print(f"[AVISO] tipo_custo sem regra de origem do valor: {sorted(desconhecidos)}")

    carteiras = montar_carteiras(processed_dfs)
    if carteiras is not None:
        processed_dfs["carteiras"] = carteiras

    # Salva todos os DataFrames em Parquet
    for target_name, df in processed_dfs.items():
        parquet_file = PROCESSED_DIR / f"{target_name}.parquet"
        df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)
        print(f"[SALVO] {parquet_file.name} ({len(df):,} linhas)")

    total = len(TARGET_FILES) + len(TARGET_POR_CENARIO)
    print(f"\n--- Concluido: {processed_count}/{total} tabelas processadas e salvas com sucesso! ---")


if __name__ == "__main__":
    convert_csv_to_parquet()
