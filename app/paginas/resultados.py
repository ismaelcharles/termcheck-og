"""Página «Resultados» (Fases 1b y 4): sugerencias para el glosario desde la anotación de desarrollo, congelar el
glosario v1 y la evaluación (desarrollo ahora; prueba cuando esté anotada entera).

Las sugerencias salen de comparar la anotación del dueño con el verificador en DESARROLLO:
- «Error de término» con una forma que el glosario no tiene → posible prohibida.
- «Correcto» que el verificador marcó (falso positivo) → posible variante válida que falta.
Nada entra al glosario sin que el dueño toque el botón (plan, regla 5).

La prueba se evalúa con el glosario congelado (data/glossary/glossary_v1.csv), una vez anotadas las 20 oraciones.
"""
import hashlib
import sys
from datetime import datetime

import streamlit as st

import anotacion as an
import datos
import vista
from termcheck import VERSION
from termcheck.normalize import normalizar

sys.path.insert(0, str(datos.RAIZ / "scripts"))
import evaluate as ev  # noqa: E402
import actualizar_readme as ar  # noqa: E402
import publicar as pub  # noqa: E402

CONGELADO = datos.GLOSARIO.parent / "glossary_v1.csv"
REGISTRO = datos.GLOSARIO.parent / "glossary_v1.txt"

vista.estilos()
st.title("Resultados")

pestana = st.segmented_control("Vista", ["sug", "dev", "prueba", "pub"], key="res_vista", default="sug",
                               format_func={"sug": "Sugerencias para el glosario", "dev": "Evaluación · desarrollo",
                                            "prueba": "Evaluación · prueba", "pub": "Publicar"}.get,
                               label_visibility="collapsed") or "sug"


def formas_de(fila):
    return {normalizar(x) for x in [fila["es_preferred"]] + datos.variantes(fila["es_allowed"])
            + datos.variantes(fila["es_forbidden"])}


def agregar(term_id, columna, forma):
    tabla = datos.leer()
    fila = tabla[tabla["id"] == term_id].iloc[0].to_dict()
    fila[columna] = datos.juntar(datos.variantes(fila[columna]) + [forma])
    datos.guardar_fila(fila)
    st.session_state.setdefault("res_hechas", []).append((term_id, columna, forma))
    st.toast(f"{term_id}: «{forma}» agregada como {'prohibida' if columna == 'es_forbidden' else 'válida'}.")


def descartar(clave):
    st.session_state.setdefault("res_descartadas", set()).add(clave)


