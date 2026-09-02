"""Envio de e-mails transacionais via SMTP próprio (Hostinger).

Não usa o serviço de e-mail do Supabase Auth — o código de verificação de
cadastro é gerado pela aplicação (ver AuthService) e enviado por aqui.
"""
import base64
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.config.settings import settings

_LOGO_PATH = Path("assets/images/logo_coronel_henrique.png")


def _get_logo_base64() -> str:
    if _LOGO_PATH.exists():
        return base64.b64encode(_LOGO_PATH.read_bytes()).decode()
    return ""


def _email_base_template(content: str) -> str:
    logo_b64 = _get_logo_base64()

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background-color:#001f3f;font-family:'Segoe UI',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#001f3f;padding:20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
                        <tr>
                            <td align="center" style="padding:30px 20px;">
                                <img src="data:image/png;base64,{logo_b64}"
                                     alt="Campanha 2026"
                                     style="width:96px;height:96px;border-radius:50%;box-shadow:0 0 30px rgba(246,197,0,0.35);">
                            </td>
                        </tr>
                        <tr>
                            <td style="background:linear-gradient(145deg,#001f3f,#003b73);border-radius:20px;padding:40px 30px;border:1px solid rgba(246,197,0,0.25);box-shadow:0 10px 40px rgba(0,0,0,0.3);">
                                {content}
                            </td>
                        </tr>
                        <tr>
                            <td align="center" style="padding:30px 20px;">
                                <p style="margin:0;color:#8aa0b8;font-size:12px;">
                                    © 2026 Campanha 2026 — Coronel Henrique
                                </p>
                                <p style="margin:8px 0 0;color:#5b7085;font-size:11px;">
                                    Este é um e-mail automático. Por favor, não responda.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


class Notificador:
    """Cliente SMTP para envio de e-mails transacionais da Campanha 2026."""

    def __init__(self) -> None:
        self.email_host = settings.EMAIL_HOST
        self.email_port = settings.EMAIL_PORT
        self.email_username = settings.EMAIL_USERNAME
        self.email_password = settings.EMAIL_PASSWORD
        self.email_use_tls = settings.EMAIL_USE_TLS
        self.email_use_ssl = settings.EMAIL_USE_SSL
        self.email_remetente = settings.EMAIL_REMETENTE
        self._validar_variaveis()

    def _validar_variaveis(self) -> None:
        faltantes = []
        if not self.email_host:
            faltantes.append("EMAIL_HOST")
        if not self.email_port:
            faltantes.append("EMAIL_PORT")
        if not self.email_username:
            faltantes.append("EMAIL_USERNAME")
        if not self.email_password:
            faltantes.append("EMAIL_PASSWORD")
        if not self.email_remetente:
            faltantes.append("EMAIL_REMETENTE")
        if self.email_use_ssl and self.email_use_tls:
            faltantes.append("EMAIL_USE_TLS/EMAIL_USE_SSL (use apenas um)")
        if faltantes:
            raise ValueError(
                "Variáveis obrigatórias ausentes para SMTP: " + ", ".join(faltantes)
            )

    def _conectar_smtp(self):
        if self.email_use_ssl:
            server = smtplib.SMTP_SSL(
                self.email_host,
                self.email_port,
                context=ssl.create_default_context(),
                timeout=30,
            )
        else:
            server = smtplib.SMTP(self.email_host, self.email_port, timeout=30)
            if self.email_use_tls:
                server.starttls(context=ssl.create_default_context())

        server.login(self.email_username, self.email_password)
        return server

    def enviar_email(self, destino: str, assunto: str, mensagem: str) -> dict:
        if not destino:
            raise ValueError("Destino do e-mail é obrigatório.")

        email = MIMEMultipart("alternative")
        email["to"] = destino
        email["from"] = self.email_remetente
        email["subject"] = assunto
        email.attach(MIMEText(mensagem, "html", "utf-8"))

        with self._conectar_smtp() as server:
            server.sendmail(self.email_remetente, [destino], email.as_string())

        return {
            "status": "sent",
            "provider": "smtp",
            "to": destino,
            "subject": assunto,
        }

    def enviar_codigo_verificacao(self, destino: str, nome: str, codigo: str) -> dict:
        """Envia o código de verificação de 6 dígitos para ativar a conta."""
        primeiro_nome = nome.split(" ")[0] if nome else "Parceiro"

        content = f"""
        <div style="text-align:center;margin-bottom:30px;">
            <h1 style="color:#f6c500;margin:0;font-size:26px;font-weight:700;">
                Verificação de e-mail
            </h1>
            <p style="color:#c7d6e6;margin:12px 0 0;font-size:15px;">
                Estamos quase lá! Só mais um passo para ativar sua conta na Campanha 2026
            </p>
        </div>

        <div style="background:rgba(246,197,0,0.06);border-radius:16px;padding:30px 20px;margin-bottom:25px;text-align:center;">
            <p style="color:#eef4fb;font-size:16px;margin:0 0 10px;">
                Olá, <strong style="color:#f6c500;">{primeiro_nome}</strong>!
            </p>
            <p style="color:#9fb2c6;font-size:14px;margin:0 0 25px;">
                Use o código abaixo para confirmar seu e-mail e ativar seu acesso
            </p>

            <div style="background:linear-gradient(145deg,#001f3f,#0d2b4d);border:2px solid rgba(246,197,0,0.5);border-radius:16px;padding:25px;display:inline-block;box-shadow:0 0 30px rgba(246,197,0,0.15);">
                <span style="font-size:36px;font-weight:800;letter-spacing:12px;color:#f6c500;font-family:'Courier New',monospace;">
                    {codigo}
                </span>
            </div>

            <p style="color:#6b7fa0;font-size:12px;margin:20px 0 0;">
                ⏱️ Este código expira em 10 minutos
            </p>
        </div>

        <div style="border-top:1px solid rgba(246,197,0,0.15);padding-top:20px;text-align:center;">
            <p style="color:#6b7fa0;font-size:12px;margin:0 0 8px;">
                🔒 Nunca compartilhe este código com ninguém.
            </p>
            <p style="color:#4b5f78;font-size:11px;margin:0;">
                Se você não solicitou este cadastro, ignore este e-mail.
            </p>
        </div>
        """

        mensagem = _email_base_template(content)

        return self.enviar_email(
            destino=destino,
            assunto="🔐 Campanha 2026 — Código de Verificação",
            mensagem=mensagem,
        )

    def testar_envio(self, destino: str) -> dict:
        """Envio de teste manual para validar a configuração SMTP."""
        content = """
        <div style="text-align:center;margin-bottom:10px;">
            <h1 style="color:#f6c500;margin:0;font-size:24px;">✅ Teste de E-mail</h1>
        </div>
        <div style="background:rgba(246,197,0,0.06);border-radius:12px;padding:20px;text-align:center;">
            <p style="color:#eef4fb;font-size:16px;margin:0 0 10px;">Parabéns! 🎉</p>
            <p style="color:#9fb2c6;font-size:14px;margin:0;">
                Se você recebeu esta mensagem, a integração SMTP da Campanha 2026 está funcionando.
            </p>
        </div>
        """

        mensagem = _email_base_template(content)

        return self.enviar_email(
            destino=destino,
            assunto="✅ Campanha 2026 — Teste de E-mail",
            mensagem=mensagem,
        )
