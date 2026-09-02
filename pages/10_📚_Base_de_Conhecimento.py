import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.config.constants import USER_ROLES, ROLE_LABELS
from src.services.ai_service import AIService
from src.services.knowledge_service import KnowledgeService

st.set_page_config(
    page_title="Base de Conhecimento | Campanha 2026",
    page_icon="📚",
    layout="wide",
)

require_roles("super_admin", "admin")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")

knowledge_service = KnowledgeService(access_token=access_token)

st.title("📚 Base de Conhecimento")
st.caption(
    "Documentos usados pelo Assistente IA para responder perguntas. "
    "Cada documento só aparece para os papéis selecionados."
)

tab_documents, tab_history = st.tabs(["Documentos", "Histórico de conversas"])

with tab_documents:
    with st.expander("➕ Novo documento"):
        with st.form("create_knowledge_document_form"):
            title = st.text_input("Título")
            content = st.text_area("Conteúdo", height=200)
            audience_roles = st.multiselect(
                "Visível para",
                options=list(USER_ROLES),
                default=["super_admin"],
                format_func=lambda role: ROLE_LABELS.get(role, role),
            )
            submitted = st.form_submit_button(
                "Criar documento", type="primary", use_container_width=True
            )

        if submitted:
            if not title.strip() or not content.strip():
                st.error("Preencha título e conteúdo.")
            elif not audience_roles:
                st.error("Selecione ao menos um papel.")
            else:
                result = knowledge_service.create_document(
                    title=title,
                    content=content,
                    audience_roles=audience_roles,
                    created_by=profile["id"],
                )
                if result.success:
                    st.success(result.message)
                    st.rerun()
                else:
                    st.error(result.message)

    st.divider()

    documents_result = knowledge_service.list_all_for_staff()
    if not documents_result.success:
        st.error(documents_result.message)
    else:
        documents = documents_result.data or []
        if not documents:
            st.info("Nenhum documento cadastrado ainda.")

        for document in documents:
            status = "🟢 Ativo" if document["is_active"] else "⚪ Inativo"
            with st.expander(f"{status} — {document['title']}"):
                with st.form(f"edit_knowledge_document_{document['id']}"):
                    new_title = st.text_input("Título", value=document["title"])
                    new_content = st.text_area(
                        "Conteúdo", value=document["content"], height=200
                    )
                    new_audience_roles = st.multiselect(
                        "Visível para",
                        options=list(USER_ROLES),
                        default=document["audience_roles"],
                        format_func=lambda role: ROLE_LABELS.get(role, role),
                    )
                    new_is_active = st.checkbox(
                        "Documento ativo", value=document["is_active"]
                    )
                    save = st.form_submit_button(
                        "Salvar alterações", use_container_width=True
                    )

                if save:
                    update_result = knowledge_service.update_document(
                        document_id=document["id"],
                        actor_id=profile["id"],
                        title=new_title,
                        content=new_content,
                        audience_roles=new_audience_roles,
                        is_active=new_is_active,
                    )
                    if update_result.success:
                        st.success(update_result.message)
                        st.rerun()
                    else:
                        st.error(update_result.message)

with tab_history:
    ai_service = AIService(access_token=access_token)
    history_result = ai_service.list_all_history()

    if not history_result.success:
        st.error(history_result.message)
    else:
        conversations = history_result.data or []
        if not conversations:
            st.info("Nenhuma conversa registrada ainda.")
        for conversation in conversations:
            author = conversation.get("profiles") or {}
            author_name = (
                f"{author.get('first_name', '')} {author.get('last_name', '')}"
            ).strip() or "—"
            with st.expander(f"{conversation['created_at']} — {author_name}"):
                st.markdown(f"**Pergunta:** {conversation['question']}")
                st.markdown(f"**Resposta:** {conversation['answer']}")
