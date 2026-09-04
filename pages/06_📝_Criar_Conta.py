import streamlit as st

from src.auth.session import initialize_session, set_pending_verification
from src.config.settings import settings
from src.services.auth_service import AuthService
from src.utils.uploads import validate_and_save_image
from src.utils.validators import (
    normalize_email,
    validate_email_address,
    validate_password,
    validate_whatsapp,
)


st.set_page_config(
    page_title="Criar Conta | Coronel Henrique 22500",
    page_icon="📝",
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

    /* Card de identidade do cadastro */
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

    /* Upload de foto: dropzone azul-escura, sem bordas brancas nativas */
    [data-testid="stFileUploaderDropzone"] {
        background-color: var(--ch-blue-inner) !important;
        border: 1px dashed rgba(255, 255, 255, .35) !important;
        border-radius: 12px !important;
    }

    [data-testid="stFileUploaderDropzone"] button {
        background: var(--ch-blue-surface) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 8px !important;
    }

    /* Checkbox de consentimento LGPD */
    [data-testid="stCheckbox"] label {
        color: var(--ch-white) !important;
        font-size: 14px !important;
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

    /* Link para login */
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


@st.dialog("✅ Conta criada")
def signup_success_dialog(email: str) -> None:
    st.success("Seu cadastro foi registrado com sucesso.")
    st.write(
        "Enviamos um código de confirmação para o seu e-mail. "
        "Digite-o na próxima tela para concluir a verificação."
    )
    st.caption(f"E-mail: {email}")

    if st.button("Verificar e-mail agora", type="primary", use_container_width=True):
        st.switch_page("pages/07_✅_Verificar_Email.py")


st.markdown(
    """
    <div class="ch-login-header">
        <div class="ch-login-badge">CORONEL HENRIQUE • 22500</div>
        <div class="ch-login-title">📝 Criar conta</div>
        <p class="ch-login-subtitle">
            Cadastre-se para acompanhar metas, apoiadores e ações da campanha.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("signup_form", clear_on_submit=False):
    col1, col2 = st.columns(2)

    with col1:
        first_name = st.text_input("Nome", max_chars=100)
        email = st.text_input("E-mail", placeholder="nome@exemplo.com")
        password = st.text_input("Senha", type="password")

    with col2:
        last_name = st.text_input("Sobrenome", max_chars=100)
        whatsapp = st.text_input(
            "WhatsApp",
            placeholder="(31) 99999-9999",
        )
        password_confirmation = st.text_input(
            "Confirmar senha",
            type="password",
        )

    job_title = st.text_input(
        "Cargo",
        max_chars=120,
        placeholder="ex: Desenvolvedor de IA",
        help="Cargo profissional. É o que aparece para outros usuários.",
    )

    profile_photo = st.file_uploader(
        "Foto de perfil (opcional)",
        type=["png", "jpg", "jpeg", "webp"],
        help="Aparecerá futuramente no Assistente IA e em listagens.",
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

    avatar_path = ""
    if profile_photo is not None:
        photo_ok, photo_result = validate_and_save_image(
            profile_photo,
            settings.PROFILE_IMAGE_DIR,
            filename_base=normalize_email(email),
        )
        if not photo_ok:
            errors.append(photo_result)
        else:
            avatar_path = photo_result

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
                job_title=job_title,
                avatar_path=avatar_path,
            )

        if result.success and result.data:
            set_pending_verification(
                result.data["email"],
                access_token=result.data.get("access_token"),
                refresh_token=result.data.get("refresh_token"),
            )

            # Código próprio (não usa o e-mail do Supabase) — falha no envio
            # não deve travar o cadastro, o usuário pode reenviar depois.
            send_result = service.send_verification_code(
                user_id=result.data["user_id"],
                email=result.data["email"],
                first_name=first_name,
            )
            if not send_result.success:
                st.warning(send_result.message)

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