"""
Assistente IA oficial do Coronel Henrique (22500)
Interface moderna, responsiva, sem duplicidades e com identidade visual 100% azul institucional.
Pode ser executada como subpágina do multipage ou diretamente de forma isolada via:
    streamlit run pages/11_💬_Fale_com_a_Campanha.py
"""
import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path mesmo ao rodar o arquivo isoladamente
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.services.ai_service import AIService
from src.services.supporter_service import SupporterService
from src.utils.validators import validate_email_address, validate_whatsapp

OFFICIAL_PARTNER_SLUG = "campanha-oficial"

# Avatar oficial com fallback elegante caso o arquivo local não exista
LOCAL_AVATAR = PROJECT_ROOT / "assets" / "images" / "logo_coronel_henrique.png"
FALLBACK_AVATAR = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f1e7-1f1f7.png"
AVATAR_IMG = str(LOCAL_AVATAR) if LOCAL_AVATAR.exists() else FALLBACK_AVATAR

SUPPORTER_INTENT_KEYWORDS = (
    "quero ser apoiador",
    "quero apoiar",
    "como me cadastro",
    "como eu me cadastro",
    "quero me cadastrar",
    "cadastrar apoiador",
    "virar apoiador",
    "apoiar a campanha",
    "apoiar o coronel",
    "quero ajudar",
    "como ajudar",
)


def _wants_to_become_supporter(text: str) -> bool:
    normalized = text.strip().lower()
    return any(keyword in normalized for keyword in SUPPORTER_INTENT_KEYWORDS)


