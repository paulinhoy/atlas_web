"""
Estado da Home e do Painel de BI guardado na URL.

Links HTML recarregam a página e o Streamlit abre uma sessão nova (session_state vazio);
a URL sobrevive ao recarregamento. Fluxo:
    - início da sessão: URL -> session_state (só valores válidos; inválidos são ignorados)
    - a cada execução: session_state -> URL (valores padrão ficam fora da URL)
    - links de navegação carregam o estado atual da URL

Parâmetros do BI levam o prefixo "bi_" para não colidir com os filtros da Home.
A ficha aberta a partir do BI recebe "de=bi" (origem) e "bi_aba" (aba de onde veio),
usados só pelo botão Voltar; não são estado e saem dos demais links.
"""

import html
from urllib.parse import urlencode
import streamlit as st

# Parâmetros de navegação: não fazem parte do estado e não são repassados pelos links
PARAMS_NAVEGACAO = ("id", "page", "de", "bi_aba")
# Origens aceitas em "de": lista fechada, nunca um endereço livre (evita redirecionamento para fora)
ORIGENS = ("bi",)
_FLAG_SEMEADO = "_estado_url_semeado"
SEPARADOR_LISTA = "|"  # filtros de seleção múltipla: ?setor=Ferroviário|Dutoviário


def inicio_da_sessao() -> bool:
    """True apenas na primeira execução da Home nesta sessão (quando a URL deve ser lida)."""
    return not st.session_state.get(_FLAG_SEMEADO, False)


def marcar_sessao_iniciada() -> None:
    st.session_state[_FLAG_SEMEADO] = True


def ler(param: str, opcoes=None, conversor=str):
    """Valor do parâmetro na URL convertido e validado; None se ausente ou inválido.
    Validar é obrigatório: um selectbox com valor fora das opções derruba a página."""
    if param not in st.query_params:
        return None
    try:
        valor = conversor(st.query_params[param])
    except (ValueError, TypeError):
        return None
    if opcoes is not None and valor not in opcoes:
        return None
    return valor


def semear_widget(chave: str, param: str, opcoes=None) -> None:
    """No início da sessão, inicializa o widget `chave` com o valor da URL (se válido)."""
    if inicio_da_sessao() and chave not in st.session_state:
        valor = ler(param, opcoes)
        if valor is not None:
            st.session_state[chave] = valor


def ler_lista(param: str, opcoes) -> list:
    """Seleção múltipla gravada como 'A|B'; mantém só os itens que existem em `opcoes`."""
    texto = ler(param) or ""
    return [v for v in texto.split(SEPARADOR_LISTA) if v in opcoes]


def ler_faixa(param: str, opcoes) -> tuple | None:
    """Faixa de slider gravada como 'min:max'; None se ausente ou fora de `opcoes`."""
    try:
        faixa = tuple(float(v) for v in (ler(param) or "").split(":"))
    except ValueError:
        return None
    if len(faixa) != 2 or not all(v in opcoes for v in faixa):
        return None
    return faixa


def texto_lista(valores: list) -> str:
    return SEPARADOR_LISTA.join(valores)


def texto_faixa(faixa: tuple, padrao: tuple) -> str:
    """'' (fora da URL) quando a faixa é a completa; senão 'min:max'."""
    if tuple(faixa) == tuple(padrao):
        return ""
    return ":".join(str(int(v)) if float(v).is_integer() else str(v) for v in faixa)


def gravar(valores: dict, padroes: dict) -> None:
    """Escreve o estado na URL sem recarregar a página; valores iguais ao padrão são removidos."""
    for param, valor in valores.items():
        texto = str(valor) if valor is not None else ""
        if texto == "" or valor == padroes.get(param):
            if param in st.query_params:
                del st.query_params[param]
        elif st.query_params.get(param) != texto:
            st.query_params[param] = texto


def _link(**extra) -> str:
    """href com o estado atual da URL; `extra` (valores None são ignorados) prevalece sobre ele."""
    extra = {k: v for k, v in extra.items() if v is not None}
    params = {k: v for k, v in st.query_params.items() if k not in PARAMS_NAVEGACAO and k not in extra}
    return html.escape("?" + urlencode({**extra, **params}))


def origem() -> str | None:
    """Página de onde a ficha foi aberta ("bi"); None quando veio da Home ou o valor é inválido."""
    return ler("de", ORIGENS)


def link_empreendimento(empreendimento_id: int, de: str | None = None, aba: str | None = None) -> str:
    """href da ficha do empreendimento levando o estado atual da URL.
    A partir do BI: de="bi" e a aba de onde veio, para o Voltar retornar ao mesmo lugar."""
    if de is None:
        return _link(id=empreendimento_id)
    return _link(id=empreendimento_id, de=de, bi_aba=aba, bi_emp=empreendimento_id)


def link_chatbot() -> str:
    return _link(page="chatbot")


def link_bi() -> str:
    """href do BI; vindo de uma ficha aberta pelo BI, reabre a aba de origem."""
    return _link(page="bi", bi_aba=st.query_params.get("bi_aba"))


def link_home() -> str:
    """href de volta para a Home com os filtros que vieram na URL."""
    return _link()
