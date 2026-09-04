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

# Injeção de CSS Dark Theme Absoluto (Zero Fundo Branco, Contraste Máximo)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-bg-root: #163259;
        --ch-bg-surface: #1e4273;
        --ch-bg-card: #122847;
        --ch-green-primary: #00a859;
        --ch-green-glow: rgba(0, 168, 89, 0.35);
        --ch-yellow-gold: #ffc72c;
        --ch-text-pure-white: #ffffff;
        --ch-text-light: #f1f5f9;
        --ch-text-secondary: #cbd5e1;
    }

    /* 1. Reset e forçamento de fundo escuro para TODA a estrutura do Streamlit */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .main, section[data-testid="stSidebar"] {
        background-color: var(--ch-bg-root) !important;
        color: var(--ch-text-pure-white) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Sidebar com tom flutuante: borda, cantos arredondados e sombra */
    section[data-testid="stSidebar"] {
        border: 3px solid var(--ch-yellow-gold) !important;
        border-radius: 18px !important;
        margin: 14px 0 14px 14px !important;
        box-shadow: 0 14px 34px rgba(0, 0, 0, .35) !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] > div {
        border-radius: 18px !important;
    }

    /* 2. Forçar todos os títulos e textos para cores claras */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        color: var(--ch-text-pure-white) !important;
    }

    p, span, label, div, li, a {
        color: var(--ch-text-light);
    }

    /* 3. Badge Superior de Identidade Visual */
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

    /* 4. Balões de Mensagem do Chat (Sem fundo claro nativo do Streamlit) */
    [data-testid="stChatMessage"] {
        background-color: var(--ch-bg-surface) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        margin-bottom: 14px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    }

    /* Balão do Usuário */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background-color: #0e2b4d !important;
        border-left: 4px solid var(--ch-yellow-gold) !important;
        border-top: 1px solid rgba(255, 199, 44, 0.4) !important;
        border-right: 1px solid rgba(255, 199, 44, 0.2) !important;
        border-bottom: 1px solid rgba(255, 199, 44, 0.2) !important;
    }

    /* Balão do Assistente */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        background-color: #081d33 !important;
        border-left: 4px solid var(--ch-green-primary) !important;
        border-top: 1px solid rgba(0, 168, 89, 0.4) !important;
        border-right: 1px solid rgba(0, 168, 89, 0.2) !important;
        border-bottom: 1px solid rgba(0, 168, 89, 0.2) !important;
    }

    /* Forçar todos os elementos internos das mensagens a serem brancos */
    [data-testid="stChatMessage"] *,
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] div,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] code {
        color: #ffffff !important;
        font-size: 15px !important;
        line-height: 1.6 !important;
    }

    /* 5. Campo de Entrada do Chat (Chat Input) */
    [data-testid="stChatInput"] {
        background-color: var(--ch-bg-surface) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 14px !important;
    }

    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #ffffff !important;
        font-size: 15px !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #94a3b8 !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: var(--ch-green-primary) !important;
        box-shadow: 0 0 16px var(--ch-green-glow) !important;
    }

    [data-testid="stChatInputSubmitButton"] svg {
        fill: var(--ch-green-primary) !important;
    }

    /* 6. Expander e Seção de Fontes com Alto Contraste */
    [data-testid="stExpander"] {
        background-color: #061424 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        margin-top: 12px !important;
    }

    [data-testid="stExpander"] summary {
        color: var(--ch-yellow-gold) !important;
        font-weight: 700 !important;
    }

    [data-testid="stExpander"] summary svg {
        fill: var(--ch-yellow-gold) !important;
    }

    [data-testid="stExpander"] [data-testid="stCaptionContainer"],
    [data-testid="stExpander"] span,
    [data-testid="stExpander"] p {
        color: #f1f5f9 !important;
        font-size: 14px !important;
    }

    /* 7. Botão Limpar Histórico */
    div.stButton > button {
        background-color: var(--ch-bg-surface) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button:hover {
        border-color: #ef4444 !important;
        color: #ffffff !important;
        background-color: rgba(239, 68, 68, 0.25) !important;
        transform: translateY(-1px);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

require_authentication()

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
role = profile.get("role")
user_avatar = resolve_avatar_path(profile)

# Header Superior
col_title, col_action = st.columns([3.5, 1.2])

with col_title:
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <div class="ch-ai-badge">INTELIGÊNCIA ARTIFICIAL • BASE 22500</div>
            <h2 style="margin: 10px 0 6px 0; font-size: 30px; font-weight: 800; color: #ffffff !important;">
                🤖 Assistente da Campanha
            </h2>
            <div style="color: #e2e8f0; font-size: 15px;">
                Consulte diretrizes, metas, regras de parceiros, apoios e dados estratégicos em tempo real.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_action:
    st.write("")
    if st.button("🗑️ Limpar histórico", help="Limpa o histórico de conversas em tela.", use_container_width=True):
        st.session_state["ai_chat_history"] = []
        st.rerun()

ai_service = AIService(access_token=access_token)

# Carregamento do histórico
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

# Card Inicial (Empty State)
if not st.session_state["ai_chat_history"]:
    st.markdown(
        """
        <div style="background-color: #0b1e33; border: 1px dashed rgba(255, 255, 255, 0.25); border-radius: 16px; padding: 32px; text-align: center; margin: 24px 0;">
            <div style="font-size: 32px; margin-bottom: 10px;">💡</div>
            <div style="color: #ffffff; font-weight: 800; font-size: 18px; margin-bottom: 6px;">Como posso orientar sua atuação hoje?</div>
            <div style="color: #e2e8f0; font-size: 15px; max-width: 600px; margin: 0 auto;">
                Exemplos de consultas: "Como cadastrar novos parceiros?", "Qual a meta diária recomendada?", "Regras de pontuação e ranking".
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Renderização das Mensagens
for message in st.session_state["ai_chat_history"]:
    avatar = user_avatar if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        sources = message.get("sources")
        if sources:
            with st.expander("📚 Fontes consultadas na resposta"):
                for source in sources:
                    title = html.escape(str(source.get("title", "Documento oficial")))
                    st.caption(f"📄 {title}")

# Campo de Pergunta
question = st.chat_input("Pergunte algo ao Assistente da Campanha...")

if question:
    st.session_state["ai_chat_history"].append({"role": "user", "content": question})
    with st.chat_message("user", avatar=user_avatar):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Processando resposta com a base de conhecimento..."):
            result = ai_service.ask(user_id=profile.get("id"), role=role, question=question)

        if result.success:
            answer = result.data.get("answer", "")
            sources = result.data.get("sources") or []
            st.markdown(answer)
            if sources:
                with st.expander("📚 Fontes consultadas na resposta"):
                    for source in sources:
                        title = html.escape(str(source.get("title", "Documento oficial")))
                        st.caption(f"📄 {title}")
            st.session_state["ai_chat_history"].append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        else:
            st.error(f"⚠️ {result.message}")
