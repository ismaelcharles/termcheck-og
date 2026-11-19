"""TermCheck público: verificador, glosario de consulta y ejemplos, sin inicio de sesión.

    .venv/bin/streamlit run app/demo.py --server.port 8502

No muestra el glosario de trabajo en edición, la anotación ni los resultados: esas páginas están en la app
completa (app/streamlit_app.py), que pide login. Acá la página Verificar corre en modo demo: usa la edición
publicada del glosario, no ofrece el corpus y pone límites de tamaño (ver app/paginas/verificar.py).

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

paginas = [st.Page("paginas/verificar.py", title="Verificador", default=True),
           st.Page("paginas/glosario_publico.py", title="Glosario", url_path="glosario"),
           st.Page("paginas/inicio.py", title="Ejemplos", url_path="ejemplos")]
pagina = st.navigation(paginas, position="hidden")
# Consultar el glosario no debe borrar el texto ni las preferencias de revisión.
for clave in ("vf_en", "vf_es", "vf_modo", "vf_editor_abierto", "vf_solo", "vf_segmento"):
    if clave in st.session_state:
        st.session_state[clave] = st.session_state[clave]
vista.estilos()
vista.cabecera(NOMBRE)
st.html('<p class="tc-brand-description">Revisión terminológica de petróleo y gas · Inglés → español de Argentina</p>')
with st.container(horizontal=True, gap="small", key="public_nav"):
    for p, icono in zip(paginas, (":material/fact_check:", ":material/menu_book:", ":material/science:")):
        if st.button(p.title, icon=icono, key=f"nav_{p.title}",
                     type="primary" if p.url_path == pagina.url_path else "tertiary"):
            st.switch_page(p)
pagina.run()
