import streamlit as st

from src.auth.guards import require_authentication
from src.auth.session import get_profile, set_authenticated_session
from src.config.settings import settings
from src.services.auth_service import AuthService
from src.utils.formatting import resolve_avatar_path, role_label
from src.utils.uploads import validate_and_save_image
from src.utils.validators import validate_password, validate_whatsapp


st.set_page_config(
    page_title="Minha Conta | Campanha 2026",
    page_icon="👤",
    layout="centered",
)

# Identidade visual oficial: azul institucional como base, branco para leitura e verde como ação.
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

    [data-testid="stFileUploader"] {
        background-color: var(--ch-blue-surface) !important;
        border: 1px dashed rgba(255, 255, 255, .35) !important;
        border-radius: 12px !important;
    }

    .sidebar-avatar-fallback {
        background-color: var(--ch-blue-inner) !important;
        color: var(--ch-white) !important;
        border-radius: 50%;
        width: 110px;
        height: 110px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 42px;
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
    </style>
    """,
    unsafe_allow_html=True,
)

require_authentication()

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
refresh_token = st.session_state.get("refresh_token")

st.title("👤 Minha conta")
st.caption(
    "Atualize seus dados pessoais. O papel de autorização não pode ser "
    "alterado nesta tela."
)

current_avatar = resolve_avatar_path(profile)

st.markdown("#### Foto de perfil")
avatar_col, uploader_col = st.columns([1, 3], vertical_alignment="center")

new_photo = uploader_col.file_uploader(
    "Nova foto (opcional)",
    type=["png", "jpg", "jpeg", "webp"],
    key="account_avatar_uploader",
)

with avatar_col:
    with st.container(key="account_avatar_preview"):
        if new_photo is not None:
            st.image(new_photo, width=110)
        elif current_avatar:
            st.image(current_avatar, width=110)
        else:
            st.markdown(
                '<div class="sidebar-avatar-fallback">🧑</div>',
                unsafe_allow_html=True,
            )

if new_photo is not None:
    uploader_col.caption("Pré-visualização da nova foto — salve para confirmar.")

st.divider()

with st.form("account_form"):
    first_name = st.text_input(
        "Nome",
        value=profile.get("first_name") or "",
        max_chars=100,
    )
    last_name = st.text_input(
        "Sobrenome",
        value=profile.get("last_name") or "",
        max_chars=100,
    )
    st.text_input(
        "E-mail",
        value=profile.get("email") or "",
        disabled=True,
        help="O e-mail é a identidade do Auth e não é editável nesta fase.",
    )
    whatsapp = st.text_input(
        "WhatsApp",
        value=profile.get("whatsapp") or "",
        placeholder="(31) 99999-9999",
    )
    job_title = st.text_input(
        "Cargo",
        value=profile.get("job_title") or "",
        max_chars=120,
        help="Cargo profissional. Não substitui o papel de autorização.",
    )
    st.text_input(
        "Tipo de acesso",
        value=role_label(profile.get("role")),
        disabled=True,
        help="Definido pela administração. O cargo acima é o que aparece para outros usuários.",
    )

    st.divider()
    st.caption("Opcional — altere a senha somente se quiser trocá-la agora.")
    new_password = st.text_input("Nova senha", type="password")
    new_password_confirmation = st.text_input(
        "Confirmar nova senha",
        type="password",
    )

    submitted = st.form_submit_button(
        "Salvar alterações",
        type="primary",
        use_container_width=True,
    )

if submitted:
    errors: list[str] = []

    if not first_name.strip():
        errors.append("Informe seu nome.")

    if not last_name.strip():
        errors.append("Informe seu sobrenome.")

    whatsapp_result = ""
    if whatsapp.strip():
        whatsapp_ok, whatsapp_result = validate_whatsapp(whatsapp)
        if not whatsapp_ok:
            errors.append(whatsapp_result)

    if new_password or new_password_confirmation:
        password_ok, password_message = validate_password(new_password)
        if not password_ok:
            errors.append(password_message)
        elif new_password != new_password_confirmation:
            errors.append("A confirmação da nova senha não corresponde.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        avatar_path = current_avatar or ""
        if new_photo is not None:
            photo_ok, photo_result = validate_and_save_image(
                new_photo,
                settings.PROFILE_IMAGE_DIR,
                filename_base=profile.get("email") or "",
            )
            if not photo_ok:
                st.error(photo_result)
                st.stop()
            avatar_path = photo_result

        service = AuthService()
        result = service.update_own_profile(
            access_token=access_token,
            user_id=profile["id"],
            first_name=first_name,
            last_name=last_name,
            whatsapp=whatsapp_result,
            job_title=job_title.strip(),
            avatar_path=avatar_path or None,
        )

        if not result.success:
            st.error(result.message)
        else:
            if new_password:
                password_result = service.update_own_password(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    password=new_password,
                )
                if not password_result.success:
                    st.warning(password_result.message)

            updated = result.data or {}
            set_authenticated_session(
                access_token=access_token,
                refresh_token=refresh_token,
                profile=updated,
            )
            st.success("Dados da conta atualizados.")
            st.rerun()
