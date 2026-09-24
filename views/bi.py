"""
Painel de Indicadores & BI — página provisória (em construção).
"""

import streamlit as st
from views.ui import inject_css, render_navbar


def render():
    inject_css("bi")
    render_navbar("bi")
    st.markdown(
        """
        <div class="bi-placeholder">
            <div class="bi-placeholder-title">Painel de Indicadores &amp; BI</div>
            <div class="bi-placeholder-text">Em construção. Em breve, indicadores e painéis da carteira do PELTMG.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
