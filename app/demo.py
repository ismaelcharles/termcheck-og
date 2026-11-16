"""TermCheck público: verificador, glosario de consulta y ejemplos, sin inicio de sesión.

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
import vista  # noqa: E402

paginas = [st.Page("paginas/verificar.py", title="Verificar", default=True),
           st.Page("paginas/glosario_publico.py", title="Glosario", url_path="glosario"),
           st.Page("paginas/inicio.py", title="Ejemplos", url_path="ejemplos")]
pagina = st.navigation(paginas, position="hidden")
# Consultar el glosario no debe borrar el texto ni las preferencias de revisión.
for clave in ("vf_en", "vf_es", "vf_modo", "vf_editor_abierto", "vf_solo", "vf_segmento"):
    if clave in st.session_state:
        st.session_state[clave] = st.session_state[clave]
vista.estilos()
vista.cabecera(NOMBRE)
st.html('<p class="tc-brand-description">Terminología de Oil &amp; Gas, en español de Argentina.</p>')
with st.container(horizontal=True, gap="medium", key="public_nav"):
    for p in paginas:
        st.page_link(p)
pagina.run()
