import streamlit as st

from src.services.supporter_service import SupporterService
from src.services.telegram_service import TelegramService
from src.utils.validators import validate_whatsapp

st.set_page_config(
    page_title="Cadastro de Apoiador | Campanha 2026",
    page_icon="🙌",
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
    </style>
    """,
    unsafe_allow_html=True,
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

