import streamlit as st

from src.auth.session import (
    initialize_session,
    is_authenticated,
    set_authenticated_session,
)
from src.services.auth_service import AuthService
from src.utils.validators import validate_email_address


st.set_page_config(
    page_title="Login | Campanha 2026",
    page_icon="🔐",
    layout="centered",
)

initialize_session()

if is_authenticated():
    st.switch_page("pages/00_🏠_Dashboard.py")

st.title("🔐 Entrar")
st.caption("Acesse sua conta da Campanha 2026.")

with st.form("login_form"):
    email = st.text_input("E-mail", placeholder="nome@exemplo.com")
    password = st.text_input("Senha", type="password")

    submitted = st.form_submit_button(
        "Entrar",
        type="primary",
        use_container_width=True,
    )

if submitted:
    email_ok, email_result = validate_email_address(email)

    if not email_ok:
        st.error(f"E-mail inválido: {email_result}")
    elif not password:
        st.error("Informe sua senha.")
    else:
        with st.spinner("Autenticando..."):
            service = AuthService()
            result = service.sign_in(
                email=email_result,
                password=password,
            )

        if result.success and result.data:
            profile_result = service.get_profile(
                user_id=result.data["user_id"],
                access_token=result.data["access_token"],
            )

            if profile_result.success and profile_result.data:
                profile = profile_result.data

                if not profile["is_active"]:
                    st.error("Sua conta está desativada. Procure a administração.")
                elif profile["verification_status"] != "verified":
                    st.warning(
                        "Seu e-mail ainda não foi confirmado. "
                        "Use a página de verificação."
                    )
                    st.session_state["pending_verification_email"] = email_result
                    st.page_link(
                        "pages/07_✅_Verificar_Email.py",
                        label="Confirmar e-mail",
                        icon="✅",
                    )
                else:
                    set_authenticated_session(
                        access_token=result.data["access_token"],
                        refresh_token=result.data["refresh_token"],
                        profile=profile,
                    )
                    st.success("Login realizado. Redirecionando...")
                    st.switch_page("pages/00_🏠_Dashboard.py")
            else:
                st.error(profile_result.message)
        else:
            st.error(result.message)

st.divider()
st.caption("Ainda não possui conta?")
st.page_link(
    "pages/06_📝_Criar_Conta.py",
    label="Criar conta",
    icon="📝",
)