import streamlit as st

from src.auth.session import initialize_session, set_pending_verification
from src.services.auth_service import AuthService
from src.utils.validators import (
    validate_email_address,
    validate_password,
    validate_whatsapp,
)


st.set_page_config(
    page_title="Criar Conta | Campanha 2026",
    page_icon="📝",
    layout="centered",
)

initialize_session()


@st.dialog("✅ Conta criada")
def signup_success_dialog(email: str) -> None:
    st.success("Seu cadastro foi registrado com sucesso.")
    st.write(
        "Enviamos um código de seis dígitos para o seu e-mail. "
        "Digite-o na próxima tela para concluir a verificação."
    )
    st.caption(f"E-mail: {email}")

    if st.button("Verificar e-mail agora", type="primary", use_container_width=True):
        st.switch_page("pages/07_✅_Verificar_Email.py")


st.title("📝 Criar conta")
st.caption("Crie sua conta para acessar a plataforma Campanha 2026.")

with st.form("signup_form", clear_on_submit=False):
    first_name = st.text_input("Nome", max_chars=100)
    last_name = st.text_input("Sobrenome", max_chars=100)
    email = st.text_input("E-mail", placeholder="nome@exemplo.com")
    whatsapp = st.text_input(
        "WhatsApp",
        placeholder="(31) 99999-9999",
    )
    password = st.text_input("Senha", type="password")
    password_confirmation = st.text_input(
        "Confirmar senha",
        type="password",
    )

    consent = st.checkbox(
        "Li e concordo com o uso dos meus dados para a finalidade da campanha."
    )

    submitted = st.form_submit_button(
        "Criar conta",
        type="primary",
        use_container_width=True,
    )

if submitted:
    errors: list[str] = []

    if not first_name.strip():
        errors.append("Informe seu nome.")

    if not last_name.strip():
        errors.append("Informe seu sobrenome.")

    email_ok, email_result = validate_email_address(email)

    if not email_ok:
        errors.append(f"E-mail inválido: {email_result}")

    whatsapp_ok, whatsapp_result = validate_whatsapp(whatsapp)

    if not whatsapp_ok:
        errors.append(whatsapp_result)

    password_ok, password_message = validate_password(password)

    if not password_ok:
        errors.append(password_message)

    if password != password_confirmation:
        errors.append("A confirmação de senha não corresponde à senha informada.")

    if not consent:
        errors.append("Você deve aceitar o uso dos dados para continuar.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        with st.spinner("Criando sua conta..."):
            service = AuthService()
            result = service.sign_up(
                first_name=first_name,
                last_name=last_name,
                email=email_result,
                whatsapp=whatsapp_result,
                password=password,
            )

        if result.success and result.data:
            set_pending_verification(result.data["email"])
            signup_success_dialog(result.data["email"])
        else:
            st.error(result.message)

st.divider()
st.caption("Já possui conta?")
st.page_link(
    "pages/05_🔐_Login.py",
    label="Ir para login",
    icon="🔐",
)