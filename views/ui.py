"""Carregamento centralizado dos estilos da aplicação (assets/css)."""

from pathlib import Path
import streamlit as st

CSS_DIR = Path(__file__).resolve().parent.parent / "assets" / "css"


def read_css(name: str) -> str:
    return (CSS_DIR / f"{name}.css").read_text(encoding="utf-8")


def inject_css(*page_styles: str) -> None:
    """Injeta base.css seguido do CSS específico de cada página informada."""
    css = "\n".join(read_css(n) for n in ("base", *page_styles))
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)
