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

# Rótulos amigáveis para o status de daily_goals (enum goal_status).
GOAL_STATUS_LABELS = {
    "active": "Em andamento",
    "achieved": "Atingida",
    "expired": "Expirada",
    "cancelled": "Cancelada",
}

ALLOWED_IMAGE_EXTENSIONS = (
    "png",
    "jpg",
    "jpeg",
    "webp",
)