"""Recorrido de bienvenida de la demo pública."""
import streamlit as st

import catalogo
from termcheck.checker import verificar
from vista import e


@st.cache_data(show_spinner=False)
def caso(termino):
    original = "The drilling rig was moved to the new location."
    traducciones = (
        "La plataforma de perforación se trasladó a la nueva locación.",
        "El equipo de perforación se trasladó a la nueva locación.",
    )
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
    termino = next((t for t in catalogo.leer() if "drilling rig" in t.en), None)
    if termino is None:
        return
    if st.button("Ir al verificador ↓", key="saltar_recorrido"):
        st.session_state.recorrido_visto = True
        st.rerun()
    inicial, corregida = caso(termino)
    st.html(f"""
    <section class="tc-recorrido" aria-labelledby="tc-titulo-caso">
      <header><p>Una traducción de campo</p>
        <h2 id="tc-titulo-caso">¿Cómo traducirías <i lang="en">drilling rig</i>?</h2>
        <p>El parte describe una perforación en tierra. Una sola palabra cambia dónde imaginamos el equipo.</p>
      </header>
      <div class="tc-caso">
        <div><small>Original en inglés</small>
          <blockquote lang="en">The <strong>drilling rig</strong> was moved to the new location.</blockquote>
        </div>
        <div><small>Traducción en revisión</small>{inicial}
          <details class="tc-correccion"><summary>Probar «equipo de perforación»</summary>{corregida}</details>
        </div>
      </div>
      <details class="tc-origen"><summary>¿Por qué aparece esta marca?</summary>
        <p>Para este encargo, la ficha de <i>drilling rig</i> prefiere «{e(termino.es_preferred)}».
        En el glosario podés consultar las variantes, las formas que conviene evitar y sus fuentes.</p>
        {catalogo.ficha(termino)}
      </details>
    </section>
    """)
