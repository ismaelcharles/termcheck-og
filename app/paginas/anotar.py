"""Página de anotación a ciegas (plan 5.4): el dueño etiqueta cada término del glosario en cada traducción.

Orden de trabajo: arriba la oración en inglés y las tres traducciones (A, B, C) una sola vez; abajo, un bloque por
término con una etiqueta para cada traducción, para comparar el mismo término en las tres de un vistazo.
Cada etiqueta se guarda apenas se elige (no hay botón de guardar).

Para ir rápido: «Lo que falta: Correcto» (por término o por oración) completa con Correcto lo que no tocaste; así
solo hay que marcar los errores.

No muestra nada del verificador ni qué sistema hizo cada traducción. Conjuntos: desarrollo (15) y prueba (40).
La lógica y el guardado están en app/anotacion.py.
"""
import streamlit as st

import anotacion as an
import vista

NOMBRES = {"CORRECTO": "Correcto", "ERROR_TERMINO": "Error de término", "OMISION": "Omisión",
           "SIN_TRADUCIR": "Sin traducir"}
OPCIONES = list(an.ETIQUETAS)
# Etiquetas en las que hay que marcar qué palabras usó la traducción (en Correcto es opcional y se conserva)
PIDEN_FORMA = {"ERROR_TERMINO", "SIN_TRADUCIR"}
AYUDA = "  \n".join(f"**{NOMBRES[k]}**: {v}" for k, v in an.ETIQUETAS.items()) + (
    "  \n**No va** (arriba a la derecha de cada término): esta aparición no se anota en ninguna de las tres "
    "traducciones, por ejemplo un término que está dentro de otro más largo. Se guarda aparte, no como etiqueta."
    "  \n\nCada etiqueta se guarda apenas la elegís.")

st.html(vista.CSS + """<style>
.an-en{font-size:1.08rem;line-height:2.1;margin:.2rem 0 .6rem}
.an-term{background:#14120F;color:#F6F3ED;border-radius:.3rem;padding:.08rem .35rem}
.an-term sup,.an-sub sup,.an-mark sup{font:600 .62rem ui-monospace,monospace;margin-left:.15rem;opacity:.8}
.an-sub{border-bottom:2px solid #E2B93B;padding-bottom:.05rem}
.an-es{font-size:1.02rem;line-height:1.9;background:#FBF9F5;border-left:3px solid #D8D0C2;padding:.35rem .8rem;
  margin:.1rem 0 .7rem}
.an-mark{background:#F1E3B5;border-radius:.25rem;padding:.02rem .2rem}
.an-letra{font:600 .95rem Inter,sans-serif;margin-top:.2rem}
.an-cab{font:500 .98rem Inter,sans-serif;line-height:1.5}
.an-cab code{font-size:.74rem;color:#7A7266;background:none}
.an-nota{font-size:.84rem;color:#4A453D;margin-top:.15rem}
.an-falta{font-size:.8rem;color:#7A5300}
</style>""")
st.title("Anotar")

CONJUNTOS = {"desarrollo": "Desarrollo (15)", "prueba": "Prueba (40)"}
conjunto = st.segmented_control("Conjunto", list(CONJUNTOS), format_func=CONJUNTOS.get, key="anot_conjunto",
                                default="desarrollo", label_visibility="collapsed") or "desarrollo"
oraciones = an.oraciones(conjunto)
if not oraciones:
    st.info("Falta la división en desarrollo y prueba (scripts/make_splits.py y scripts/recortar_splits.py).")
    st.stop()
lista_terminos = an.terminos()
trad = an.traducciones([o["seg_id"] for o in oraciones])
hechas = an.anotadas()
apar = {o["seg_id"]: an.apariciones(o["source_en"], lista_terminos) for o in oraciones}


def lista(fila):
    """Una celda está lista si tiene etiqueta y, cuando hace falta, las palabras marcadas."""
    return bool(fila) and bool(fila.get("label")) and (fila["label"] not in PIDEN_FORMA or bool(fila.get("es_used")))


def estado(seg_id):
    """Cuántas anotaciones de la oración están listas, sobre el total (términos × 3 traducciones)."""
    total = len(apar[seg_id]) * len(an.SISTEMAS)
    hechas_o = sum(lista(hechas.get((seg_id, s, a["id"]))) for s in an.SISTEMAS for a in apar[seg_id])
    return hechas_o, total


def icono(a, b):
    return "✓" if a == b else "◐" if a else "○"


