"""Página «Verificar» (Fase 5 del plan): pegar un texto en inglés y su traducción, o subir un archivo (TSV, CSV,
XLIFF o TMX), y ver el reporte.

Usa el glosario del proyecto o uno que sube la persona (mismo formato de columnas). El verificador es el de
src/termcheck (el mismo que se evalúa); esta página solo lo muestra.

Del corpus del proyecto solo ofrece el conjunto de desarrollo: ver el resultado del verificador sobre la prueba
antes de anotarla rompería la anotación a ciegas.

En la demo pública (app/demo.py, TERMCHECK_DEMO=1) la página funciona sin login, usa la edición publicada del
glosario, no ofrece el corpus y tiene límites de tamaño, porque el servidor es compartido.
"""
import csv
import os
import hashlib
import re

import streamlit as st

import datos
import vista
from entrada import leer_tabla
from limites import MAX_LETRAS, MAX_SEGMENTOS, MAX_TERMINOS, aplicar
from termcheck.checker import verificar
from termcheck.consistency import inconsistencias
from termcheck.formatos import ErrorDeFormato, es_de_traduccion, leer as leer_formato
from termcheck.glossary import ErrorDeGlosario, cargar_bytes, publicado, validar
from termcheck import NOMBRE, VERSION
from termcheck import report

RAIZ = datos.RAIZ
DEMO = os.environ.get("TERMCHECK_DEMO") == "1"

vista.estilos()
st.html("<style>" + report.CSS + "</style>")


@st.cache_data(show_spinner=False)
def leer_tsv(ruta, marca):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


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
    st.session_state.pop("vf_aviso", None)
    st.session_state.vf_pedir = False
    st.session_state.vf_editor_abierto = True


def recordar_archivo(widget, memoria):
    """Conserva la carga al navegar; una eliminación explícita también borra la copia de sesión."""
    actual = st.session_state.get(widget)
    if actual is None:
        st.session_state.pop(memoria, None)
    else:
        st.session_state[memoria] = actual


MODOS = {"pegar": "Pegar texto", "tsv": "Subir archivo", "corpus": "Corpus (desarrollo)"}
if DEMO:
    del MODOS["corpus"]

st.session_state.setdefault("vf_editor_abierto", True)
if st.session_state.pop("vf_cerrar_editor", False):
    st.session_state.vf_editor_abierto = False
