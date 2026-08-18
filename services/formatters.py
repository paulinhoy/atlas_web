"""
Serviço Centralizado de Formatação e Tratamento de Dados (Atlas Web)
Padronização de formatação brasileira (moeda, números, datas) e limpeza de strings.
"""

from typing import Any, Union
import pandas as pd


def fix_mojibake(text: Any) -> Any:
    """
    Corrige strings que sofreram double-encoding (ex: UTF-8 lido como Latin1 gerando 'Ã§Ã£o').
    Exemplo: 'ConservaÃ§Ã£o' -> 'Conservação'.
    """
    if not isinstance(text, str):
        return text
    if any(m in text for m in ["Ã", "Â", "â", "©"]):
        try:
            return text.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return text


def fmt_int_br(valor: Any) -> str:
    """
    Formata números inteiros com separador de milhar brasileiro: 1.682.
    Retorna 'N/D' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        val = int(float(valor))
    except (ValueError, TypeError):
        return "N/D"
    return f"{val:,}".replace(",", ".")


def fmt_decimal_br(valor: Any, casas: int = 4) -> str:
    """
    Formata número decimal no padrão brasileiro com vírgula: 0,4031.
    Retorna 'N/D' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "N/D"
    return f"{val:.{casas}f}".replace(".", ",")


def fmt_decimal_br_2(valor: Any) -> str:
    """
    Formata número decimal com 2 casas decimais e separador de milhar: 1.234,56.
    Retorna 'N/D' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "N/D"
    inteiro = int(abs(val))
    frac = round((abs(val) - inteiro) * 100)
    parte_int = f"{inteiro:,}".replace(",", ".")
    sinal = "-" if val < 0 else ""
    return f"{sinal}{parte_int},{frac:02d}"


def fmt_brl(valor: Any) -> str:
    """
    Formata valor monetário no padrão brasileiro: R$ 1.234.567,89.
    Retorna 'N/D' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "N/D"
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
    Retorna 'N/D' caso o valor seja nulo ou inválido.
    """
    if pd.isna(valor) or valor is None:
        return "N/D"
    try:
        val = float(valor)
    except (ValueError, TypeError):
        return "N/D"
    return f"{val:.{casas}f}".replace(".", ",") + "%"


def fmt_mes_ano_br(mes_base: Any) -> str:
    """
    Formata data/mês de atualização para exibição textual brasileira: jan/24.
    Retorna 'N/D' caso o valor seja nulo ou inválido.
    """
    if pd.isna(mes_base) or mes_base is None or str(mes_base).strip() in ("", "N/D"):
        return "N/D"
    try:
        dt = pd.to_datetime(mes_base)
        meses_pt = {
            1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
            7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez",
        }
        return f"{meses_pt.get(dt.month, '')}/{str(dt.year)[2:]}"
    except Exception:
        return str(mes_base)
