import html
import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.config.constants import ROLE_LABELS, USER_ROLES
from src.services.ai_service import AIService
from src.services.knowledge_service import KnowledgeService

st.set_page_config(
    page_title="Base de Conhecimento | Coronel Henrique 22500",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS: fundo azul oficial; somente as abas recebem bordas brancas.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-blue-bg: #163259;
        --ch-blue-surface: #1e4273;
        --ch-blue-inner: #122847;
        --ch-green-primary: #00a859;
        --ch-green-hover: #008f4c;
        --ch-yellow-gold: #ffc72c;
        --ch-white-pure: #ffffff;
    }

    /* Fundo azul e texto claro em toda a página */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    [data-testid="stToolbar"], .main, section[data-testid="stSidebar"] {
        background-color: var(--ch-blue-bg) !important;
        color: var(--ch-white-pure) !important;
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

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
        color: var(--ch-white-pure) !important;
    }

    p, span, label, div, li, a, small {
        color: var(--ch-white-pure) !important;
    }

    /* Badge: sem borda */
    .ch-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: var(--ch-green-primary);
        color: var(--ch-white-pure) !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }

    /* Tabs: único componente com bordas brancas */
    [data-testid="stTabs"] {
        background-color: transparent !important;
        margin-top: 10px;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background-color: var(--ch-blue-surface) !important;
        border: 1px solid var(--ch-white-pure) !important;
        border-radius: 14px !important;
        padding: 6px !important;
        gap: 8px !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab"] {
        background-color: transparent !important;
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        border: 1px solid transparent !important;
        border-radius: 10px !important;
        padding: 10px 22px !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        background-color: var(--ch-blue-inner) !important;
        border-color: var(--ch-white-pure) !important;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        background-color: var(--ch-green-primary) !important;
        color: var(--ch-white-pure) !important;
        border-color: var(--ch-white-pure) !important;
        box-shadow: 0 4px 14px rgba(0, 168, 89, 0.4) !important;
    }

    /* Expanders: sem bordas */
    [data-testid="stExpander"],
    [data-testid="stExpander"] details,
    div[data-testid="stExpander"] > details {
        background-color: var(--ch-blue-surface) !important;
        border: none !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18) !important;
        margin-bottom: 16px !important;
    }

    [data-testid="stExpander"] summary {
        background-color: var(--ch-blue-surface) !important;
        color: var(--ch-white-pure) !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        border-radius: 12px !important;
    }

    [data-testid="stExpander"] summary:hover {
        background-color: var(--ch-blue-inner) !important;
    }

    [data-testid="stExpander"] summary svg {
        fill: var(--ch-white-pure) !important;
    }

    [data-testid="stExpanderDetails"],
    [data-testid="stExpander"] details > div {
        background-color: var(--ch-blue-surface) !important;
        padding-top: 12px !important;
    }

    /* Formulários: sem bordas */
    [data-testid="stForm"],
    [data-testid="stExpander"] [data-testid="stForm"] {
        background-color: var(--ch-blue-inner) !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 24px 26px !important;
    }

    [data-testid="stForm"] label,
    [data-testid="stForm"] p {
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }

    /* Campos: preenchimento azul, sem bordas */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stMultiSelect"] > div > div {
        background-color: var(--ch-blue-bg) !important;
        color: var(--ch-white-pure) !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 15px !important;
    }

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: rgba(255, 255, 255, 0.65) !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        box-shadow: 0 0 0 2px var(--ch-green-primary) !important;
    }

    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background-color: var(--ch-green-primary) !important;
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
    }

    /* Botões em verde, sem bordas */
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"],
    div.stFormSubmitButton > button {
        background: var(--ch-green-primary) !important;
        color: var(--ch-white-pure) !important;
        font-weight: 800 !important;
        font-size: 15px !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 26px !important;
        box-shadow: 0 4px 16px rgba(0, 168, 89, 0.4) !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background: var(--ch-green-hover) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(0, 168, 89, 0.6) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

require_roles("super_admin")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
knowledge_service = KnowledgeService(access_token=access_token)

# Cabeçalho da Página
st.markdown(
    """
    <div style="margin-bottom: 24px;">
        <div class="ch-badge">INTELIGÊNCIA ARTIFICIAL • BASE CONHECIMENTO 22500</div>
        <h2 style="margin: 8px 0 6px 0; font-size: 32px; font-weight: 900; color: #ffffff !important;">
            📚 Base de Conhecimento & RAG
        </h2>
        <div style="color: #ffffff; font-size: 15px; font-weight: 500;">
            Gerencie os documentos oficiais, permissões de acesso por perfil e audite o histórico de consultas ao assistente.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_documents, tab_history = st.tabs(["📑 Documentos Oficiais", "💬 Auditoria de Conversas"])

with tab_documents:
    with st.expander("➕ Cadastrar Novo Documento Oficial", expanded=False):
        with st.form("create_knowledge_document_form"):
            st.markdown("### 📝 Informações do Documento")
            title = st.text_input("Título do Documento:")
            content = st.text_area("Conteúdo Completo (Texto de Referência):", height=220)
            audience_roles = st.multiselect(
                "Níveis de Acesso Permitidos:",
                options=list(USER_ROLES),
                default=["super_admin"],
                format_func=lambda role: ROLE_LABELS.get(role, role),
            )
            is_public = st.checkbox(
                "Disponibilizar no Assistente IA Público (sem necessidade de login)",
                help="Utilizado no canal de atendimento público oficial do Coronel Henrique.",
            )
            submitted = st.form_submit_button(
                "💾 Salvar Documento na Base",
                type="primary",
                use_container_width=True,
            )

            if submitted:
                if not title.strip() or not content.strip():
                    st.error("⚠️ Preencha obrigatoriamente o título e o conteúdo do documento.")
                elif not audience_roles:
                    st.error("⚠️ Selecione pelo menos um perfil de acesso para visualização.")
                else:
                    result = knowledge_service.create_document(
                        title=title,
                        content=content,
                        audience_roles=audience_roles,
                        created_by=profile.get("id"),
                        is_public=is_public,
                    )
                    if result.success:
                        st.success("✅ Documento cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"⚠️ {result.message}")

    st.write("")
    st.markdown("### 📚 Acervo de Documentos Cadastrados")

    documents_result = knowledge_service.list_all_for_staff()
    if not documents_result.success:
        st.error(f"⚠️ {documents_result.message}")
    else:
        documents = documents_result.data or []
        if not documents:
            st.info("ℹ️ Nenhum documento cadastrado na base até o momento.")

        for document in documents:
            is_active = document.get("is_active", True)
            is_pub = document.get("is_public", False)
            status_badge = "🟢 Ativo" if is_active else "⚪ Inativo"
            public_badge = " • 🌐 Público" if is_pub else " • 🔒 Restrito"
            doc_title = document.get("title", "Sem título")

            with st.expander(f"{status_badge}{public_badge} — {doc_title}"):
                with st.form(f"edit_knowledge_document_{document.get('id')}"):
                    new_title = st.text_input("Título:", value=doc_title)
                    new_content = st.text_area(
                        "Conteúdo de Referência:", value=document.get("content", ""), height=220
                    )
                    new_audience_roles = st.multiselect(
                        "Permissões de Acesso:",
                        options=list(USER_ROLES),
                        default=document.get("audience_roles", []),
                        format_func=lambda role: ROLE_LABELS.get(role, role),
                    )
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        new_is_active = st.checkbox(
                            "Documento Ativo para Consulta", value=is_active
                        )
                    with c_col2:
                        new_is_public = st.checkbox(
                            "Acesso Público (Sem Login)", value=is_pub
                        )
                    save = st.form_submit_button(
                        "💾 Atualizar Documento", use_container_width=True
                    )

                    if save:
                        update_result = knowledge_service.update_document(
                            document_id=document.get("id"),
                            actor_id=profile.get("id"),
                            title=new_title,
                            content=new_content,
                            audience_roles=new_audience_roles,
                            is_active=new_is_active,
                            is_public=new_is_public,
                        )
                        if update_result.success:
                            st.success("✅ Documento atualizado com sucesso!")
                            st.rerun()
                        else:
                            st.error(f"⚠️ {update_result.message}")

with tab_history:
    st.markdown("### 🔍 Histórico de Interações com a IA")
    ai_service = AIService(access_token=access_token)
    history_result = ai_service.list_all_history()

    if not history_result.success:
        st.error(f"⚠️ {history_result.message}")
    else:
        conversations = history_result.data or []
        if not conversations:
            st.info("ℹ️ Nenhuma conversa registrada na base até o momento.")
        for conversation in conversations:
            author = conversation.get("profiles") or {}
            author_name = (
                f"{author.get('first_name', '')} {author.get('last_name', '')}"
            ).strip() or "Usuário Anônimo"
            created_at_val = conversation.get("created_at", "")

            with st.expander(f"🗓 {created_at_val} — 👤 {author_name}"):
                st.markdown(
                    f"""
                    <div style="background-color: var(--ch-blue-inner); padding: 14px 18px; border-radius: 8px; margin-bottom: 12px;">
                        <span style="font-weight: 800; color: var(--ch-yellow-gold);">❓ Pergunta Realizada:</span><br>
                        <span style="color: #ffffff;">{html.escape(conversation.get('question', ''))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"""
                    <div style="background-color: var(--ch-blue-inner); padding: 14px 18px; border-radius: 8px;">
                        <span style="font-weight: 800; color: var(--ch-green-primary);">🤖 Resposta do Assistente:</span><br>
                        <span style="color: #ffffff;">{html.escape(conversation.get('answer', ''))}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
