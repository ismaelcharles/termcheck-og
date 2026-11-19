"""Recorrido de bienvenida de la demo pública."""
import random

import streamlit as st

import catalogo
from termcheck.checker import verificar
from vista import e


# Las cuatro alternativas usan decisiones de la edición publicada.
from termcheck.ejemplos import PORTADA as EJEMPLOS


def elegir(terminos):
    disponibles = [ej for ej in EJEMPLOS if any(t.id == ej["id"] for t in terminos)]
    if not disponibles:
        return None
    if st.session_state.get("portada_ejemplo") not in [ej["id"] for ej in disponibles]:
        st.session_state.portada_ejemplo = random.choice(disponibles)["id"]
    return next(ej for ej in disponibles if ej["id"] == st.session_state.portada_ejemplo)


@st.cache_data(show_spinner=False)
def caso(termino, ejemplo):
    original = ejemplo["original"]
    traducciones = (ejemplo["inicial"], ejemplo["corregida"])
    lecturas = []
    for traduccion in traducciones:
        ocurrencia, = verificar(original, traduccion, [termino])
        if ocurrencia.start >= 0:
            frase = (e(traduccion[:ocurrencia.start]) + "<mark>" + e(ocurrencia.es_found)
                     + "</mark>" + e(traduccion[ocurrencia.end:]))
        else:
            frase = e(traduccion)
        estado = "Revisar el término" if ocurrencia.marcada else "Forma aceptada"
        lecturas.append(f'<div class="tc-lectura"><p>{frase}</p><small>{estado}</small></div>')
    return lecturas


def mostrar():
    terminos = catalogo.leer()
    ejemplo = elegir(terminos)
    if ejemplo is None:
        return
    if st.button("Ir al verificador ↓", key="saltar_recorrido"):
        st.session_state.recorrido_visto = True
        st.rerun()
    termino = next(t for t in terminos if t.id == ejemplo["id"])
    inicial, corregida = caso(termino, ejemplo)
    antes, _, despues = ejemplo["original"].partition(ejemplo["en"])
    original = e(antes) + "<strong>" + e(ejemplo["en"]) + "</strong>" + e(despues)
    st.html(f"""
    <section class="tc-recorrido" aria-labelledby="tc-titulo-caso">
      <header>
        <h2 id="tc-titulo-caso">¿Cómo traducirías <i lang="en">{e(ejemplo["en"])}</i>?</h2>
        <p>{e(ejemplo["contexto"])}</p>
      </header>
      <div class="tc-caso">
        <div><small>Original en inglés</small>
          <blockquote lang="en">{original}</blockquote>
        </div>
        <div><small>Traducción en revisión</small>{inicial}
          <details class="tc-correccion"><summary>Probar «{e(termino.es_preferred)}»</summary>{corregida}</details>
        </div>
      </div>
      <details class="tc-origen"><summary>¿Por qué aparece esta marca?</summary>
        <p>Para este encargo, la ficha de <i>{e(ejemplo["en"])}</i> prefiere «{e(termino.es_preferred)}».
        En el glosario podés consultar las variantes, las formas que conviene evitar y sus fuentes.</p>
        {catalogo.ficha(termino)}
      </details>
    </section>
    """)
