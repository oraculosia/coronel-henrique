USER_ROLES = (
    "super_admin",
    "admin",
    "parceiro",
    "apoiador",
)

# Rótulos amigáveis para exibir ao usuário — nunca mostrar o termo técnico
# do enum (ex.: "super_admin") diretamente na interface.
ROLE_LABELS = {
    "super_admin": "Administração",
    "admin": "Administração",
    "parceiro": "Parceiro(a)",
    "apoiador": "Apoiador(a)",
}

VERIFICATION_STATUS = (
    "pending",
    "verified",
    "blocked",
    "rejected",
)

ALLOWED_IMAGE_EXTENSIONS = (
    "png",
    "jpg",
    "jpeg",
    "webp",
)