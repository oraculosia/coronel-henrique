"""Assistente IA público — sem login, para moradores de Minas Gerais tirarem
dúvidas sobre os projetos do Coronel Henrique e se cadastrarem como
apoiadores. Reachable só por link direto (não aparece no menu)."""
import streamlit as st

from src.services.ai_service import AIService
from src.services.supporter_service import SupporterService
from src.utils.validators import validate_whatsapp

st.set_page_config(
    page_title="Fale com Agente de IA | Coronel Henrique",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Página institucional sem menu: esconde a sidebar/o botão de abrir por
# completo (app.py já não desenha conteúdo nela para esta página). Também
# aplica a identidade visual da campanha (cores-da-campanha.pdf) ao
# chat_input e ao botão de cadastro, que são específicos desta página.
st.markdown(
    """
    <style>
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none;
    }

    [data-testid="stChatInput"] {
        border: 2px solid var(--campaign-yellow, #f6c500) !important;
        border-radius: 12px !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: var(--campaign-yellow, #f6c500) !important;
        box-shadow: 0 0 0 3px rgba(246, 197, 0, 0.25);
    }

    .st-key-public_supporter_cta {
        display: flex;
        justify-content: center;
        margin: 0 0 1rem 0;
    }

    .st-key-public_supporter_cta .stButton > button {
        min-height: 38px;
        padding: 0.3rem 1.1rem;
        font-size: 0.85rem;
        font-weight: 800;
        border: 2px solid var(--campaign-yellow, #f6c500) !important;
        border-radius: 999px !important;
        background: var(--campaign-navy, #001f3f) !important;
        color: #ffffff !important;
    }

    .st-key-public_supporter_cta .stButton > button:hover {
        background: var(--campaign-deep-blue, #003b73) !important;
        border-color: var(--campaign-yellow, #f6c500) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Conta institucional usada para atribuir apoiadores cadastrados por aqui,
# já que não vêm de um link de referência de um parceiro específico.
OFFICIAL_PARTNER_SLUG = "campanha-oficial"

SUPPORTER_INTENT_KEYWORDS = (
    "quero ser apoiador",
    "quero apoiar",
    "como me cadastro",
    "como eu me cadastro",
    "quero me cadastrar",
    "cadastrar apoiador",
    "virar apoiador",
    "apoiar a campanha",
    "apoiar o coronel",
    "quero ajudar",
    "como ajudar",
)


def _wants_to_become_supporter(text: str) -> bool:
    normalized = text.strip().lower()
    return any(keyword in normalized for keyword in SUPPORTER_INTENT_KEYWORDS)


@st.dialog("🙌 Quero ser apoiador")
def supporter_signup_dialog() -> None:
    st.write("Preencha seus dados para apoiar a campanha do Coronel Henrique.")

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
            "content": (
                f"Prontinho, {first_name}! Seu cadastro como apoiador da campanha "
                "foi registrado com sucesso. 🎉"
            ),
        }
    )
    st.success(result.message)
    st.rerun()


with st.container(key="public_chat_logo"):
    st.image("assets/images/logo_coronel_henrique.png", width=170)

st.title("💬Pergunte sobre os projetos do Coronel Henrique")
st.caption(
    "Tire suas dúvidas sobre os projetos do Coronel Henrique para Minas Gerais "
    "e, se quiser, cadastre-se como apoiador da campanha."
)

with st.container(key="public_supporter_cta"):
    if st.button("🙌 Quero ser apoiador"):
        supporter_signup_dialog()

st.divider()

ai_service = AIService()

if "public_chat_history" not in st.session_state:
    st.session_state["public_chat_history"] = [
        {
            "role": "assistant",
            "content": (
                "Olá! Eu sou o assistente da campanha do Coronel Henrique. "
                "Pode perguntar sobre os projetos para Minas Gerais ou me dizer "
                "que quer ser apoiador. 😊"
            ),
        }
    ]

for message in st.session_state["public_chat_history"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

question = st.chat_input("Digite sua pergunta...")

if question:
    st.session_state["public_chat_history"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            result = ai_service.ask_public(question=question)

        if result.success:
            answer = result.data["answer"]
            st.write(answer)
            st.session_state["public_chat_history"].append(
                {"role": "assistant", "content": answer}
            )
        else:
            st.error(result.message)

    if _wants_to_become_supporter(question):
        supporter_signup_dialog()
