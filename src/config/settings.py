from pathlib import Path
import os

from dotenv import load_dotenv

from src.config.env import getenv_aliased, validate_foundation_settings

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class Settings:
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_NAME = os.getenv("APP_NAME", "Campanha 2026")
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8501")

    SUPABASE_URL = getenv_aliased("SUPABASE_URL")
    SUPABASE_PUBLISHABLE_KEY = getenv_aliased("SUPABASE_PUBLISHABLE_KEY")
    SUPABASE_SERVICE_ROLE_KEY = getenv_aliased("SUPABASE_SERVICE_ROLE_KEY")

    SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "")
    SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "")
    SUPER_ADMIN_FIRST_NAME = os.getenv("SUPER_ADMIN_FIRST_NAME", "William")
    SUPER_ADMIN_LAST_NAME = os.getenv("SUPER_ADMIN_LAST_NAME", "Eustáquio")
    SUPER_ADMIN_WHATSAPP = os.getenv("SUPER_ADMIN_WHATSAPP", "31998417976")
    SUPER_ADMIN_JOB_TITLE = os.getenv(
        "SUPER_ADMIN_JOB_TITLE",
        "Desenvolvedor de IA",
    )

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "")

    USUARIO_AGENTE = os.getenv("USUARIO_AGENTE", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")

    PROFILE_IMAGE_DIR = ROOT_DIR / os.getenv(
        "PROFILE_IMAGE_DIR",
        "src/images/usuarios",
    )
    SUPPORTER_IMAGE_DIR = ROOT_DIR / os.getenv(
        "SUPPORTER_IMAGE_DIR",
        "src/images/apoiadores",
    )
    MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "3"))

    # E-mail transacional (SMTP) — usado por src/services/notification.py
    # para enviar o código de verificação próprio (não usa o e-mail do Supabase).
    EMAIL_HOST = os.getenv("EMAIL_HOST", "")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").strip().lower() == "true"
    EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").strip().lower() == "true"
    EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "")

    def foundation_errors(self) -> list[str]:
        return validate_foundation_settings(
            supabase_url=self.SUPABASE_URL,
            publishable_key=self.SUPABASE_PUBLISHABLE_KEY,
            service_role_key=self.SUPABASE_SERVICE_ROLE_KEY,
        )


settings = Settings()