import html
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.auth.session import get_profile, is_authenticated
from src.services.goal_service import GoalService
from src.services.partner_service import PartnerService
from src.services.supporter_service import SupporterService, find_duplicate_whatsapp
from src.utils.formatting import display_job_title, format_date_br, goal_status_label

st.set_page_config(
    page_title="Dashboard | Coronel Henrique 22500",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Tema visual consolidado: azul institucional como base, branco para contraste,
# verde para ações e amarelo somente para destaques e indicadores.
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

    /* Fundo azul obrigatório: evita qualquer superfície clara do Streamlit */
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main, [data-testid="stMainBlockContainer"],
    [data-testid="stHeader"], [data-testid="stToolbar"],
    section[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
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

    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3 {
        color: var(--ch-white) !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
    }

    p, span, label, div, li, a, small {
        color: var(--ch-white) !important;
    }

    /* Hero público */
    .ch-hero {
        background: var(--ch-blue-surface) !important;
        border-radius: 20px;
        padding: 40px 34px;
        text-align: center;
        margin: 16px 0 28px;
        box-shadow: 0 12px 30px rgba(0, 0, 0, .25);
    }

    .ch-badge {
        display: inline-block;
        background: var(--ch-green) !important;
        color: var(--ch-white) !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: .08em;
        text-transform: uppercase;
        margin-bottom: 14px;
    }

    .ch-hero-title {
        color: var(--ch-white) !important;
        font: 900 38px/1.1 'Montserrat', sans-serif;
        margin: 0 0 10px;
    }

    .ch-number { color: var(--ch-yellow) !important; }

    .ch-hero-subtitle {
        color: var(--ch-white) !important;
        font-size: 16px;
        font-weight: 700;
        margin: 0 0 12px;
    }

    .ch-hero-copy {
        color: var(--ch-white) !important;
        font-size: 15px;
        line-height: 1.6;
        margin: 0 auto;
        max-width: 760px;
    }

    /* Cabeçalho do usuário */
    .ch-welcome {
        background: var(--ch-blue-surface) !important;
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 26px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 10px 26px rgba(0, 0, 0, .20);
    }

    .ch-role {
        background: var(--ch-green) !important;
        color: var(--ch-white) !important;
        border-radius: 999px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 800;
        text-transform: uppercase;
    }

    /* Métricas sem bordas: cor e sombra assumem a hierarquia visual */
    .ch-metric {
        background: var(--ch-blue-surface) !important;
        border-radius: 16px;
        padding: 21px 23px;
        min-height: 106px;
        box-shadow: 0 8px 22px rgba(0, 0, 0, .20);
        transition: transform .2s ease, box-shadow .2s ease;
    }

    .ch-metric:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0, 168, 89, .28);
    }

    .ch-metric-label {
        color: var(--ch-white) !important;
        font-size: 13px;
        font-weight: 700;
        letter-spacing: .04em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }

    .ch-metric-value {
        color: var(--ch-white) !important;
        font: 900 32px/1 'Montserrat', sans-serif;
    }

    .ch-metric-value.green { color: var(--ch-green) !important; }
    .ch-metric-value.yellow { color: var(--ch-yellow) !important; }

    .ch-section-title {
        color: var(--ch-white) !important;
        font: 800 20px 'Montserrat', sans-serif;
        margin: 32px 0 15px;
    }

    /* Elementos nativos: azul em todos os estados */
    [data-testid="stDataFrame"],
    [data-testid="stExpander"],
    [data-testid="stExpander"] details {
        background-color: var(--ch-blue-surface) !important;
        border: none !important;
        border-radius: 14px !important;
        box-shadow: 0 7px 20px rgba(0, 0, 0, .16) !important;
    }

    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] details > div {
        background-color: var(--ch-blue-surface) !important;
        color: var(--ch-white) !important;
    }

    [data-testid="stProgressBar"] > div {
        background-color: var(--ch-blue-inner) !important;
    }

    [data-testid="stProgressBar"] > div > div {
        background-color: var(--ch-green) !important;
    }

    div.stButton > button[kind="primary"],
    div.stDownloadButton > button {
        background: var(--ch-green) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        box-shadow: 0 5px 17px rgba(0, 168, 89, .35) !important;
        transition: all .2s ease !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div.stDownloadButton > button:hover {
        background: var(--ch-green-hover) !important;
        transform: translateY(-2px) !important;
    }

    div.stButton > button[kind="secondary"] {
        background: var(--ch-blue-surface) !important;
        color: var(--ch-white) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _render_duplicates(supporters: list[dict], scope_label: str) -> None:
    duplicates = find_duplicate_whatsapp(supporters)

    if not duplicates:
        st.success("✅ Nenhuma duplicidade de WhatsApp identificada.")
        return

    st.warning(f"⚠️ **{len(duplicates)}** WhatsApp com mais de um cadastro {scope_label}.")
    with st.expander("🔍 Detalhes dos cadastros duplicados"):
        for group in duplicates:
            names = ", ".join(
                f"{supporter.get('first_name', '')} {supporter.get('last_name', '')}".strip()
                for supporter in group["supporters"]
            )
            st.markdown(
                f"📱 **{html.escape(str(group['whatsapp']))}** ({group['count']}x): {html.escape(names)}"
            )


def _partner_label(row: dict) -> str:
    owner = (row.get("partners") or {}).get("profiles") or {}
    name = f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip()
    slug = (row.get("partners") or {}).get("public_slug", "")
    return name or slug or "—"


def _metric_card(label: str, value: str | int, icon: str, accent: str = "") -> None:
    accent_class = f" {accent}" if accent else ""
    st.markdown(
        f"""
        <div class="ch-metric">
            <div class="ch-metric-label">{html.escape(label)} <span>{icon}</span></div>
            <div class="ch-metric-value{accent_class}">{html.escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_partner_dashboard(profile: dict, access_token: str) -> None:
    partner_service = PartnerService(access_token=access_token)
    partner_result = partner_service.get_partner_for_profile(profile.get("id"))

    if not partner_result.success:
        st.error(partner_result.message)
        return

    partner = partner_result.data
    if not partner:
        st.warning(
            "Seu perfil ainda não está vinculado como parceiro oficial. "
            "Entre em contato com a coordenação da campanha."
        )
        return

    goal_service = GoalService(access_token=access_token)
    supporter_service = SupporterService(access_token=access_token)
    today = date.today()

    goal_result = goal_service.get_goal(partner_id=partner["id"], goal_date=today)
    goal = goal_result.data if goal_result.success else None
    total_result = supporter_service.count_for_partner(partner["id"])
    total_supporters = total_result.data or 0

    target_today = goal.get("target_count", 0) if goal else 0
    achieved_today = goal.get("achieved_count", 0) if goal else 0

    st.markdown('<div class="ch-section-title">📊 Desempenho operacional</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        _metric_card("Total de apoiadores", total_supporters, "👥")
    with col2:
        _metric_card("Meta de hoje", target_today if target_today else "—", "🎯", "yellow")
    with col3:
        _metric_card("Cadastros hoje", achieved_today, "🚀", "green")

    if goal and target_today > 0:
        ratio = min(achieved_today / target_today, 1.0)
        st.write("")
        st.progress(ratio, text=f"Progresso da meta diária: {int(ratio * 100)}% ({achieved_today}/{target_today})")
        if goal.get("status") == "achieved":
            st.success("🎉 Meta diária atingida. Excelente trabalho de mobilização!")
    else:
        st.info("ℹ️ Nenhuma meta definida para hoje. Configure uma meta no menu **Metas Diárias**.")

    st.markdown('<div class="ch-section-title">📅 Histórico recente de metas</div>', unsafe_allow_html=True)
    history_result = goal_service.list_recent(partner_id=partner["id"])
    history = history_result.data or []
    if history:
        df_history = pd.DataFrame(
            [
                {
                    "Data": format_date_br(entry.get("goal_date")),
                    "Meta": entry.get("target_count", 0),
                    "Cadastros": entry.get("achieved_count", 0),
                    "Status": goal_status_label(entry.get("status")),
                }
                for entry in history
            ]
        )
        st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Nenhum registro de meta disponível até o momento.")

    supporters_result = supporter_service.list_for_partner(partner["id"])
    supporters = supporters_result.data or []

    st.markdown('<div class="ch-section-title">🔎 Qualidade e exportação da base</div>', unsafe_allow_html=True)
    _render_duplicates(supporters, "entre seus apoiadores")

    if supporters:
        csv_df = pd.DataFrame(supporters)
        desired_columns = ["first_name", "last_name", "whatsapp", "created_at"]
        available_columns = [column for column in desired_columns if column in csv_df.columns]
        csv = csv_df[available_columns].to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar minha base de apoiadores (.CSV)",
            data=csv,
            file_name=f"apoiadores_{partner.get('public_slug', 'parceiro')}.csv",
            mime="text/csv",
        )


def _render_staff_dashboard(access_token: str) -> None:
    partner_service = PartnerService(access_token=access_token)
    goal_service = GoalService(access_token=access_token)
    supporter_service = SupporterService(access_token=access_token)
    today = date.today()

    partners_result = partner_service.list_partners()
    goals_today_result = goal_service.list_today_for_staff(goal_date=today)
    supporters_result = supporter_service.list_all_for_staff()

    for result in (partners_result, goals_today_result, supporters_result):
        if not result.success:
            st.error(result.message)

    partners = partners_result.data or []
    goals_today = goals_today_result.data or []
    supporters = supporters_result.data or []

    active_partners = sum(1 for partner in partners if partner.get("is_accepting_supporters"))
    goals_achieved = sum(1 for goal in goals_today if goal.get("status") == "achieved")

    st.markdown('<div class="ch-section-title">📊 Indicadores gerais da campanha</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _metric_card("Parceiros cadastrados", len(partners), "🏢")
    with col2:
        _metric_card("Parceiros ativos", active_partners, "🟢", "green")
    with col3:
        _metric_card("Total de apoiadores", len(supporters), "👥", "yellow")
    with col4:
        _metric_card("Metas atingidas hoje", goals_achieved, "🎯", "green")

    st.markdown('<div class="ch-section-title">🏆 Ranking de captação do dia</div>', unsafe_allow_html=True)
    if goals_today:
        ranking = sorted(goals_today, key=lambda item: item.get("achieved_count", 0), reverse=True)
        df_ranking = pd.DataFrame(
            [
                {
                    "Posição": f"{index}º",
                    "Parceiro": _partner_label(goal),
                    "Cadastros hoje": goal.get("achieved_count", 0),
                    "Meta diária": goal.get("target_count", 0),
                    "Status": "✅ Atingida" if goal.get("status") == "achieved" else "⏳ Em andamento",
                }
                for index, goal in enumerate(ranking, start=1)
            ]
        )
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Nenhuma meta cadastrada para hoje.")

    st.markdown('<div class="ch-section-title">📅 Consolidado semanal</div>', unsafe_allow_html=True)
    week_start = today - timedelta(days=6)
    week_result = goal_service.list_range_for_staff(start_date=week_start, end_date=today)
    if not week_result.success:
        st.error(week_result.message)
    week_goals = week_result.data or []

    if week_goals:
        week_target = sum(goal.get("target_count", 0) for goal in week_goals)
        week_achieved = sum(goal.get("achieved_count", 0) for goal in week_goals)
        week_goal_count = sum(1 for goal in week_goals if goal.get("status") == "achieved")

        col1, col2, col3 = st.columns(3)
        with col1:
            _metric_card("Meta semanal", week_target, "🎯", "yellow")
        with col2:
            _metric_card("Cadastros semanais", week_achieved, "🚀", "green")
        with col3:
            _metric_card("Metas diárias batidas", week_goal_count, "🏆")

        totals_by_partner: dict[str, dict[str, int]] = {}
        for entry in week_goals:
            label = _partner_label(entry)
            bucket = totals_by_partner.setdefault(label, {"target": 0, "achieved": 0})
            bucket["target"] += entry.get("target_count", 0)
            bucket["achieved"] += entry.get("achieved_count", 0)

        df_week = pd.DataFrame(
            [
                {
                    "Parceiro": label,
                    "Meta semanal": totals["target"],
                    "Cadastros semanais": totals["achieved"],
                    "Aproveitamento": (
                        f"{int((totals['achieved'] / totals['target']) * 100)}%"
                        if totals["target"] > 0
                        else "—"
                    ),
                }
                for label, totals in sorted(
                    totals_by_partner.items(),
                    key=lambda item: item[1]["achieved"],
                    reverse=True,
                )
            ]
        )
        st.dataframe(df_week, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Não há metas registradas nos últimos 7 dias.")

    st.markdown('<div class="ch-section-title">🔎 Auditoria da base</div>', unsafe_allow_html=True)
    _render_duplicates(supporters, "em toda a base da campanha")

    if supporters:
        rows = []
        for supporter in supporters:
            partner_info = supporter.get("partners") or {}
            owner = partner_info.get("profiles") or {}
            rows.append(
                {
                    "Nome": supporter.get("first_name", ""),
                    "Sobrenome": supporter.get("last_name", ""),
                    "WhatsApp": supporter.get("whatsapp", ""),
                    "Parceiro": f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip() or partner_info.get("public_slug", ""),
                    "Data de cadastro": supporter.get("created_at", ""),
                }
            )

        csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar base completa da campanha (.CSV)",
            data=csv,
            file_name="apoiadores_campanha_completo.csv",
            mime="text/csv",
        )


if not is_authenticated():
    st.markdown(
        """
        <div class="ch-hero">
            <div class="ch-badge">PARTIDO LIBERAL • 22</div>
            <div class="ch-hero-title">CORONEL HENRIQUE <span class="ch-number">22500</span></div>
            <div class="ch-hero-subtitle">ORDEM E TRABALHO PARA PROTEGER O FUTURO</div>
            <p class="ch-hero-copy">
                Plataforma oficial de mobilização, organização de lideranças e acompanhamento de metas
                para ampliar a rede de apoiadores em Minas Gerais.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, center_column, _ = st.columns([1, 1.4, 1])
    with center_column:
        if st.button("🔐 Acessar Painel", type="primary", use_container_width=True):
            st.switch_page("pages/05_🔐_Login.py")

else:
    profile = get_profile() or {}
    first_name = profile.get("first_name", "Usuário")
    role = profile.get("role", "usuario")
    cargo = display_job_title(profile)
    access_token = st.session_state.get("access_token", "")

    st.markdown(
        f"""
        <div class="ch-welcome">
            <div>
                <div style="font-size:13px; font-weight:700; color:#ffffff; text-transform:uppercase;">Portal de Lideranças e Gestão</div>
                <div style="font:800 26px 'Montserrat', sans-serif; color:#ffffff; margin-top:4px;">Bem-vindo(a), {html.escape(first_name)}! 👋</div>
                <div style="font-size:15px; color:#ffffff; margin-top:6px;">Cargo: <b>{html.escape(cargo)}</b></div>
            </div>
            <div class="ch-role">{html.escape(role.replace('_', ' '))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if role == "parceiro":
        _render_partner_dashboard(profile, access_token)
    elif role in {"admin", "super_admin"}:
        _render_staff_dashboard(access_token)
    else:
        st.info("ℹ️ Seu painel operacional será disponibilizado em breve.")
