import re
import uuid
from pathlib import Path

from src.config.constants import ALLOWED_IMAGE_EXTENSIONS
from src.config.settings import settings


def _safe_filename_base(text: str) -> str:
    """Sanitiza texto livre (ex.: e-mail) para uso seguro como nome de arquivo."""
    return re.sub(r"[^a-z0-9@._-]", "_", text.strip().lower())


def validate_and_save_image(
    uploaded_file,
    target_dir: Path,
    filename_base: str = "",
) -> tuple[bool, str]:
    """Valida extensão/tamanho e salva a imagem localmente.

    O nome do arquivo é o `filename_base` (normalmente o e-mail cadastrado)
    + a extensão — assim um novo upload do mesmo usuário substitui a foto
    anterior em vez de acumular arquivos. Sem `filename_base`, cai para um
    nome aleatório.

    Retorna (ok, caminho_relativo_ou_mensagem_de_erro).
    """
    if uploaded_file is None:
        return True, ""

    name = getattr(uploaded_file, "name", "") or ""
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(ALLOWED_IMAGE_EXTENSIONS)
        return False, f"Formato de imagem não permitido. Use: {allowed}."

    data = uploaded_file.getvalue()
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024
    if len(data) > max_bytes:
        return False, f"A imagem deve ter até {settings.MAX_IMAGE_SIZE_MB}MB."

    target_dir.mkdir(parents=True, exist_ok=True)
    base = _safe_filename_base(filename_base) if filename_base else uuid.uuid4().hex
    filename = f"{base}.{extension}"
    destination = target_dir / filename
    destination.write_bytes(data)

    return True, str(destination)