# --- Sugerencias ------------------------------------------------------------------------------------------------
if pestana == "sug":
    st.markdown("Salen de comparar **tu anotación de desarrollo** con lo que dijo el verificador. Son sugerencias a "
                "verificar: cada una entra al glosario solo si tocás el botón.")
    if CONGELADO.exists():
        st.info("El glosario v1 ya está congelado. Si agregás algo, cambia el glosario de trabajo, no el v1.")
    casos = ev.evaluar("desarrollo")
    tabla = datos.leer()
    glos = {f["id"]: f for _, f in tabla.iterrows()}
    descartadas = st.session_state.get("res_descartadas", set())

    prohibidas, validas = {}, []
    for c in casos:
        f = glos.get(c["term_id"])
        if f is None:
            continue
        if c["label"] == "ERROR_TERMINO" and c["es_used"] and normalizar(c["es_used"]) not in formas_de(f):
            prohibidas.setdefault((c["term_id"], c["es_used"].lower()), []).append(c)
        elif c["label"] == "CORRECTO" and c["marca_verificador"]:
            validas.append(c)

    st.subheader(f"Posibles prohibidas ({len(prohibidas)})")
    st.caption("Formas que marcaste como «Error de término» y que el glosario todavía no tiene.")
    if not prohibidas:
        st.caption("Ninguna por ahora.")
    for (term_id, _), cs in sorted(prohibidas.items()):
        f = glos[term_id]
        forma = cs[0]["es_used"]
        clave = ("p", term_id, forma.lower())
        if clave in descartadas:
            continue
        with st.container(border=True):
            st.html(f'<b>{vista.e(f["en"])}</b> <span class="tc-id">{term_id}</span> · preferida '
                    f'{vista.chip(f["es_preferred"], "OK")} · usada {vista.chip(forma, "PROHIBIDO", tachado=True)} '
                    f'<span class="tc-meta">en {len(cs)} traducción(es): '
                    f'{vista.e(", ".join(sorted({c["seg_id"] for c in cs})))}</span>')
            comentarios = [c["comment"] for c in cs if c["comment"]]
            if comentarios:
                st.caption("Tu comentario: " + " · ".join(comentarios))
            b1, b2, _ = st.columns([1.3, 1, 2])
            b1.button("Agregar como prohibida", key=f"ap_{term_id}_{forma}", on_click=agregar,
                      args=(term_id, "es_forbidden", forma), icon=":material/block:", width="stretch")
            b2.button("No", key=f"np_{term_id}_{forma}", on_click=descartar, args=(clave,), width="stretch")

    st.subheader(f"Posibles variantes válidas ({len(validas)})")
    st.caption("Términos que anotaste como «Correcto» pero el verificador marcó: probablemente la traducción usó "
               "una forma que el glosario no lista. Escribí la forma exacta y agregala, o dejala pasar.")
    if not validas:
        st.caption("Ninguna por ahora.")
    for c in validas:
        f = glos[c["term_id"]]
        clave = ("v", c["seg_id"], c["system"], c["term_id"])
        if clave in descartadas:
            continue
        with st.container(border=True):
            st.html(f'<b>{vista.e(f["en"])}</b> <span class="tc-id">{c["term_id"]} · {c["seg_id"]}</span> · '
                    f'glosario: {vista.chip(f["es_preferred"], "OK")}'
                    + "".join(vista.chip(v, "VARIANTE") for v in datos.variantes(f["es_allowed"]))
                    + f'<div class="tc-oracion" style="font-size:.95rem;line-height:1.7">'
                      f'{vista.e(c["target_es"])}</div>')
            k = f"fv_{c['seg_id']}_{c['system']}_{c['term_id']}"
            sug = c["es_used"] or ""
            a1, a2, a3 = st.columns([2, 1.3, .7], vertical_alignment="bottom")
            forma = a1.text_input("Forma a agregar", value=sug, key=k, placeholder="Copiá las palabras de la traducción")
            a2.button("Agregar como válida", key=f"av_{k}", on_click=agregar, args=(c["term_id"], "es_allowed",
                      forma.strip()), disabled=not forma.strip() or normalizar(forma) in formas_de(f),
                      icon=":material/add:", width="stretch")
            a3.button("No", key=f"nv_{k}", on_click=descartar, args=(clave,), width="stretch")

    hechas = st.session_state.get("res_hechas", [])
    if hechas:
        st.success("Agregadas en esta visita: " + "; ".join(f"{t} «{x}»" for t, _, x in hechas))

    st.subheader("Congelar el glosario v1")
    st.markdown("Cuando termines con las sugerencias, congelá el glosario: la evaluación de la prueba usa esa "
                "copia, para que nadie ajuste el glosario mirando la prueba (plan, Fase 1b).")
    if CONGELADO.exists():
        st.caption(REGISTRO.read_text(encoding="utf-8") if REGISTRO.exists() else "Congelado.")
    else:
        confirmar = st.checkbox("Terminé de revisar el glosario y las sugerencias")

        def congelar():
            contenido = datos.GLOSARIO.read_bytes()
            CONGELADO.write_bytes(contenido)
            n = len(datos.leer())
            REGISTRO.write_text(f"glossary-v1 · {datetime.now():%Y-%m-%d %H:%M} · {n} términos · sha256 "
                                f"{hashlib.sha256(contenido).hexdigest()[:16]}\n", encoding="utf-8")

        st.button("Congelar glosario v1", on_click=congelar, disabled=not confirmar, type="primary",
                  icon=":material/lock:")

# --- Evaluación -------------------------------------------------------------------------------------------------
elif pestana == "dev":
    casos = ev.evaluar("desarrollo")
    if not casos:
        st.info("Todavía no hay anotaciones de desarrollo.")
        st.stop()
    texto, v, b = ev.informe(casos, "desarrollo")
    c1, c2, c3 = st.columns(3)
    c1.metric("Recall de TermCheck", ev.fmt(v["recall"]), f"{ev.fmt(v['recall'] - b['recall'])} vs. baseline")
    c2.metric("Precisión de TermCheck", ev.fmt(v["precision"]), f"{ev.fmt(v['precision'] - b['precision'])} vs. baseline")
    c3.metric("Términos anotados", v["n"])
    st.caption("Desarrollo: con estas oraciones se ajustan el código y el glosario. Sirve para ver que todo funciona; "
               "el resultado que vale es el de la prueba.")
    st.markdown(texto.split("\n", 2)[2])

