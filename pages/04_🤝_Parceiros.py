import streamlit as st

from src.auth.guards import require_roles

st.set_page_config(
    page_title="Parceiros | Campanha 2026",
    page_icon="🤝",
)

require_roles("super_admin", "admin")

st.title("🤝 Parceiros")
st.info("A gestão de parceiros será implementada na Fase 3.")