# Se completa al final, cuando sabemos si hay un resultado vigente.
titulo_entrada = st.container(key="vf_intro")
with st.container(key="vf_editor"):
    with st.expander("Textos", expanded=True, key="vf_editor_abierto", on_change="rerun"):
        with st.container(horizontal=True, vertical_alignment="center", gap="small"):
            modo = st.segmented_control("Entrada", list(MODOS), format_func=MODOS.get,
                                        default="pegar", required=True, key="vf_modo",
                                        label_visibility="collapsed")
            with st.popover("Cambiar glosario"):
                st.caption("Incluido: glosario O&G. Podés cargar otro en CSV.")
                nuevo_glosario = st.file_uploader("Glosario propio (CSV)", type=["csv"], key="vf_glosario",
                                          max_upload_size=1 if DEMO else None,
                                          on_change=recordar_archivo, args=("vf_glosario", "vf_glosario_memoria"),
                                          help="Columnas: id, en, pos, es_preferred, es_allowed, es_forbidden, "
                                               "subdomain, note, source. Variantes separadas por |.")
                propio = nuevo_glosario or st.session_state.get("vf_glosario_memoria")
                if propio and not nuevo_glosario:
                    st.caption(f"Glosario en uso: {propio.name}")
                    if st.button("Volver al glosario del proyecto"):
                        st.session_state.pop("vf_glosario_memoria", None)
                        st.rerun()
        if propio:
            try:
                bytes_glosario = propio.getvalue()
                terminos = cargar_bytes(bytes_glosario)
            except ErrorDeGlosario as e:
                st.error(f"No se pudo usar ese glosario: {e}")
                st.stop()
            errores = [p for p in validar(terminos) if p.tipo == "error"]
            if errores:
                st.error(f"No se puede verificar con este glosario: tiene {len(errores)} errores.  \n"
                           + "  \n".join(str(p) for p in errores[:5]))
                st.stop()
            if not terminos:
                st.error("El glosario no tiene términos. Agregá al menos uno para verificar.")
                st.stop()
            if DEMO and len(terminos) > MAX_TERMINOS:
                st.error(f"El glosario subido tiene {len(terminos)} términos. En la demo el máximo es {MAX_TERMINOS}.")
                st.stop()
            nombre_glosario = "Glosario propio"
        else:
            ruta_glosario = publicado(datos.GLOSARIO.parent) if DEMO else datos.GLOSARIO
            bytes_glosario = ruta_glosario.read_bytes()
            terminos = cargar_bytes(bytes_glosario)
            nombre_glosario = "Glosario O&G"

        referencia_glosario = ((propio.name if propio else ruta_glosario.name)
                              + " · SHA-256 " + hashlib.sha256(bytes_glosario).hexdigest())
        pares = []
        pedir = st.session_state.pop("vf_pedir", False)
        if modo == "pegar":
            with st.container(key="vf_textos"):
                c1, c2 = st.columns(2)
                tope = MAX_LETRAS if DEMO else None
                en = c1.text_area("Original · inglés", key="vf_en", height=210, placeholder="Pegá el original",
                                  max_chars=tope, help="Si hay varios segmentos, poné uno por línea en ambos textos.")
                es = c2.text_area("Traducción · español", key="vf_es", height=210, max_chars=tope,
                                  placeholder="Pegá la traducción")
                with st.container(horizontal=True, vertical_alignment="center"):
                    pedir = st.button("Verificar", type="primary") or pedir
                    st.button("Vaciar", on_click=vaciar, type="tertiary")
                    st.caption(f"{nombre_glosario} · {len(terminos)} términos" + (" · Los textos no se guardan." if DEMO else ""))
            l_en = en.splitlines()
            l_es = es.splitlines()
            if en.strip() and es.strip():
                if len(l_en) == len(l_es):
                    if any(not a.strip() and b.strip() for a, b in zip(l_en, l_es)):
                        if pedir:
                            st.warning("Hay una línea con traducción pero sin original en inglés. "
                                       "Alineá los textos: una pareja por línea. No se verificó el texto.")
                    else:
                        pares = [(f"L{i}", "", a, b) for i, (a, b) in enumerate(zip(l_en, l_es), start=1)
                                 if a.strip()]
                else:
                    if pedir:
                        st.warning(f"El inglés tiene {len(l_en)} líneas y la traducción {len(l_es)}. "
                                   "Alineá los textos: una pareja por línea. No se verificó el texto.")
            elif pedir:
                st.info("Completá el inglés y la traducción para verificar.")

        elif modo == "tsv":
            st.caption("Subí un archivo bilingüe en TSV, CSV, XLIFF o TMX.")
            nuevo_archivo = st.file_uploader("Archivo", type=["tsv", "csv", "txt", "xliff", "xlf", "tmx"],
                                       label_visibility="collapsed", key="vf_archivo", max_upload_size=1 if DEMO else None,
                                       on_change=recordar_archivo, args=("vf_archivo", "vf_archivo_memoria"))
            archivo = nuevo_archivo or st.session_state.get("vf_archivo_memoria")
            if archivo and not nuevo_archivo:
                st.caption(f"Archivo en uso: {archivo.name}")
                if st.button("Quitar archivo"):
                    st.session_state.pop("vf_archivo_memoria", None)
                    st.rerun()
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
                    filas = leer_tabla(archivo.getvalue())
                except ValueError as e:
                    st.warning(str(e))
                    st.stop()
                pares = [(f"F{i}", "", f[0], f[1]) for i, f in enumerate(filas, start=1)]

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
            with st.container(horizontal=True, vertical_alignment="center"):
                pedir = st.button("Verificar", type="primary")
                st.caption(f"{nombre_glosario} · {len(terminos)} términos")
            if modo == "tsv":
                with st.expander("Formatos y límites"):
                    st.markdown("TSV/CSV en UTF-8: dos columnas (`source_en`, `target_es`), con o sin encabezado, "
                                "separadas por tabulación, coma o punto y coma. "
                                "Una fila por segmento. XLIFF 1.2, XLIFF 2.0 y TMX: se leen los segmentos con traducción. "
                                "No se admiten SDLXLIFF ni MQXLIFF; no se probaron exportaciones reales de Trados o memoQ.")
                    if DEMO:
                        st.caption("Hasta 1 MB, 200 segmentos y 20.000 caracteres por idioma.")

