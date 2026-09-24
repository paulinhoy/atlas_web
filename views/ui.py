"""Estilos (assets/css) e componentes visuais compartilhados entre as páginas."""

import html
from pathlib import Path
import streamlit as st
from views import estado_url

CSS_DIR = Path(__file__).resolve().parent.parent / "assets" / "css"


def read_css(name: str) -> str:
    return (CSS_DIR / f"{name}.css").read_text(encoding="utf-8")


def inject_css(*page_styles: str) -> None:
    """Injeta base.css seguido do CSS específico de cada página informada."""
    css = "\n".join(read_css(n) for n in ("base", *page_styles))
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


# Ícones de linha (estilo Lucide) em SVG: seguem a cor do texto via currentColor
_SVG = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{}</svg>'
ICONE_CASA = _SVG.format('<path d="M3 10.5 12 3l9 7.5"></path><path d="M5 9.5V21h14V9.5"></path><path d="M10 21v-6h4v6"></path>')
ICONE_BARRAS = _SVG.format('<path d="M3 3v18h18"></path><path d="M8 17v-5"></path><path d="M13 17V8"></path><path d="M18 17v-9"></path>')
ICONE_BALAO = _SVG.format('<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>')

# Itens da barra superior: (id da página, rótulo, ícone, função que monta o link)
NAV_ITENS = [
    ("home", "Página Inicial", ICONE_CASA, estado_url.link_home),
    ("bi", "Painel de Indicadores & BI", ICONE_BARRAS, estado_url.link_bi),
    ("chatbot", "Assistente Virtual", ICONE_BALAO, estado_url.link_chatbot),
]


def render_navbar(ativa: str, container=st) -> None:
    """Barra de navegação fixa no topo; `ativa` é o id da página aberta (ex.: "home").
    `container` permite desenhá-la num st.empty() preenchido depois (ver Home)."""
    itens = []
    for pagina, rotulo, icone, link in NAV_ITENS:
        classe = "atlas-navbar-item is-active" if pagina == ativa else "atlas-navbar-item"
        itens.append(f'<a href="{link()}" target="_self" class="{classe}">{icone}<span>{html.escape(rotulo)}</span></a>')
    separador = '<span class="atlas-navbar-sep"></span>'
    container.markdown(
        f'<nav class="atlas-navbar"><div class="atlas-navbar-inner">{separador.join(itens)}</div></nav>',
        unsafe_allow_html=True,
    )


def render_back_button() -> None:
    """Botão flutuante "Voltar para a Lista", devolvendo os filtros da Home que vieram na URL."""
    st.markdown(
        f"""
        <a href="{estado_url.link_home()}" target="_self" class="atlas-floating-back-btn">
            <span class="back-arrow">←</span>
            <span>Voltar para a Lista</span>
        </a>
        """,
        unsafe_allow_html=True,
    )