cuentas = [estado(o["seg_id"]) for o in oraciones]
listas, total = sum(c[0] for c in cuentas), sum(c[1] for c in cuentas)
completas = sum(1 for a, b in cuentas if a == b)

st.markdown(f"Conjunto de **{conjunto}**: {len(oraciones)} oraciones. Las tres traducciones de cada oración "
            f"aparecen como A, B y C, sin decir de qué sistema son y en otro orden en cada oración.")
st.progress(listas / total if total else 0,
            text=f"{listas} de {total} anotaciones · {completas} de {len(oraciones)} oraciones completas")

st.caption("Lo más rápido: marcá solo los errores y después tocá «Lo que falta: Correcto». Lo que ya marcaste "
           "no se toca.")
with st.expander("Qué significa cada etiqueta", icon=":material/help:"):
    st.markdown(AYUDA)
    st.caption("Los casos dudosos y las decisiones van en docs/annotation_guidelines.md.")

# Elegir oración
ids = [o["seg_id"] for o in oraciones]
if "anot_seg" not in st.session_state or st.session_state.anot_seg not in ids:
    st.session_state.anot_seg = next((i for i, (a, b) in zip(ids, cuentas) if a < b), ids[0])


def marca(i):
    a, b = cuentas[ids.index(i)]
    return f"{icono(a, b)}  {i}  ({a}/{b})"


def mover(paso):
    st.session_state.anot_seg = ids[(ids.index(st.session_state.anot_seg) + paso) % len(ids)]


def proxima():
    actual = ids.index(st.session_state.anot_seg)
    for k in list(range(actual + 1, len(ids))) + list(range(0, actual)):
        if cuentas[k][0] < cuentas[k][1]:
            st.session_state.anot_seg = ids[k]
            return


c1, c2, c3, c4 = st.columns([3, .6, .6, 2.4], vertical_alignment="bottom")
c1.selectbox("Oración", ids, key="anot_seg", format_func=marca)
c2.button("", on_click=mover, args=(-1,), icon=":material/chevron_left:", width="stretch", help="Anterior")
c3.button("", on_click=mover, args=(1,), icon=":material/chevron_right:", width="stretch", help="Siguiente")
c4.button("Próxima sin terminar", on_click=proxima, type="primary", icon=":material/skip_next:", width="stretch",
          disabled=completas == len(oraciones))

seg = next(o for o in oraciones if o["seg_id"] == st.session_state.anot_seg)
seg_id = seg["seg_id"]
aps = apar[seg_id]
numero = {a["id"]: n for n, a in enumerate(aps, start=1)}
orden = an.orden_ciego(seg_id)


def externo_de(a):
    """El término más largo que contiene a esta aparición, o None."""
    return next((b for b in aps if b is not a and an.dentro_de_otro(a, [a, b])), None)


# Oración en inglés: cada término resaltado y numerado; los que están dentro de otro, subrayados por dentro
def html_en():
    texto, partes, pos = seg["source_en"], [], 0
    for a in aps:
        if a["inicio"] < pos:  # dentro de otro (ya se dibujó) o solapado
            continue
        internos = [b for b in aps if b is not a and an.dentro_de_otro(b, [a, b])]
        dentro, p = [], a["inicio"]
        for b in internos:
            if b["inicio"] < p:
                continue
            dentro.append(vista.e(texto[p:b["inicio"]]))
            dentro.append(f'<span class="an-sub">{vista.e(texto[b["inicio"]:b["fin"]])}<sup>{numero[b["id"]]}</sup>'
                          f'</span>')
            p = b["fin"]
        dentro.append(vista.e(texto[p:a["fin"]]))
        partes.append(vista.e(texto[pos:a["inicio"]]))
        partes.append(f'<span class="an-term">{"".join(dentro)}<sup>{numero[a["id"]]}</sup></span>')
        pos = a["fin"]
    partes.append(vista.e(texto[pos:]))
    return "".join(partes)


