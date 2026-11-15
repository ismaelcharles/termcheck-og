"""Página «Verificar» (Fase 5 del plan): pegar un texto en inglés y su traducción, o subir un archivo (TSV, CSV,
XLIFF o TMX), y ver el reporte.

Usa el glosario del proyecto o uno que sube la persona (mismo formato de columnas). El verificador es el de
src/termcheck (el mismo que se evalúa); esta página solo lo muestra.

Del corpus del proyecto solo ofrece el conjunto de desarrollo: ver el resultado del verificador sobre la prueba
antes de anotarla rompería la anotación a ciegas.

En la demo pública (app/demo.py, TERMCHECK_DEMO=1) la página funciona sin login, usa el glosario v1 congelado si
existe, no ofrece el corpus y tiene límites de tamaño, porque el servidor es compartido.
"""
import csv
import io
import os
import hashlib
import re

import streamlit as st

import datos
import vista
from limites import MAX_LETRAS, MAX_SEGMENTOS, MAX_TERMINOS, aplicar
from termcheck.checker import verificar
from termcheck.consistency import inconsistencias
from termcheck.formatos import ErrorDeFormato, es_de_traduccion, leer as leer_formato
from termcheck.glossary import ErrorDeGlosario, cargar, cargar_bytes, validar
from termcheck import NOMBRE
from termcheck import report
from termcheck.report import a_csv_texto, a_html

RAIZ = datos.RAIZ
ORDEN = ["PROHIBIDO", "SIN_TRADUCIR", "NO_ENCONTRADO", "VARIANTE", "OK"]
DEMO = os.environ.get("TERMCHECK_DEMO") == "1"

vista.estilos()
st.html("<style>" + report.CSS + "</style>")
if DEMO:
    vista.cabecera(NOMBRE)
    st.caption("Demo pública. Inglés → español técnico de Argentina, en Oil & Gas. "
               "Los textos no se guardan. [Código y evaluación](https://github.com/ismaelcharles/termcheck-og).")
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    fila = re.search(r"^\| TermCheck \| 120 \|.*$", readme, re.M)
    if fila:
        columnas = [c.strip() for c in fila.group().split("|")[1:-1]]
        st.caption(f"Evaluación publicada de la versión 0.1: precisión {columnas[6].split()[0]}, "
                   f"recall {columnas[7].split()[0]}, F1 {columnas[8]}. La demo usa la versión 0.2.")
else:
    st.title("Verificar")
st.markdown("Pegá el inglés y su traducción. TermCheck compara los términos con el glosario y señala qué revisar.")


@st.cache_data(show_spinner=False)
def leer_tsv(ruta, marca):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def glosario_proyecto():
    """El glosario del proyecto. La demo usa el v1 congelado (el que se evaluó), si ya existe."""
    congelado = datos.GLOSARIO.parent / "glossary_v1.csv"
    return cargar(congelado if DEMO and congelado.exists() else datos.GLOSARIO)


# --- Glosario ---------------------------------------------------------------------------------------------------
with st.expander("Usar otro glosario (CSV)"):
    propio = st.file_uploader("Glosario propio", type=["csv"], key="vf_glosario", max_upload_size=1 if DEMO else None,
                              help="Columnas: id, en, pos, es_preferred, es_allowed, es_forbidden, subdomain, note, "
                                   "source. Variantes separadas por «|».")
if propio:
    try:
        terminos = cargar_bytes(propio.getvalue())
    except ErrorDeGlosario as e:
        st.error(f"No se pudo usar ese glosario: {e}")
        st.stop()
    errores = [p for p in validar(terminos) if p.tipo == "error"]
    if errores:
        st.warning(f"El glosario subido tiene {len(errores)} errores; el resultado puede fallar.  \n"
                   + "  \n".join(str(p) for p in errores[:5]))
    if DEMO and len(terminos) > MAX_TERMINOS:
        st.error(f"El glosario subido tiene {len(terminos)} términos. En la demo el máximo es {MAX_TERMINOS}.")
        st.stop()
    st.caption(f"Glosario subido: {len(terminos)} términos.")
else:
    terminos = glosario_proyecto()
    st.caption(f"Glosario del proyecto: {len(terminos)} términos.")

