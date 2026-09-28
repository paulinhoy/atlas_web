"""
Cálculos do Painel de Indicadores & BI (só pandas; a tela fica em views/bi.py).

Ideia central: comparar cada empreendimento com os seus pares (mesmo setor e mesmo recorte:
intervenção principal, região, momento, esfera) em várias métricas. Assim aparecem empreendimentos
que vão bem num recorte específico mesmo sem estar no topo do IC geral.
"""

from dataclasses import dataclass
import math
import pandas as pd

# Presente = já contratado ou iniciado; o restante do ciclo é Futuro
STATUS_PRESENTE = {"Contratado - execução não iniciada", "Contratado - em execução", "Paralisado"}

# Cortes da TIRM (fração) que separam os modelos de execução — mesmos da classificação de viabilidade
CORTE_PPP = 0.0
CORTE_CONCESSAO = 0.112
MODELOS = ["Execução pública", "PPP", "Concessão comum"]

# Regiões intermediárias de MG (as demais, de estados vizinhos, ficam fora do recorte por região)
REGIOES_MG = {
    "Barbacena", "Belo Horizonte", "Divinópolis", "Governador Valadares", "Ipatinga",
    "Juiz de Fora", "Montes Claros", "Patos de Minas", "Pouso Alegre", "Teófilo Otoni",
    "Uberaba", "Uberlândia", "Varginha",
}

# Destaque = estar entre os TOP_PCT% melhores do grupo (no mínimo o 1º), em grupos com pelo menos MIN_GRUPO
TOP_PCT = 10
MIN_GRUPO = 5


@dataclass(frozen=True)
class Metrica:
    rotulo: str
    coluna: str
    maior_melhor: bool = True
    zero_conta: bool = True  # False: nota zero = "não pontuou" e fica fora do ranking


METRICAS = {
    "ic": Metrica("Índice (IC)", "ic_3_pond"),
    "estrategica": Metrica("Dimensão Estratégica", "dimensao_estrategica", zero_conta=False),
    "socioeconomica": Metrica("Dimensão Socioeconômica", "dimensao_socioeconomica_pond", zero_conta=False),
    "gerencial": Metrica("Dimensão Gerencial", "dimensao_gerencial", zero_conta=False),
    "comercial": Metrica("Dimensão Comercial", "dimensao_comercial", zero_conta=False),
    "financeira": Metrica("Dimensão Financeira", "dimensao_financeira", zero_conta=False),
    "tirm": Metrica("TIRM", "tirm"),
}

# Recortes: id -> (rótulo, coluna). "regiao" é coluna-lista: o empreendimento entra em cada região que toca
RECORTES = {
    "setor": ("Setor inteiro", "setor"),
    "intervencao": ("Intervenção principal", "intervencao_principal"),
    "regiao": ("Região intermediária", "regioes_mg"),
    "momento": ("Presente × Futuro", "momento"),
    "esfera": ("Esfera", "esfera_acao"),
}


