import html

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.config.settings import settings
from src.services.auth_service import AuthService
from src.services.partner_service import PartnerService
from src.services.supporter_service import SupporterService
from src.utils.formatting import format_datetime_br, role_label

st.set_page_config(
    page_title="Gestão de Parceiros | Coronel Henrique 22500",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeção de CSS Rigoroso: Background Azul Institucional Obrigatório e Zero Fundo Claro
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-blue-bg: #163259;          /* Fundo Oficial da Campanha */
        --ch-blue-surface: #1e4273;     /* Superfície dos Cards e Containers */
        --ch-blue-card-inner: #122847;  /* Fundo de Inputs, Códigos e Modais */
        --ch-green-primary: #00a859;    /* Verde Patriota */
        --ch-green-hover: #008f4c;
        --ch-yellow-gold: #ffc72c;      /* Amarelo Ouro */
        --ch-white-pure: #ffffff;       /* Branco Puro */
        --ch-border-light: rgba(255, 255, 255, 0.25);
    }

    /* 1. Reset Global do Fundo Azul em Toda a Estrutura */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .main, section[data-testid="stSidebar"] {
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

    /* 2. Forçar Todos os Títulos e Subtítulos para Branco Puro */
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

    /* 3. Badge Superior Institucional */
    .ch-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: var(--ch-green-primary);
        border: 1px solid var(--ch-yellow-gold);
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

    /* 4. Card de Convite de Parceiro com Borda Ouro */
    .ch-invite-card {
        background: var(--ch-blue-surface);
        border: 2px solid var(--ch-yellow-gold);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(255, 199, 44, 0.2);
    }

    .ch-invite-title {
        font-size: 20px;
        font-weight: 800;
        color: var(--ch-yellow-gold) !important;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'Montserrat', sans-serif;
    }

    .ch-invite-desc {
        font-size: 15px;
        color: var(--ch-white-pure) !important;
        margin-bottom: 14px;
        line-height: 1.6;
    }

    /* 5. Customização Rígida de Blocos de Código (st.code) - Zero Fundo Branco */
    [data-testid="stCodeBlock"],
    [data-testid="stCodeBlock"] pre,
    [data-testid="stCodeBlock"] pre > code,
    [data-testid="stCodeBlock"] code {
        background-color: var(--ch-blue-card-inner) !important;
        color: var(--ch-white-pure) !important;
        border: 1px solid var(--ch-green-primary) !important;
        border-radius: 12px !important;
        font-family: monospace !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }

    [data-testid="stCodeBlock"] button {
        background-color: var(--ch-blue-surface) !important;
        color: var(--ch-white-pure) !important;
        border: 1px solid var(--ch-border-light) !important;
        border-radius: 8px !important;
    }

    /* 6. Cards dos Parceiros Cadastrados com Bordas Alternadas */
    .ch-partner-box {
        background-color: var(--ch-blue-surface);
        border: 2px solid var(--ch-green-primary);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 22px;
        box-shadow: 0 8px 24px rgba(0, 168, 89, 0.25);
        transition: transform 0.2s ease;
    }

    .ch-partner-box:hover {
        transform: translateY(-2px);
    }

    .ch-partner-name {
        font-size: 22px;
        font-weight: 900;
        color: var(--ch-white-pure) !important;
        font-family: 'Montserrat', sans-serif;
        margin-bottom: 4px;
    }

    .ch-partner-email {
        font-size: 14px;
        color: var(--ch-yellow-gold) !important;
        margin-bottom: 12px;
        font-weight: 700;
    }

    /* Status Pills */
    .ch-status-pill-active {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: rgba(0, 168, 89, 0.35);
        border: 2px solid var(--ch-green-primary);
        color: var(--ch-white-pure) !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
    }

    .ch-status-pill-paused {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: rgba(239, 68, 68, 0.35);
        border: 2px solid #ef4444;
        color: var(--ch-white-pure) !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 800;
    }

    /* 7. Formulários e Inputs com Fundo Azul Escuro */
    [data-testid="stForm"] {
        background-color: var(--ch-blue-surface) !important;
        border: 2px solid var(--ch-border-light) !important;
        border-radius: 16px !important;
        padding: 24px 28px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;
    }

    [data-testid="stForm"] label,
    [data-testid="stForm"] p {
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }

    /* Inputs de Texto, Textarea e Placeholders */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: var(--ch-blue-card-inner) !important;
        color: var(--ch-white-pure) !important;
        border: 1px solid var(--ch-border-light) !important;
        border-radius: 10px !important;
        font-size: 15px !important;
    }

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: rgba(255, 255, 255, 0.6) !important;
    }

    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: var(--ch-yellow-gold) !important;
        box-shadow: 0 0 12px rgba(255, 199, 44, 0.4) !important;
    }

    /* Selectbox */
    [data-testid="stSelectbox"] label {
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
    }

    [data-testid="stSelectbox"] > div > div {
        background-color: var(--ch-blue-card-inner) !important;
        color: var(--ch-white-pure) !important;
        border: 1px solid var(--ch-border-light) !important;
        border-radius: 10px !important;
    }

    /* Expander no Fundo Azul */
    [data-testid="stExpander"] {
        background-color: var(--ch-blue-surface) !important;
        border: 2px solid var(--ch-yellow-gold) !important;
        border-radius: 14px !important;
        box-shadow: 0 6px 20px rgba(255, 199, 44, 0.15) !important;
        margin-bottom: 24px !important;
    }

    [data-testid="stExpander"] summary {
        color: var(--ch-yellow-gold) !important;
        font-weight: 800 !important;
        font-size: 16px !important;
    }

    /* Botões de Ação em Verde Patriota */
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
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

    div.stButton > button[kind="primary"]:hover,
    div.stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--ch-green-hover) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(0, 168, 89, 0.6) !important;
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
        background-color: var(--ch-blue-card-inner) !important;
        border-color: var(--ch-white-pure) !important;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        background-color: var(--ch-green-primary) !important;
        color: var(--ch-white-pure) !important;
        border-color: var(--ch-white-pure) !important;
        box-shadow: 0 4px 14px rgba(0, 168, 89, 0.4) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