# --- Entrada ----------------------------------------------------------------------------------------------------
MODOS = {"pegar": "Pegar texto", "tsv": "Subir archivo", "corpus": "Corpus (desarrollo)"}
if DEMO:
    del MODOS["corpus"]
modo = st.segmented_control("Entrada", list(MODOS), format_func=MODOS.get, default="pegar", key="vf_modo",
                            label_visibility="collapsed") or "pegar"

def cargar_ejemplo():
    seg = {f["seg_id"]: f["source_en"] for f in leer_tsv(str(RAIZ / "data/corpus/segments.tsv"), 0)}
    tr = {(f["seg_id"], f["system"]): f["target_es"]
          for f in leer_tsv(str(RAIZ / "data/mt/translations.tsv"), 0)}
    ids = ["S004", "S078", "S079"]  # desarrollo; nunca la prueba
    st.session_state.vf_en = "\n".join(seg[i] for i in ids)
    st.session_state.vf_es = "\n".join(tr[(i, "opusmt")] for i in ids)
    st.session_state.vf_pedir = True


def vaciar():
    st.session_state.vf_en = ""
    st.session_state.vf_es = ""
    st.session_state.pop("vf_resultado", None)
    st.session_state.vf_pedir = False


if DEMO and "vf_iniciada" not in st.session_state:
    cargar_ejemplo()
    st.session_state.vf_iniciada = True

pares = []
pedir = st.session_state.pop("vf_pedir", False)
if modo == "pegar":
    b1, b2, _ = st.columns([1.5, 1, 4])
    b1.button("Cargar un ejemplo", on_click=cargar_ejemplo, type="tertiary")
    b2.button("Vaciar", on_click=vaciar, type="tertiary")
    with st.form("vf_textos", border=False):
        c1, c2 = st.columns(2)
        tope = MAX_LETRAS if DEMO else None
        en = c1.text_area("Inglés", key="vf_en", height=180, placeholder="Una oración por línea", max_chars=tope)
        es = c2.text_area("Traducción", key="vf_es", height=180, max_chars=tope,
                          placeholder="La traducción de cada línea, en el mismo orden")
        pedir = st.form_submit_button("Verificar", type="primary") or pedir
    l_en = [x for x in en.splitlines() if x.strip()]
    l_es = [x for x in es.splitlines() if x.strip()]
    if l_en and l_es:
        if len(l_en) == len(l_es):
            pares = [(f"L{i}", "", a, b) for i, (a, b) in enumerate(zip(l_en, l_es), start=1)]
        else:
            if pedir:
                st.info(f"El inglés tiene {len(l_en)} líneas y la traducción {len(l_es)}. Se verifica como un solo "
                        "segmento. Para separar las oraciones, poné una por línea en los dos lados.")
            pares = [("L1", "", " ".join(l_en), " ".join(l_es))]
    elif pedir:
        st.info("Completá el inglés y la traducción para verificar.")

elif modo == "tsv":
    st.caption("TSV o CSV con dos columnas: inglés y traducción (con encabezado `source_en` y `target_es`, o "
               "sin encabezado). Una fila por segmento. También XLIFF 1.2, XLIFF 2.0 y TMX (`.xliff`, `.xlf`, "
               "`.tmx`): se probaron con archivos armados a mano según la norma, no con exportaciones reales de "
               "Trados o memoQ, y no se leen `.sdlxliff` ni `.mqxliff`."
               + (f" En la demo: hasta 1 MB y {MAX_SEGMENTOS} segmentos." if DEMO else ""))
    archivo = st.file_uploader("Archivo", type=["tsv", "csv", "txt", "xliff", "xlf", "tmx"],
                               label_visibility="collapsed", key="vf_archivo", max_upload_size=1 if DEMO else None)
    if archivo and es_de_traduccion(archivo.name):
        try:
            leidos, sin_traduccion = leer_formato(archivo.getvalue(), archivo.name)
        except ErrorDeFormato as e:
            st.warning(str(e))
            st.stop()
        pares = [(seg_id, "", en, es) for seg_id, en, es in leidos]
        if sin_traduccion:
            st.caption(f"Se saltearon {sin_traduccion} segmentos sin traducción." if sin_traduccion != 1 else
                       "Se salteó 1 segmento sin traducción.")
        if not pares:
            st.warning("Ningún segmento del archivo tiene traducción.")
    elif archivo:
        try:
            texto = archivo.getvalue().decode("utf-8-sig")
        except UnicodeDecodeError:
            st.warning("No pude leer el archivo. Tiene que ser texto en UTF-8.")
            st.stop()
        if not texto.strip():
            st.warning("El archivo está vacío.")
            st.stop()
        sep = "\t" if "\t" in texto.splitlines()[0] else ","
        filas = list(csv.reader(io.StringIO(texto), delimiter=sep))
        if filas and [c.strip().lower() for c in filas[0][:2]] == ["source_en", "target_es"]:
            filas = filas[1:]
        filas = [f for f in filas if len(f) >= 2 and f[0].strip()]
        pares = [(f"F{i}", "", f[0], f[1]) for i, f in enumerate(filas, start=1)]
        if not pares:
            st.warning("No encontré filas con dos columnas.")

