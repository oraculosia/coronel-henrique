from datetime import date

import pandas as pd
import streamlit as st

from src.auth.session import get_profile, is_authenticated
from src.services.goal_service import GoalService
from src.services.partner_service import PartnerService
from src.services.supporter_service import SupporterService, find_duplicate_whatsapp
from src.utils.formatting import display_job_title

st.set_page_config(
    page_title="Dashboard | Campanha 2026",
    page_icon="🏠",
)


def _render_duplicates(supporters: list[dict], scope_label: str) -> None:
    duplicates = find_duplicate_whatsapp(supporters)

    if not duplicates:
        st.success("Nenhuma duplicidade encontrada.")
        return

    st.warning(f"⚠️ {len(duplicates)} WhatsApp com mais de um cadastro {scope_label}.")
    with st.expander("Ver duplicidades"):
        for group in duplicates:
            names = ", ".join(
                f"{s['first_name']} {s['last_name']}" for s in group["supporters"]
            )
            st.write(f"**{group['whatsapp']}** ({group['count']}x): {names}")


def _render_partner_dashboard(profile: dict, access_token: str) -> None:
    partner_service = PartnerService(access_token=access_token)
    partner_result = partner_service.get_partner_for_profile(profile["id"])

    if not partner_result.success:
        st.error(partner_result.message)
        return

    partner = partner_result.data
    if not partner:
        st.warning(
            "Seu perfil ainda não está vinculado como parceiro. "
            "Fale com um administrador."
        )
        return

    goal_service = GoalService(access_token=access_token)
    supporter_service = SupporterService(access_token=access_token)
    today = date.today()

    goal = (goal_service.get_goal(partner_id=partner["id"], goal_date=today)).data
    total_supporters = (
        supporter_service.count_for_partner(partner["id"])
    ).data or 0

    st.divider()
    st.subheader("📊 Seu painel")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Apoiadores (total)", total_supporters)
    with col2:
        st.metric("Meta de hoje", goal["target_count"] if goal else "—")
    with col3:
        st.metric("Cadastros hoje", goal["achieved_count"] if goal else 0)

    if goal and goal["target_count"]:
        st.progress(min(goal["achieved_count"] / goal["target_count"], 1.0))
        if goal["status"] == "achieved":
            st.caption("✅ Meta de hoje atingida.")
    else:
        st.caption("Nenhuma meta criada para hoje. Configure em Metas Diárias.")

    history = (goal_service.list_recent(partner_id=partner["id"])).data or []
    if history:
        st.caption("Histórico recente")
        df_history = pd.DataFrame(history)[
            ["goal_date", "target_count", "achieved_count", "status"]
        ]
        st.dataframe(df_history, use_container_width=True, hide_index=True)

    supporters = (supporter_service.list_for_partner(partner["id"])).data or []

    st.divider()
    _render_duplicates(supporters, "entre seus apoiadores")

    if supporters:
        df = pd.DataFrame(supporters)[
            ["first_name", "last_name", "whatsapp", "created_at"]
        ]
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar meus apoiadores (CSV)",
            data=csv,
            file_name=f"apoiadores_{partner['public_slug']}.csv",
            mime="text/csv",
        )


def _partner_label(row: dict) -> str:
    owner = (row.get("partners") or {}).get("profiles") or {}
    name = f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip()
    slug = (row.get("partners") or {}).get("public_slug", "")
    return name or slug or "—"


def _render_staff_dashboard(access_token: str) -> None:
    partner_service = PartnerService(access_token=access_token)
    goal_service = GoalService(access_token=access_token)
    supporter_service = SupporterService(access_token=access_token)
    today = date.today()

    partners = (partner_service.list_partners()).data or []
    goals_today = (goal_service.list_today_for_staff(goal_date=today)).data or []
    supporters = (supporter_service.list_all_for_staff()).data or []

    st.divider()
    st.subheader("📊 Painel administrativo")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Parceiros", len(partners))
    with col2:
        st.metric(
            "Parceiros ativos",
            sum(1 for p in partners if p["is_accepting_supporters"]),
        )
    with col3:
        st.metric("Apoiadores (total)", len(supporters))
    with col4:
        st.metric(
            "Metas atingidas hoje",
            sum(1 for g in goals_today if g["status"] == "achieved"),
        )

    st.divider()
    st.markdown("### 🏆 Ranking de hoje")

    if not goals_today:
        st.info("Nenhuma meta criada para hoje ainda.")
    else:
        ranking = sorted(goals_today, key=lambda g: g["achieved_count"], reverse=True)
        df_ranking = pd.DataFrame(
            [
                {
                    "Parceiro": _partner_label(g),
                    "Cadastros hoje": g["achieved_count"],
                    "Meta": g["target_count"],
                    "Status": (
                        "✅ Atingida" if g["status"] == "achieved" else "⏳ Em andamento"
                    ),
                }
                for g in ranking
            ]
        )
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🔎 Duplicidade de cadastros")
    _render_duplicates(supporters, "na base")

    if supporters:
        st.divider()
        rows = []
        for supporter in supporters:
            partner_info = supporter.get("partners") or {}
            owner = partner_info.get("profiles") or {}
            rows.append(
                {
                    "first_name": supporter["first_name"],
                    "last_name": supporter["last_name"],
                    "whatsapp": supporter["whatsapp"],
                    "partner_slug": partner_info.get("public_slug", ""),
                    "partner_name": (
                        f"{owner.get('first_name', '')} {owner.get('last_name', '')}"
                    ).strip(),
                    "created_at": supporter["created_at"],
                }
            )
        csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar todos os apoiadores (CSV)",
            data=csv,
            file_name="apoiadores_campanha.csv",
            mime="text/csv",
        )


if not is_authenticated():
    st.markdown(
        """
        <section class="campaign-hero">
            <span class="campaign-eyebrow">CAMPANHA 2026</span>
            <h1>Trabalho para<br>proteger o futuro de Minas Gerais</h1>
            <p>
                Uma plataforma para organizar parceiros, acompanhar metas diárias
                e ampliar a rede de apoiadores da campanha.
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
else:
    profile = get_profile() or {}
    first_name = profile.get("first_name", "Usuário")
    cargo = display_job_title(profile)
    role = profile.get("role")
    access_token = st.session_state.get("access_token")

    st.markdown(
        f"""
        <section class="campaign-hero">
            <h1>Olá, {first_name}! 👋</h1>
            <p>
                Seu cargo é <strong>{cargo}</strong>.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if role == "parceiro":
        _render_partner_dashboard(profile, access_token)
    elif role in {"admin", "super_admin"}:
        _render_staff_dashboard(access_token)
    else:
        st.divider()
        st.info("Seu painel operacional será disponibilizado em breve.")
