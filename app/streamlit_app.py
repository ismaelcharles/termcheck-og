"""La app web de TermCheck O&G. Se lanza con:

    .venv/bin/streamlit run app/streamlit_app.py

Acceso: con la cuenta de Google. Solo entran los correos de [acceso] correos en .streamlit/secrets.toml
(ese archivo no va a git: tiene la clave de Google). Para probar en la propia máquina sin Google:
    TERMCHECK_SIN_LOGIN=1 .venv/bin/streamlit run app/streamlit_app.py

Tiene una página por archivo en app/paginas/.
"""
import os
import sys
from pathlib import Path

import streamlit as st

# Para poder importar el paquete del proyecto (src/termcheck) sin instalarlo
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from termcheck import NOMBRE  # noqa: E402

import vista  # noqa: E402

st.set_page_config(page_title=NOMBRE, layout="wide", page_icon=":material/fact_check:")


def puerta():
    """Pantalla para entrar. Devuelve True si la persona puede pasar."""
    if os.environ.get("TERMCHECK_SIN_LOGIN") == "1":
        return True
    if not st.user.is_logged_in:
        vista.estilos()
        _, centro, _ = st.columns([1, 1.4, 1])
        with centro:
            st.title(NOMBRE)
            st.write("Verificador de terminología para traducción automática inglés → español en Oil & Gas.")
            st.button("Entrar con Google", type="primary", icon=":material/login:", on_click=st.login,
                      width="stretch")
        return False
    permitidos = [c.lower() for c in st.secrets.get("acceso", {}).get("correos", [])]
    if str(st.user.get("email", "")).lower() not in permitidos:
        st.title(NOMBRE)
        st.warning(f"La cuenta {st.user.get('email')} no tiene acceso.")
        st.button("Salir y entrar con otra cuenta", on_click=st.logout)
        return False
    return True


if puerta():
    paginas = st.navigation([
        st.Page("paginas/inicio.py", title="Inicio", icon=":material/home:", default=True),
        st.Page("paginas/verificar.py", title="Verificar", icon=":material/fact_check:", url_path="verificar"),
        st.Page("paginas/glosario.py", title="Glosario", icon=":material/menu_book:", url_path="glosario"),
        st.Page("paginas/traducciones.py", title="Traducciones", icon=":material/translate:", url_path="traducciones"),
        st.Page("paginas/anotar.py", title="Anotar", icon=":material/edit_note:", url_path="anotar"),
        st.Page("paginas/resultados.py", title="Resultados", icon=":material/analytics:", url_path="resultados"),
    ])
    if st.user.is_logged_in:
        with st.sidebar:
            st.caption(st.user.get("email", ""))
            st.button("Salir", on_click=st.logout, type="tertiary", icon=":material/logout:")
    paginas.run()
