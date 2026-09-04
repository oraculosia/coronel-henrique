from datetime import date
import html
import pandas as pd
import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.services.goal_service import GoalService
from src.services.partner_service import PartnerService
from src.services.telegram_service import TelegramService
from src.utils.formatting import format_date_br, goal_status_label

st.set_page_config(
    page_title="Metas Diárias | Coronel Henrique 22500",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeção de CSS com a Paleta Oficial Estrita (Azul Royal, Verde, Amarelo e Branco)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-blue-bg: #163259;          /* Fundo Oficial da Campanha */
        --ch-blue-surface: #1e4273;     /* Superfície dos Cards */
        --ch-blue-card-hover: #25518c;
        --ch-green-primary: #00a859;    /* Verde Patriota */
        --ch-green-hover: #008f4c;
        --ch-yellow-gold: #ffc72c;      /* Amarelo Ouro */
        --ch-white-pure: #ffffff;       /* Branco Puro */
        --ch-border-light: rgba(255, 255, 255, 0.22);
    }

    /* 1. Fundo Global Azul Oficial em toda a aplicação */
    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], .main {
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

    /* 2. Títulos e Tipografia em Branco Puro */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
        color: var(--ch-white-pure) !important;
    }

    p, span, label, div, li, a {
        color: var(--ch-white-pure);
    }

    /* 3. Badge Institucional (Verde com Borda Amarela) */
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

    /* 4. Cards de Métricas com Bordas e Sombras Alternadas (Verde / Amarelo) */
    .ch-goal-card-green {
        background-color: var(--ch-blue-surface);
        border: 2px solid var(--ch-green-primary);
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: 0 8px 24px rgba(0, 168, 89, 0.28);
        transition: transform 0.2s ease;
    }

    .ch-goal-card-yellow {
        background-color: var(--ch-blue-surface);
        border: 2px solid var(--ch-yellow-gold);
        border-radius: 16px;
        padding: 22px 24px;
        box-shadow: 0 8px 24px rgba(255, 199, 44, 0.28);
        transition: transform 0.2s ease;
    }

    .ch-goal-card-green:hover, .ch-goal-card-yellow:hover {
        transform: translateY(-2px);
    }

    .ch-goal-card-label {
        font-size: 13px;
        font-weight: 700;
        color: var(--ch-white-pure);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
        display: flex;
        justify-content: space-between;
    }

    .ch-goal-card-val-gold {
        font-size: 36px;
        font-weight: 900;
        color: var(--ch-yellow-gold);
        font-family: 'Montserrat', sans-serif;
        line-height: 1;
    }

    .ch-goal-card-val-green {
        font-size: 36px;
        font-weight: 900;
        color: var(--ch-green-primary);
        font-family: 'Montserrat', sans-serif;
        line-height: 1;
    }

    .ch-goal-card-val-white {
        font-size: 26px;
        font-weight: 800;
        color: var(--ch-white-pure);
        font-family: 'Montserrat', sans-serif;
        line-height: 1;
    }

    /* 5. Formulários em Fundo Azul com Borda Amarela */
    [data-testid="stForm"] {
        background-color: var(--ch-blue-surface) !important;
        border: 2px solid var(--ch-yellow-gold) !important;
        border-radius: 16px !important;
        padding: 24px 28px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;
    }

    [data-testid="stForm"] label {
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }

    [data-testid="stNumberInput"] input {
        background-color: var(--ch-blue-bg) !important;
        color: var(--ch-white-pure) !important;
        border: 1px solid var(--ch-border-light) !important;
        border-radius: 10px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
    }

    /* 6. Selectbox no Dark Theme */
    [data-testid="stSelectbox"] label {
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }

    [data-testid="stSelectbox"] > div > div {
        background-color: var(--ch-blue-surface) !important;
        color: var(--ch-white-pure) !important;
        border: 1px solid var(--ch-border-light) !important;
        border-radius: 12px !important;
    }

    /* 7. Botões Primários em Verde Patriota */
    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background: var(--ch-green-primary) !important;
        color: var(--ch-white-pure) !important;
        font-weight: 800 !important;
        font-size: 16px !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 16px rgba(0, 168, 89, 0.4) !important;
        transition: all 0.2s ease !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div.stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--ch-green-hover) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(0, 168, 89, 0.6) !important;
    }

    /* 8. DataFrames */
    [data-testid="stDataFrame"] {
        border: 2px solid var(--ch-border-light) !important;
        border-radius: 14px !important;
        background-color: var(--ch-blue-surface) !important;
    }

    /* 9. Barra de Progresso Verde */
    [data-testid="stProgressBar"] > div > div {
        background-color: var(--ch-green-primary) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

require_roles("super_admin", "admin", "parceiro")

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
role = profile.get("role")

partner_service = PartnerService(access_token=access_token)

# Cabeçalho da Página
st.markdown(
    """
    <div style="margin-bottom: 24px;">
        <div class="ch-badge">GESTÃO ESTRATÉGICA • CORONEL HENRIQUE 22500</div>
        <h2 style="margin: 8px 0 6px 0; font-size: 32px; font-weight: 900; color: #ffffff !important;">
            🎯 Metas Diárias de Captação
        </h2>
        <div style="color: #ffffff; font-size: 15px; font-weight: 500;">
            Defina objetivos diários, monitore o avanço em tempo real e impulsione a equipe de lideranças.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

partner = None
partner_label = ""

if role == "parceiro":
    partner_result = partner_service.get_partner_for_profile(profile.get("id"))
    if not partner_result.success:
        st.error(f"⚠️ {partner_result.message}")
        st.stop()
    partner = partner_result.data
    if not partner:
        st.warning(
            "⚠️ Seu perfil ainda não está vinculado como parceiro oficial. "
            "Entre em contato com a coordenação."
        )
        st.stop()
    partner_label = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
else:
    partners_result = partner_service.list_partners()
    partners = partners_result.data or []
    if not partners_result.success:
        st.error(f"⚠️ {partners_result.message}")
        st.stop()
    if not partners:
        st.info("ℹ️ Nenhum parceiro cadastrado no sistema até o momento.")
        st.stop()

    def _label(p: dict) -> str:
        owner = p.get("profiles") or {}
        name = f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip()
        return name or p.get("public_slug", "—")

    options = {_label(p): p for p in partners}
    
    col_sel, _ = st.columns([1.5, 1])
    with col_sel:
        selected_label = st.selectbox("Selecione o Parceiro / Liderança:", options=list(options.keys()))
        partner = options[selected_label]
        partner_label = selected_label

goal_service = GoalService(access_token=access_token)
today = date.today()
today_br = today.strftime("%d/%m/%Y")

goal_result = goal_service.get_goal(partner_id=partner.get("id"), goal_date=today)
if not goal_result.success:
    st.error(f"⚠️ {goal_result.message}")
    st.stop()

goal = goal_result.data

st.markdown(
    f"""
    <div style="background-color: var(--ch-blue-surface); border-left: 4px solid var(--ch-yellow-gold); padding: 12px 18px; border-radius: 8px; margin: 16px 0 24px 0;">
        <span style="font-size: 15px; font-weight: 700; color: #ffffff;">Liderança em Foco:</span> 
        <span style="font-size: 15px; font-weight: 800; color: var(--ch-yellow-gold);">{html.escape(partner_label or 'Não identificado')}</span>
        <span style="color: rgba(255,255,255,0.6); margin: 0 8px;">•</span>
        <span style="font-size: 14px; color: #ffffff;">Data: <b>{today_br}</b></span>
    </div>
    """,
    unsafe_allow_html=True,
)

if goal is None:
    st.info("ℹ️ Ainda não existe meta diária configurada para o dia de hoje.")

    with st.form("create_goal_form"):
        st.markdown("### ➕ Estabelecer Nova Meta Diária")
        target_count = st.number_input(
            "Quantidade de novos apoiadores como meta de hoje:",
            min_value=1,
            value=10,
            step=1,
        )
        submitted = st.form_submit_button(
            "🎯 Salvar Meta de Hoje",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            result = goal_service.create_goal(
                partner_id=partner.get("id"),
                goal_date=today,
                target_count=int(target_count),
                created_by=profile.get("id"),
            )
            if result.success:
                st.success("✅ Meta criada com sucesso!")
                st.rerun()
            else:
                st.error(f"⚠️ {result.message}")
else:
    achieved = goal.get("status") == "achieved"
    target = goal.get("target_count", 0)
    current = goal.get("achieved_count", 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="ch-goal-card-yellow">
                <div class="ch-goal-card-label">Meta de Hoje <span>🎯</span></div>
                <div class="ch-goal-card-val-gold">{target}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="ch-goal-card-green">
                <div class="ch-goal-card-label">Cadastros Realizados <span>🚀</span></div>
                <div class="ch-goal-card-val-green">{current}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        status_text = "✅ Atingida" if achieved else "⏳ Em andamento"
        card_class = "ch-goal-card-green" if achieved else "ch-goal-card-yellow"
        st.markdown(
            f"""
            <div class="{card_class}">
                <div class="ch-goal-card-label">Status da Meta <span>📊</span></div>
                <div class="ch-goal-card-val-white">{status_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if target > 0:
        ratio = min(current / target, 1.0)
        st.write("")
        st.progress(ratio, text=f"Progresso: {int(ratio * 100)}% ({current}/{target} apoiadores)")

    if achieved:
        telegram = TelegramService()
        notify_result = telegram.notify_goal_if_reached(
            partner_id=partner.get("id"), partner_label=partner_label
        )
        if notify_result.success and not (notify_result.data or {}).get("skipped"):
            st.toast("📲 Notificação de meta atingida enviada ao Telegram!")

    st.write("")
    with st.form("edit_goal_form"):
        st.markdown("### ⚙️ Ajustar Meta de Hoje")
        new_target = st.number_input(
            "Atualizar quantidade alvo de apoiadores:",
            min_value=1,
            value=int(goal.get("target_count", 1)),
            step=1,
        )
        submitted = st.form_submit_button(
            "💾 Atualizar Meta",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            result = goal_service.update_target(
                goal_id=goal.get("id"), target_count=int(new_target), actor_id=profile.get("id")
            )
            if result.success:
                st.success("✅ Meta atualizada com sucesso!")
                st.rerun()
            else:
                st.error(f"⚠️ {result.message}")

st.write("")
st.markdown("### 📅 Histórico Recente de Metas")

history_result = goal_service.list_recent(partner_id=partner.get("id"))
history = history_result.data or []

if not history_result.success:
    st.error(f"⚠️ {history_result.message}")
elif not history:
    st.info("ℹ️ Ainda não há histórico de metas registradas para este parceiro.")
else:
    df_history = pd.DataFrame(
        [
            {
                "Data": format_date_br(entry.get("goal_date")),
                "Meta Estabelecida": entry.get("target_count"),
                "Apoiadores Cadastrados": entry.get("achieved_count"),
                "Status": goal_status_label(entry.get("status")),
            }
            for entry in history
        ]
    )
    st.dataframe(df_history, use_container_width=True, hide_index=True)