def modelo_execucao(tirm) -> str | None:
    """Modelo sugerido pela TIRM: < 0 Execução pública | 0 a 11,2% PPP | >= 11,2% Concessão comum."""
    if pd.isna(tirm):
        return None
    if tirm < CORTE_PPP:
        return "Execução pública"
    return "Concessão comum" if tirm >= CORTE_CONCESSAO else "PPP"


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as colunas derivadas usadas no painel (sem alterar o DataFrame recebido)."""
    df = df.copy()
    df["momento"] = df["descr_status_empreendimento"].map(lambda s: "Presente" if s in STATUS_PRESENTE else "Futuro")
    df["modelo"] = df["tirm"].map(modelo_execucao)
    df["regioes_mg"] = df["regioes_intermediarias"].map(
        lambda regs: [r for r in regs if r in REGIOES_MG] if regs is not None and not isinstance(regs, float) else []
    )
    # Posição geral no setor pelo IC (referência para achar destaques "escondidos")
    df["pos_ic_setor"] = df.groupby("setor")["ic_3_pond"].rank(ascending=False, method="first").astype(int)
    df["total_setor"] = df.groupby("setor")["ic_3_pond"].transform("size")
    return df


def _concorrentes(df: pd.DataFrame, metrica: Metrica) -> pd.DataFrame:
    """Linhas que entram no ranking da métrica (sem valor ou, se for o caso, com nota zero ficam fora)."""
    ok = df[metrica.coluna].notna()
    if not metrica.zero_conta:
        ok &= df[metrica.coluna] > 0
    return df[ok]


def ranking(df: pd.DataFrame, metrica_id: str, recorte_id: str) -> pd.DataFrame:
    """Posição de cada empreendimento dentro do seu grupo no recorte.
    Colunas novas: grupo, posicao, total, top_pct (posição em % do grupo; 1 = melhor 1%).
    Desempate pelo IC (maior primeiro)."""
    metrica = METRICAS[metrica_id]
    coluna_grupo = RECORTES[recorte_id][1]
    base = _concorrentes(df, metrica)
    base = base.assign(grupo=base[coluna_grupo]).explode("grupo").dropna(subset=["grupo"])
    base = base.sort_values(
        ["grupo", metrica.coluna, "ic_3_pond"], ascending=[True, not metrica.maior_melhor, False]
    )
    base["posicao"] = base.groupby("grupo").cumcount() + 1
    base["total"] = base.groupby("grupo")["grupo"].transform("size")
    base["top_pct"] = (base["posicao"] / base["total"] * 100).map(math.ceil)
    return base


def limite_destaque(total: int) -> int:
    """Quantas posições contam como destaque num grupo de `total` empreendimentos."""
    return max(1, math.floor(total * TOP_PCT / 100))


def destaques(df: pd.DataFrame, recortes=None, metricas=None) -> pd.DataFrame:
    """Todas as combinações (métrica × recorte × grupo) em que o empreendimento está no topo do grupo.
    Uma linha por destaque: id_empreendimento, metrica, recorte, grupo, posicao, total."""
    partes = []
    for recorte_id in recortes or RECORTES:
        for metrica_id in metricas or METRICAS:
            r = ranking(df, metrica_id, recorte_id)
            r = r[(r["total"] >= MIN_GRUPO) & (r["posicao"] <= r["total"].map(limite_destaque))]
            partes.append(r[["id_empreendimento", "grupo", "posicao", "total"]].assign(metrica=metrica_id, recorte=recorte_id))
    if not partes:
        return pd.DataFrame(columns=["id_empreendimento", "grupo", "posicao", "total", "metrica", "recorte"])
    return pd.concat(partes, ignore_index=True)


def perfil(df: pd.DataFrame, empreendimento_id: int) -> pd.DataFrame:
    """Posição do empreendimento em cada métrica × recorte (uma linha por grupo em que ele está)."""
    linhas = []
    for recorte_id in RECORTES:
        for metrica_id, metrica in METRICAS.items():
            r = ranking(df, metrica_id, recorte_id)
            r = r[r["id_empreendimento"] == empreendimento_id]
            for _, row in r.iterrows():
                linhas.append({
                    "metrica": metrica_id, "recorte": recorte_id, "grupo": row["grupo"],
                    "valor": row[metrica.coluna], "posicao": row["posicao"], "total": row["total"],
                    "top_pct": row["top_pct"],
                })
    return pd.DataFrame(linhas)


def fronteira_eficiencia(df: pd.DataFrame, coluna_grupo: str = "intervencao_principal") -> pd.Series:
    """True para quem está na fronteira CAPEX × IC do seu grupo: nenhum outro empreendimento do mesmo
    grupo entrega IC maior (ou igual) gastando menos. CAPEX zero fica fora."""
    na_fronteira = pd.Series(False, index=df.index)
    for _, g in df[df["capex"] > 0].groupby(coluna_grupo):
        melhor_ic = -math.inf
        for idx, ic in g.sort_values(["capex", "ic_3_pond"], ascending=[True, False])["ic_3_pond"].items():
            if ic > melhor_ic:
                na_fronteira[idx] = True
                melhor_ic = ic
    return na_fronteira
