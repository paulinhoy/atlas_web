"""
Serviço Centralizado de Formatação e Tratamento de Dados (Atlas Web)
Padronização de formatação brasileira (moeda, números, datas).
"""

from typing import Any, Union
import pandas as pd


def fmt_int_br(valor: Any) -> str:
    """
    Formata números inteiros com separador de milhar brasileiro: 1.682.
    Retorna '-' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "-"
    try:
        val = int(float(valor))
    except (ValueError, TypeError):
        return "-"
    return f"{val:,}".replace(",", ".")


def fmt_decimal_br(valor: Any, casas: int = 4) -> str:
    """
    Formata número decimal no padrão brasileiro com vírgula: 0,4031.
    Retorna '-' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "-"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "-"
    return f"{val:.{casas}f}".replace(".", ",")


def fmt_decimal_br_2(valor: Any) -> str:
    """
    Formata número decimal com 2 casas decimais e separador de milhar: 1.234,56.
    Retorna '-' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "-"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "-"
    inteiro = int(abs(val))
    frac = round((abs(val) - inteiro) * 100)
    parte_int = f"{inteiro:,}".replace(",", ".")
    sinal = "-" if val < 0 else ""
    return f"{sinal}{parte_int},{frac:02d}"


def fmt_brl(valor: Any) -> str:
    """
    Formata valor monetário no padrão brasileiro: R$ 1.234.567,89.
    Retorna '-' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "-"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "-"
    negativo = val < 0
    val_abs = abs(val)
    inteiro = int(val_abs)
    centavos = round((val_abs - inteiro) * 100)
    parte_int = f"{inteiro:,}".replace(",", ".")
    resultado = f"R$ {parte_int},{centavos:02d}"
    return f"-{resultado}" if negativo else resultado


def fmt_pct_br(valor: Any, casas: int = 1) -> str:
    """
    Formata percentual no padrão brasileiro: 19,9%.
    Retorna '-' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "-"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "-"
    return f"{val:.{casas}f}".replace(".", ",") + "%"


def fmt_mes_ano_br(mes_base: Any) -> str:
    """
    Formata data/mês de atualização para exibição textual brasileira: jan/24.
    Retorna '-' caso o valor seja nulo ou inválido.
    """
    if pd.isna(mes_base) or mes_base is None or str(mes_base).strip() in ("", "-", "N/D"):
        return "-"
    try:
        dt = pd.to_datetime(mes_base)
        meses_pt = {
            1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
            7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
        }
        return f"{meses_pt.get(dt.month, '')}/{str(dt.year)[2:]}"
    except Exception:
        return str(mes_base)


def fmt_bilhoes_br(valor: Any, com_cifrao: bool = True) -> str:
    """
    Formata valor monetário em bilhões no padrão brasileiro arredondado.
    Exemplo: 481441025165.75 -> 'R$ 481 Bi' (ou '481Bi' se com_cifrao=False).
    Retorna '-' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "-"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "-"

    bi = val / 1e9
    if abs(bi) >= 1:
        num_str = f"{round(bi)}"
    elif abs(bi) > 0:
        num_str = f"{bi:.1f}".replace(".", ",")
    else:
        num_str = "0"

    prefixo = "R$ " if com_cifrao else ""
    return f"{prefixo}{num_str} Bi"
