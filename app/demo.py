"""La demo pública de TermCheck O&G: solo la página Verificar, sin inicio de sesión.

    .venv/bin/streamlit run app/demo.py --server.port 8502

No muestra el glosario de trabajo en edición, la anotación ni los resultados: esas páginas están en la app
completa (app/streamlit_app.py), que pide login. Acá la página Verificar corre en modo demo: usa el glosario v1
congelado si existe, no ofrece el corpus y pone límites de tamaño (ver app/paginas/verificar.py).

En el servidor se publica con `sudo bash deploy/demo.sh`.
"""
import os
import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
os.environ["TERMCHECK_DEMO"] = "1"  # este proceso es solo la demo

from termcheck import NOMBRE  # noqa: E402

st.set_page_config(page_title=f"{NOMBRE} · demo", layout="wide", page_icon=":material/fact_check:")
st.navigation([st.Page("paginas/verificar.py", title="Verificar", icon=":material/fact_check:", default=True)],
              position="hidden").run()