require_roles("super_admin", "admin", "parceiro")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
role = profile.get("role")
service = PartnerService(access_token=access_token)
supporter_service = SupporterService(access_token=access_token)


def _buscar_fuzzy(itens, termo, extrair_texto, limiar=60):
    """Filtra itens tolerando erro de digitação/ordem de palavras (fuzzy)."""
    if not termo.strip():
        return itens

    pontuados = []
    for item in itens:
        pontuacao = fuzz.token_sort_ratio(termo.lower(), extrair_texto(item).lower())
        if pontuacao >= limiar:
            pontuados.append((pontuacao, item))

    pontuados.sort(key=lambda par: par[0], reverse=True)
    return [item for _, item in pontuados]


def _render_supporters_table(supporters: list[dict], key_prefix: str, show_partner_column: bool = False) -> None:
    termo_busca = st.text_input(
        "🔍 Pesquisar apoiador (nome, sobrenome ou WhatsApp)",
        key=f"{key_prefix}_busca",
    )
    filtrados = _buscar_fuzzy(
        supporters,
        termo_busca,
        lambda s: f"{s.get('first_name', '')} {s.get('last_name', '')} {s.get('whatsapp', '')}",
    )
    st.caption(f"{len(filtrados)} de {len(supporters)} apoiadores exibidos.")

    if not filtrados:
        st.info("ℹ️ Nenhum apoiador encontrado.")
        return

    rows = []
    for supporter in filtrados:
        row = {
            "Nome": supporter.get("first_name", ""),
            "Sobrenome": supporter.get("last_name", ""),
            "WhatsApp": supporter.get("whatsapp", ""),
            "Status": "✅ Válido" if supporter.get("is_valid") else "⚠️ Pendente",
            "Data de Cadastro": format_datetime_br(supporter.get("created_at")),
        }
        if show_partner_column:
            partner_info = supporter.get("partners") or {}
            owner = partner_info.get("profiles") or {}
            row["Parceiro"] = (
                f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip()
                or partner_info.get("public_slug", "—")
            )
        rows.append(row)

    df_supporters = pd.DataFrame(rows)
    st.dataframe(df_supporters, use_container_width=True, hide_index=True)

    csv_data = df_supporters.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exportar Tabela para Planilha (.CSV)",
        data=csv_data,
        file_name=f"apoiadores_{key_prefix}.csv",
        mime="text/csv",
        key=f"{key_prefix}_download",
    )

