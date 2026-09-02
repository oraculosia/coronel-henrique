import streamlit as st

from src.auth.guards import require_authentication
from src.auth.session import get_profile, set_authenticated_session
from src.services.auth_service import AuthService
from src.utils.formatting import role_label
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
        service = AuthService()
        result = service.update_own_profile(
            access_token=access_token,
            user_id=profile["id"],
            first_name=first_name,
            last_name=last_name,
            whatsapp=whatsapp_result,
            job_title=job_title.strip(),
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
