import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from slugify import slugify
from supabase_auth.errors import AuthApiError

from src.database.supabase_client import get_supabase, get_supabase_admin
from src.services.activity_log_service import log_activity
from src.services.notification import Notificador
from src.utils.validators import normalize_email

VERIFICATION_CODE_TTL_MINUTES = 10


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
        job_title: str = "",
        avatar_path: str = "",
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
                            "job_title": job_title.strip(),
                            "avatar_path": avatar_path,
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
                    "access_token": (
                        response.session.access_token if response.session else None
                    ),
                    "refresh_token": (
                        response.session.refresh_token if response.session else None
                    ),
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

    def send_verification_code(
        self, user_id: str, email: str, first_name: str
    ) -> ServiceResult:
        """Gera um código próprio (não usa o e-mail do Supabase) e o envia por SMTP."""
        try:
            code = self._generate_and_store_code(user_id)
            Notificador().enviar_codigo_verificacao(
                destino=normalize_email(email),
                nome=first_name,
                codigo=code,
            )

            return ServiceResult(
                success=True,
                message="Enviamos um código de confirmação para o seu e-mail.",
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Não foi possível enviar o e-mail de verificação. "
                    "Use o botão de reenviar na tela seguinte."
                ),
            )

    def verify_own_code(self, email: str, code: str) -> ServiceResult:
        """Valida o código de verificação próprio e marca o perfil como verificado."""
        try:
            admin = get_supabase_admin()
            normalized_email = normalize_email(email)

            profile_response = (
                admin.table("profiles")
                .select("id, first_name, last_name")
                .eq("email", normalized_email)
                .single()
                .execute()
            )

            if not profile_response.data:
                return ServiceResult(
                    success=False,
                    message="Não encontramos um cadastro para este e-mail.",
                )

            user_id = profile_response.data["id"]

            code_response = (
                admin.table("email_verification_codes")
                .select("id, code_hash, expires_at, consumed_at")
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            rows = code_response.data or []

            if not rows or rows[0]["consumed_at"]:
                return ServiceResult(
                    success=False,
                    message="Código inválido ou expirado. Solicite um novo.",
                )

            row = rows[0]
            expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))

            if datetime.now(timezone.utc) > expires_at:
                return ServiceResult(
                    success=False,
                    message="Código expirado. Solicite um novo.",
                )

            if row["code_hash"] != self._hash_code(code):
                return ServiceResult(
                    success=False,
                    message="Código inválido ou expirado. Solicite um novo.",
                )

            now_iso = datetime.now(timezone.utc).isoformat()
            admin.table("email_verification_codes").update(
                {"consumed_at": now_iso}
            ).eq("id", row["id"]).execute()
            admin.table("profiles").update({"verification_status": "verified"}).eq(
                "id", user_id
            ).execute()

            self._ensure_partner_link(
                admin,
                user_id=user_id,
                first_name=profile_response.data.get("first_name") or "",
                last_name=profile_response.data.get("last_name") or "",
            )

            return ServiceResult(
                success=True,
                message="E-mail confirmado com sucesso.",
                data={"user_id": user_id, "email": normalized_email},
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Não foi possível validar o código. "
                    "Tente novamente em alguns instantes."
                ),
            )

    def resend_own_code(self, email: str) -> ServiceResult:
        """Gera e envia um novo código de verificação próprio."""
        try:
            admin = get_supabase_admin()
            normalized_email = normalize_email(email)

            profile_response = (
                admin.table("profiles")
                .select("id, first_name, verification_status")
                .eq("email", normalized_email)
                .single()
                .execute()
            )

            if not profile_response.data:
                return ServiceResult(
                    success=False,
                    message="Não encontramos um cadastro para este e-mail.",
                )

            profile = profile_response.data

            if profile.get("verification_status") == "verified":
                return ServiceResult(
                    success=False,
                    message="Este e-mail já está confirmado. Faça login.",
                )

            code = self._generate_and_store_code(profile["id"])
            Notificador().enviar_codigo_verificacao(
                destino=normalized_email,
                nome=profile.get("first_name") or "",
                codigo=code,
            )

            return ServiceResult(
                success=True,
                message="Reenviamos o código de confirmação para o seu e-mail.",
            )

        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Não foi possível reenviar o código. "
                    "Tente novamente em alguns instantes."
                ),
            )

    @staticmethod
    def _hash_code(code: str) -> str:
        return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()

    def _generate_and_store_code(self, user_id: str) -> str:
        """Gera um código de 6 dígitos, grava só o hash e invalida códigos antigos."""
        admin = get_supabase_admin()
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=VERIFICATION_CODE_TTL_MINUTES
        )

        admin.table("email_verification_codes").delete().eq(
            "user_id", user_id
        ).execute()
        admin.table("email_verification_codes").insert(
            {
                "user_id": user_id,
                "code_hash": self._hash_code(code),
                "expires_at": expires_at.isoformat(),
            }
        ).execute()

        return code

    @staticmethod
    def _ensure_partner_link(admin, user_id: str, first_name: str, last_name: str) -> None:
        """Cria o registro em partners assim que o parceiro confirma o e-mail.

        Silencioso em caso de falha: o vínculo pode ser feito manualmente por
        um admin depois, e isso não deve derrubar a confirmação do e-mail.
        """
        try:
            existing = (
                admin.table("partners").select("id").eq("id", user_id).limit(1).execute()
            )
            if existing.data:
                return

            base_slug = slugify(f"{first_name} {last_name}".strip()) or "parceiro"
            candidate = base_slug
            suffix = 1
            while (
                admin.table("partners")
                .select("id")
                .eq("public_slug", candidate)
                .limit(1)
                .execute()
            ).data:
                suffix += 1
                candidate = f"{base_slug}-{suffix}"

            admin.table("partners").insert(
                {
                    "id": user_id,
                    "public_slug": candidate,
                    "is_accepting_supporters": True,
                    "created_by": user_id,
                }
            ).execute()
        except Exception:
            pass

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
                    job_title,
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

    def update_own_profile(
        self,
        access_token: str,
        user_id: str,
        first_name: str,
        last_name: str,
        whatsapp: str,
        job_title: str,
        avatar_path: str | None = None,
    ) -> ServiceResult:
        try:
            user_client = get_supabase()
            user_client.postgrest.auth(access_token)

            payload = {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "whatsapp": whatsapp or None,
                "job_title": job_title.strip() or None,
            }
            if avatar_path is not None:
                payload["avatar_path"] = avatar_path or None

            response = (
                user_client.table("profiles")
                .update(payload)
                .eq("id", user_id)
                .execute()
            )

            if not response.data:
                return ServiceResult(
                    success=False,
                    message="Não foi possível atualizar o perfil.",
                )

            return self.get_profile(user_id=user_id, access_token=access_token)

        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível salvar os dados da conta.",
            )

    def update_own_password(
        self,
        access_token: str,
        refresh_token: str,
        password: str,
    ) -> ServiceResult:
        try:
            user_client = get_supabase()
            user_client.auth.set_session(access_token, refresh_token)
            user_client.auth.update_user({"password": password})
            return ServiceResult(
                success=True,
                message="Senha atualizada.",
            )
        except Exception:
            return ServiceResult(
                success=False,
                message=(
                    "Os dados do perfil foram salvos, mas a senha "
                    "não pôde ser alterada agora."
                ),
            )

    def list_all_profiles(self, access_token: str) -> ServiceResult:
        """Todos os perfis do sistema, para a gestão de usuários do
        super_admin. Só admin/super_admin (policy profiles_staff_manage)."""
        try:
            user_client = get_supabase()
            user_client.postgrest.auth(access_token)

            response = (
                user_client.table("profiles")
                .select(
                    "id, first_name, last_name, email, role, is_active, "
                    "verification_status, created_at"
                )
                .order("created_at", desc=True)
                .execute()
            )
            return ServiceResult(success=True, message="ok", data=response.data or [])
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar os usuários.",
                data=[],
            )

    def list_auth_login_status(self) -> ServiceResult:
        """Último login (last_sign_in_at) de cada usuário via Auth Admin API.

        Usa service_role — só deve ser chamado a partir de uma página já
        protegida por require_roles("super_admin").
        """
        try:
            admin = get_supabase_admin()
            listed = admin.auth.admin.list_users()
            users = getattr(listed, "users", listed) or []
            status = {
                str(user.id): getattr(user, "last_sign_in_at", None)
                for user in users
            }
            return ServiceResult(success=True, message="ok", data=status)
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível carregar o status de login.",
                data={},
            )

    def set_profile_active_status(
        self,
        access_token: str,
        actor_id: str,
        user_id: str,
        is_active: bool,
    ) -> ServiceResult:
        """Ativa/desativa uma conta. Só admin/super_admin (policy
        profiles_staff_manage). Um usuário desativado não consegue mais
        logar (bloqueado em pages/05_🔐_Login.py)."""
        try:
            user_client = get_supabase()
            user_client.postgrest.auth(access_token)

            response = (
                user_client.table("profiles")
                .update({"is_active": is_active})
                .eq("id", user_id)
                .execute()
            )

            if not response.data:
                return ServiceResult(
                    success=False,
                    message="Não foi possível atualizar o usuário.",
                )

            log_activity(
                user_client,
                actor_id=actor_id,
                entity_type="profile",
                action="activated" if is_active else "deactivated",
                entity_id=user_id,
            )

            return ServiceResult(
                success=True,
                message="Usuário ativado." if is_active else "Usuário desativado.",
                data=response.data[0],
            )
        except Exception:
            return ServiceResult(
                success=False,
                message="Não foi possível atualizar o usuário.",
            )