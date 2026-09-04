"""Assistente IA público com identidade visual Coronel Henrique 22500."""

import html
import streamlit as st

from src.services.ai_service import AIService
from src.services.supporter_service import SupporterService
from src.utils.validators import validate_whatsapp

st.set_page_config(
    page_title="Fale com a Campanha | Coronel Henrique",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Tema azul oficial: verde e amarelo somente como destaques.
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

    h1, h2, h3, h4, h5, h6 {
        color: var(--ch-white) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
    }

    p, span, label, div, li, a, small {
        color: var(--ch-white) !important;
    }

    .ch-brand-card {
        position: relative;
        overflow: hidden;
        background: var(--ch-blue-surface);
        border-radius: 18px;
        padding: 24px 26px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 9px 28px rgba(0, 0, 0, .22);
    }

    /* Faixa diagonal verde/amarela — mesmo padrão do material oficial da campanha */
    .ch-brand-card::after {
        content: "";
        position: absolute;
        top: -70px;
        right: -60px;
        width: 200px;
        height: 240px;
        background: repeating-linear-gradient(
            45deg,
            var(--ch-green) 0px,
            var(--ch-green) 18px,
            var(--ch-yellow) 18px,
            var(--ch-yellow) 36px
        );
        opacity: .3;
        z-index: 0;
    }

    .ch-brand-card > * {
        position: relative;
        z-index: 1;
    }

    .st-key-public_chat_logo {
        text-align: center;
    }

    .st-key-public_chat_logo img {
        border-radius: 50%;
        border: 4px solid var(--ch-yellow);
        box-shadow: 0 10px 26px rgba(0, 0, 0, .3);
    }

    .ch-badge {
        display: inline-block;
        background: var(--ch-green);
        color: var(--ch-white) !important;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .ch-public-title {
        color: var(--ch-white) !important;
        font: 900 27px/1.2 'Montserrat', sans-serif;
        margin: 4px 0 8px;
    }

    .ch-public-subtitle {
        color: var(--ch-white) !important;
        font-size: 15px;
        line-height: 1.55;
    }

    /* CTA sem borda */
    div.stButton > button[kind="primary"] {
        background: var(--ch-green) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        box-shadow: 0 6px 18px rgba(0, 168, 89, .35) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background: var(--ch-green-hover) !important;
        transform: translateY(-2px);
    }

    /* Chat */
    [data-testid="stChatMessage"] {
        background: var(--ch-blue-surface) !important;
        border: none !important;
        border-radius: 15px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 6px 18px rgba(0, 0, 0, .18) !important;
    }

    [data-testid="stChatMessage"] * {
        color: var(--ch-white) !important;
    }

    [data-testid="stChatInput"] {
        background: var(--ch-blue-surface) !important;
        border: none !important;
        border-radius: 13px !important;
    }

    [data-testid="stChatInput"] textarea {
        background: var(--ch-blue-inner) !important;
        color: var(--ch-white) !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: rgba(255, 255, 255, .68) !important;
    }

    [data-testid="stChatInput"]:focus-within {
        box-shadow: 0 0 0 2px var(--ch-green) !important;
    }

    /* Dialog, formulário e inputs: fundo azul, sem branco nativo */
    [role="dialog"], [role="dialog"] > div, [data-testid="stDialog"] {
        background: var(--ch-blue-surface) !important;
        color: var(--ch-white) !important;
    }

    [data-testid="stForm"] {
        background: var(--ch-blue-inner) !important;
        border: none !important;
        border-radius: 14px !important;
    }

    [data-testid="stTextInput"] input {
        background: var(--ch-blue-bg) !important;
        color: var(--ch-white) !important;
        border: none !important;
    }

    [data-testid="stTextInput"] input::placeholder {
        color: rgba(255, 255, 255, .68) !important;
    }

    [data-testid="stCheckbox"] label {
        color: var(--ch-white) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

OFFICIAL_PARTNER_SLUG = "campanha-oficial"

SUPPORTER_INTENT_KEYWORDS = (
    "quero ser apoiador", "quero apoiar", "como me cadastro",
    "como eu me cadastro", "quero me cadastrar", "cadastrar apoiador",
    "virar apoiador", "apoiar a campanha", "apoiar o coronel",
    "quero ajudar", "como ajudar",
)


def _wants_to_become_supporter(text: str) -> bool:
    normalized = text.strip().lower()
    return any(keyword in normalized for keyword in SUPPORTER_INTENT_KEYWORDS)


@st.dialog("🙌 Quero ser apoiador")
def supporter_signup_dialog() -> None:
    st.markdown(
        "<div class='ch-public-subtitle'>Preencha seus dados para apoiar a campanha do Coronel Henrique.</div>",
        unsafe_allow_html=True,
    )

    with st.form("public_supporter_signup_form"):
        first_name = st.text_input("Nome", max_chars=100)
        last_name = st.text_input("Sobrenome", max_chars=100)
        whatsapp = st.text_input("WhatsApp", placeholder="(31) 99999-9999")
        consent_lgpd = st.checkbox(
            "Autorizo o uso dos meus dados para os fins desta campanha (LGPD)."
        )
        submitted = st.form_submit_button(
            "Confirmar cadastro", type="primary", use_container_width=True
        )

    if not submitted:
        return

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
        return

    supporter_service = SupporterService()
    partner_result = supporter_service.resolve_partner_by_slug(OFFICIAL_PARTNER_SLUG)

    if not partner_result.success:
        st.error(partner_result.message)
        return

    with st.spinner("Enviando seu cadastro..."):
        result = supporter_service.register_public(
            partner_id=partner_result.data["id"],
            slug=OFFICIAL_PARTNER_SLUG,
            first_name=first_name,
            last_name=last_name,
            whatsapp=whatsapp_result,
            consent_lgpd=consent_lgpd,
        )

    if not result.success:
        st.error(result.message)
        return

    st.session_state["public_chat_history"].append(
        {
            "role": "assistant",
            "content": f"Prontinho, {first_name}! Seu cadastro como apoiador foi registrado com sucesso. 🎉",
        }
    )
    st.success(result.message)
    st.rerun()


ASSISTANT_AVATAR = "assets/images/logo_coronel_henrique.png"

with st.container(key="public_chat_logo"):
    _, logo_col, _ = st.columns([1, 1, 1])
    with logo_col:
        st.image(ASSISTANT_AVATAR, width=110)

    st.markdown(
        """
        <div class="ch-brand-card">
            <div class="ch-badge">CORONEL HENRIQUE • 22500</div>
            <div class="ch-public-title">💬 Fale com a Campanha</div>
            <div class="ch-public-subtitle">
                Tire suas dúvidas sobre os projetos para Minas Gerais e converse com o assistente oficial.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.container(key="public_supporter_cta"):
    if st.button("🙌 Quero ser apoiador", type="primary", use_container_width=True):
        supporter_signup_dialog()

st.write("")
ai_service = AIService()

if "public_chat_history" not in st.session_state:
    st.session_state["public_chat_history"] = [
        {
            "role": "assistant",
            "content": (
                "Olá! Eu sou o assistente da campanha do Coronel Henrique. "
                "Pergunte sobre os projetos para Minas Gerais ou diga que deseja ser apoiador. 😊"
            ),
        }
    ]

for message in st.session_state["public_chat_history"]:
    avatar = ASSISTANT_AVATAR if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

question = st.chat_input("Digite sua pergunta...")

if question:
    st.session_state["public_chat_history"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("Pensando..."):
            result = ai_service.ask_public(question=question)

        if result.success:
            answer = result.data.get("answer", "")
            st.markdown(answer)
            st.session_state["public_chat_history"].append(
                {"role": "assistant", "content": answer}
            )
        else:
            st.error(result.message)

    if _wants_to_become_supporter(question):
        supporter_signup_dialog()