"""Página de inicio: qué hace TermCheck, ejemplos interactivos de cada etiqueta y en qué fase está el proyecto."""
import streamlit as st

import datos
import vista
from termcheck import NOMBRE, VERSION, report
from termcheck.checker import Ocurrencia


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


vista.estilos()
st.html("<style>" + report.CSS + "</style>")
vista.cabecera(NOMBRE)
st.markdown("Revisá la terminología de una traducción inglés → español de Oil & Gas con un glosario de español "
            "técnico de Argentina.")
st.markdown("1. Pegá el inglés y la traducción, o subí un archivo.\n"
            "2. Usá el glosario del proyecto o cargá el tuyo.\n"
            "3. Verificá y revisá los términos señalados. Podés descargar el reporte en HTML o CSV.")
st.page_link("paginas/verificar.py", label="Probalo con tu propio texto")
st.subheader("Cómo marca cada caso")
titulos = [x["titulo"] for x in EJEMPLOS]
elegido = st.selectbox("Ejemplo", titulos, label_visibility="collapsed")
ej = EJEMPLOS[titulos.index(elegido)]
def quitar_marcas(texto):
    return texto.replace("[[", "").replace("]]", "").replace("((", "").replace("))", "")
def tramo(texto):
    antes, resto = texto.split("[[", 1)
    dentro = resto.split("]]", 1)[0]
    return len(quitar_marcas(antes)), dentro
ini_en, term = tramo(ej["en"])
ini_es, encontrada = tramo(ej["es"])
# Ejemplos ilustrativos ya escritos: se muestran sin agregar contenido al glosario.
o = Ocurrencia("Ejemplo", "", "Ejemplo", term, ej["etiqueta"], encontrada,
               ini_es, ini_es + len(encontrada), ini_en, ini_en + len(term), "")
st.html(report.bloque_segmento(quitar_marcas(ej["en"]), quitar_marcas(ej["es"]), [o], cabecera="Ejemplo ilustrativo"))
st.markdown(ej["porque"])
st.caption("Ejemplos ilustrativos. En tus textos, las formas preferidas y válidas las decide el glosario.")
with st.expander("Las seis etiquetas"):
    st.html(report.leyenda())
st.subheader("Estado del proyecto")
st.write(f"Versión {VERSION}. El glosario de trabajo tiene {len(datos.leer())} términos. "
         "La evaluación publicada corresponde a la versión 0.1; los resultados de 0.2 se informan aparte en el README. "
         "Falta probar la herramienta con traductores y ampliar la anotación.")
st.page_link("paginas/glosario.py", label="Ir al glosario")
