"""Página de inicio: qué hace TermCheck, ejemplos interactivos de cada etiqueta y en qué fase está el proyecto."""
import os
import streamlit as st

import datos
import vista
from termcheck import NOMBRE, VERSION, report
from termcheck.checker import Ocurrencia, verificar


# Ejemplos ilustrativos con los términos del plan (sección 3). Entre [[ ]] va el término; entre (( )), lo que el
# verificador ve pero no cuenta como término. No son datos del glosario: el glosario lo decide el dueño.
from termcheck.ejemplos import ILUSTRATIVOS as EJEMPLOS


vista.estilos()
st.html("<style>" + report.CSS + "</style>")
DEMO = os.environ.get("TERMCHECK_DEMO") == "1"
if not DEMO:
    vista.cabecera(NOMBRE)
    st.markdown("Revisá la terminología de una traducción inglés → español de Oil & Gas con un glosario de español "
                "técnico de Argentina.")
    st.markdown("1. Pegá el inglés y la traducción, o subí un archivo.\n"
                "2. Usá el glosario del proyecto o cargá el tuyo.\n"
                "3. Verificá y revisá los términos señalados. Podés descargar el reporte en HTML o CSV.")
else:
    st.html('<div class="tc-page-intro"><h2>Ejemplos</h2></div>')
if not DEMO:
    st.page_link("paginas/verificar.py", label="Probar con una traducción →")
if not DEMO:
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
if DEMO:
    import catalogo
    original = quitar_marcas(ej["en"])
    st.caption("Original · inglés")
    st.write(original)
    traduccion = st.text_area("Probá otra traducción", value=quitar_marcas(ej["es"]),
                              key=f"ej_traduccion_{titulos.index(elegido)}", max_chars=1500,
                              help="Al salir del campo se actualizan las marcas.")
    if traduccion.strip():
        ocurrencias = verificar(original, traduccion, catalogo.leer())
        st.html(report.bloque_segmento(original, traduccion, ocurrencias, cabecera="Resultado con el glosario O&G"))
        if traduccion == quitar_marcas(ej["es"]):
            st.markdown(ej["porque"])
else:
    st.html(report.bloque_segmento(quitar_marcas(ej["en"]), quitar_marcas(ej["es"]), [o], cabecera="Ejemplo ilustrativo"))
    st.markdown(ej["porque"])
with st.expander("Las seis etiquetas"):
    st.html(report.leyenda())
    st.caption("Ejemplos ilustrativos. En tus textos, las formas preferidas y válidas las decide el glosario.")
if not DEMO:
    st.subheader("Estado del proyecto")
    st.write(f"Versión {VERSION}. El glosario de trabajo tiene {len(datos.leer())} términos. "
             "La evaluación publicada corresponde a la versión 0.1; los resultados de 0.2 se informan aparte en el README. "
             "Falta probar la herramienta con traductores y ampliar la anotación.")
    st.page_link("paginas/glosario.py", label="Ir al glosario")