def html_es(sistema, texto_es):
    """La traducción con las palabras ya marcadas resaltadas y con el número del término."""
    if not texto_es:
        return "(falta)"
    marcas = {}
    palabras_t = an.palabras(texto_es)
    for a in aps:
        fila = hechas.get((seg_id, sistema, a["id"]), {})
        for i in an.indices_de(fila.get("es_used", ""), palabras_t):
            marcas.setdefault(i, []).append(numero[a["id"]])
    partes, pos, ultimo = [], 0, {}
    tramos = list(an.PALABRA.finditer(texto_es))
    for i, m in enumerate(tramos):
        partes.append(vista.e(texto_es[pos:m.start()]))
        if i in marcas:
            # el número va solo en la última palabra de cada término marcado
            nums = [n for n in marcas[i] if i + 1 not in marcas or n not in marcas[i + 1]]
            sup = f"<sup>{','.join(map(str, nums))}</sup>" if nums else ""
            partes.append(f'<span class="an-mark">{vista.e(m.group(0))}{sup}</span>')
        else:
            partes.append(vista.e(m.group(0)))
        pos = m.end()
    partes.append(vista.e(texto_es[pos:]))
    return "".join(partes)


st.html(f'<div class="tc-idioma">Inglés · {seg_id}</div><div class="an-en">{html_en()}</div>')
if seg.get("url"):
    st.caption(f"Fuente: {seg['url']}")

if not aps:
    st.info("En esta oración no aparece ningún término del glosario actual.")
    st.stop()

for letra, sistema in orden:
    a_, b_ = sum(lista(hechas.get((seg_id, sistema, a["id"]))) for a in aps), len(aps)
    st.html(f'<div class="tc-idioma">Traducción {letra} {icono(a_, b_)}</div>'
            f'<div class="an-es">{html_es(sistema, trad.get(seg_id, {}).get(sistema, ""))}</div>')


def celdas_de(lista_aps):
    return [(s, a["id"]) for a in lista_aps for _, s in orden]


def completar(lista_aps, y_seguir=False):
    an.completar_correcto(seg_id, celdas_de(lista_aps))
    for a in lista_aps:
        for _, s in orden:
            st.session_state.pop(f"r_{seg_id}_{s}_{a['id']}", None)
    if y_seguir:
        actual = ids.index(seg_id)
        resto = [i for i in ids[actual + 1:] + ids[:actual] if i != seg_id]
        pendientes = [i for i in resto if cuentas[ids.index(i)][0] < cuentas[ids.index(i)][1]]
        if pendientes:
            st.session_state.anot_seg = pendientes[0]


faltan_oracion = sum(1 for s, t in celdas_de(aps) if not hechas.get((seg_id, s, t), {}).get("label"))
b1, b2 = st.columns(2)
b1.button(f"Lo que falta en la oración: Correcto ({faltan_oracion})", on_click=completar, args=(aps,),
          icon=":material/done_all:", width="stretch", disabled=not faltan_oracion)
b2.button("Lo que falta: Correcto, y a la próxima", on_click=completar, args=(aps, True), type="primary",
          icon=":material/fast_forward:", width="stretch", disabled=not faltan_oracion)


# Guardado inmediato
def guardar_celda(sistema, term_id, clave, palabras_t):
    s = st.session_state
    previo = an.anotadas().get((seg_id, sistema, term_id), {})
    etiqueta = s.get(f"r_{clave}")
    comentario = s.get(f"c_{clave}", previo.get("comment", ""))
    if etiqueta in PIDEN_FORMA and f"p_{clave}" in s:
        es_used = an.forma(palabras_t, s[f"p_{clave}"] or [])
    elif etiqueta in PIDEN_FORMA or etiqueta == "CORRECTO":
        es_used = previo.get("es_used", "")
    else:
        es_used = ""
    if etiqueta is None and comentario:
        return  # un comentario sin etiqueta no se guarda todavía
    an.guardar_uno(seg_id, sistema, term_id, etiqueta, es_used, comentario)


def guardar_no_va(term_id, clave_t):
    """Activar «No va» guarda una copia de las etiquetas que había; desactivarlo las devuelve."""
    activo = st.session_state[f"nv_{clave_t}"]
    copias = st.session_state.setdefault("anot_copias", {})
    for _, sistema in orden:
        previo = an.anotadas().get((seg_id, sistema, term_id), {})
        if activo:
            if previo.get("label") and previo["label"] != an.NO_VA:
                copias[(seg_id, sistema, term_id)] = previo
            an.guardar_uno(seg_id, sistema, term_id, an.NO_VA, "", previo.get("comment", ""))
        else:
            antes = copias.pop((seg_id, sistema, term_id), {})
            an.guardar_uno(seg_id, sistema, term_id, antes.get("label"), antes.get("es_used", ""),
                           antes.get("comment", ""))
        for pref in ("r_", "p_", "c_"):
            st.session_state.pop(f"{pref}{seg_id}_{sistema}_{term_id}", None)


