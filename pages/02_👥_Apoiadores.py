import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.config.settings import settings
from src.services.partner_service import PartnerService
from src.services.supporter_service import SupporterService

st.set_page_config(
    page_title="Apoiadores | Campanha 2026",
    page_icon="👥",
    layout="wide",
)

require_roles("super_admin", "admin", "parceiro")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
role = profile.get("role")

partner_service = PartnerService(access_token=access_token)

st.title("👥 Apoiadores")

partner = None
partner_label = ""

if role == "parceiro":
    partner_result = partner_service.get_partner_for_profile(profile["id"])
    if not partner_result.success:
        st.error(partner_result.message)
        st.stop()
    partner = partner_result.data
    if not partner:
        st.warning(
            "Seu perfil ainda não está vinculado como parceiro. "
            "Fale com um administrador."
        )
        st.stop()
    partner_label = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

    public_url = f"{settings.APP_BASE_URL}/apoiar?p={partner['public_slug']}"
    st.info("🔗 **Seu link de cadastro:** compartilhe para receber novos apoiadores.")
    st.code(public_url, language=None)
else:
    partners_result = partner_service.list_partners()
    partners = partners_result.data or []
    if not partners_result.success:
        st.error(partners_result.message)
        st.stop()
    if not partners:
        st.info("Nenhum parceiro cadastrado ainda.")
        st.stop()

    def _label(p: dict) -> str:
        owner = p.get("profiles") or {}
        name = f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip()
        return name or p["public_slug"]

    options = {_label(p): p for p in partners}
    selected_label = st.selectbox("Parceiro", options=list(options.keys()))
    partner = options[selected_label]
    partner_label = selected_label

st.caption(f"Parceiro: **{partner_label or 'sem nome'}**")

supporter_service = SupporterService(access_token=access_token)
result = supporter_service.list_for_partner(partner_id=partner["id"])

supporters = result.data or []

if not result.success:
    st.error(result.message)
elif not supporters:
    st.info("Ainda não há apoiadores cadastrados para este parceiro.")
else:
    st.metric("Total de apoiadores", len(supporters))
    st.dataframe(
        supporters,
        use_container_width=True,
        hide_index=True,
        column_order=[
            "first_name",
            "last_name",
            "whatsapp",
            "is_valid",
            "created_at",
        ],
    )