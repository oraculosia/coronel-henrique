from dataclasses import dataclass
from typing import Any

from gotrue.errors import AuthApiError

from src.database.supabase_client import get_supabase
from src.utils.validators import normalize_email


@dataclass
class ServiceResult:
    success: bool
    message: str
    data: dict[str, Any] | None = None


class AuthService:
    def __init__(self) -> None:
        self.client = get_supabase()

    def sign_up(
        self,
        first_name: str,
        last_name: str,
        email: str,
        whatsapp: str,
        password: str,
    ) -> ServiceResult:
        try:
            response = self.client.auth.sign_up(
                {
                    "email": normalize_email(email),
                    "password": password,
                    "options": {
                        "data": {
                            "first_name": first_name.strip(),
                            "last_name": last_name.strip(),
                            "whatsapp": whatsapp,
                        },
                    },
                }
            )

            if not response.user:
                return ServiceResult(
                    success=False,
                    message=(
                        "Não foi possível criar a conta. "
                        "Verifique os dados e tente novamente."
                    ),
                )

            return ServiceResult(
                success=True,
                message=(
                    "Conta criada. Enviamos um código de confirmação "
                    "para seu e-mail."
                ),
                data={
                    "user_id": str(response.user.id),
                    "email": normalize_email(email),
                    "session_exists": response.session is not None,
                },
            )

        except AuthApiError as error:
            error_message = str(error)

            if "already registered" in error_message.lower():
                error_message = "Este e-mail já possui cadastro."

            return ServiceResult(
                success=False,
                message=error_message,
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Ocorreu um erro inesperado ao criar a conta. "
                    "Verifique a configuração do Supabase."
                ),
            )

    def verify_signup_otp(self, email: str, token: str) -> ServiceResult:
        try:
            response = self.client.auth.verify_otp(
                {
                    "email": normalize_email(email),
                    "token": token.strip(),
                    "type": "email",
                }
            )

            if not response.user or not response.session:
                return ServiceResult(
                    success=False,
                    message=(
                        "Não foi possível validar o código. "
                        "Solicite um novo cadastro, se necessário."
                    ),
                )

            return ServiceResult(
                success=True,
                message="E-mail confirmado com sucesso.",
                data={
                    "user_id": str(response.user.id),
                    "email": response.user.email,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                },
            )

        except AuthApiError as error:
            return ServiceResult(
                success=False,
                message=(
                    "Código inválido ou expirado. "
                    f"Detalhe: {str(error)}"
                ),
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Não foi possível validar o código. "
                    "Tente novamente em alguns instantes."
                ),
            )

    def sign_in(self, email: str, password: str) -> ServiceResult:
        try:
            response = self.client.auth.sign_in_with_password(
                {
                    "email": normalize_email(email),
                    "password": password,
                }
            )

            if not response.user or not response.session:
                return ServiceResult(
                    success=False,
                    message="E-mail ou senha inválidos.",
                )

            return ServiceResult(
                success=True,
                message="Login realizado com sucesso.",
                data={
                    "user_id": str(response.user.id),
                    "email": response.user.email,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                },
            )

        except AuthApiError:
            return ServiceResult(
                success=False,
                message="E-mail ou senha inválidos, não confirmados ou bloqueados.",
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Não foi possível realizar login. "
                    "Confira a conexão com o Supabase."
                ),
            )

    def get_profile(self, user_id: str, access_token: str) -> ServiceResult:
        try:
            user_client = get_supabase()

            user_client.postgrest.auth(access_token)

            response = (
                user_client.table("profiles")
                .select(
                    """
                    id,
                    first_name,
                    last_name,
                    email,
                    whatsapp,
                    avatar_path,
                    role,
                    verification_status,
                    is_active
                    """
                )
                .eq("id", user_id)
                .single()
                .execute()
            )

            if not response.data:
                return ServiceResult(
                    success=False,
                    message="Perfil não encontrado para este usuário.",
                )

            return ServiceResult(
                success=True,
                message="Perfil carregado.",
                data=response.data,
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Não foi possível carregar seu perfil. "
                    "Tente entrar novamente."
                ),
            )