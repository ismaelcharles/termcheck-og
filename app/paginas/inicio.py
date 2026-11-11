"""Página de inicio: qué hace TermCheck, ejemplos interactivos de cada etiqueta y en qué fase está el proyecto."""
import re

import streamlit as st

import datos
import vista
from termcheck import NOMBRE

PROGRESO = datos.RAIZ / "PROGRESO.md"
META_TERMINOS = 100  # tamaño del glosario v1 según el plan

# Ejemplos ilustrativos con los términos del plan (sección 3). Entre [[ ]] va el término; entre (( )), lo que el
# verificador ve pero no cuenta como término. No son datos del glosario: el glosario lo decide el dueño.
EJEMPLOS = [
    {"titulo": "Traducción prohibida", "etiqueta": "PROHIBIDO",
     "en": "The [[shale]] formation lies 3,000 m below the surface.",
     "es": "La formación de [[esquisto]] está a 3.000 m de profundidad.",
     "porque": "«Esquisto» es *schist*, otra roca. El glosario lo marca como error frecuente de la traducción "
               "automática: en Vaca Muerta se dice «shale» o «lutita»."},
    {"titulo": "Error que suena bien", "etiqueta": "PROHIBIDO",
     "en": "The [[drilling rig]] was moved to the new location.",
     "es": "La [[plataforma de perforación]] se trasladó a la nueva locación.",
     "porque": "La frase es fluida, pero «plataforma» implica offshore. En un yacimiento en tierra es «equipo de "
               "perforación». Es el tipo de error que se escapa al leer de corrido."},
    {"titulo": "Plural que coincide", "etiqueta": "OK",
     "en": "Check the [[drilling fluids]] every shift.",
     "es": "Controlá los [[lodos de perforación]] en cada turno.",
     "porque": "El glosario dice «lodo de perforación», en singular. El verificador compara lemas "
               "(«lodos» → «lodo»), así que el plural no es error."},
    {"titulo": "Préstamo aceptado", "etiqueta": "OK",
     "en": "Run the [[casing]] to 2,000 m.",
     "es": "Bajar el [[casing]] hasta 2.000 m.",
     "porque": "Quedó en inglés, pero en el campo argentino se dice «casing». Como el glosario lo acepta, no se marca."},
    {"titulo": "Quedó en inglés", "etiqueta": "SIN_TRADUCIR",
     "en": "The [[pumpjack]] stopped at noon.",
     "es": "El [[pumpjack]] se detuvo al mediodía.",
     "porque": "El glosario prefiere «AIB» y no acepta «pumpjack» como préstamo. Hay que traducirlo."},
    {"titulo": "No aparece", "etiqueta": "NO_ENCONTRADO",
     "en": "The [[blowout preventer]] was tested before drilling.",
     "es": "El [[equipo de seguridad]] se probó antes de perforar.",
     "porque": "Ninguna traducción conocida («BOP», «preventor de reventones») está en la traducción. Puede ser "
               "una omisión o un sinónimo que falta en el glosario: lo decide quien revisa."},
    {"titulo": "«well» que no es pozo", "etiqueta": "OK",
     "en": "Check the [[BOP]] as ((well)) as the choke manifold.",
     "es": "Revisá el [[BOP]] y también el choke manifold.",
     "porque": "Acá «well» es adverbio (*as well as* = «además de»), no el sustantivo «pozo». El verificador mira "
               "la categoría gramatical y no lo cuenta como término.", "apagado": "ADV: no es el término «pozo»"},
]


def leer_fases():
    fases = []
    for linea in PROGRESO.read_text(encoding="utf-8").splitlines():
        m = re.match(r"- \[( |x|~)\] (Fase .+)", linea)  # [~] = en curso
        if m:
            fases.append((m.group(1), m.group(2)))
    return fases


vista.estilos()
st.title(NOMBRE)
st.markdown("Revisa la **terminología** de una traducción automática inglés → español de Oil & Gas, "
            "contra un glosario en la variante técnica de Argentina. No traduce: marca qué término revisar y por qué.")

st.html('<div class="tc-flujo">'
        '<span class="tc-paso"><b>Texto en inglés</b></span><span class="tc-flecha">+</span>'
        '<span class="tc-paso"><b>Traducción automática</b></span><span class="tc-flecha">+</span>'
        '<span class="tc-paso"><b>Glosario</b></span><span class="tc-flecha">→</span>'
        '<span class="tc-paso">Busca cada término en el inglés</span><span class="tc-flecha">→</span>'
        '<span class="tc-paso">Mira cómo quedó en la traducción</span><span class="tc-flecha">→</span>'
        '<span class="tc-paso"><b>Etiqueta</b> y reporte</span></div>')

st.page_link("paginas/verificar.py", label="Probalo con tu propio texto", icon=":material/fact_check:")

st.subheader("Cómo marca cada caso")
titulos = [x["titulo"] for x in EJEMPLOS]
elegido = st.pills("Ejemplo", titulos, default=titulos[0], label_visibility="collapsed") or titulos[0]
ej = EJEMPLOS[titulos.index(elegido)]
with st.container(border=True):
    st.html(f'<div class="tc-idioma">Inglés</div>{vista.oracion(ej["en"], ej["etiqueta"], ej.get("apagado"))}'
            f'<div class="tc-idioma">Traducción automática</div>{vista.oracion(ej["es"], ej["etiqueta"])}'
            f'<div style="margin:.2rem 0 .4rem">{vista.etiqueta(ej["etiqueta"])}</div>')
    st.markdown(ej["porque"])
st.caption("Ejemplos ilustrativos con los términos del plan. Lo que vale en cada caso lo decide el glosario.")

with st.expander("Las seis etiquetas"):
    st.html(vista.leyenda())

st.subheader("Avance")
n = len(datos.leer())
fases = leer_fases()
hechas = sum(1 for marca, _ in fases if marca == "x")
c1, c2 = st.columns(2)
c1.metric("Términos en el glosario", n, help=f"La versión 1 apunta a unos {META_TERMINOS}.")
c2.metric("Fases terminadas", f"{hechas} de {len(fases)}")
st.progress(min(n / META_TERMINOS, 1.0), text=f"Glosario: {n} de {META_TERMINOS}")
st.page_link("paginas/glosario.py", label="Ir al glosario", icon=":material/arrow_forward:")
with st.expander("Fases del proyecto"):
    for marca, texto in fases:
        st.markdown(f"{ {'x': '✓', '~': '◐'}.get(marca, '○') }&nbsp;&nbsp;{texto}")
