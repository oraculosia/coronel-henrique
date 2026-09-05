from unittest.mock import MagicMock

import pytest

from src.services.notification import Notificador


@pytest.fixture
def notificador(monkeypatch) -> Notificador:
    monkeypatch.setattr(
        "src.services.notification.settings.EMAIL_HOST", "smtp.example.com"
    )
    monkeypatch.setattr("src.services.notification.settings.EMAIL_PORT", 587)
    monkeypatch.setattr("src.services.notification.settings.EMAIL_USERNAME", "user")
    monkeypatch.setattr("src.services.notification.settings.EMAIL_PASSWORD", "pass")
    monkeypatch.setattr("src.services.notification.settings.EMAIL_USE_TLS", True)
    monkeypatch.setattr("src.services.notification.settings.EMAIL_USE_SSL", False)
    monkeypatch.setattr(
        "src.services.notification.settings.EMAIL_REMETENTE", "campanha@example.com"
    )
    return Notificador()


def test_enviar_boas_vindas_apoiador_replaces_placeholders_and_keeps_video(
    monkeypatch, notificador: Notificador
) -> None:
    monkeypatch.setattr(
        "src.services.notification.settings.WELCOME_EMAIL_VIDEO_URL",
        "https://app.example.com/app/static/video.mp4",
    )
    monkeypatch.setattr(
        "src.services.notification.settings.WELCOME_EMAIL_VIDEO_THUMBNAIL_URL",
        "https://app.example.com/app/static/video-thumbnail.jpg",
    )

    sent = MagicMock(return_value={"status": "sent"})
    monkeypatch.setattr(notificador, "enviar_email", sent)

    notificador.enviar_boas_vindas_apoiador(
        destino="ana@example.com",
        nome_apoiador="Ana Silva",
        nome_parceiro="Padaria do João",
        link_cadastro_parceiro="https://app.example.com/apoiar?p=padaria",
    )

    sent.assert_called_once()
    html = sent.call_args.kwargs["mensagem"]

    assert "{{" not in html
    assert "Ana" in html
    assert "Padaria do João" in html
    assert "https://app.example.com/apoiar?p=padaria" in html
    assert "https://app.example.com/app/static/video.mp4" in html
    assert "data:image/png;base64," in html


def test_enviar_boas_vindas_apoiador_strips_video_section_without_config(
    monkeypatch, notificador: Notificador
) -> None:
    monkeypatch.setattr(
        "src.services.notification.settings.WELCOME_EMAIL_VIDEO_URL", ""
    )
    monkeypatch.setattr(
        "src.services.notification.settings.WELCOME_EMAIL_VIDEO_THUMBNAIL_URL", ""
    )

    sent = MagicMock(return_value={"status": "sent"})
    monkeypatch.setattr(notificador, "enviar_email", sent)

    notificador.enviar_boas_vindas_apoiador(
        destino="ana@example.com",
        nome_apoiador="Ana Silva",
        nome_parceiro="Padaria do João",
        link_cadastro_parceiro="https://app.example.com/apoiar?p=padaria",
    )

    html = sent.call_args.kwargs["mensagem"]

    assert "{{" not in html
    assert "VIDEO_SECTION" not in html
    assert "Mensagem Exclusiva em Vídeo" not in html
