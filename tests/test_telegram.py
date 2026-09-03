from datetime import datetime, timezone
from src.services.telegram_service import TelegramService


def run_tests() -> None:
    service = TelegramService()

    print("--- Testando envio de novo apoiador para admin ---")
    res1 = service.notify_new_supporter(
        partner_id="uuid-fake-partner",
        partner_label="Liderança Betim",
        supporter_id="supporter-123",
        first_name="Carlos",
        last_name="Eduardo Silva",
        phone="(31) 98765-4321",
        created_at=datetime.now(timezone.utc),
    )
    print(f"Resultado: {res1}\n")

    print("--- Testando alerta de aproximação de meta ---")
    res2 = service.notify_goal_progress(
        partner_id="uuid-fake-partner",
        partner_label="Liderança Betim",
        current_count=42,
        target_count=50,
    )
    print(f"Resultado: {res2}\n")

    print("--- Testando cadastro de novo parceiro ---")
    res3 = service.notify_new_partner_onboarded(
        partner_name="Comitê Regional Centro",
        email="contato@comite.org",
        phone="(31) 99999-8888",
        city="Betim / MG",
    )
    print(f"Resultado: {res3}\n")

    print("--- Testando resumo diário ---")
    res4 = service.notify_daily_summary(
        summary_date=None,
        total_supporters=138,
        active_partners_count=7,
        top_partners=[
            {"name": "Liderança Betim", "count": 50},
            {"name": "Comitê Norte", "count": 34},
            {"name": "Equipe Sul", "count": 22},
        ],
    )
    print(f"Resultado: {res4}\n")

    print("--- Testando alerta de erro do sistema ---")
    res5 = service.notify_system_error(
        service_name="Supabase Webhook",
        error_message="Falha de autenticação ao processar webhook de pagamento",
        details="HTTP 401 Unauthorized: Invalid API Key provided in headers.",
    )
    print(f"Resultado: {res5}\n")


if __name__ == "__main__":
    run_tests()
