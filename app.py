from pathlib import Path

import streamlit as st

from src.auth.session import (
    clear_session,
    get_profile,
    initialize_session,
    is_authenticated,
)
from src.config.settings import settings


st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session()


def load_css() -> None:
    css_path = Path("assets/styles/premium.css")

    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def render_guest_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🎯 Campanha 2026")
        st.caption("Gestão de apoiadores e parceiros")
        st.divider()

        st.info("Você ainda não está autenticado.")

        st.page_link(
            "pages/05_🔐_Login.py",
            label="🔐 Entrar",
            icon="🔐",
            use_container_width=True,
        )

        st.page_link(
            "pages/06_📝_Criar_Conta.py",
            label="📝 Criar conta",
            icon="📝",
            use_container_width=True,
        )


def render_authenticated_sidebar() -> None:
    profile = get_profile() or {}

    with st.sidebar:
        st.markdown("## 🎯 Campanha 2026")
        st.caption("Gestão de apoiadores e parceiros")
        st.divider()

        full_name = (
            f"{profile.get('first_name', '')} "
            f"{profile.get('last_name', '')}"
        ).strip()

        st.markdown(f"### 👤 {full_name or 'Usuário'}")
        st.caption(profile.get("email", ""))
        st.info(f"Perfil: {profile.get('role', 'apoiador')}")

        st.divider()
        st.markdown("### MENU")

        st.page_link("app.py", label="🏠 Início", icon="🏠")
        st.page_link(
            "pages/01_🤖_Assistente_IA.py",
            label="🤖 Assistente IA",
            icon="🤖",
        )

        if profile.get("role") in {"super_admin", "admin", "parceiro"}:
            st.page_link(
                "pages/02_👥_Apoiadores.py",
                label="👥 Apoiadores",
                icon="👥",
            )
            st.page_link(
                "pages/03_🎯_Metas.py",
                label="🎯 Metas Diárias",
                icon="🎯",
            )

        if profile.get("role") in {"super_admin", "admin"}:
            st.page_link(
                "pages/04_🤝_Parceiros.py",
                label="🤝 Parceiros",
                icon="🤝",
            )

        st.divider()
        st.markdown("### CONTA")

        if st.button("🚪 Sair", use_container_width=True):
            clear_session()
            st.rerun()


def render_home() -> None:
    if not is_authenticated():
        st.markdown(
            """
            <section class="campaign-hero">
                <h1>Campanha 2026</h1>
                <p>
                    Uma plataforma para organizar parceiros, acompanhar metas
                    diárias e ampliar o número de apoiadores.
                </p>
            </section>
            """,
            unsafe_allow_html=True,
        )

        left, right = st.columns(2)

        with left:
            if st.button(
                "Criar minha conta",
                type="primary",
                use_container_width=True,
            ):
                st.switch_page("pages/06_📝_Criar_Conta.py")

        with right:
            if st.button("Entrar", use_container_width=True):
                st.switch_page("pages/05_🔐_Login.py")

        st.divider()
        st.caption("Acesso protegido por autenticação e permissões.")
        return

    profile = get_profile() or {}
    first_name = profile.get("first_name", "Usuário")
    role = profile.get("role", "apoiador")

    st.markdown(
        f"""
        <section class="campaign-hero">
            <h1>Olá, {first_name}! 👋</h1>
            <p>
                Seu perfil atual é <strong>{role}</strong>.
                O dashboard operacional será implementado na Fase 3.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Status da conta", "Ativa")

    with col2:
        st.metric("E-mail", "Confirmado")

    with col3:
        st.metric("Papel", role.replace("_", " ").title())

    st.divider()
    st.success("Autenticação e sessão estão funcionando.")


def main() -> None:
    load_css()

    if is_authenticated():
        render_authenticated_sidebar()
    else:
        render_guest_sidebar()

    render_home()


if __name__ == "__main__":
    main()