else:
    seg = {f["seg_id"]: f["source_en"] for f in leer_tsv(str(RAIZ / "data/corpus/segments.tsv"), 0)}
    dev = [l.strip() for l in (RAIZ / "data/splits/dev_ids.txt").read_text().splitlines() if l.strip()]
    tr = leer_tsv(str(RAIZ / "data/mt/translations.tsv"), 0)
    sistemas = sorted({f["system"] for f in tr})
    c1, c2 = st.columns([1, 2])
    elegidos = c1.multiselect("Sistemas", sistemas, default=sistemas)
    ids = c2.multiselect("Oraciones (desarrollo)", dev, default=dev[:5],
                         help="Solo el conjunto de desarrollo: la prueba se anota a ciegas.")
    pares = [(f["seg_id"], f["system"], seg[f["seg_id"]], f["target_es"]) for f in tr
             if f["seg_id"] in ids and f["system"] in elegidos]
    pares.sort(key=lambda p: (p[0], p[1]))

if modo != "pegar":
    pedir = st.button("Verificar", type="primary")

# El glosario y el modo forman parte del resultado. No se muestran resultados de otra entrada.
firma = hashlib.sha256(repr((modo, terminos, pares)).encode()).hexdigest()
if pedir:
    st.session_state.pop("vf_resultado", None)
    if pares:
        seguir = True
        aviso = ""
        if DEMO:
            pares, aviso, seguir = aplicar(pares)
        if aviso:
            st.warning(aviso)
        if seguir:
            with st.spinner("Verificando…"):
                resultado = [(p, verificar(p[2], p[3], terminos, p[0], p[1])) for p in pares]
            todas = [o for _, oc in resultado for o in oc]
            st.session_state.vf_resultado = (firma, resultado, todas, inconsistencias(todas))

previo = st.session_state.get("vf_resultado")
if not previo or previo[0] != firma:
    st.stop()
_, resultado, todas, advertencias = previo
st.subheader("Reporte")
st.markdown(report.resumen(todas, len(resultado)))
st.caption(report.recuento(todas))
c1, c2, c3 = st.columns([1, 1, 3])
solo = c3.checkbox("Mostrar solo lo que hay que revisar", value=False)
c1.download_button("CSV", a_csv_texto(todas), "termcheck.csv", "text/csv", width="stretch", on_click="ignore")
segmentos = {p[0]: p[2] for p, _ in resultado}
traducciones = [{"seg_id": p[0], "system": p[1], "target_es": p[3]} for p, _ in resultado]
c2.download_button("HTML", a_html(segmentos, traducciones, todas, advertencias), "termcheck.html", "text/html",
                   width="stretch", on_click="ignore")
if advertencias:
    st.html(report.avisos_html(advertencias))
for (seg_id, sistema, en, es), oc in resultado:
    if solo and not any(o.marcada for o in oc):
        continue
    st.html(report.bloque_segmento(en, es, oc, solo=solo,
                                   cabecera=" · ".join(x for x in (seg_id, sistema) if x)))
with st.expander("Qué significa cada etiqueta"):
    st.html(report.leyenda())
    st.caption("Las sugerencias se basan en el parecido de letras. Nunca cambian la etiqueta.")
