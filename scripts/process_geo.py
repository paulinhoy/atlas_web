"""
Script de processamento e conversão de dados geoespaciais: JSON -> Parquet.
Converte o arquivo mvw_empreendimento_geo_*.json da pasta data/raw/ para
data/processed/empreendimento_geo.parquet com correção de codificação (Mojibake).
"""

from pathlib import Path
import json
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def fix_mojibake(text):
    """Corrige strings que sofreram double-encoding."""
    if not isinstance(text, str):
        return text
    if any(m in text for m in ["Ã", "Â", "â", "©"]):
        try:
            return text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica a correção de caracteres em todas as colunas de texto (exceto geometrias WKT)."""
    for col in df.select_dtypes(include="object").columns:
        if col not in ("geom_ponto", "geom_linha"):
            df[col] = df[col].apply(fix_mojibake)
    return df


def convert_geo_json_to_parquet():
    """Lê o JSON bruto de geometrias e salva em Parquet otimizado."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("--- Iniciando Conversao de JSON Geoespacial para Parquet ---")
    json_files = list(RAW_DIR.glob("mvw_empreendimento_geo*.json"))

    if not json_files:
        print("[ERRO] Nenhum arquivo mvw_empreendimento_geo*.json encontrado em data/raw/.")
        return

    json_file = sorted(json_files)[-1]
    parquet_file = PROCESSED_DIR / "empreendimento_geo.parquet"

    print(f"Origem: {json_file.name}")
    print(f"Destino: {parquet_file.name}\n")

    try:
        # Tenta carregar com UTF-8, fallback para Latin1
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with open(json_file, "r", encoding="latin-1") as f:
                data = json.load(f)

        # Extrai a lista de registros
        records = data.get("mvw_empreendimento_geo", data)
        if not isinstance(records, list):
            print(f"[ERRO] Formato inesperado no JSON. Esperado lista em 'mvw_empreendimento_geo'.")
            return

        print(f"Registros encontrados no JSON: {len(records):,}")
        df = pd.DataFrame(records)

        # Limpeza de nomes de colunas
        df.columns = [c.strip().strip('"') for c in df.columns]

        # Tipagens corretas
        if "id_empreendimento" in df.columns:
            df["id_empreendimento"] = pd.to_numeric(df["id_empreendimento"], errors="coerce")
        if "extensao_km" in df.columns:
            df["extensao_km"] = pd.to_numeric(df["extensao_km"], errors="coerce")
        if "id_setor" in df.columns:
            df["id_setor"] = pd.to_numeric(df["id_setor"], errors="coerce")

        # Correção de acentuação e textos
        df = clean_dataframe(df)

        # Salva em Parquet com compressão snappy
        df.to_parquet(parquet_file, engine="pyarrow", compression="snappy", index=False)

        pontos_count = df["geom_ponto"].notna().sum() if "geom_ponto" in df.columns else 0
        linhas_count = df["geom_linha"].notna().sum() if "geom_linha" in df.columns else 0

        print(f"[OK] {parquet_file.name} gerado com sucesso!")
        print(f"     Total de empreendimentos: {len(df):,}")
        print(f"     Com geometria de ponto:   {pontos_count:,}")
        print(f"     Com geometria de linha:   {linhas_count:,}")
        print(f"     Tamanho do Parquet:       {parquet_file.stat().st_size / (1024*1024):.2f} MB")

    except Exception as e:
        print(f"[ERRO] Falha ao converter {json_file.name}: {e}")


if __name__ == "__main__":
    convert_geo_json_to_parquet()
