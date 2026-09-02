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


# -----------------------------------------------------------------------------
# Páginas — declaradas uma única vez aqui. st.navigation() passa a ser a
# ÚNICA fonte de navegação: substitui a listagem automática de pages/,
# eliminando a duplicidade entre o menu nativo do Streamlit e um menu
# customizado com st.page_link.
# -----------------------------------------------------------------------------
home_page = st.Page(
    "pages/00_🏠_Início.py", title="Início", icon="🏠", url_path="inicio", default=True
)
assistant_page = st.Page(
    "pages/01_🤖_Assistente_IA.py",
    title="Assistente IA",
    icon="🤖",
    url_path="assistente-ia",
)
supporters_page = st.Page(
    "pages/02_👥_Apoiadores.py", title="Apoiadores", icon="👥", url_path="apoiadores"
)
goals_page = st.Page(
    "pages/03_🎯_Metas.py", title="Metas Diárias", icon="🎯", url_path="metas"
)
partners_page = st.Page(
    "pages/04_🤝_Parceiros.py", title="Parceiros", icon="🤝", url_path="parceiros"
)
login_page = st.Page(
    "pages/05_🔐_Login.py", title="Entrar", icon="🔐", url_path="entrar"
)
signup_page = st.Page(
    "pages/06_📝_Criar_Conta.py",
    title="Criar conta",
    icon="📝",
    url_path="criar-conta",
)
# Reachable via link (fluxo pós-cadastro / link público), mas fora do menu
# visível — evita duplicidade e ruído para quem já está navegando.
verify_email_page = st.Page(
    "pages/07_✅_Verificar_Email.py",
    title="Verificar e-mail",
    icon="✅",
    url_path="verificar-email",
    visibility="hidden",
)
account_page = st.Page(
    "pages/08_👤_Minha_Conta.py",
    title="Minha conta",
    icon="👤",
    url_path="minha-conta",
)
public_signup_page = st.Page(
    "pages/09_🙌_Cadastro_Apoiador.py",
    title="Cadastro de apoiador",
    icon="🙌",
    url_path="apoiar",
    visibility="hidden",
)
knowledge_page = st.Page(
    "pages/10_📚_Base_de_Conhecimento.py",
    title="Base de Conhecimento",
    icon="📚",
    url_path="conhecimento",
)


def build_navigation() -> dict[str, list[st.Page]]:
    # Roteáveis por link direto (pós-cadastro / link público), mas ocultas:
    # visibility="hidden" já basta para não aparecerem, a seção é só rótulo.
    hidden_pages = [verify_email_page, public_signup_page]

    if not is_authenticated():
        return {
            "": [home_page],
            "MENU": [login_page, signup_page, *hidden_pages],
        }

    profile = get_profile() or {}
    role = profile.get("role")

    menu_pages = [home_page, assistant_page]

    if role in {"super_admin", "admin", "parceiro"}:
        menu_pages += [supporters_page, goals_page]

    if role in {"super_admin", "admin"}:
        menu_pages.append(partners_page)
        menu_pages.append(knowledge_page)

    return {
        "MENU": [*menu_pages, *hidden_pages],
        "CONTA": [account_page],
    }


def render_guest_sidebar_footer() -> None:
    with st.sidebar:
        st.divider()
        st.info("Você ainda não está autenticado.")


def render_authenticated_sidebar_footer() -> None:
    with st.sidebar:
        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            clear_session()
            st.rerun()


def main() -> None:
    load_css()

    # st.logo() é a única forma suportada de colocar algo ACIMA do widget
    # de navegação — o próprio st.navigation() fixa o menu no topo da
    # sidebar, ignorando a ordem de execução do código.
    st.logo("🎯", size="medium")

    authenticated = is_authenticated()

    pg = st.navigation(build_navigation())

    if authenticated:
        render_authenticated_sidebar_footer()
    else:
        render_guest_sidebar_footer()

    pg.run()


if __name__ == "__main__":
    main()