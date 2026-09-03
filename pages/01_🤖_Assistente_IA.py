import streamlit as st

from src.auth.guards import require_authentication
from src.auth.session import get_profile
from src.services.ai_service import AIService
from src.utils.formatting import resolve_avatar_path

st.set_page_config(
    page_title="Assistente IA | Campanha 2026",
    page_icon="🤖",
)

require_authentication()

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
role = profile.get("role")
user_avatar = resolve_avatar_path(profile)

st.title("🤖 Assistente IA")
st.caption("Tire dúvidas sobre a campanha, parceiros, apoiadores e metas.")

ai_service = AIService(access_token=access_token)

if "ai_chat_history" not in st.session_state:
    history_result = ai_service.list_own_history(user_id=profile["id"], limit=10)
    past = list(reversed(history_result.data or []))
    st.session_state["ai_chat_history"] = [
        message
        for entry in past
        for message in (
            {"role": "user", "content": entry["question"]},
            {
                "role": "assistant",
                "content": entry["answer"],
                "sources": entry.get("sources") or [],
            },
        )
    ]

for message in st.session_state["ai_chat_history"]:
    avatar = user_avatar if message["role"] == "user" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])
        sources = message.get("sources")
        if sources:
            with st.expander("Fontes"):
                for source in sources:
                    st.caption(f"📄 {source.get('title', '—')}")


question = st.chat_input("Digite sua pergunta...")

if question:
    st.session_state["ai_chat_history"].append({"role": "user", "content": question})
    with st.chat_message("user", avatar=user_avatar):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            result = ai_service.ask(user_id=profile["id"], role=role, question=question)

        if result.success:
            answer = result.data["answer"]
            sources = result.data["sources"]
            st.write(answer)
            if sources:
                with st.expander("Fontes"):
                    for source in sources:
                        st.caption(f"📄 {source.get('title', '—')}")
            st.session_state["ai_chat_history"].append(
                {"role": "assistant", "content": answer, "sources": sources}
            )
        else:
            st.error(result.message)

with st.container(key="chat_clear_bar"):
    if st.button("🗑️ Limpar histórico", help="Limpa o histórico de conversas do Assistente IA."):
        # Lista vazia (não remover a chave!): o bloco acima só recarrega o
        # histórico do banco quando "ai_chat_history" NÃO existe em session_state.
        st.session_state["ai_chat_history"] = []
        st.rerun()