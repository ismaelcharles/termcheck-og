"""Página «Verificar» (Fase 5 del plan): pegar un texto en inglés y su traducción, o subir un TSV, y ver el reporte.

Usa el glosario del proyecto o uno que sube la persona (mismo formato de columnas). El verificador es el de
src/termcheck (el mismo que se evalúa); esta página solo lo muestra.

Del corpus del proyecto solo ofrece el conjunto de desarrollo: ver el resultado del verificador sobre la prueba
antes de anotarla rompería la anotación a ciegas.
"""
import csv
import io
import tempfile
from collections import Counter
from pathlib import Path

import streamlit as st

import datos
import vista
from termcheck.checker import verificar
from termcheck.consistency import inconsistencias
from termcheck.glossary import ErrorDeGlosario, cargar, validar
from termcheck.report import NOMBRES, a_csv_texto, a_html

RAIZ = datos.RAIZ
ORDEN = ["PROHIBIDO", "SIN_TRADUCIR", "NO_ENCONTRADO", "VARIANTE", "OK"]

st.html(vista.CSS + """<style>
.vf-seg{border:1px solid #D8D0C2;border-radius:.6rem;padding:.7rem 1rem .5rem;margin:.6rem 0;background:#FFFEFB}
.vf-txt{font-size:1.02rem;line-height:2}
.vf-es{border-left:3px solid #D8D0C2;padding-left:.8rem;margin:.2rem 0 .5rem}
.vf-items{list-style:none;padding:0;margin:.2rem 0 .2rem;font-size:.9rem}
.vf-items li{margin:.2rem 0}
.vf-items code{font-size:.74rem;color:#7A7266;background:none}
.vf-sug{color:#5E4682;font-style:italic}
.vf-cab{font:600 .78rem ui-monospace,monospace;color:#7A7266;margin-bottom:.2rem}
.vf-resumen{display:flex;flex-wrap:wrap;gap:.4rem;margin:.3rem 0 .6rem}
</style>""")
st.title("Verificar")
st.markdown("Pegá un texto en inglés y su traducción automática. TermCheck busca cada término del glosario en el "
            "inglés y te dice cómo quedó en la traducción.")


@st.cache_data(show_spinner=False)
def leer_tsv(ruta, marca):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def glosario_proyecto():
    return cargar(datos.GLOSARIO)


# --- Glosario ---------------------------------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Glosario")
    propio = st.file_uploader("Usar otro glosario (CSV)", type=["csv"],
                              help="Columnas: id, en, pos, es_preferred, es_allowed, es_forbidden, subdomain, note, "
                                   "source. Variantes separadas por «|».")
if propio:
    with tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False) as f:
        f.write(propio.getvalue())
    try:
        terminos = cargar(f.name)
    except ErrorDeGlosario as e:
        st.error(f"No se pudo usar ese glosario: {e}")
        st.stop()
    finally:
        Path(f.name).unlink(missing_ok=True)
    errores = [p for p in validar(terminos) if p.tipo == "error"]
    if errores:
        st.warning(f"El glosario subido tiene {len(errores)} errores; el resultado puede fallar.  \n"
                   + "  \n".join(str(p) for p in errores[:5]))
    st.sidebar.caption(f"Glosario subido: {len(terminos)} términos.")
else:
    terminos = glosario_proyecto()
    st.sidebar.caption(f"Glosario del proyecto: {len(terminos)} términos.")

# --- Entrada ----------------------------------------------------------------------------------------------------
MODOS = {"pegar": "Pegar texto", "tsv": "Subir archivo", "corpus": "Corpus (desarrollo)"}
modo = st.segmented_control("Entrada", list(MODOS), format_func=MODOS.get, default="pegar", key="vf_modo",
                            label_visibility="collapsed") or "pegar"

pares = []  # [(seg_id, system, en, es)]
if modo == "pegar":
    def cargar_ejemplo():
        seg = {f["seg_id"]: f["source_en"] for f in leer_tsv(str(RAIZ / "data/corpus/segments.tsv"), 0)}
        tr = {(f["seg_id"], f["system"]): f["target_es"]
              for f in leer_tsv(str(RAIZ / "data/mt/translations.tsv"), 0)}
        ids = ["S004", "S078", "S079"]  # del conjunto de desarrollo
        st.session_state.vf_en = "\n".join(seg[i] for i in ids)
        st.session_state.vf_es = "\n".join(tr[(i, "opusmt")] for i in ids)

    st.button("Cargar un ejemplo", on_click=cargar_ejemplo, type="tertiary", icon=":material/science:",
              help="Tres oraciones del corpus (desarrollo) traducidas con Opus-MT.")
    c1, c2 = st.columns(2)
    en = c1.text_area("Inglés", key="vf_en", height=180, placeholder="Una oración por línea")
    es = c2.text_area("Traducción", key="vf_es", height=180, placeholder="La traducción de cada línea, en el mismo orden")
    l_en = [x for x in en.splitlines() if x.strip()]
    l_es = [x for x in es.splitlines() if x.strip()]
    if l_en and l_es:
        if len(l_en) == len(l_es):
            pares = [(f"L{i}", "", a, b) for i, (a, b) in enumerate(zip(l_en, l_es), start=1)]
        else:
            st.info(f"El inglés tiene {len(l_en)} líneas y la traducción {len(l_es)}. Se verifica todo como un solo "
                    "segmento; para ver oración por oración, poné una por línea en los dos lados.")
            pares = [("L1", "", " ".join(l_en), " ".join(l_es))]