# Cabeçalho da Página
st.markdown(
    """
    <div style="margin-bottom: 24px;">
        <div class="ch-badge">EXPANSÃO DE BASE • CORONEL HENRIQUE 22500</div>
        <h2 style="margin: 8px 0 6px 0; font-size: 32px; font-weight: 900; color: #ffffff !important;">
            🤝 Gestão de Parceiros & Lideranças
        </h2>
        <div style="color: #ffffff; font-size: 15px; font-weight: 500;">
            Cadastre, vincule e gerencie as configurações públicas e alertas de cada parceiro regional.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def _render_partners_tab() -> None:
    signup_url = f"{settings.APP_BASE_URL}/criar-conta"

    st.markdown(
        """
        <div class="ch-invite-card">
            <div class="ch-invite-title">📨 Link de Convite para Novos Parceiros</div>
            <div class="ch-invite-desc">
                Envie este link para lideranças que desejam criar uma conta. Após o cadastro e a confirmação de e-mail,
                você poderá vincular o parceiro e gerar o link público de captação abaixo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(signup_url, language=None)

    unlinked_result = service.list_unlinked_partner_profiles()
    partners_result = service.list_partners()

    with st.expander("➕ Vincular Novo Perfil de Parceiro", expanded=not partners_result.data):
        unlinked = unlinked_result.data or []

        if not unlinked_result.success:
            st.error(f"⚠️ {unlinked_result.message}")
        elif not unlinked:
            st.info(
                "ℹ️ Não há perfis com perfil 'parceiro' aguardando vínculo. "
                "A liderança deve primeiro criar a conta e confirmar o e-mail."
            )
        else:
            options = {
                f"{p.get('first_name', '')} {p.get('last_name', '')} ({p.get('email', '')})".strip(): p
                for p in unlinked
            }

            with st.form("create_partner_form"):
                selected_label = st.selectbox("Selecione o Usuário Cadastrado:", options=list(options.keys()))
                campaign_message = st.text_area(
                    "Mensagem de Apresentação Oficial (opcional):",
                    max_chars=500,
                    help="Exibida na página pública de cadastro dos apoiadores vinculados a este parceiro.",
                )
                telegram_chat_id = st.text_input(
                    "Telegram Chat ID Individual (opcional):",
                    help="Caso não informado, os alertas serão direcionados ao chat padrão do sistema.",
                )
                custom_slug = st.text_input(
                    "Link Personalizado / Slug (opcional):",
                    placeholder="ex: lideranca-betim-centro",
                    help="Se não preenchido, o slug será gerado automaticamente a partir do nome.",
                )
                submitted = st.form_submit_button(
                    "🤝 Ativar e Vincular Parceiro",
                    type="primary",
                    use_container_width=True,
                )

                if submitted:
                    selected_profile = options[selected_label]
                    result = service.create_partner(
                        profile_id=selected_profile.get("id"),
                        created_by=profile.get("id"),
                        campaign_message=campaign_message,
                        telegram_chat_id=telegram_chat_id,
                        slug_seed=f"{selected_profile.get('first_name', '')} {selected_profile.get('last_name', '')}",
                        custom_slug=custom_slug.strip() or None,
                    )
                    if result.success:
                        st.success("✅ Parceiro ativado com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"⚠️ {result.message}")

    st.write("")
    st.markdown("### 🏢 Parceiros e Lideranças Cadastradas")

    partners = partners_result.data or []

    if not partners_result.success:
        st.error(f"⚠️ {partners_result.message}")
        return
    if not partners:
        st.info("ℹ️ Nenhum parceiro vinculado até o momento.")
        return

    termo_busca_parceiro = st.text_input(
        "🔍 Pesquisar parceiro (nome, e-mail ou link)",
        key="partners_busca",
    )
    filtrados = _buscar_fuzzy(
        partners,
        termo_busca_parceiro,
        lambda p: (
            f"{(p.get('profiles') or {}).get('first_name', '')} "
            f"{(p.get('profiles') or {}).get('last_name', '')} "
            f"{(p.get('profiles') or {}).get('email', '')} {p.get('public_slug', '')}"
        ),
    )
    st.caption(f"{len(filtrados)} de {len(partners)} parceiros exibidos.")

    if not filtrados:
        st.info("ℹ️ Nenhum parceiro encontrado.")
        return

    for partner in filtrados:
        owner = partner.get("profiles") or {}
        owner_name = f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip() or "Parceiro Oficial"
        owner_email = owner.get("email", "Sem e-mail cadastrado")
        is_active = partner.get("is_accepting_supporters", True)

        st.markdown(
            f"""
            <div class="ch-partner-box">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <div class="ch-partner-name">👤 {html.escape(owner_name)}</div>
                        <div class="ch-partner-email">📧 {html.escape(owner_email)}</div>
                    </div>
                    <div>
                        <span class="{'ch-status-pill-active' if is_active else 'ch-status-pill-paused'}">
                            {'🟢 Ativo / Recebendo Apoiadores' if is_active else '🔴 Captação Pausada'}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 4px;">
                🔗 Link de referência do parceiro:
            </div>
            """,
            unsafe_allow_html=True,
        )
        partner_public_url = f"{settings.APP_BASE_URL}/apoiar?p={partner.get('public_slug')}"
        st.code(partner_public_url, language=None)

        with st.form(f"edit_partner_{partner.get('id')}"):
            st.markdown("#### ⚙️ Configurações do Parceiro")
            new_message = st.text_area(
                "Mensagem pública de apresentação:",
                value=partner.get("campaign_message") or "",
                max_chars=500,
                key=f"message_{partner.get('id')}",
            )
            new_chat_id = st.text_input(
                "Telegram Chat ID:",
                value=partner.get("telegram_chat_id") or "",
                key=f"chat_{partner.get('id')}",
            )
            new_accepting = st.checkbox(
                "Manter parceiro ativo para receber novos cadastros",
                value=is_active,
                key=f"accepting_{partner.get('id')}",
            )
            save = st.form_submit_button("💾 Salvar Alterações", type="primary")

            if save:
                update_result = service.update_partner(
                    partner_id=partner.get("id"),
                    actor_id=profile.get("id"),
                    campaign_message=new_message,
                    telegram_chat_id=new_chat_id,
                    is_accepting_supporters=new_accepting,
                )
                if update_result.success:
                    st.success("✅ Configurações atualizadas com sucesso!")
                    st.rerun()
                else:
                    st.error(f"⚠️ {update_result.message}")

        st.write("")


def _render_all_supporters_tab(key_prefix: str) -> None:
    st.markdown("### 🙌 Apoiadores Cadastrados pelos Parceiros")
    supporters_result = supporter_service.list_all_for_staff()
    if not supporters_result.success:
        st.error(f"⚠️ {supporters_result.message}")
        return
    _render_supporters_table(
        supporters_result.data or [], key_prefix=key_prefix, show_partner_column=True
    )


if role == "super_admin":
    tab_admins, tab_partners, tab_supporters = st.tabs(
        ["🛡️ Administradores", "🤝 Parceiros", "🙌 Apoiadores"]
    )

    with tab_admins:
        st.markdown("### 🛡️ Administradores Cadastrados")
        auth_service = AuthService()
        profiles_result = auth_service.list_all_profiles(access_token=access_token)

        if not profiles_result.success:
            st.error(f"⚠️ {profiles_result.message}")
        else:
            admins = [
                p for p in (profiles_result.data or [])
                if p.get("role") in {"admin", "super_admin"}
            ]
            termo_busca_admin = st.text_input(
                "🔍 Pesquisar administrador (nome, e-mail ou papel)",
                key="admins_busca",
            )
            filtrados_admins = _buscar_fuzzy(
                admins,
                termo_busca_admin,
                lambda p: f"{p.get('first_name', '')} {p.get('last_name', '')} {p.get('email', '')}",
            )
            st.caption(f"{len(filtrados_admins)} de {len(admins)} administradores exibidos.")

            if not filtrados_admins:
                st.info("ℹ️ Nenhum administrador encontrado.")
            else:
                df_admins = pd.DataFrame(
                    [
                        {
                            "Nome": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                            "E-mail": p.get("email", ""),
                            "Papel": role_label(p.get("role")),
                            "Status": "🟢 Ativo" if p.get("is_active", True) else "🔴 Inativo",
                            "Cadastrado em": format_datetime_br(p.get("created_at")),
                        }
                        for p in filtrados_admins
                    ]
                )
                st.dataframe(df_admins, use_container_width=True, hide_index=True)

    with tab_partners:
        _render_partners_tab()

    with tab_supporters:
        _render_all_supporters_tab(key_prefix="staff_super_admin")

elif role == "admin":
    tab_partners, tab_supporters = st.tabs(["🤝 Parceiros", "🙌 Apoiadores"])

    with tab_partners:
        _render_partners_tab()

    with tab_supporters:
        _render_all_supporters_tab(key_prefix="staff_admin")

else:  # parceiro
    (tab_supporters,) = st.tabs(["🙌 Meus Apoiadores"])

    with tab_supporters:
        partner_result = service.get_partner_for_profile(profile.get("id"))

        if not partner_result.success:
            st.error(f"⚠️ {partner_result.message}")
        elif not partner_result.data:
            st.warning(
                "⚠️ Seu perfil ainda não está vinculado como parceiro oficial. "
                "Entre em contato com a coordenação."
            )
        else:
            partner_record = partner_result.data
            st.markdown("### 🙌 Apoiadores Cadastrados pelo Seu Link")
            supporters_result = supporter_service.list_for_partner(
                partner_id=partner_record.get("id")
            )
            if not supporters_result.success:
                st.error(f"⚠️ {supporters_result.message}")
            else:
                _render_supporters_table(
                    supporters_result.data or [], key_prefix="own_partner"
                )
