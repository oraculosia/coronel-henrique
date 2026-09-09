"""Transforma o bot do Telegram (@coronel_henrique_bot) num canal de
perguntas e respostas via IA.

DECISÃO DE SEGURANÇA: as respostas usam SEMPRE o modo PÚBLICO do
Assistente IA (o mesmo de pages/11_💬_Fale_com_a_Campanha.py — só conteúdo
institucional + knowledge_documents públicos). Não há como associar com
segurança um chat_id do Telegram a uma sessão autenticada real do
Supabase (parceiro/admin/super_admin) sem guardar tokens de usuário fora
do controle do Streamlit — isso abriria brecha de personificação
(qualquer um que descobrisse o chat_id de um parceiro teria acesso aos
dados dele). Se no futuro for necessário liberar dados internos via
Telegram, é preciso um fluxo de vinculação explícito (ex.: código de
verificação enviado no app, parecido com o e-mail) antes de confiar no
chat_id sozinho.

Usa long-polling (getUpdates) em vez de webhook — não exige endpoint
HTTP público, o que o Streamlit Cloud não oferece nativamente.
"""
import html
import logging
import re
import threading
import time

from src.config.settings import settings
from src.services.ai_service import AIService
from src.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

_MAX_TELEGRAM_MESSAGE_CHARS = 4000
_ERROR_RETRY_SECONDS = 5
_WELCOME_TEXT = (
    "👋 <b>Bem-vindo(a) à Campanha do Coronel Henrique (22500)!</b>\n\n"
    "Sou o assistente virtual oficial. Pode perguntar sobre os projetos, "
    "propostas ou como apoiar a campanha!"
)

# O Assistente IA usa markdown (**negrito**) pra titulos/subtitulos — funciona
# direto no chat web (pages/11, renderizado via st.markdown), mas o Telegram
# usa parse_mode HTML e mostraria os asteriscos literalmente. Por isso
# escapamos primeiro (protege contra <, > e & quebrando o HTML) e só depois
# convertemos **negrito**/*italico* pras tags reais.
_BOLD_MARKDOWN_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_MARKDOWN_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def format_for_telegram(text: str) -> str:
    """Converte a resposta em markdown do Assistente IA pra HTML do Telegram
    (negrito em titulos/subtitulos, itálico e ícones/emojis preservados)."""
    escaped = html.escape(text)
    escaped = _BOLD_MARKDOWN_RE.sub(r"<b>\1</b>", escaped)
    escaped = _ITALIC_MARKDOWN_RE.sub(r"<i>\1</i>", escaped)
    return escaped


def _answer_and_reply(telegram: TelegramService, ai_service: AIService, chat_id: str, text: str) -> None:
    result = ai_service.ask_public(text)

    if not result.success:
        telegram.send_message(
            chat_id, "⚠️ Não consegui responder agora, tente novamente em instantes."
        )
        return

    answer = ((result.data or {}).get("answer") or "").strip()
    if not answer:
        answer = "Desculpe, não consegui gerar uma resposta agora."

    formatted = format_for_telegram(answer)[:_MAX_TELEGRAM_MESSAGE_CHARS]
    telegram.send_message(chat_id, formatted)


def _process_update(telegram: TelegramService, ai_service: AIService, update: dict) -> None:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if not text or chat_id is None:
        return

    if text.startswith("/start"):
        telegram.send_message(str(chat_id), _WELCOME_TEXT)
        return

    _answer_and_reply(telegram, ai_service, str(chat_id), text)


def run_polling_loop() -> None:
    """Roda para sempre (chamar sempre dentro de uma thread daemon)."""
    telegram = TelegramService()
    ai_service = AIService()
    telegram.delete_webhook()

    offset: int | None = None

    while True:
        try:
            result = telegram.get_updates(offset=offset, timeout=25)
            if not result.success:
                logger.warning("Falha ao buscar updates do Telegram: %s", result.message)
                time.sleep(_ERROR_RETRY_SECONDS)
                continue

            for update in result.data or []:
                offset = update["update_id"] + 1
                try:
                    _process_update(telegram, ai_service, update)
                except Exception:
                    logger.exception("Erro processando update do Telegram: %s", update)

        except Exception:
            logger.exception("Erro no loop de polling do Telegram")
            time.sleep(_ERROR_RETRY_SECONDS)


def start_background_polling() -> None:
    """Inicia o loop numa thread daemon, só se a feature estiver habilitada
    (TELEGRAM_BOT_POLLING_ENABLED=true) e o bot configurado."""
    if not settings.TELEGRAM_BOT_POLLING_ENABLED or not settings.TELEGRAM_BOT_TOKEN:
        return

    thread = threading.Thread(target=run_polling_loop, daemon=True, name="telegram-bot-polling")
    thread.start()