elif modo == "tsv":
    st.caption("TSV o CSV con dos columnas: inglés y traducción (con encabezado `source_en` y `target_es`, o "
               "sin encabezado). Una fila por segmento.")
    archivo = st.file_uploader("Archivo", type=["tsv", "csv", "txt"], label_visibility="collapsed")
    if archivo:
        texto = archivo.getvalue().decode("utf-8-sig")
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

if not pares:
    st.stop()

# --- Verificación -----------------------------------------------------------------------------------------------
with st.spinner("Verificando…"):
    resultado = [(p, verificar(p[2], p[3], terminos, p[0], p[1])) for p in pares]
todas = [o for _, oc in resultado for o in oc]
advertencias = inconsistencias(todas)

cuenta = Counter(o.label for o in todas)
marcadas = sum(o.marcada for o in todas)
st.subheader("Reporte")
st.html('<div class="vf-resumen">' + "".join(
    f'{vista.chip(f"{NOMBRES[k]}: {cuenta[k]}", k)}' for k in ORDEN if cuenta[k]) + "</div>")
st.markdown(f"**{len(todas)}** términos encontrados en {len(pares)} segmento(s); **{marcadas}** para revisar.")

c1, c2, c3 = st.columns([1, 1, 2])
solo = c3.toggle("Mostrar solo lo que hay que revisar", value=False)
c1.download_button("CSV", a_csv_texto(todas), "termcheck.csv", "text/csv", icon=":material/download:",
                   width="stretch")
segmentos = {p[0]: p[2] for p in pares}
traducciones = [{"seg_id": p[0], "system": p[1], "target_es": p[3]} for p in pares]
c2.download_button("HTML", a_html(segmentos, traducciones, todas, advertencias), "termcheck.html", "text/html",
                   icon=":material/download:", width="stretch")

if advertencias:
    with st.container(border=True):
        st.html(f'{vista.etiqueta("INCONSISTENTE")} <b>El mismo término, traducido de formas distintas</b>')
        for a in advertencias:
            formas = " · ".join(f"«{f}» ({', '.join(s)})" for f, s in a.formas.items())
            st.markdown(f"- `{a.term_id}`{' ' + a.system if a.system else ''}: {formas}")


def resaltar(texto, tramos):
    partes, pos = [], 0
    for inicio, fin, label, titulo in sorted(t for t in tramos if t[0] >= 0):
        if inicio < pos:
            continue
        color, fondo, _ = vista.ETIQUETAS[label]
        partes.append(vista.e(texto[pos:inicio]))
        partes.append(f'<span class="tc-marca" style="color:{color};background:{fondo};border-color:{color}" '
                      f'title="{vista.e(titulo)}">{vista.e(texto[inicio:fin])}</span>')
        pos = fin
    partes.append(vista.e(texto[pos:]))
    return "".join(partes)


por_id = {t.id: t for t in terminos}
for (seg_id, sistema, en, es), oc in resultado:
    if solo and not any(o.marcada for o in oc):
        continue
    t_en = resaltar(en, [(o.src_start, o.src_end, o.label, f"{o.term_id} · {NOMBRES[o.label]}") for o in oc])
    t_es = resaltar(es, [(o.start, o.end, o.label, f"{o.term_id} · {NOMBRES[o.label]}") for o in oc])
    items = []
    for o in sorted(oc, key=lambda o: ORDEN.index(o.label)):
        if solo and not o.marcada:
            continue
        t = por_id.get(o.term_id)
        if o.label == "OK":
            det = f"«{vista.e(o.es_found)}»"
        elif o.label == "VARIANTE":
            det = f"«{vista.e(o.es_found)}», válida; la preferida es «{vista.e(o.es_expected)}»"
        elif o.label == "PROHIBIDO":
            det = f"«{vista.e(o.es_found)}» está marcada como error. Usar «{vista.e(o.es_expected)}»"
        elif o.label == "SIN_TRADUCIR":
            det = f"quedó en inglés («{vista.e(o.es_found)}»). Usar «{vista.e(o.es_expected)}»"
        else:
            conocidas = [o.es_expected] + (t.es_allowed if t else [])
            det = "no aparece ninguna traducción conocida: " + ", ".join(f"«{vista.e(x)}»" for x in conocidas)
            if o.suggestion:
                det += f' <span class="vf-sug">¿quizás «{vista.e(o.suggestion)}»?</span>'
        items.append(f'<li>{vista.etiqueta(o.label)} <b>{vista.e(o.term_en)}</b> <code>{o.term_id}</code> → {det}'
                     f'</li>')
    cab = " · ".join(x for x in [seg_id, sistema] if x)
    st.html(f'<div class="vf-seg"><div class="vf-cab">{vista.e(cab)}</div>'
            f'<div class="tc-idioma">Inglés</div><div class="vf-txt">{t_en}</div>'
            f'<div class="tc-idioma">Traducción</div><div class="vf-txt vf-es">{t_es}</div>'
            + (f'<ul class="vf-items">{"".join(items)}</ul>' if items else
               '<div class="tc-meta">Ningún término del glosario en este segmento.</div>') + '</div>')

with st.expander("Qué significa cada etiqueta"):
    st.html(vista.leyenda())
    st.caption("Las sugerencias («¿quizás…?») salen de un parecido de letras (rapidfuzz). Nunca cambian la etiqueta.")
