import html
import streamlit as st

from src.auth.guards import require_authentication
from src.auth.session import get_profile
from src.services.ai_service import AIService
from src.utils.formatting import resolve_avatar_path

st.set_page_config(
    page_title="Assistente IA | Coronel Henrique 22500",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Injeção de CSS Dark Theme Azul Oficial e Borda Dourada
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-bg-root: #0f274a;
        --ch-bg-surface: #163664;
        --ch-bg-card: #122847;
        --ch-green-primary: #00a859;
        --ch-green-glow: rgba(0, 168, 89, 0.35);
        --ch-yellow-gold: #ffc72c;
        --ch-text-pure-white: #ffffff;
        --ch-text-light: #f1f5f9;
        --ch-text-secondary: #cbd5e1;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .main, section[data-testid="stSidebar"] {
        background-color: var(--ch-bg-root) !important;
        color: var(--ch-text-pure-white) !important;
        font-family: 'Inter', sans-serif !important;
    }

    section[data-testid="stSidebar"] {
        border: 3px solid var(--ch-yellow-gold) !important;
        border-radius: 18px !important;
        margin: 14px 0 14px 14px !important;
        box-shadow: 0 14px 34px rgba(0, 0, 0, .35) !important;
        overflow: hidden !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        color: var(--ch-text-pure-white) !important;
    }

    .ch-ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: rgba(0, 168, 89, 0.25);
        border: 1px solid var(--ch-green-primary);
        color: #22c55e !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    /* Balões do Chat */
    [data-testid="stChatMessage"] {
        background-color: var(--ch-bg-surface) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]),
    [data-testid="stChatMessage"]:has(img[alt="user avatar"]) {
        background-color: #1b457e !important;
        border-left: 4px solid var(--ch-yellow-gold) !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    [data-testid="stChatMessage"]:has(img[alt="assistant avatar"]) {
        background-color: #14335c !important;
        border-left: 4px solid var(--ch-green-primary) !important;
    }

    [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] div, [data-testid="stChatMessage"] span {
        color: #ffffff !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    [data-testid="stChatInput"] {
        background-color: var(--ch-bg-surface) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 14px !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Autenticação e Perfil
# -----------------------------------------------------------------------------
require_authentication()
profile = get_profile() or {}
access_token = st.session_state.get("access_token")
role = profile.get("role", "apoiador")
user_avatar = resolve_avatar_path(profile)

# Títulos de gestão por papel
role_labels = {
    "super_admin": "Super Administrador (Gestão Global)",
    "admin": "Administrador (Gestão de Parceiros e Campanha)",
    "parceiro": "Parceiro Oficial (Gestão do seu Negócio)",
    "apoiador": "Apoiador Oficial",
}
role_display = role_labels.get(role, role.capitalize())

# -----------------------------------------------------------------------------
# Header Superior
# -----------------------------------------------------------------------------
col_title, col_action = st.columns([3.5, 1.2])

with col_title:
    st.markdown(
        f"""
        <div style="margin-bottom: 20px;">
            <div class="ch-ai-badge">INTELIGÊNCIA ARTIFICIAL · BASE 22500</div>
            <h2 style="margin: 10px 0 6px 0; font-size: 28px; font-weight: 800; color: #ffffff !important;">
                Assistente de Gestão e Projetos
            </h2>
            <div style="color: #cbd5e1; font-size: 15px;">
                Conectado como <strong>{html.escape(profile.get('first_name', ''))}</strong> ({role_display}).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_action:
    if st.button("🗑️ Limpar histórico", help="Limpa o histórico de conversas em tela.", use_container_width=True):
        st.session_state["ai_chat_history"] = []
        st.rerun()

# -----------------------------------------------------------------------------
# Inicialização e Histórico
# -----------------------------------------------------------------------------
ai_service = AIService(access_token=access_token)

if "ai_chat_history" not in st.session_state:
    history_result = ai_service.list_own_history(user_id=profile.get("id"), limit=10)
    past = list(reversed(history_result.data or []))
    st.session_state["ai_chat_history"] = [
        message
        for entry in past
        for message in (
            {"role": "user", "content": entry.get("question", "")},
            {
                "role": "assistant",
                "content": entry.get("answer", ""),
                "sources": entry.get("sources") or [],
            },
        )
    ]

# -----------------------------------------------------------------------------
# Sugestões e Card Informativo Personalizado por Papel
# -----------------------------------------------------------------------------
if not st.session_state["ai_chat_history"]:
    if role == "parceiro":
        subtext = (
            "Exemplos de perguntas para o seu negócio:<br>"
            "• <em>'Quantos apoiadores já se cadastraram pelo meu link?'</em><br>"
            "• <em>'Qual é a minha meta de hoje e como está meu progresso?'</em><br>"
            "• <em>'Como apresentar as Escolas Cívico-Militares para convencer novos apoiadores?'</em>"
        )
    elif role in ("admin", "super_admin"):
        subtext = (
            "Exemplos de perguntas para a gestão da campanha:<br>"
            "• <em>'Qual é o total geral de apoiadores cadastrados na campanha?'</em><br>"
            "• <em>'Quantos parceiros temos ativos no sistema?'</em><br>"
            "• <em>'Quais são os principais argumentos do projeto do Mineirão?'</em>"
        )
    else:
        subtext = "Consulte informações sobre os projetos e propostas do Coronel Henrique para Minas Gerais."

    st.markdown(
        f"""
        <div style="background-color: #122847; border: 1px dashed rgba(255, 199, 44, 0.4); border-radius: 16px; padding: 24px; text-align: center; margin: 18px 0;">
            <div style="font-size: 30px; margin-bottom: 8px;">🤖</div>
            <div style="color: #ffffff; font-weight: 800; font-size: 17px; margin-bottom: 6px;">
                Como posso orientar sua atuação hoje?
            </div>
            <div style="color: #cbd5e1; font-size: 14px; max-width: 650px; margin: 0 auto; line-height: 1.5;">
                {subtext}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# Renderização das Mensagens
# -----------------------------------------------------------------------------
for message in st.session_state["ai_chat_history"]:
    avatar = user_avatar if message["role"] == "user" else "assets/images/logo_coronel_henrique.png"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# -----------------------------------------------------------------------------
# Campo de Entrada e Processamento com IA
# -----------------------------------------------------------------------------
question = st.chat_input("Pergunte algo sobre seus dados ou sobre os projetos do Coronel Henrique...")

if question:
    st.session_state["ai_chat_history"].append({"role": "user", "content": question})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(question)

    with st.chat_message("assistant", avatar="assets/images/logo_coronel_henrique.png"):
        with st.spinner("Consultando dados de gestão e projetos..."):
            result = ai_service.ask(
                user_id=profile.get("id"),
                role=role,
                question=question,
            )

        if result.success and result.data:
            answer = result.data.get("answer", "")
            sources = result.data.get("sources") or []
            st.markdown(answer)

            st.session_state["ai_chat_history"].append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        else:
            st.error(f"⚠️ {result.message}")