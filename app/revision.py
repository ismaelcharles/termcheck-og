"""Revisar un segmento por vez. El filtro y la selección no vuelven a analizar el documento."""
import streamlit as st

from termcheck import report


def mostrar(resultado, todas, advertencias, glosario="", terminos=()):
    marcadas = sum(o.marcada for o in todas)
    with st.container(horizontal=True, vertical_alignment="center", key="vf_result_header"):
        st.subheader("Revisión")
        with st.popover("Descargar"):
            segmentos = {p[0]: p[2] for p, _ in resultado}
            traducciones = [{"seg_id": p[0], "system": p[1], "target_es": p[3]} for p, _ in resultado]
            contextos = {(p[0], p[1]): (p[2], p[3]) for p, _ in resultado}
            st.download_button("Reporte HTML", report.a_html(segmentos, traducciones, todas, advertencias,
                                                              glosario=glosario),
                               "termcheck.html", "text/html", on_click="ignore", width="stretch")
            st.download_button("Tabla CSV", report.a_csv_texto(todas, contextos), "termcheck.csv", "text/csv",
                               on_click="ignore", width="stretch")
    # Cuenta apariciones, como el CSV, aunque los detalles iguales se agrupen en la pantalla.
    con_terminos = sum(bool(oc) for _, oc in resultado)
    if todas:
        st.html('<p class="tc-result-summary">'
                f'<strong>{marcadas} para revisar</strong> · {len(todas)} '
                f'{"término" if len(todas) == 1 else "términos"} · '
                f'{len(resultado)} {"segmento" if len(resultado) == 1 else "segmentos"}</p>')
        if con_terminos < len(resultado):
            st.caption(f"Con términos del glosario: {con_terminos} de {len(resultado)} segmentos.")
        if not marcadas:
            st.success("Sin observaciones en los términos reconocidos.")
    else:
        st.info("No se encontraron términos del glosario en el original.")
    # Sin avisos se muestra directamente el texto: no hay que desactivar un filtro vacío.
    solo = st.checkbox("Solo observaciones", value=True, key="vf_solo") if marcadas else False
    indices = [i for i, (_, oc) in enumerate(resultado) if not todas or not solo or any(o.marcada for o in oc)]
    if not indices:
        st.info("No hay segmentos en esta vista.")
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
            ids = {o.term_id for o in oc if o.marcada or not solo}
            fichas = [t for t in terminos if t.id in ids]
            if fichas:
                import catalogo
                with st.expander("Consultar las fichas de este segmento"):
                    st.html(catalogo.fichas(fichas))
    if advertencias:
        with st.expander("Términos usados de formas distintas"):
            st.html(report.avisos_html(advertencias))
    with st.expander("Cómo leer las marcas"):
        st.html(report.leyenda())
        st.caption("Solo se revisan términos del glosario, no la traducción completa. Una forma no encontrada "
                   "puede ser válida. Las sugerencias por parecido no cambian la etiqueta.")
