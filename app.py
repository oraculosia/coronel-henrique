from pathlib import Path

import streamlit as st

from src.auth.session import (
    clear_session,
    get_profile,
    initialize_session,
    is_authenticated,
)
from src.config.settings import settings
from src.utils.formatting import display_job_title, resolve_avatar_path, role_label


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
    # visibility="hidden" já basta para não aparecerem no menu nativo; como
    # a navegação visível agora é 100% custom (st.page_link), essas páginas só
    # precisam continuar registradas aqui para permanecerem roteáveis.
    hidden_pages = [verify_email_page, public_signup_page]

    if not is_authenticated():
        return {
            "": [home_page],
            "MENU": [login_page, signup_page, *hidden_pages],
        }

    profile = get_profile() or {}
    role = profile.get("role")

    # Ordem do modelo padrão: Assistente IA primeiro, depois Início.
    menu_pages = [assistant_page, home_page]

    if role in {"super_admin", "admin", "parceiro"}:
        menu_pages += [supporters_page, goals_page]

    if role in {"super_admin", "admin"}:
        menu_pages.append(partners_page)
        menu_pages.append(knowledge_page)

    return {
        "MENU": [*menu_pages, *hidden_pages],
        "CONTA": [account_page],
    }


def _visible_menu_pages(role: str | None) -> list[st.Page]:
    menu_pages = [assistant_page, home_page]

    if role in {"super_admin", "admin", "parceiro"}:
        menu_pages += [supporters_page, goals_page]

    if role in {"super_admin", "admin"}:
        menu_pages.append(partners_page)
        menu_pages.append(knowledge_page)

    return menu_pages


def render_user_card() -> None:
    """Card do usuário no topo da sidebar: foto · nome · e-mail · papel."""

    profile = get_profile() or {}
    full_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
    email = profile.get("email", "")
    role = role_label(profile.get("role"))
    cargo = display_job_title(profile)
    avatar_path = resolve_avatar_path(profile)

    with st.container(key="sidebar_user_card"):
        col_avatar, col_data = st.columns([1, 2.4], vertical_alignment="center")

        with col_avatar:
            if avatar_path:
                st.image(avatar_path, width=60)
            else:
                st.markdown(
                    '<div class="sidebar-avatar-fallback">🧑</div>',
                    unsafe_allow_html=True,
                )

        with col_data:
            st.markdown(
                f"""
                <div class="sidebar-user-data">
                    <span class="name">{full_name or 'Usuário'}</span>
                    <span class="cargo">{cargo}</span>
                    <span class="email">{email}</span>
                    <span class="role-chip">{role}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()


def render_guest_sidebar_header() -> None:
    st.markdown(
        """
        <div class="sidebar-guest-card">
            Você ainda não está autenticado.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()


def render_menu_section(pages: list[st.Page]) -> None:
    st.markdown('<span class="sidebar-section-label">Menu</span>', unsafe_allow_html=True)

    for page in pages:
        st.page_link(page, use_container_width=True)


def render_account_section(pages: list[st.Page]) -> None:
    st.divider()
    st.markdown('<span class="sidebar-section-label">Conta</span>', unsafe_allow_html=True)

    for page in pages:
        st.page_link(page, use_container_width=True)


def render_authenticated_sidebar_footer() -> None:
    st.divider()

    if st.button("🚪 Sair", use_container_width=True):
        clear_session()
        st.rerun()


def main() -> None:
    load_css()

    # Navegação oculta: o próprio st.navigation() continua sendo a fonte
    # única de verdade (registra as páginas e resolve rotas), mas o widget
    # nativo fica escondido porque ele sempre se fixa no TOPO da sidebar,
    # à frente de qualquer coisa escrita antes dele. Para o card do usuário
    # aparecer logo abaixo da logo — antes do menu — desenhamos a navegação
    # visível nós mesmos com st.page_link, na ordem exata que quisermos.
    authenticated = is_authenticated()
    navigation_map = build_navigation()
    pg = st.navigation(navigation_map, position="hidden")

    with st.sidebar:
        with st.container(key="sidebar_logo"):
            st.image("assets/images/logo_coronel_henrique.png", width=132)

        if authenticated:
            render_user_card()

            profile = get_profile() or {}
            render_menu_section(_visible_menu_pages(profile.get("role")))
            render_account_section(navigation_map.get("CONTA", []))
            render_authenticated_sidebar_footer()
        else:
            render_guest_sidebar_header()
            render_menu_section([login_page, signup_page])

    pg.run()


if __name__ == "__main__":
    main()