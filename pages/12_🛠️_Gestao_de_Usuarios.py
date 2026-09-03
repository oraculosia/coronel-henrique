import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.services.auth_service import AuthService
from src.utils.formatting import role_label

st.set_page_config(
    page_title="Gestão de Usuários | Campanha 2026",
    page_icon="🛠️",
    layout="wide",
)

require_roles("super_admin")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
service = AuthService()

st.title("🛠️ Gestão de Usuários")
st.caption(
    "Funcionalidade técnica exclusiva do super_admin: acompanhe se cada "
    "usuário já fez login e ative ou desative contas do sistema."
)

profiles_result = service.list_all_profiles(access_token=access_token)
login_result = service.list_auth_login_status()

if not profiles_result.success:
    st.error(profiles_result.message)
    st.stop()

users = profiles_result.data or []
login_status = login_result.data or {}

if not login_result.success:
    st.warning(login_result.message)

if not users:
    st.info("Nenhum usuário cadastrado ainda.")
    st.stop()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total de usuários", len(users))
with col2:
    st.metric("Ativos", sum(1 for u in users if u["is_active"]))
with col3:
    st.metric("Desativados", sum(1 for u in users if not u["is_active"]))

st.divider()

for user in users:
    last_sign_in = login_status.get(user["id"])
    is_self = user["id"] == profile.get("id")

    with st.container(border=True):
        col_info, col_status, col_action = st.columns([3, 2, 1.4])

        with col_info:
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            st.markdown(f"**{full_name or 'Usuário'}**")
            st.caption(user.get("email", ""))
            st.caption(f"Papel: {role_label(user.get('role'))}")

        with col_status:
            st.caption(
                f"🟢 Já entrou (último login: {last_sign_in.split('T')[0]})"
                if last_sign_in
                else "⚪ Nunca fez login"
            )
            st.caption("🟢 Conta ativa" if user["is_active"] else "🔴 Conta desativada")

        with col_action:
            if is_self:
                st.caption("Sua própria conta")
            else:
                label = "Desativar" if user["is_active"] else "Ativar"
                if st.button(
                    label,
                    key=f"toggle_active_{user['id']}",
                    use_container_width=True,
                ):
                    result = service.set_profile_active_status(
                        access_token=access_token,
                        actor_id=profile["id"],
                        user_id=user["id"],
                        is_active=not user["is_active"],
                    )
                    if result.success:
                        st.success(result.message)
                        st.rerun()
                    else:
                        st.error(result.message)
