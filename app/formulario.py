"""Formulario guiado para un término: una pregunta por campo y, al lado, cómo queda la ficha y qué marcaría el
verificador. Se usa para agregar (pestaña «Agregar») y para editar (botón «Editar» de cada ficha)."""
import streamlit as st

import datos
import vista


def _lista(clave, etiqueta, ayuda, valores, marcador):
    """Campo de varias formas: se escribe una, Enter, y queda como chip."""
    return st.multiselect(etiqueta, options=valores, default=valores, accept_new_options=True, key=clave,
                          help=ayuda, placeholder=marcador)


def formulario(fila, clave, al_guardar):
    """Dibuja el formulario. `fila` trae los valores iniciales (vacíos para un término nuevo); `clave` separa los
    campos de cada formulario; `al_guardar(id)` se llama después de guardar."""
    izq, der = st.columns([1.35, 1], gap="large")
    with izq:
        en = _lista(f"{clave}_en", "¿Cómo aparece en inglés?",
                    "Escribí cada forma y apretá Enter. Ej.: wellhead, well-head, well head.",
                    datos.variantes(fila["en"]), "Escribí y apretá Enter")
        codigos = list(datos.CATEGORIAS)
        pos = st.segmented_control("¿Qué tipo de palabra es?", codigos, key=f"{clave}_pos",
                                   default=fila["pos"] if fila["pos"] in codigos else "NOUN",
                                   format_func=lambda c: datos.CATEGORIAS[c],
                                   help="Sirve para no confundir, por ejemplo, «well» sustantivo (pozo) con «as well as».")
        preferida = st.text_input("¿Cómo debería traducirse?", value=fila["es_preferred"], key=f"{clave}_pref",
                                  placeholder="La traducción que querés ver",
                                  help="Si en campo se usa en inglés (casing, shale), escribila en inglés.")
        aceptadas = _lista(f"{clave}_acep", "¿Qué otras traducciones también valen? (opcional)",
                           "Variantes correctas que no son la preferida.", datos.variantes(fila["es_allowed"]),
                           "Escribí y apretá Enter")
        prohibidas = _lista(f"{clave}_proh", "¿Qué traducciones son un error? (opcional)",
                            "Mejor si salen de errores que viste en traducciones automáticas reales.",
                            datos.variantes(fila["es_forbidden"]), "Escribí y apretá Enter")
        areas = sorted(set(datos.AREAS) | ({fila["subdomain"]} if fila["subdomain"] else set()), key=str.lower)
        area = st.selectbox("¿De qué área es?", areas, key=f"{clave}_area", accept_new_options=True,
                            index=areas.index(fila["subdomain"]) if fila["subdomain"] in areas else None,
                            placeholder="Elegí o escribí una")
        nota = st.text_area("¿Algo que aclarar? (opcional)", value=fila["note"], key=f"{clave}_nota", height=80,
                            placeholder="Uso en Argentina, contexto, por qué es error…")
        fuente = st.text_input("¿De dónde sale la decisión?", value=fila["source"], key=f"{clave}_fuente",
                               placeholder="Documento y página, o «criterio propio»",
                               help="Si es tuya, poné «criterio propio» y explicala en la aclaración.")

    nueva = {"id": fila["id"], "en": datos.juntar(en), "pos": pos or "", "es_preferred": preferida.strip(),
             "es_allowed": datos.juntar(aceptadas), "es_forbidden": datos.juntar(prohibidas),
             "subdomain": (area or "").strip(), "note": nota.strip(), "source": fuente.strip()}

    with der:
        st.markdown("**Así queda la ficha**")
        st.html(vista.ficha(dict(nueva, id=nueva["id"] or "nuevo")))
        if vista.que_pasaria(nueva):
            st.markdown("**Qué marcaría el verificador** si la traducción dice…")
            st.html(vista.casos(nueva))
            prueba = st.text_input("Probá una traducción", key=f"{clave}_prueba",
                                   placeholder="Ej.: lo que puso el traductor automático")
            if prueba.strip():
                st.html(f'<div class="tc-fila tc-centro"><div style="flex:1">{vista.chip(prueba)}</div>'
                        f'{vista.etiqueta(vista.probar(nueva, prueba))}</div>')
                st.caption("Por ahora compara la frase entera, sin tildes ni mayúsculas. Plurales y género "
                           "(«tuberías» = «tubería») llegan con el verificador, en la Fase 3.")

    if st.button("Guardar término", type="primary", key=f"{clave}_guardar", disabled=not (nueva["en"] or preferida)):
        id_guardado = datos.guardar_fila(nueva)
        al_guardar(id_guardado)
