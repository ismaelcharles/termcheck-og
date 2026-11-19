"""Glosario de consulta. Los datos de trabajo y las funciones de edición quedan en la app con acceso."""
import math

import streamlit as st

import catalogo


terminos = catalogo.leer()
st.html('<div class="tc-page-intro"><h2>Glosario</h2></div>')
with st.container(horizontal=True, vertical_alignment="center"):
    st.caption("Inglés → español técnico de Argentina")
    st.download_button("Descargar glosario CSV", catalogo.archivo().read_bytes(), "glosario-termcheck.csv",
                       "text/csv", on_click="ignore")


def primera_pagina():
    st.session_state.gp_pagina = 0


buscar, filtrar = st.columns([2, 1])
consulta = buscar.text_input("Buscar un término", placeholder="En inglés o en español", key="gp_buscar",
                              on_change=primera_pagina)
area = filtrar.selectbox("Área", ["Todas las áreas", *sorted({t.subdomain for t in terminos if t.subdomain})],
                        key="gp_area", on_change=primera_pagina)
filtrados = catalogo.buscar(terminos, consulta, area)
st.caption(f"{len(filtrados)} términos" if len(filtrados) == len(terminos) else
           f"{len(filtrados)} de {len(terminos)} términos")
if not filtrados:
    st.info("No hay términos que coincidan. Probá otra palabra o elegí otra área.")
else:
    paginas = math.ceil(len(filtrados) / 6)
    indice = st.selectbox("Página", range(paginas), format_func=lambda i: f"{i + 1} de {paginas}",
                          key="gp_pagina", width=150) if paginas > 1 else 0
    st.html(catalogo.fichas(filtrados[indice * 6:(indice + 1) * 6]))
with st.expander("Sobre el glosario"):
    st.caption("La consulta y el verificador usan la misma edición. Las equivalencias reflejan el criterio terminológico "
               "que apliqué y documenté; las preferencias pueden cambiar según el contexto o el cliente.")
