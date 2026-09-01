import streamlit as st

from src.auth.guards import require_authentication

st.set_page_config(
    page_title="Assistente IA | Campanha 2026",
    page_icon="🤖",
)

require_authentication()

st.title("🤖 Assistente IA")
st.info("O agente IA será implementado na Fase 5.")