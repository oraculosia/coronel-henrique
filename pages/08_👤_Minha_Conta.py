import streamlit as st

from src.auth.guards import require_authentication
from src.auth.session import get_profile, set_authenticated_session
from src.config.settings import settings
from src.services.auth_service import AuthService
from src.utils.formatting import resolve_avatar_path, role_label
from src.utils.uploads import validate_and_save_image
from src.utils.validators import validate_password, validate_whatsapp


st.set_page_config(
    page_title="Minha Conta | Campanha 2026",
    page_icon="👤",
    layout="centered",
)

require_authentication()

profile = get_profile() or {}
access_token = st.session_state.get("access_token")
refresh_token = st.session_state.get("refresh_token")

st.title("👤 Minha conta")
st.caption(
    "Atualize seus dados pessoais. O papel de autorização não pode ser "
    "alterado nesta tela."
)

current_avatar = resolve_avatar_path(profile)

st.markdown("#### Foto de perfil")
avatar_col, uploader_col = st.columns([1, 3], vertical_alignment="center")

new_photo = uploader_col.file_uploader(
    "Nova foto (opcional)",
    type=["png", "jpg", "jpeg", "webp"],
    key="account_avatar_uploader",
)

with avatar_col:
    with st.container(key="account_avatar_preview"):
        if new_photo is not None:
            st.image(new_photo, width=110)
        elif current_avatar:
            st.image(current_avatar, width=110)
        else:
            st.markdown(
                '<div class="sidebar-avatar-fallback">🧑</div>',
                unsafe_allow_html=True,
            )

if new_photo is not None:
    uploader_col.caption("Pré-visualização da nova foto — salve para confirmar.")

st.divider()

with st.form("account_form"):
    first_name = st.text_input(
        "Nome",
        value=profile.get("first_name") or "",
        max_chars=100,
    )
    last_name = st.text_input(
        "Sobrenome",
        value=profile.get("last_name") or "",
        max_chars=100,
    )
    st.text_input(
        "E-mail",
        value=profile.get("email") or "",
        disabled=True,
        help="O e-mail é a identidade do Auth e não é editável nesta fase.",
    )
    whatsapp = st.text_input(
        "WhatsApp",
        value=profile.get("whatsapp") or "",
        placeholder="(31) 99999-9999",
    )
    job_title = st.text_input(
        "Cargo",
        value=profile.get("job_title") or "",
        max_chars=120,
        help="Cargo profissional. Não substitui o papel de autorização.",
    )
    st.text_input(
        "Tipo de acesso",
        value=role_label(profile.get("role")),
        disabled=True,
        help="Definido pela administração. O cargo acima é o que aparece para outros usuários.",
    )

    st.divider()
    st.caption("Opcional — altere a senha somente se quiser trocá-la agora.")
    new_password = st.text_input("Nova senha", type="password")
    new_password_confirmation = st.text_input(
        "Confirmar nova senha",
        type="password",
    )

    submitted = st.form_submit_button(
        "Salvar alterações",
        type="primary",
        use_container_width=True,
    )

if submitted:
    errors: list[str] = []

    if not first_name.strip():
        errors.append("Informe seu nome.")

    if not last_name.strip():
        errors.append("Informe seu sobrenome.")

    whatsapp_result = ""
    if whatsapp.strip():
        whatsapp_ok, whatsapp_result = validate_whatsapp(whatsapp)
        if not whatsapp_ok:
            errors.append(whatsapp_result)

    if new_password or new_password_confirmation:
        password_ok, password_message = validate_password(new_password)
        if not password_ok:
            errors.append(password_message)
        elif new_password != new_password_confirmation:
            errors.append("A confirmação da nova senha não corresponde.")

    if errors:
        for error in errors:
            st.error(error)
    else:
        avatar_path = current_avatar or ""
        if new_photo is not None:
            photo_ok, photo_result = validate_and_save_image(
                new_photo, settings.PROFILE_IMAGE_DIR
            )
            if not photo_ok:
                st.error(photo_result)
                st.stop()
            avatar_path = photo_result

        service = AuthService()
        result = service.update_own_profile(
            access_token=access_token,
            user_id=profile["id"],
            first_name=first_name,
            last_name=last_name,
            whatsapp=whatsapp_result,
            job_title=job_title.strip(),
            avatar_path=avatar_path or None,
        )

        if not result.success:
            st.error(result.message)
        else:
            if new_password:
                password_result = service.update_own_password(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    password=new_password,
                )
                if not password_result.success:
                    st.warning(password_result.message)

            updated = result.data or {}
            set_authenticated_session(
                access_token=access_token,
                refresh_token=refresh_token,
                profile=updated,
            )
            st.success("Dados da conta atualizados.")
            st.rerun()
