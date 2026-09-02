import re

import streamlit as st

from src.auth.session import initialize_session, set_authenticated_session
from src.services.auth_service import AuthService
from src.utils.validators import validate_email_address


st.set_page_config(
    page_title="Verificar E-mail | Campanha 2026",
    page_icon="✅",
    layout="centered",
)

initialize_session()

st.title("✅ Confirmar e-mail")
st.caption(
    "Informe o código enviado para o e-mail usado no cadastro."
)

default_email = st.session_state.get("pending_verification_email") or ""

with st.form("verify_otp_form"):
    email = st.text_input("E-mail", value=default_email)
    token = st.text_input(
        "Código de confirmação",
        max_chars=10,
        placeholder="Código recebido por e-mail",
    )

    col_confirm, col_resend = st.columns(2)

    with col_confirm:
        submitted = st.form_submit_button(
            "Confirmar código",
            type="primary",
            use_container_width=True,
        )

    with col_resend:
        resend_clicked = st.form_submit_button(
            "📩 Reenviar código",
            use_container_width=True,
        )

if submitted:
    email_ok, email_result = validate_email_address(email)
    sanitized_token = re.sub(r"\D", "", token)

    if not email_ok:
        st.error(f"E-mail inválido: {email_result}")
    elif not (6 <= len(sanitized_token) <= 10):
        st.error("Informe o código recebido por e-mail.")
    else:
        with st.spinner("Validando código..."):
            service = AuthService()
            result = service.verify_own_code(
                email=email_result,
                code=sanitized_token,
            )

        if result.success:
            tokens = st.session_state.get("pending_verification_tokens") or {}
            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            if access_token and refresh_token:
                profile_result = service.get_profile(
                    user_id=result.data["user_id"],
                    access_token=access_token,
                )

                if profile_result.success and profile_result.data:
                    set_authenticated_session(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        profile=profile_result.data,
                    )
                    st.success("E-mail confirmado. Redirecionando para o painel...")
                    st.switch_page("pages/00_🏠_Dashboard.py")
                else:
                    st.error(profile_result.message)
            else:
                # Sessão do cadastro não está mais disponível (ex.: aba
                # fechada antes de confirmar) — pede login normal.
                st.success("E-mail confirmado com sucesso! Faça login para continuar.")
                st.page_link(
                    "pages/05_🔐_Login.py",
                    label="Ir para login",
                    icon="🔐",
                )
        else:
            st.error(result.message)

if resend_clicked:
    email_ok, email_result = validate_email_address(email)

    if not email_ok:
        st.error(f"E-mail inválido: {email_result}")
    else:
        with st.spinner("Reenviando código..."):
            resend_result = AuthService().resend_own_code(email=email_result)

        if resend_result.success:
            st.success(resend_result.message)
        else:
            st.error(resend_result.message)

st.divider()
st.page_link(
    "pages/06_📝_Criar_Conta.py",
    label="Voltar ao cadastro",
    icon="📝",
)