elif pestana == "pub":
    st.subheader("1. Actualizar el README")
    final = (ev.DATOS / "salida" / "eval_prueba.md").exists()
    if ar.fijos(datos.DATOS / "README.md"):
        st.markdown("Las tablas del README son las de la evaluación final que se publicó y quedaron fijas. Este "
                    "botón ya no las cambia: lo que se mida con otra versión del verificador va en su propia sección.")
    else:
        st.markdown("Copia las tablas de resultados al README. " + (
            "Ya está la evaluación final: copia esas tablas." if final else
            "Todavía no está la evaluación final: copia las de desarrollo, con el aviso de que son provisorias."))

    def actualizar_readme():
        ar.refrescar_desarrollo()
        st.session_state.res_readme = ar.actualizar(datos.DATOS / "README.md", ev.DATOS / "salida")

    st.button("Actualizar el README", on_click=actualizar_readme, icon=":material/description:")
    if st.session_state.get("res_readme"):
        bien, texto = st.session_state.res_readme
        (st.success if bien else st.error)(texto)
    st.caption("Los dos ejemplos de errores y los hallazgos no se escriben solos: los completás vos en el paso 2.")

    st.subheader("2. Tus textos del README")
    st.markdown("El README tiene dos partes que escribís vos. Escribilas acá y tocá **Guardar en el README**: "
                "quedan en su lugar sin abrir el archivo.")
    readme = datos.DATOS / "README.md"
    with st.form("res_autor", border=False):
        st.text_area("Dos ejemplos de errores reales", value=ar.leer_autor(readme, "ejemplos"), height=220,
                     key="res_txt_ejemplos",
                     help="Sección 1 del README. Para cada ejemplo: la oración en inglés, lo que tradujo el "
                          "sistema y la forma que se usa en Argentina.")
        st.text_area("Hallazgos", value=ar.leer_autor(readme, "hallazgos"), height=220, key="res_txt_hallazgos",
                     help="Sección de resultados. Qué sistema maneja mejor la terminología, qué tipos de error "
                          "aparecen más y por qué falla el verificador cuando falla. Se escribe con la "
                          "evaluación final.")
        if st.form_submit_button("Guardar en el README", icon=":material/save:"):
            st.session_state.res_autor_msj = [ar.escribir_autor(readme, n, st.session_state[f"res_txt_{n}"])
                                              for n in ar.AUTOR]
    for bien, texto in st.session_state.get("res_autor_msj", []):
        (st.success if bien else st.error)(texto)
    st.caption("Podés usar Markdown: una línea en blanco separa párrafos, «- » arma una lista y `**texto**` va en "
               "negrita. Si dejás un cuadro vacío, en el README vuelve el recuadro «Pendiente». Lo que guardás "
               "acá se sube a GitHub con el botón de abajo.")

    st.subheader("3. Publicar en GitHub")
    st.markdown("Guarda en GitHub lo que cambiaste: la anotación, el glosario (y el v1 congelado), el README y los "
                "documentos del informe. No sube nada más.")
    cambios = pub.pendientes(datos.RAIZ)
    if cambios:
        st.markdown("**Cambios sin publicar:**\n" + "\n".join(f"- `{c}`" for c in cambios))
    else:
        st.caption("No hay cambios sin publicar.")

    def publicar():
        st.session_state.res_publicado = pub.publicar(datos.RAIZ)

    st.button("Publicar en GitHub", on_click=publicar, type="primary", icon=":material/cloud_upload:")
    if st.session_state.get("res_publicado"):
        bien, texto = st.session_state.res_publicado
        (st.success if bien else st.error)(texto)
    st.caption("La primera vez que publiques con el glosario congelado se pone la etiqueta `glossary-v1`, que deja "
               "registrado con qué glosario se evaluó la prueba.")

else:
    ids = an.ids_conjunto("prueba")
    hechas = an.anotadas()
    total = listas = 0
    for o in an.oraciones("prueba"):
        aps = an.apariciones(o["source_en"], an.terminos())
        for s in an.SISTEMAS:
            for a in aps:
                total += 1
                listas += bool(hechas.get((o["seg_id"], s, a["id"]), {}).get("label"))
    st.progress(listas / total if total else 0, text=f"Prueba anotada: {listas} de {total}")
    if not CONGELADO.exists():
        st.warning("Primero congelá el glosario v1 (en «Sugerencias para el glosario»).")
    elif listas < total:
        st.info("La evaluación final se calcula cuando la prueba esté anotada entera.")
    else:
        guardada = ev.DATOS / "salida" / "eval_prueba.md"
        version = ev.version_de(guardada)  # None si todavía no se calculó
        if version and version != VERSION:
            st.info(f"La evaluación guardada se calculó con la versión {version} del verificador. El de hoy es la "
                    f"versión {VERSION}. Si la volvés a calcular, la anterior queda guardada en salida/v{version}/ "
                    "y el README no cambia.")
        if st.button("Calcular la evaluación final", type="primary" if not version else "secondary",
                     icon=":material/analytics:"):
            casos = ev.evaluar("prueba", CONGELADO)
            texto, v, b = ev.escribir(casos, "prueba")  # tablas y lista de FP y FN, en salida/
            st.session_state.res_prueba = texto
        if st.session_state.get("res_prueba"):
            st.success("Guardado en salida/eval_prueba.md (tablas) y salida/eval_prueba_casos.csv (falsos positivos "
                       "y falsos negativos, para el análisis de errores).")
            st.markdown(st.session_state.res_prueba.split("\n", 2)[2])
        elif version:
            # La que ya está guardada se ve sin tener que volver a calcularla
            st.caption(f"Calculada el {datetime.fromtimestamp(guardada.stat().st_mtime):%d/%m/%Y} con la versión "
                       f"{version} del verificador.")
            st.markdown(guardada.read_text(encoding="utf-8").split("\n", 2)[2])
