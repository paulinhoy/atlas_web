"""Estilos (assets/css) e componentes visuais compartilhados entre as páginas."""

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
