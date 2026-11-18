"""Revisar un segmento por vez. El filtro y la selección no vuelven a analizar el documento."""
import streamlit as st

from termcheck import report


def mostrar(resultado, todas, advertencias, glosario=""):
    marcadas = sum(o.marcada for o in todas)
    with st.container(horizontal=True, vertical_alignment="center"):
        st.subheader("Revisión")
        with st.popover("Descargar"):
            segmentos = {p[0]: p[2] for p, _ in resultado}
            traducciones = [{"seg_id": p[0], "system": p[1], "target_es": p[3]} for p, _ in resultado]
            st.download_button("Reporte HTML", report.a_html(segmentos, traducciones, todas, advertencias,
                                                              glosario=glosario),
                               "termcheck.html", "text/html", on_click="ignore", width="stretch")
            st.download_button("Tabla CSV", report.a_csv_texto(todas), "termcheck.csv", "text/csv",
                               on_click="ignore", width="stretch")
    # Cuenta apariciones, como el CSV, aunque los detalles iguales se agrupen en la pantalla.
    st.html('<p class="tc-result-summary">'
            f'<strong>{marcadas} para revisar</strong> · {len(todas)} '
            f'{"término encontrado" if len(todas) == 1 else "términos encontrados"} en '
            f'{len(resultado)} {"segmento" if len(resultado) == 1 else "segmentos"}</p>')
    con_terminos = sum(bool(oc) for _, oc in resultado)
    st.caption(f"{con_terminos} de {len(resultado)} segmentos con términos del glosario. "
               "La revisión solo cubre esos términos; una coincidencia no valida la traducción completa.")
    if not todas:
        st.info("No se encontraron términos del glosario en el original. "
                "Podés consultar el glosario o cargar uno propio para este texto.")
    solo = st.checkbox("Solo lo que hay que revisar", value=True, key="vf_solo", disabled=not todas)
    indices = [i for i, (_, oc) in enumerate(resultado) if not todas or not solo or any(o.marcada for o in oc)]
    if not indices:
        st.success("No hay términos para revisar." if not marcadas else "No hay segmentos en esta vista.")
        st.caption("Desmarcá el filtro para ver también las formas aceptadas y los segmentos sin términos.")
    else:
        def etiqueta(i):
            (seg_id, sistema, _, _), oc = resultado[i]
            n = sum(o.marcada for o in oc)
            return f"Segmento {i + 1} de {len(resultado)} · {n} para revisar" + (f" · {sistema}" if sistema else "")

        # Sin selector para un único segmento: el texto y sus observaciones ya están a la vista.
        seleccionado = st.selectbox("Segmento", indices, format_func=etiqueta, key="vf_segmento",
                                    label_visibility="collapsed") if len(indices) > 1 else indices[0]
        (seg_id, sistema, en, es), oc = resultado[seleccionado]
        with st.container(border=True, key="vf_revision"):
            st.html(report.bloque_segmento(en, es, oc, solo=solo,
                                          cabecera=" · ".join(x for x in (f"Segmento {seleccionado + 1}", sistema) if x)))
    if advertencias:
        with st.expander("Términos usados de formas distintas"):
            st.html(report.avisos_html(advertencias))
    with st.expander("Cómo leer las marcas"):
        st.html(report.leyenda())
        st.caption("Una forma no encontrada puede ser una omisión o una variante que falta en el glosario. "
                   "Las sugerencias por parecido de letras no cambian la etiqueta.")
