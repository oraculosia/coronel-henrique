import streamlit as st

from src.auth.guards import require_roles

st.set_page_config(
    page_title="Apoiadores | Campanha 2026",
    page_icon="👥",
)

require_roles("super_admin", "admin", "parceiro")

st.title("👥 Apoiadores")
st.info("O módulo de apoiadores será implementado na Fase 3.")