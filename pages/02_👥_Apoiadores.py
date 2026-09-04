import html
import pandas as pd
import streamlit as st

from src.auth.guards import require_roles
from src.auth.session import get_profile
from src.config.settings import settings
from src.services.partner_service import PartnerService
from src.services.supporter_service import SupporterService
from src.utils.formatting import format_datetime_br

st.set_page_config(
    page_title="Apoiadores | Coronel Henrique 22500",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Injeção de CSS Estrito: Paleta 100% Oficial (Azul Royal Médio, Verde, Amarelo e Branco)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --ch-blue-bg: #163259;          /* Azul mais claro e vívido da identidade */
        --ch-blue-surface: #1e4273;     /* Superfície dos cards */
        --ch-blue-card-hover: #25518c;
        --ch-green-primary: #00a859;    /* Verde Patriota */
        --ch-yellow-gold: #ffc72c;      /* Amarelo Ouro */
        --ch-white-pure: #ffffff;       /* Branco Puro */
        --ch-border-light: rgba(255, 255, 255, 0.22);
    }

    /* 1. Fundo Global Azul Real em toda a estrutura */
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

    /* 2. Títulos e Textos em Branco Puro */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 800 !important;
        color: var(--ch-white-pure) !important;
    }

    p, span, label, div, li, a {
        color: var(--ch-white-pure);
    }

    /* 3. Badge Institucional (Verde e Amarelo com Branco) */
    .ch-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: var(--ch-green-primary);
        color: var(--ch-white-pure) !important;
        padding: 6px 16px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    /* 4. Card de Link de Captação */
    .ch-share-box {
        background: linear-gradient(135deg, var(--ch-blue-surface) 0%, #163561 100%);
        border: 2px solid var(--ch-yellow-gold);
        border-radius: 16px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    .ch-share-title {
        font-size: 19px;
        font-weight: 800;
        color: var(--ch-yellow-gold);
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: 'Montserrat', sans-serif;
    }

    .ch-share-desc {
        font-size: 14px;
        color: var(--ch-white-pure);
        margin-bottom: 14px;
        line-height: 1.5;
    }

    /* 5. Card de Estatísticas */
    .ch-stat-card {
        background-color: var(--ch-blue-surface);
        border: 2px solid var(--ch-green-primary);
        border-radius: 16px;
        padding: 20px 28px;
        margin-bottom: 20px;
        display: inline-block;
        min-width: 280px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }

    .ch-stat-label {
        font-size: 13px;
        font-weight: 700;
        color: var(--ch-white-pure);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }

    .ch-stat-value {
        font-size: 38px;
        font-weight: 900;
        color: var(--ch-yellow-gold);
        font-family: 'Montserrat', sans-serif;
        line-height: 1;
    }

    /* 6. Selectbox */
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

    /* 7. DataFrames */
    [data-testid="stDataFrame"] {
        border: 2px solid var(--ch-border-light) !important;
        border-radius: 14px !important;
        background-color: var(--ch-blue-surface) !important;
    }

    /* 8. Bloco de Código do Link */
    [data-testid="stCodeBlock"] {
        background-color: var(--ch-blue-bg) !important;
        border: 1px solid var(--ch-green-primary) !important;
        border-radius: 12px !important;
    }

    [data-testid="stCodeBlock"] code {
        color: var(--ch-white-pure) !important;
        font-weight: 700 !important;
        font-size: 15px !important;
    }

    /* 9. Botão de Download em Verde Oficial */
    div.stDownloadButton > button {
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

    div.stDownloadButton > button:hover {
        background: #008f4c !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 22px rgba(0, 168, 89, 0.6) !important;
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
        <div class="ch-badge">GESTÃO DE BASE • CORONEL HENRIQUE 22500</div>
        <h2 style="margin: 8px 0 6px 0; font-size: 32px; font-weight: 900; color: #ffffff !important;">
            👥 Base de Apoiadores
        </h2>
        <div style="color: #ffffff; font-size: 15px; font-weight: 500;">
            Acompanhe, audite e exporte os cadastros vinculados à sua rede de captação.
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

    public_url = f"{settings.APP_BASE_URL}/apoiar?p={partner.get('public_slug')}"
    
    st.markdown(
        """
        <div class="ch-share-box">
            <div class="ch-share-title">🔗 Seu Link Exclusivo de Captação</div>
            <div class="ch-share-desc">
                Compartilhe este link no WhatsApp, redes sociais e materiais de divulgação. 
                Todos os cadastros feitos através dele serão computados diretamente para a sua meta.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.code(public_url, language=None)

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

supporter_service = SupporterService(access_token=access_token)
result = supporter_service.list_for_partner(partner_id=partner.get("id"))

supporters = result.data or []

if not result.success:
    st.error(f"⚠️ {result.message}")
elif not supporters:
    st.markdown(
        f"""
        <div style="background-color: var(--ch-blue-surface); border: 2px dashed rgba(255,255,255,0.3); border-radius: 14px; padding: 28px; text-align: center; margin-top: 20px;">
            <div style="font-size: 28px; margin-bottom: 8px;">📭</div>
            <div style="color: #ffffff; font-weight: 700; font-size: 16px;">Nenhum apoiador cadastrado ainda</div>
            <div style="color: #ffffff; font-size: 14px; margin-top: 4px;">
                Os novos apoiadores cadastrados por <b>{html.escape(partner_label)}</b> aparecerão automaticamente aqui.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div style="display: flex; gap: 16px; margin: 20px 0 16px 0; align-items: center;">
            <div class="ch-stat-card">
                <div class="ch-stat-label">Total de Apoiadores ({html.escape(partner_label)})</div>
                <div class="ch-stat-value">{len(supporters)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    table_rows = [
        {
            "Nome": supporter.get("first_name", ""),
            "Sobrenome": supporter.get("last_name", ""),
            "WhatsApp": supporter.get("whatsapp", ""),
            "Status": "✅ Válido" if supporter.get("is_valid") else "⚠️ Pendente",
            "Data de Cadastro": format_datetime_br(supporter.get("created_at")),
        }
        for supporter in supporters
    ]

    df_supporters = pd.DataFrame(table_rows)
    st.dataframe(df_supporters, use_container_width=True, hide_index=True)

    # Botão de exportação
    st.write("")
    csv_data = df_supporters.to_csv(index=False).encode("utf-8")
    slug_name = partner.get("public_slug", "parceiro")
    st.download_button(
        label="⬇️ Exportar Tabela para Planilha (.CSV)",
        data=csv_data,
        file_name=f"apoiadores_{slug_name}.csv",
        mime="text/csv",
    )
