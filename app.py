from pathlib import Path

import streamlit as st

from src.config.settings import settings


st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    css_path = Path("assets/styles/premium.css")

    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🎯 Campanha 2026")
        st.caption("Gestão de apoiadores e parceiros")
        st.divider()

        st.markdown("### 👤 Acesso")
        st.info("Sessão não autenticada")

        st.divider()
        st.markdown("### MENU")
        st.page_link("app.py", label="🏠 Início", icon="🏠", disabled=True)
        st.page_link(
            "pages/01_🤖_Assistente_IA.py",
            label="🤖 Assistente IA",
            icon="🤖",
            disabled=True,
        )
        st.page_link(
            "pages/02_👥_Apoiadores.py",
            label="👥 Apoiadores",
            icon="👥",
            disabled=True,
        )
        st.page_link(
            "pages/03_🎯_Metas.py",
            label="🎯 Metas Diárias",
            icon="🎯",
            disabled=True,
        )
        st.page_link(
            "pages/04_🤝_Parceiros.py",
            label="🤝 Parceiros",
            icon="🤝",
            disabled=True,
        )

        st.divider()
        st.markdown("### CONTA")
        st.caption("Configurações e login serão habilitados na Fase 2.")


def main() -> None:
    load_css()
    render_sidebar()

    st.markdown(
        """
        <section class="campaign-hero">
            <h1>Campanha 2026</h1>
            <p>
                Plataforma de gestão de metas, parceiros e apoiadores.
                Cada novo cadastro fortalece a campanha.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="neon-card">
                <h3>👥 Apoiadores</h3>
                <p>Cadastros, acompanhamento e origem por parceiro.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="neon-card">
                <h3>🎯 Metas diárias</h3>
                <p>Metas individuais, progresso em tempo real e alertas.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="neon-card">
                <h3>🤖 Assistente IA</h3>
                <p>Respostas autorizadas sobre os projetos da campanha.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption(
        "Fase 1 concluída localmente: estrutura, dependências, visual base e configuração."
    )


if __name__ == "__main__":
    main()