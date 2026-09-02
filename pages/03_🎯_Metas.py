from datetime import date

import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.services.goal_service import GoalService
from src.services.partner_service import PartnerService
from src.services.telegram_service import TelegramService

st.set_page_config(
    page_title="Metas Diárias | Campanha 2026",
    page_icon="🎯",
    layout="wide",
)

require_roles("super_admin", "admin", "parceiro")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
role = profile.get("role")

partner_service = PartnerService(access_token=access_token)

st.title("🎯 Metas Diárias")

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

goal_service = GoalService(access_token=access_token)
today = date.today()

goal_result = goal_service.get_goal(partner_id=partner["id"], goal_date=today)
if not goal_result.success:
    st.error(goal_result.message)
    st.stop()

goal = goal_result.data
st.caption(f"Parceiro: **{partner_label or 'sem nome'}**")

if goal is None:
    st.info("Ainda não existe meta criada para hoje.")

    with st.form("create_goal_form"):
        target_count = st.number_input(
            "Meta de cadastros para hoje", min_value=1, value=10, step=1
        )
        submitted = st.form_submit_button(
            "Criar meta de hoje", type="primary", use_container_width=True
        )

    if submitted:
        result = goal_service.create_goal(
            partner_id=partner["id"],
            goal_date=today,
            target_count=int(target_count),
            created_by=profile["id"],
        )
        if result.success:
            st.success(result.message)
            st.rerun()
        else:
            st.error(result.message)
else:
    achieved = goal["status"] == "achieved"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Meta de hoje", goal["target_count"])
    with col2:
        st.metric("Cadastros hoje", goal["achieved_count"])
    with col3:
        st.metric("Status", "✅ Atingida" if achieved else "⏳ Em andamento")

    if goal["target_count"]:
        st.progress(min(goal["achieved_count"] / goal["target_count"], 1.0))

    if achieved:
        telegram = TelegramService()
        notify_result = telegram.notify_goal_if_reached(
            partner_id=partner["id"], partner_label=partner_label
        )
        if notify_result.success and not (notify_result.data or {}).get("skipped"):
            st.toast("Notificação de meta enviada ao Telegram.")

    st.divider()

    with st.form("edit_goal_form"):
        new_target = st.number_input(
            "Meta de cadastros para hoje",
            min_value=1,
            value=int(goal["target_count"]),
            step=1,
        )
        submitted = st.form_submit_button(
            "Salvar meta", type="primary", use_container_width=True
        )

    if submitted:
        result = goal_service.update_target(
            goal_id=goal["id"], target_count=int(new_target), actor_id=profile["id"]
        )
        if result.success:
            st.success(result.message)
            st.rerun()
        else:
            st.error(result.message)

st.divider()
st.subheader("Histórico recente")

history_result = goal_service.list_recent(partner_id=partner["id"])
history = history_result.data or []

if not history_result.success:
    st.error(history_result.message)
elif not history:
    st.info("Ainda não há histórico de metas para este parceiro.")
else:
    for entry in history:
        status_icon = "✅" if entry.get("status") == "achieved" else "⏳"
        st.write(
            f"{status_icon} {entry['goal_date']} — "
            f"{entry['achieved_count']}/{entry['target_count']}"
        )