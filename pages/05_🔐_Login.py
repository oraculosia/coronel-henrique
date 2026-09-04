import streamlit as st

from src.auth.session import (
    initialize_session,
    is_authenticated,
    set_authenticated_session,
)
from src.services.auth_service import AuthService
from src.utils.validators import validate_email_address

st.set_page_config(
    page_title="Login | Coronel Henrique 22500",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Identidade visual oficial: azul como base, branco para leitura e verde como ação.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-blue-bg: #163259;
        --ch-blue-surface: #1e4273;
        --ch-blue-inner: #122847;
        --ch-green: #00a859;
        --ch-green-hover: #008f4c;
        --ch-yellow: #ffc72c;
        --ch-white: #ffffff;
    }

    /* Fundo azul institucional em toda a página e componentes nativos */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    [data-testid="stToolbar"], .main, section[data-testid="stSidebar"] {
        background-color: var(--ch-blue-bg) !important;
        color: var(--ch-white) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Sidebar com tom flutuante: borda, cantos arredondados e sombra */
    section[data-testid="stSidebar"] {
        border: 3px solid var(--ch-yellow) !important;
        border-radius: 18px !important;
        margin: 14px 0 14px 14px !important;
        box-shadow: 0 14px 34px rgba(0, 0, 0, .35) !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] > div {
        border-radius: 18px !important;
    }

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2 {
        color: var(--ch-white) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
    }

    p, span, label, div, small {
        color: var(--ch-white) !important;
    }

    /* Card de identidade do login */
    .ch-login-header {
        background: var(--ch-blue-surface);
        border-radius: 18px;
        padding: 26px 24px 22px;
        text-align: center;
        margin: 24px 0 18px;
        box-shadow: 0 10px 28px rgba(0, 0, 0, .24);
    }

    .ch-login-badge {
        display: inline-block;
        background: var(--ch-green);
        color: var(--ch-white) !important;
        padding: 6px 15px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    .ch-login-title {
        color: var(--ch-white) !important;
        font: 900 29px/1.1 'Montserrat', sans-serif;
        margin: 0 0 8px;
    }

    .ch-login-subtitle {
        color: var(--ch-white) !important;
        font-size: 15px;
        line-height: 1.5;
        margin: 0;
    }

    /* Formulário sem fundo claro e sem bordas */
    [data-testid="stForm"] {
        background: var(--ch-blue-surface) !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 26px 24px !important;
        box-shadow: 0 9px 24px rgba(0, 0, 0, .20) !important;
    }

    [data-testid="stForm"] label {
        color: var(--ch-white) !important;
        font-size: 14px !important;
        font-weight: 700 !important;
    }

    [data-testid="stTextInput"] input {
        background-color: var(--ch-blue-inner) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 15px !important;
    }

    [data-testid="stTextInput"] input::placeholder {
        color: rgba(255, 255, 255, .65) !important;
    }

    [data-testid="stTextInput"] input:focus {
        box-shadow: 0 0 0 2px var(--ch-green) !important;
    }

    /* Botão primário verde, sem bordas */
    div.stFormSubmitButton > button,
    div.stButton > button[kind="primary"] {
        background: var(--ch-green) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        padding: 12px 22px !important;
        box-shadow: 0 6px 18px rgba(0, 168, 89, .38) !important;
        transition: all .2s ease !important;
    }

    div.stFormSubmitButton > button:hover,
    div.stButton > button[kind="primary"]:hover {
        background: var(--ch-green-hover) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(0, 168, 89, .52) !important;
    }

    /* Link de verificação */
    [data-testid="stPageLink"] a {
        background: var(--ch-green) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

initialize_session()

if is_authenticated():
    st.switch_page("pages/00_🏠_Dashboard.py")

st.markdown(
    """
    <div class="ch-login-header">
        <div class="ch-login-badge">ACESSO RESTRITO • CORONEL HENRIQUE 22500</div>
        <div class="ch-login-title">🔐 Acesse seu painel</div>
        <p class="ch-login-subtitle">
            Entre com suas credenciais para acompanhar metas, apoiadores e ações da campanha.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("login_form"):
    email = st.text_input("E-mail", placeholder="nome@exemplo.com")
    password = st.text_input("Senha", type="password", placeholder="Digite sua senha")

    submitted = st.form_submit_button(
        "Entrar no Painel",
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
        with st.spinner("Autenticando acesso..."):
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
                        "Use a página de verificação para liberar seu acesso."
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
