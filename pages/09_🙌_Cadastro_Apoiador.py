import streamlit as st

from src.services.supporter_service import SupporterService
from src.services.telegram_service import TelegramService
from src.utils.validators import validate_whatsapp

st.set_page_config(
    page_title="Cadastro de Apoiador | Campanha 2026",
    page_icon="🙌",
    layout="centered",
)

st.title("🙌 Cadastro de apoiador")

slug = st.query_params.get("p", "")

if not slug:
    st.warning(
        "Link inválido. Peça ao seu parceiro o link correto de cadastro."
    )
    st.stop()

supporter_service = SupporterService()
partner_result = supporter_service.resolve_partner_by_slug(slug)

if not partner_result.success:
    st.error(partner_result.message)
    st.stop()

partner = partner_result.data
partner_label = partner.get("campaign_message") or "esta campanha"
st.caption(f"Você está se cadastrando com **{partner_label}**.")

with st.form("supporter_signup_form"):
    first_name = st.text_input("Nome", max_chars=100)
    last_name = st.text_input("Sobrenome", max_chars=100)
    whatsapp = st.text_input("WhatsApp", placeholder="(31) 99999-9999")
    consent_lgpd = st.checkbox(
        "Autorizo o uso dos meus dados para os fins desta campanha (LGPD)."
    )

    submitted = st.form_submit_button(
        "Confirmar cadastro", type="primary", use_container_width=True
    )

if submitted:
    errors: list[str] = []

    if not first_name.strip():
        errors.append("Informe seu nome.")

    if not last_name.strip():
        errors.append("Informe seu sobrenome.")

    whatsapp_ok, whatsapp_result = validate_whatsapp(whatsapp)
    if not whatsapp_ok:
        errors.append(whatsapp_result)

    if not consent_lgpd:
        errors.append("É necessário autorizar o uso dos dados (LGPD) para continuar.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        with st.spinner("Enviando seu cadastro..."):
            result = supporter_service.register_public(
                partner_id=partner["id"],
                slug=slug,
                first_name=first_name,
                last_name=last_name,
                whatsapp=whatsapp_result,
                consent_lgpd=consent_lgpd,
            )

        if not result.success:
            st.error(result.message)
        else:
            st.success(result.message)
            supporter = result.data or {}

            telegram = TelegramService()
            telegram.notify_new_supporter(
                partner_id=partner["id"],
                partner_label=partner_label,
                supporter_id=supporter.get("id", ""),
                first_name=first_name,
                last_name=last_name,
            )
            telegram.notify_goal_if_reached(
                partner_id=partner["id"],
                partner_label=partner_label,
            )

