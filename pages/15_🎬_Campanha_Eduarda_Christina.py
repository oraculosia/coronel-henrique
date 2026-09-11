"""
Página institucional pública da campanha (parceira Eduarda Christina).
Renderiza static/pages/campanha_eduarda_christina.html dentro de um iframe
isolado (components.html) para não misturar o CSS da landing page com o CSS
do app Streamlit. Vídeos referenciados no HTML usam caminho absoluto
/app/static/documentos/... (enableStaticServing em .streamlit/config.toml).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

HTML_PATH = PROJECT_ROOT / "static" / "pages" / "campanha_eduarda_christina.html"


def main() -> None:
    st.set_page_config(
        page_title="Coronel Henrique 22500 | Apoie com Eduarda Christina",
        page_icon="🇧🇷",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.iframe(HTML_PATH, height=6000)


if __name__ == "__main__":
    main()