def apply_custom_styles() -> None:
    """Aplica o Design System oficial: 100% Azul Institucional com toques verde e dourado vibrante."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap');

        :root {
            /* Paleta Azul Oficial da Campanha */
            --ch-blue-bg: #0f274a;          /* Fundo principal azul institucional */
            --ch-blue-card: #163664;        /* Superfícies, cards e balões */
            --ch-blue-input: #1b4178;       /* Inputs, botões de ação e modal */
            --ch-blue-border: #2c5999;      /* Bordas em tom de azul contrastante */
            
            --ch-green: #00a859;            /* Verde bandeira da campanha */
            --ch-green-light: #00c86b;
            --ch-yellow-solid: #ffcc00;     /* Amarelo ouro 100% sólido e vibrante */
            --ch-white: #ffffff;
            --ch-text-dim: #c5d7f2;         /* Texto claro sobre fundo azul */
        }

        /* 1. Background Geral da Aplicação (Azul Profundo) */
        html, body, [data-testid="stAppViewContainer"], .main, [data-testid="stMainBlockContainer"] {
            background-color: var(--ch-blue-bg) !important;
            color: var(--ch-white) !important;
            font-family: 'Inter', sans-serif !important;
        }

        /* Header e decorações nativas */
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 5rem !important;
            max-width: 780px !important;
        }

        /* 2. Hero Card Superior com 22500 em Amarelo Ouro Sólido */
        .ch-hero-card {
            background: linear-gradient(135deg, #13335e 0%, #1e4782 100%);
            border: 1px solid var(--ch-blue-border);
            border-top: 4px solid var(--ch-green);
            border-radius: 18px;
            padding: 24px 26px;
            margin-bottom: 18px;
            box-shadow: 0 10px 30px rgba(10, 25, 48, 0.45);
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        }

        .ch-hero-content {
            flex: 1;
            padding-right: 18px;
            z-index: 2;
        }

        /* Número 22500 em Amarelo Ouro Puro (Opacidade 100%, sem transparência apagada) */
        .ch-watermark-number {
            font-family: 'Montserrat', sans-serif !important;
            font-size: clamp(48px, 9vw, 84px) !important;
            font-weight: 900 !important;
            color: var(--ch-yellow-solid) !important;
            opacity: 1 !important;
            letter-spacing: -2px;
            line-height: 1;
            text-shadow: 0 4px 18px rgba(0, 0, 0, 0.5), 0 0 25px rgba(255, 204, 0, 0.45);
            user-select: none;
            z-index: 2;
            text-align: right;
            white-space: nowrap;
        }

        .ch-tag-container {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
        }

        .ch-tag-pl {
            background: var(--ch-yellow-solid);
            color: #0d2242 !important;
            font-weight: 900;
            font-size: 11px;
            padding: 3px 10px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            font-family: 'Montserrat', sans-serif;
        }

        .ch-tag-number {
            background: rgba(0, 168, 89, 0.25);
            border: 1px solid var(--ch-green);
            color: #4efbb0 !important;
            font-weight: 800;
            font-size: 12px;
            padding: 3px 10px;
            border-radius: 4px;
            font-family: 'Montserrat', sans-serif;
        }

        .ch-hero-title {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 24px !important;
            font-weight: 900 !important;
            color: var(--ch-white) !important;
            margin: 0 0 6px 0 !important;
            letter-spacing: -0.5px;
            line-height: 1.2;
        }

        .ch-hero-desc {
            color: var(--ch-text-dim) !important;
            font-size: 14px;
            line-height: 1.5;
            margin: 0;
        }

        /* 3. Animação Pulsante e Borda Branca no Botão de Apoio */
        @keyframes pulse-white-glow {
            0% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.8), 0 4px 16px rgba(0, 168, 89, 0.4);
            }
            50% {
                transform: scale(1.02);
                box-shadow: 0 0 0 9px rgba(255, 255, 255, 0), 0 8px 24px rgba(0, 168, 89, 0.7);
            }
            100% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(255, 255, 255, 0), 0 4px 16px rgba(0, 168, 89, 0.4);
            }
        }

        /* Botão CTA Principal com Borda Branca Sólida e Pulsação */
        div.stButton button[kind="primary"] {
            background: linear-gradient(135deg, #00a859 0%, #008244 100%) !important;
            border: 2px solid #ffffff !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            font-size: 15px !important;
            letter-spacing: 0.4px;
            padding: 12px 22px !important;
            animation: pulse-white-glow 2.2s infinite ease-in-out !important;
            transition: all 0.25s ease !important;
        }
        div.stButton button[kind="primary"]:hover {
            transform: scale(1.04) !important;
            background: linear-gradient(135deg, #00bd64 0%, #009950 100%) !important;
            border-color: #ffffff !important;
            box-shadow: 0 0 25px rgba(255, 255, 255, 0.6) !important;
        }

        /* 4. Balões de Mensagem (Chat) em Azul */
        [data-testid="stChatMessage"] {
            padding: 14px 18px !important;
            margin-bottom: 12px !important;
            border-radius: 14px !important;
            box-shadow: 0 4px 16px rgba(10, 25, 48, 0.35) !important;
            font-size: 14.5px !important;
            line-height: 1.55 !important;
        }

        /* Mensagem do Usuário (Azul Real + Borda Amarela) */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            background: linear-gradient(135deg, #1b457e 0%, #153868 100%) !important;
            border: 1px solid var(--ch-blue-border) !important;
            border-right: 4px solid var(--ch-yellow-solid) !important;
        }

        /* Mensagem do Assistente (Azul Profundo + Borda Verde) */
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
        [data-testid="stChatMessage"]:has(img) {
            background: #14335c !important;
            border: 1px solid var(--ch-blue-border) !important;
            border-left: 4px solid var(--ch-green) !important;
        }

        /* 5. Botões de Sugestão e Botão Limpar Conversa */
        div[data-testid="stHorizontalBlock"] button[kind="secondary"],
        div.stButton button[kind="secondary"] {
            background: #163664 !important;
            color: #e2edff !important;
            border: 1px solid var(--ch-blue-border) !important;
            border-radius: 10px !important;
            font-size: 12.5px !important;
            padding: 6px 12px !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover,
        div.stButton button[kind="secondary"]:hover {
            background: #1d4580 !important;
            border-color: var(--ch-yellow-solid) !important;
            color: var(--ch-yellow-solid) !important;
            transform: translateY(-2px);
        }

        /* 6. Campo do Chat Input (Azul com foco Dourado) */
        [data-testid="stChatInput"] {
            background-color: var(--ch-blue-card) !important;
            border: 1.5px solid var(--ch-blue-border) !important;
            border-radius: 14px !important;
            box-shadow: 0 8px 24px rgba(10, 25, 48, 0.4) !important;
        }
        [data-testid="stChatInput"] textarea {
            color: var(--ch-white) !important;
            background: transparent !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: #8faecf !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--ch-yellow-solid) !important;
            box-shadow: 0 0 0 2px rgba(255, 204, 0, 0.3) !important;
        }

        /* 7. Modal / Dialog em Azul */
        [data-testid="stDialog"] {
            background-color: var(--ch-blue-card) !important;
            color: var(--ch-white) !important;
            border: 1.5px solid var(--ch-yellow-solid) !important;
            border-radius: 16px !important;
        }
        [data-testid="stDialog"] [data-testid="stForm"] {
            background-color: #122c52 !important;
            border: 1px solid var(--ch-blue-border) !important;
            border-radius: 12px !important;
            padding: 16px !important;
        }
        [data-testid="stDialog"] input {
            background-color: #0d213d !important;
            border: 1px solid var(--ch-blue-border) !important;
            color: var(--ch-white) !important;
            border-radius: 8px !important;
        }
        [data-testid="stDialog"] input:focus {
            border-color: var(--ch-green) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("🇧🇷 Cadastro Oficial de Apoiador")
def supporter_signup_dialog() -> None:
    st.markdown(
        """
        <p style='color: #c5d7f2; font-size: 14px; margin-top: -8px;'>
            Preencha seus dados para receber materiais oficiais e apoiar a caminhada do <strong>Coronel Henrique (22500)</strong> em Minas Gerais.
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("public_supporter_signup_form", clear_on_submit=False):
        first_name = st.text_input("Nome", max_chars=100, placeholder="Ex: Rodrigo")
        last_name = st.text_input("Sobrenome", max_chars=100, placeholder="Ex: Silva")
        email = st.text_input("E-mail", placeholder="nome@exemplo.com")
        whatsapp = st.text_input("WhatsApp com DDD", placeholder="(31) 99999-9999")
        consent_lgpd = st.checkbox(
            "Autorizo o contato da campanha para envio de propostas e notícias (LGPD).",
            value=True,
        )

        submitted = st.form_submit_button(
            "Concluir Cadastro",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    errors: list[str] = []
    if not first_name.strip():
        errors.append("Por favor, preencha o seu nome.")
    if not last_name.strip():
        errors.append("Por favor, preencha o seu sobrenome.")

    # Validação do e-mail
    email_ok, email_result = validate_email_address(email)
    if not email_ok:
        errors.append(f"E-mail inválido: {email_result}")

    # Validação do WhatsApp
    whatsapp_ok, whatsapp_result = validate_whatsapp(whatsapp)
    if not whatsapp_ok:
        errors.append(whatsapp_result)

    if not consent_lgpd:
        errors.append("É necessário aceitar os termos da LGPD para prosseguir.")

    if errors:
        for err in errors:
            st.error(err)
        return

    supporter_service = SupporterService()
    partner_result = supporter_service.resolve_partner_by_slug(OFFICIAL_PARTNER_SLUG)

    if not partner_result.success or not partner_result.data:
        st.error("Não foi possível validar o registro oficial no momento.")
        return

    with st.spinner("Registrando seu apoio..."):
        try:
            result = supporter_service.register_public(
                partner_id=partner_result.data["id"],
                slug=OFFICIAL_PARTNER_SLUG,
                first_name=first_name,
                last_name=last_name,
                whatsapp=whatsapp_result,
                email=email_result,
                consent_lgpd=consent_lgpd,
            )
        except TypeError:
            result = supporter_service.register_public(
                partner_id=partner_result.data["id"],
                slug=OFFICIAL_PARTNER_SLUG,
                first_name=first_name,
                last_name=last_name,
                whatsapp=whatsapp_result,
                consent_lgpd=consent_lgpd,
            )

    if not result.success:
        st.error(result.message)
        return

    st.session_state["public_chat_history"].append(
        {
            "role": "assistant",
            "content": f"Muito obrigado, **{first_name}**! Seu apoio foi registrado com sucesso. Enviamos os detalhes também para o seu e-mail **{email_result}**. Juntos por Minas Gerais! 🇧🇷",
        }
    )
    st.success("Cadastro confirmado com sucesso!")
    st.rerun()


def main() -> None:
    # 1. Configuração da página e estilos azuis institucionais
    st.set_page_config(
        page_title="Conversar com Coronel Henrique | 22500",
        page_icon="🇧🇷",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    apply_custom_styles()

    # 2. Inicialização do histórico de mensagens
    if "public_chat_history" not in st.session_state:
        st.session_state["public_chat_history"] = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Seja muito bem-vindo. Sou o assistente virtual oficial do **Coronel Henrique (22500)**.\n\n"
                    "Aqui você pode tirar dúvidas sobre projetos de lei, propostas para o agro, segurança, "
                    "escolas cívico-militares ou saber como se tornar um apoiador oficial da campanha."
                ),
            }
        ]

    # 3. Header Hero Institucional com 22500 em Amarelo Ouro Sólido à Direita
    st.markdown(
        """
        <div class="ch-hero-card">
            <div class="ch-hero-content">
                <div class="ch-tag-container">
                    <span class="ch-tag-pl">PARTIDO LIBERAL 22</span>
                    <span class="ch-tag-number">DEPUTADO ESTADUAL</span>
                </div>
                <h1 class="ch-hero-title">Coronel Henrique</h1>
                <p class="ch-hero-desc">
                    <em>Ordem e Trabalho para Proteger o Futuro de Minas Gerais</em>
                </p>
            </div>
            <!-- Número 22500 100% visível, sólido em Amarelo Ouro Oficial -->
            <div class="ch-watermark-number">22500</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. CTA Principal Superior (Destaque exclusivo com borda branca e animação pulsante)
    if st.button("🤝 Quero ser um Apoiador Oficial", type="primary", use_container_width=True):
        supporter_signup_dialog()

    # 5. Sugestões de Perguntas Rápidas (Chips)
    st.markdown(
        "<p style='color: #9cbce0; font-size: 12px; margin: 14px 0 6px 2px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Sugestões para perguntar:</p>",
        unsafe_allow_html=True,
    )
    sug_cols = st.columns(3)
    quick_prompts = [
        ("🏫 Escolas Cívico-Militares", "Como funcionam as Escolas Cívico-Militares em Minas?"),
        ("🌱 Apoio ao Produtor Rural", "Quais são as propostas do Coronel Henrique para o Agronegócio?"),
        ("🛡️ Segurança e Família", "Qual é a atuação do Coronel Henrique na segurança pública?"),
    ]

    for col, (label, prompt_text) in zip(sug_cols, quick_prompts):
        with col:
            if st.button(label, key=f"sug_{label}", use_container_width=True):
                st.session_state["pending_user_prompt"] = prompt_text

    # 6. Renderização do Histórico de Conversa
    for msg in st.session_state["public_chat_history"]:
        avatar = AVATAR_IMG if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # 7. Barra Inferior Acima do st.chat_input: Botão "Limpar Conversa"
    _, clear_col = st.columns([3, 1])
    with clear_col:
        if st.button("🗑️ Limpar Conversa", key="btn_clear_chat", use_container_width=True):
            st.session_state["public_chat_history"] = [
                {
                    "role": "assistant",
                    "content": "Conversa reiniciada. Como posso ajudar você agora?",
                }
            ]
            st.rerun()

    # 8. Captura e Processamento da Interação (st.chat_input)
    ai_service = AIService()
    user_input = st.chat_input("Pergunte sobre propostas, projetos ou como apoiar...")
    final_prompt = None

    if "pending_user_prompt" in st.session_state:
        final_prompt = st.session_state.pop("pending_user_prompt")
    elif user_input:
        final_prompt = user_input

    if final_prompt:
        # Pergunta do usuário
        st.session_state["public_chat_history"].append({"role": "user", "content": final_prompt})
        with st.chat_message("user"):
            st.markdown(final_prompt)

        # Resposta do assistente
        with st.chat_message("assistant", avatar=AVATAR_IMG):
            with st.spinner("Consultando propostas do Coronel Henrique..."):
                result = ai_service.ask_public(final_prompt)

            if result.success and result.data:
                answer = result.data.get("answer", "")
                st.markdown(answer)
                st.session_state["public_chat_history"].append({"role": "assistant", "content": answer})
            else:
                error_msg = result.message or "Desculpe, não consegui obter a resposta no momento."
                st.error(error_msg)
                st.session_state["public_chat_history"].append({"role": "assistant", "content": error_msg})

        # Abre modal se houver intenção de apoiar
        if _wants_to_become_supporter(final_prompt):
            supporter_signup_dialog()


if __name__ == "__main__":
    main()