st.subheader("Términos")
for n, a in enumerate(aps, start=1):
    clave_t = f"{seg_id}_{a['id']}"
    filas = {s: hechas.get((seg_id, s, a["id"]), {}) for _, s in orden}
    no_va = all(f.get("label") == an.NO_VA for f in filas.values())
    hechas_t = sum(lista(f) for f in filas.values())
    with st.container(border=True):
        cab, interruptor = st.columns([4, 1], vertical_alignment="center")
        extra = f" · aparece {a['veces']} veces" if a["veces"] > 1 else ""
        cab.html(f'<div class="an-cab">{icono(hechas_t, len(orden))} {n}. <b>{vista.e(a["forma"])}</b> '
                 f'<code>{a["id"]}</code>{vista.e(extra)}</div>')
        interruptor.toggle("No va", value=no_va, key=f"nv_{clave_t}", on_change=guardar_no_va,
                           args=(a["id"], clave_t))
        externo = externo_de(a)
        if externo:
            cab.html(f'<div class="an-nota">Está dentro de «{vista.e(externo["forma"])}» '
                     f'(n.º {numero[externo["id"]]}). Si se anota junto con ese término, marcá «No va».</div>')
        if no_va:
            st.caption("No se anota en ninguna de las tres traducciones.")
            continue

        columnas = st.columns(len(orden))
        for col, (letra, sistema) in zip(columnas, orden):
            fila = filas[sistema]
            clave = f"{seg_id}_{sistema}_{a['id']}"
            palabras_t = an.palabras(trad.get(seg_id, {}).get(sistema, ""))
            with col:
                st.html(f'<div class="an-letra">{letra} {icono(int(lista(fila)), 1)}</div>')
                st.radio(f"Traducción {letra}", OPCIONES, format_func=NOMBRES.get,
                         index=OPCIONES.index(fila["label"]) if fila.get("label") in OPCIONES else None,
                         key=f"r_{clave}", label_visibility="collapsed", on_change=guardar_celda,
                         args=(sistema, a["id"], clave, palabras_t))

        # Marcar las palabras, solo donde hace falta, debajo de las tres columnas
        for letra, sistema in orden:
            fila = filas[sistema]
            if fila.get("label") not in PIDEN_FORMA:
                continue
            clave = f"{seg_id}_{sistema}_{a['id']}"
            palabras_t = an.palabras(trad.get(seg_id, {}).get(sistema, ""))
            # Streamlit reconoce cada botón por su texto: las palabras repetidas («de», «la») llevan al final una
            # cantidad distinta de espacios invisibles para que cada una sea un botón distinto.
            visto, rotulos = {}, []
            for palabra in palabras_t:
                visto[palabra] = visto.get(palabra, 0) + 1
                rotulos.append(palabra + "​" * (visto[palabra] - 1))
            if f"p_{clave}" not in st.session_state:
                st.session_state[f"p_{clave}"] = an.indices_de(fila.get("es_used", ""), palabras_t)
            st.pills(f"Traducción {letra} ({NOMBRES[fila['label']].lower()}): tocá las palabras que usó para "
                     f"«{a['forma']}»", list(range(len(palabras_t))), format_func=lambda i, r=rotulos: r[i],
                     selection_mode="multi", key=f"p_{clave}", on_change=guardar_celda,
                     args=(sistema, a["id"], clave, palabras_t))
            if not fila.get("es_used"):
                st.html('<div class="an-falta">Falta marcar las palabras.</div>')

        faltan_t = sum(1 for f in filas.values() if not f.get("label"))
        if faltan_t and faltan_t < len(orden):
            st.button(f"Las que faltan de este término: Correcto ({faltan_t})", key=f"ct_{clave_t}",
                      on_click=completar, args=([a],), icon=":material/done_all:", type="tertiary")
        con_comentario = sum(bool(f.get("comment")) for f in filas.values())
        with st.popover(f"Comentario{f' ({con_comentario})' if con_comentario else ''}",
                        icon=":material/edit_note:"):
            for letra, sistema in orden:
                fila = filas[sistema]
                clave = f"{seg_id}_{sistema}_{a['id']}"
                st.text_input(f"Traducción {letra}", value=fila.get("comment", ""), key=f"c_{clave}",
                              placeholder="Opcional: el porqué en casos dudosos", on_change=guardar_celda,
                              args=(sistema, a["id"], clave, an.palabras(trad.get(seg_id, {}).get(sistema, ""))),
                              disabled=not fila.get("label"),
                              help=None if fila.get("label") else "Primero elegí la etiqueta.")