# El glosario y el modo forman parte del resultado. No se muestran resultados de otra entrada.
firma = hashlib.sha256(repr((modo, terminos, pares)).encode()).hexdigest()
if pedir:
    st.session_state.pop("vf_resultado", None)
    st.session_state.pop("vf_aviso", None)
    if pares:
        seguir = True
        aviso = ""
        if DEMO:
            pares, aviso, seguir = aplicar(pares)
        if aviso:
            st.session_state.vf_aviso = aviso
        if seguir:
            with st.spinner("Verificando…"):
                resultado = [(p, verificar(p[2], p[3], terminos, p[0], p[1])) for p in pares]
            todas = [o for _, oc in resultado for o in oc]
            st.session_state.vf_resultado = (firma, resultado, todas, inconsistencias(todas))
            st.session_state.recorrido_visto = True
            st.session_state.vf_cerrar_editor = True
            st.rerun()


if st.session_state.get("vf_aviso"):
    st.warning(st.session_state.vf_aviso)
previo = st.session_state.get("vf_resultado")
if not previo or previo[0] != firma:
    with titulo_entrada:
        with st.container(horizontal=True, vertical_alignment="center"):
            st.html('<div class="tc-page-intro tc-workspace-title"><h2>Verificar traducción</h2></div>')
            if modo == "pegar":
                st.button("Usar ejemplo", on_click=cargar_ejemplo, type="tertiary")
if previo and previo[0] == firma:
    from revision import mostrar
    _, resultado, todas, advertencias = previo
    mostrar(resultado, todas, advertencias, glosario=referencia_glosario, terminos=terminos)
elif not pares:
    if DEMO:
        import catalogo
        proyecto = catalogo.leer()
        with st.container(horizontal=True, vertical_alignment="center"):
            st.subheader("Glosario O&G")
            st.page_link("paginas/glosario_publico.py", label=f"Ver los {len(proyecto)} términos →")
        st.html(catalogo.fichas(catalogo.destacados(proyecto), compactas=True))
    else:
        st.html('<p class="tc-empty">Pegá los dos textos o usá el ejemplo para empezar.</p>')

if DEMO:
    with st.expander("Acerca de TermCheck"):
        st.markdown("Compara los términos con un glosario técnico de español de Argentina. "
                    "Señala qué revisar; no traduce ni corrige el estilo. Los textos no se guardan.")
        edicion = publicado(datos.GLOSARIO.parent).stem.removeprefix("glossary_").replace("_", ".")
        st.caption(f"Versión {VERSION} · Glosario {edicion}")
        st.markdown("[Código, método y evaluación](https://github.com/ismaelcharles/termcheck-og)")
        readme = (RAIZ / "README.md").read_text(encoding="utf-8")
        fila = re.search(r"^\| TermCheck \| 120 \|.*$", readme, re.M)
        if fila:
            columnas = [c.strip() for c in fila.group().split("|")[1:-1]]
            st.caption(f"Demo pública · Evaluación publicada de la versión 0.1 con glosario v1: "
                       f"precisión {columnas[6].split()[0]}, recall {columnas[7].split()[0]}, F1 {columnas[8]}.")
