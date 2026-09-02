import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.config.settings import settings
from src.services.partner_service import PartnerService

st.set_page_config(
    page_title="Parceiros | Campanha 2026",
    page_icon="🤝",
    layout="wide",
)

require_roles("super_admin", "admin")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
service = PartnerService(access_token=access_token)

st.title("🤝 Parceiros")
st.caption("Vincule perfis de parceiro a um link público de cadastro.")

signup_url = f"{settings.APP_BASE_URL}/criar-conta"
st.info(
    "📨 **Convidar novo parceiro:** compartilhe o link abaixo. A pessoa cria "
    "a conta e confirma o e-mail; depois vincule-a aqui embaixo."
)
st.code(signup_url, language=None)

unlinked_result = service.list_unlinked_partner_profiles()
partners_result = service.list_partners()

with st.expander("➕ Vincular novo parceiro", expanded=not partners_result.data):
    unlinked = unlinked_result.data or []

    if not unlinked_result.success:
        st.error(unlinked_result.message)
    elif not unlinked:
        st.info(
            "Não há perfis com papel 'parceiro' aguardando vínculo. "
            "O parceiro precisa criar conta e confirmar o e-mail primeiro."
        )
    else:
        options = {
            f"{p['first_name']} {p['last_name']} ({p['email']})": p
            for p in unlinked
        }

        with st.form("create_partner_form"):
            selected_label = st.selectbox("Perfil", options=list(options.keys()))
            campaign_message = st.text_area(
                "Mensagem de apresentação (opcional)",
                max_chars=500,
                help="Exibida na página pública de cadastro do apoiador.",
            )
            telegram_chat_id = st.text_input(
                "Chat ID do Telegram deste parceiro (opcional)",
                help="Se vazio, os alertas vão para o chat padrão do .env.",
            )
            custom_slug = st.text_input(
                "Link personalizado (opcional)",
                placeholder="ex: joao-silva",
                help="Se vazio, geramos automaticamente a partir do nome.",
            )
            submitted = st.form_submit_button(
                "Criar parceiro", type="primary", use_container_width=True
            )

        if submitted:
            selected_profile = options[selected_label]
            result = service.create_partner(
                profile_id=selected_profile["id"],
                created_by=profile["id"],
                campaign_message=campaign_message,
                telegram_chat_id=telegram_chat_id,
                slug_seed=(
                    f"{selected_profile['first_name']} {selected_profile['last_name']}"
                ),
                custom_slug=custom_slug.strip() or None,
            )
            if result.success:
                st.success(result.message)
                st.rerun()
            else:
                st.error(result.message)

st.divider()
st.subheader("Parceiros cadastrados")

partners = partners_result.data or []

if not partners_result.success:
    st.error(partners_result.message)
elif not partners:
    st.info("Nenhum parceiro cadastrado ainda.")
else:
    for partner in partners:
        owner = partner.get("profiles") or {}
        owner_name = f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip()
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"### {owner_name or 'Parceiro'}")
                st.caption(owner.get("email", ""))
                st.code(f"?p={partner['public_slug']}", language=None)

            with col2:
                status = (
                    "🟢 Aceitando cadastros"
                    if partner["is_accepting_supporters"]
                    else "🔴 Pausado"
                )
                st.markdown(status)

            with st.form(f"edit_partner_{partner['id']}"):
                new_message = st.text_area(
                    "Mensagem de apresentação",
                    value=partner.get("campaign_message") or "",
                    max_chars=500,
                    key=f"message_{partner['id']}",
                )
                new_chat_id = st.text_input(
                    "Chat ID do Telegram",
                    value=partner.get("telegram_chat_id") or "",
                    key=f"chat_{partner['id']}",
                )
                new_accepting = st.checkbox(
                    "Aceitando novos cadastros",
                    value=partner["is_accepting_supporters"],
                    key=f"accepting_{partner['id']}",
                )
                save = st.form_submit_button("Salvar")

            if save:
                update_result = service.update_partner(
                    partner_id=partner["id"],
                    actor_id=profile["id"],
                    campaign_message=new_message,
                    telegram_chat_id=new_chat_id,
                    is_accepting_supporters=new_accepting,
                )
                if update_result.success:
                    st.success(update_result.message)
                    st.rerun()
                else:
                    st.error(update_result.message)