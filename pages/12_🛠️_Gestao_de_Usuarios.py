import html
import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.services.auth_service import AuthService
from src.utils.formatting import role_label

st.set_page_config(
    page_title="Gestão de Usuários | Coronel Henrique 22500",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Identidade visual: fundo azul, textos brancos, verde e amarelo apenas nos destaques.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-blue-bg: #163259;
        --ch-blue-surface: #1e4273;
        --ch-blue-inner: #122847;
        --ch-green: #00a859;
        --ch-green-hover: #008f4c;
        --ch-yellow: #ffc72c;
        --ch-white: #ffffff;
    }

    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    [data-testid="stToolbar"], .main, section[data-testid="stSidebar"] {
        background-color: var(--ch-blue-bg) !important;
        color: var(--ch-white) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Sidebar com tom flutuante: borda, cantos arredondados e sombra */
    section[data-testid="stSidebar"] {
        border: 3px solid var(--ch-yellow) !important;
        border-radius: 18px !important;
        margin: 14px 0 14px 14px !important;
        box-shadow: 0 14px 34px rgba(0, 0, 0, .35) !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] > div {
        border-radius: 18px !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: var(--ch-white) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
    }

    p, span, label, div, li, a, small {
        color: var(--ch-white) !important;
    }

    .ch-badge {
        display: inline-flex;
        background: var(--ch-green);
        color: var(--ch-white) !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        box-shadow: 0 5px 16px rgba(0, 168, 89, .28);
    }

    .ch-stat {
        background: var(--ch-blue-surface);
        border-radius: 15px;
        padding: 20px 22px;
        min-height: 100px;
        box-shadow: 0 8px 22px rgba(0, 0, 0, .2);
    }

    .ch-stat-label {
        color: var(--ch-white) !important;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .04em;
    }

    .ch-stat-value {
        color: var(--ch-yellow) !important;
        font: 900 32px/1 'Montserrat', sans-serif;
        margin-top: 9px;
    }

    .ch-user-card {
        background: var(--ch-blue-surface);
        border-radius: 16px;
        padding: 22px 24px;
        margin: 16px 0;
        box-shadow: 0 8px 24px rgba(0, 168, 89, .18);
    }

    .ch-user-name {
        color: var(--ch-white) !important;
        font: 800 20px 'Montserrat', sans-serif;
    }

    .ch-user-email, .ch-user-role {
        color: var(--ch-white) !important;
        font-size: 14px;
        margin-top: 5px;
    }

    .ch-status-active, .ch-status-inactive, .ch-login-state {
        display: inline-block;
        color: var(--ch-white) !important;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 800;
        margin: 4px 0;
    }

    .ch-status-active { background: var(--ch-green); }
    .ch-status-inactive { background: var(--ch-blue-inner); }
    .ch-login-state { background: var(--ch-blue-inner); }

    /* Botões: sem borda e dentro da paleta */
    div.stButton > button {
        background: var(--ch-green) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 11px !important;
        font-weight: 800 !important;
        transition: all .2s ease !important;
    }

    div.stButton > button:hover {
        background: var(--ch-green-hover) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 168, 89, .4) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

require_roles("super_admin")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
service = AuthService()

st.markdown(
    """
    <div style="margin-bottom: 26px;">
        <div class="ch-badge">CONTROLE ADMINISTRATIVO • ACESSO RESTRITO</div>
        <h2 style="margin: 8px 0 6px; font-size: 32px; color: #ffffff !important;">
            🛠️ Gestão de Usuários
        </h2>
        <div style="color: #ffffff; font-size: 15px;">
            Acompanhe acessos e controle o status das contas da plataforma.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

profiles_result = service.list_all_profiles(access_token=access_token)
login_result = service.list_auth_login_status()

if not profiles_result.success:
    st.error(f"⚠️ {profiles_result.message}")
    st.stop()

users = profiles_result.data or []
login_status = login_result.data or {}

if not login_result.success:
    st.warning(login_result.message)

if not users:
    st.info("ℹ️ Nenhum usuário cadastrado ainda.")
    st.stop()

active_count = sum(1 for user in users if user.get("is_active"))
inactive_count = len(users) - active_count

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(
        f'<div class="ch-stat"><div class="ch-stat-label">Total de usuários</div><div class="ch-stat-value">{len(users)}</div></div>',
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        f'<div class="ch-stat"><div class="ch-stat-label">Contas ativas</div><div class="ch-stat-value">{active_count}</div></div>',
        unsafe_allow_html=True,
    )
with m3:
    st.markdown(
        f'<div class="ch-stat"><div class="ch-stat-label">Contas desativadas</div><div class="ch-stat-value">{inactive_count}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("### 👥 Usuários cadastrados")

for user in users:
    last_sign_in = login_status.get(user.get("id"))
    is_self = user.get("id") == profile.get("id")
    full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or "Usuário"
    email = user.get("email", "E-mail não informado")
    is_active = user.get("is_active", False)
    role_text = role_label(user.get("role"))
    login_text = (
        f"🟢 Último acesso: {html.escape(str(last_sign_in).split('T')[0])}"
        if last_sign_in
        else "⚪ Ainda não realizou login"
    )

    col_info, col_status, col_action = st.columns([3.2, 2.2, 1.4])

    with col_info:
        st.markdown(
            f"""
            <div class="ch-user-card">
                <div class="ch-user-name">👤 {html.escape(full_name)}</div>
                <div class="ch-user-email">📧 {html.escape(email)}</div>
                <div class="ch-user-role">🏷️ Papel: {html.escape(str(role_text))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_status:
        st.markdown(
            f"""
            <div class="ch-user-card">
                <span class="ch-login-state">{login_text}</span><br>
                <span class="{'ch-status-active' if is_active else 'ch-status-inactive'}">
                    {'🟢 Conta ativa' if is_active else '⚪ Conta desativada'}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_action:
        st.write("")
        if is_self:
            st.caption("Sua própria conta")
        else:
            action_label = "Desativar" if is_active else "Ativar"
            if st.button(action_label, key=f"toggle_active_{user.get('id')}", use_container_width=True):
                result = service.set_profile_active_status(
                    access_token=access_token,
                    actor_id=profile.get("id"),
                    user_id=user.get("id"),
                    is_active=not is_active,
                )
                if result.success:
                    st.success(result.message)
                    st.rerun()
                else:
                    st.error(result.message)
