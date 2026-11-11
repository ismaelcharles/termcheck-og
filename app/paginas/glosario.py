"""Página Glosario. Tres formas de trabajar el mismo archivo (data/glossary/glossary_en_es.csv):
- Fichas: cada término como tarjeta visual, con búsqueda y filtro por área; «Editar» abre el formulario.
- Agregar: formulario guiado, pregunta por pregunta, con la ficha y lo que marcaría el verificador a la vista.
- Tabla: todas las columnas a la vez, para cargar o corregir rápido. Guarda sola con cada cambio.

La revisión de fondo del glosario (formas repetidas entre filas, etc.) es la Fase 1 (src/termcheck/glossary.py).
"""
import time

import streamlit as st

import candidatos
import datos
import originales
import vista
from formulario import formulario

vista.estilos()
st.title("Glosario")

tabla = datos.leer()
cand = candidatos.leer()
n_pend = int((cand["estado"] == "pendiente").sum()) if not cand.empty else 0
VISTAS = {"fichas": "Fichas", "agregar": "Agregar término", "candidatos": f"Candidatos ({n_pend})", "tabla": "Tabla",
          "fuentes": "Fuentes"}
if "vista_glosario" not in st.session_state:
    st.session_state.vista_glosario = "fichas" if len(tabla) else "agregar"
modo = st.segmented_control("Vista", list(VISTAS), format_func=VISTAS.get, key="vista_glosario",
                            label_visibility="collapsed")
modo = modo or "fichas"

if "aviso_guardado" in st.session_state:
    st.toast(st.session_state.pop("aviso_guardado"), icon=":material/check:")


# ─────────────── Fichas ───────────────

@st.dialog("Editar término", width="large")
def editar(id_termino):
    fila = datos.leer().set_index("id").loc[id_termino].to_dict()
    fila["id"] = id_termino

    def listo(i):
        st.session_state.aviso_guardado = f"{i} guardado"
        st.rerun()

    formulario(fila, f"editar_{id_termino}", listo)
    with st.expander("Borrar este término"):
        st.write("Se borra del glosario. Queda una copia del archivo anterior en el historial.")
        if st.button(f"Borrar {id_termino}", key=f"borrar_{id_termino}"):
            datos.borrar_fila(id_termino)
            st.session_state.aviso_guardado = f"{id_termino} borrado"
            st.rerun()


def ver_fichas():
    if tabla.empty:
        st.info("Todavía no hay términos. Empezá por «Agregar término». Así se ve una ficha (ejemplo del plan):")
        st.html(vista.ficha({"id": "ejemplo", "en": "drilling rig|rig", "pos": "NOUN",
                             "es_preferred": "equipo de perforación", "es_allowed": "equipo perforador",
                             "es_forbidden": "plataforma de perforación", "subdomain": "perforación",
                             "note": "«plataforma» implica offshore; en tierra es «equipo»", "source": "VERIFICAR"}))
        return
    buscar, filtro = st.columns([2, 3])
    texto = buscar.text_input("Buscar", placeholder="Buscar en inglés o en español", label_visibility="collapsed")
    areas = sorted({a for a in tabla["subdomain"] if a}, key=str.lower)
    elegidas = filtro.pills("Área", areas, selection_mode="multi", label_visibility="collapsed") if areas else []
    filas = tabla
    if texto.strip():
        q = vista.plegar(texto)
        filas = filas[filas.apply(lambda f: any(q in vista.plegar(f[c]) for c in datos.COLUMNAS[1:]), axis=1)]
    if elegidas:
        filas = filas[filas["subdomain"].isin(elegidas)]
    incompletas = sum(1 for _, f in tabla.iterrows() if datos.faltantes(f))
    st.caption(f"{len(filas)} de {len(tabla)} términos"
               + (f" · {incompletas} con datos por completar" if incompletas else ""))
    columnas = st.columns(3, gap="medium")
    for n, (_, fila) in enumerate(filas.iterrows()):
        with columnas[n % 3]:
            st.html(vista.ficha(fila))
            if st.button("Editar", key=f"ed_{fila['id']}_{n}", icon=":material/edit:", type="tertiary"):
                editar(fila["id"])


# ─────────────── Agregar ───────────────

def ver_agregar():
    st.caption("Respondé las preguntas. A la derecha ves cómo queda la ficha y qué marcaría el verificador.")
    st.session_state.setdefault("nuevo_n", 0)

    def listo(i):
        st.session_state.aviso_guardado = f"{i} guardado. Podés seguir con el próximo."
        st.session_state.nuevo_n += 1  # campos vacíos para el próximo término
        st.rerun()

    vacia = {c: "" for c in datos.COLUMNAS}
    formulario(vacia, f"nuevo_{st.session_state.nuevo_n}", listo)


# ─────────────── Tabla ───────────────

def ver_tabla():
    st.caption("Todas las columnas a la vez. Cada cambio se guarda solo. Para agregar una fila, usá el + que aparece "
               "arriba a la derecha de la tabla; para borrar, marcá la casilla de la izquierda y tocá el tacho.")
    # La base se lee una sola vez por visita: el editor guarda las ediciones como cambios sobre esa base, y si la
    # base se volviera a leer en cada vuelta, una fila nueva aparecería dos veces.
    if "base" not in st.session_state:
        st.session_state.base = datos.leer()
        st.session_state.guardado = datos.ordenar(st.session_state.base)
        st.session_state.fecha = datos.fecha_archivo()
        st.session_state.setdefault("vuelta", 0)
    texto = st.column_config.TextColumn
    editado = st.data_editor(
        st.session_state.base, key=f"editor_{st.session_state.vuelta}", num_rows="dynamic", hide_index=True,
        width="stretch", height=520,
        column_config={
            "id": texto("id", default="", width="small", help="Se completa solo si lo dejás vacío"),
            "en": texto("en", default="", help="Formas en inglés, separadas con |"),
            "pos": st.column_config.SelectboxColumn("pos", options=list(datos.CATEGORIAS), default="NOUN",
                                                    width="small", help=" · ".join(
                                                        f"{k} {v.lower()}" for k, v in datos.CATEGORIAS.items())),
            "es_preferred": texto("es_preferred", default="", help="La traducción que debería usarse"),
            "es_allowed": texto("es_allowed", default="", help="Otras traducciones válidas, separadas con |"),
            "es_forbidden": texto("es_forbidden", default="", help="Traducciones incorrectas, separadas con |"),
            "subdomain": texto("subdomain", default="", help="Perforación, terminación, producción, HSE…"),
            "note": texto("note", default="", width="large", help="Uso, región, contexto"),
            "source": texto("source", default="", help="De dónde sale la decisión"),
        },
    )
    nuevo = datos.ordenar(editado)
    if not nuevo.equals(st.session_state.guardado):
        if datos.fecha_archivo() != st.session_state.fecha:
            st.error("El archivo del glosario cambió por otro lado mientras tenías esta página abierta "
                     "(por ejemplo, lo subiste por scp). No guardé para no pisarlo. Recargá la página.")
            st.stop()
        datos.guardar(nuevo)
        st.session_state.guardado = nuevo
        st.session_state.fecha = datos.fecha_archivo()
        st.toast(f"Guardado a las {time.strftime('%H:%M:%S')}", icon=":material/check:")
        # Si se le puso id a una fila nueva, se recarga la tabla para que se vea. Las filas vacías no fuerzan
        # recarga: puede ser una que acabás de agregar y vas a completar.
        sin_id = editado["id"].fillna("").astype(str).str.strip() == ""
        con_algo = (editado[datos.COLUMNAS_DE_CONTENIDO].fillna("").astype(str)
                    .apply(lambda c: c.str.strip()) != "").any(axis=1)
        if (sin_id & con_algo).any():
            st.session_state.base = nuevo
            st.session_state.vuelta += 1
            st.rerun()
    lista = datos.avisos(st.session_state.guardado)
    if lista:
        with st.expander(f"Para revisar ({len(lista)})"):
            for aviso in lista:
                st.markdown(f"- {aviso}")


# ─────────────── Candidatos ───────────────

# Qué hacer con cada traducción que no es la preferida
ROLES = {"válida": "Vale", "no": "No se usa", "error": "Error"}


@st.dialog("Editar antes de agregar", width="large")
def agregar_candidato(id_candidato, fila):
    st.caption("El formulario completo, con lo que ya elegiste. Corregí lo que haga falta y guardá.")

    def listo(i):
        candidatos.marcar(id_candidato, "aprobado", i)
        recordar(id_candidato, fila["en"], "agregado", i)
        st.rerun()

    formulario(fila, f"cand_{id_candidato}", listo)


def recordar(id_candidato, en, que, id_termino=""):
    """Guarda la última decisión para poder deshacerla, y avisa."""
    st.session_state.cand_deshacer = {"id": id_candidato, "en": en, "que": que, "termino": id_termino}
    st.session_state.aviso_guardado = f"«{en}» {que}" + (f" como {id_termino}" if id_termino else "")


def boton_deshacer():
    ultimo = st.session_state.get("cand_deshacer")
    if not ultimo:
        return
    if st.button(f"Deshacer: «{ultimo['en']}» {ultimo['que']}", icon=":material/undo:", type="tertiary",
                 key="cand_deshacer_btn", shortcut="z"):
        candidatos.marcar(ultimo["id"], "pendiente")
        if ultimo["termino"]:
            datos.borrar_fila(ultimo["termino"])
        st.session_state.cand_ir_a = ultimo["id"]
        st.session_state.aviso_guardado = f"«{ultimo['en']}» volvió a pendientes"
        del st.session_state.cand_deshacer
        st.rerun()


def insignias(c):
    chips = []
    if c["en_osha"]:
        chips.append(vista.chip("en el glosario de OSHA"))
    if c.get("en_slb", "").startswith("sí"):
        chips.append(vista.chip("inglés confirmado en SLB"))
    if c.get("area"):
        chips.append(vista.chip(c["area"]))
    if c["coinciden"] == "sí":
        chips.append(vista.chip("las dos fuentes coinciden", "OK"))
    elif c["coinciden"] == "no":
        chips.append(vista.chip("las fuentes no coinciden", "SIN_TRADUCIR"))
    return "".join(chips)


def fuentes_html(lista, catalogo, origen=""):
    """Las citas de una forma: nivel de confiabilidad para el uso en Argentina, fuente, página o enlace, y qué respalda."""
    if not lista and origen == "revisión previa":
        return ('<div class="tc-cita">Sin cita en las fuentes del candidato: la trajo la revisión previa. De dónde '
                'sale está en «Por qué», arriba.</div>')
    if not lista:
        return '<div class="tc-cita">Sin fuente propia: es el término en inglés, por si en campo se usa así.</div>'
    renglones = []
    for x in lista:
        f = catalogo.get(x["fuente"], {})
        uso, concepto = f.get("para_uso_ar", "sin datos"), f.get("para_concepto", "sin datos")
        donde = (f'<a href="{vista.e(x["cita"])}" target="_blank" rel="noopener">ver la página</a>'
                 if x["cita"].startswith("http") else vista.e(x["cita"]))
        porque = vista.e(f"Concepto: {concepto}. Uso en Argentina: {uso}. {f.get('motivos', '')}")
        texto, estado = candidatos.comprobacion(x, catalogo)
        marca = (f' · <span style="color:{COLOR_COMPROBADA[estado]};font-weight:500">{vista.e(texto)}</span>'
                 if texto else "")
        renglones.append(f'<div class="tc-cita" title="{porque}">{vista.nivel(f"AR {uso}", COLOR_AR)}'
                         f'<b>{vista.e(f.get("nombre", x["fuente"]))}</b> {donde} · {vista.e(x["respaldo"])}{marca}</div>')
    return "".join(renglones)


COLOR_AR = {f"AR {n}": c for n, c in candidatos.NIVELES.items()}
COLOR_COMPROBADA = {"bien": "#2E6B3A", "dudosa": "#7A5300", "mal": "#A3312A", "": "#4A453D"}
COLOR_SUG = {"Aceptar": "OK", "Revisar": "SIN_TRADUCIR", "Unir a otro": "VARIANTE", "Sin fuente": "PROHIBIDO",
             "Descartar": "PROHIBIDO"}
COLOR_CONF = {f"confianza {n}": c for n, c in candidatos.NIVELES.items()}


def sugerencia_html(sug, pend):
    """El recuadro con lo que sugiere la revisión previa para este candidato."""
    que = candidatos.SUGERENCIAS.get(sug["sugerencia"], sug["sugerencia"])
    cabeza = (vista.nivel(que, COLOR_SUG) + vista.nivel(f"confianza {sug['confianza']}", COLOR_CONF)
              + vista.nivel("versión 1" if sug["prioridad"] == "v1" else "puede esperar a la versión 2", {}))
    cuerpo = ""
    if sug["sugerencia"] == "fusionar":
        destino = pend.loc[pend["id"] == sug["destino"], "en"]
        nombre = f"{sug['destino']} ({destino.iloc[0]})" if len(destino) else sug["destino"]
        cuerpo += (f"<div>Unirlo a <b>{vista.e(nombre)}</b>: su inglés ya está sumado ahí. Si estás de acuerdo, "
                   "rechazá este.</div>")
    elif sug["sugerencia"] in ("descartar", "sin fuente"):
        cuerpo += "<div>Si estás de acuerdo, rechazalo.</div>"
    elif not sug["preferida"]:
        cuerpo += "<div>No elegí preferida: la tenés que decidir vos.</div>"
    cuerpo += f'<div class="tc-meta" style="margin-top:.3rem"><b>Por qué:</b> {vista.e(sug["motivo"])}</div>'
    if sug["para_vos"]:
        cuerpo += f'<div class="tc-falta">Para vos: {vista.e(sug["para_vos"])}</div>'
    return (f'<div class="tc-ficha" style="margin:.2rem 0 .6rem"><div style="margin-bottom:.3rem">'
            f'<b>Revisión previa de Claude</b> {cabeza}</div>{cuerpo}</div>')


def ver_candidatos():
    if cand.empty:
        st.info("No hay candidatos cargados.")
        return
    total = len(cand)
    aprobados = int((cand["estado"] == "aprobado").sum())
    descartados = int((cand["estado"] == "descartado").sum())
    st.progress((aprobados + descartados) / total,
                text=f"{aprobados + descartados} de {total} revisados · {aprobados} agregados · {descartados} rechazados")
    boton_deshacer()
    st.download_button("Bajar los pendientes (.md)", data=candidatos.markdown_pendientes().encode("utf-8"),
                       file_name="candidatos-pendientes.md", mime="text/markdown", icon=":material/download:",
                       type="tertiary", key="bajar_pendientes")
    metodo = datos.RAIZ / "docs" / "revision-previa.pdf"
    if metodo.exists():
        st.download_button("Cómo se hizo la revisión previa (PDF)", data=metodo.read_bytes(),
                           file_name="revision-previa.pdf", mime="application/pdf", icon=":material/picture_as_pdf:",
                           type="tertiary", key="bajar_revision")
    pend = cand[cand["estado"] == "pendiente"].copy()
    if pend.empty:
        st.success("Revisaste todos los candidatos.")
        return
    pend["grupo"] = pend.apply(candidatos.grupo, axis=1)
    cuentas = pend["grupo"].value_counts()
    grupos = [g for g in candidatos.GRUPOS if cuentas.get(g, 0)]

    # Después de deshacer, se vuelve al candidato que estaba
    ir_a = st.session_state.pop("cand_ir_a", None)
    if ir_a in set(pend["id"]):
        st.session_state.cand_grupo = pend.loc[pend["id"] == ir_a, "grupo"].iloc[0]
    if st.session_state.get("cand_grupo") not in grupos:
        st.session_state.cand_grupo = grupos[0]
    elegido = st.pills("Grupo", grupos, key="cand_grupo", label_visibility="collapsed",
                       on_change=lambda: st.session_state.update(cand_i=0),
                       format_func=lambda g: f"{candidatos.GRUPOS[g]} ({cuentas.get(g, 0)})") or grupos[0]
    lista = pend[pend["grupo"] == elegido]
    sugs = candidatos.revision()
    if sugs:
        de_grupo = lista["id"].map(lambda x: sugs.get(x, {}).get("sugerencia", "")).value_counts()
        tipos = ["todas"] + [s for s in candidatos.SUGERENCIAS if de_grupo.get(s, 0)]
        clave_sug = f"cand_sug_{elegido}"
        if st.session_state.get(clave_sug) not in tipos:
            st.session_state[clave_sug] = "todas"
        if ir_a in set(lista["id"]):
            st.session_state[clave_sug] = "todas"
        filtro = st.pills("Sugerencia", tipos, key=clave_sug, label_visibility="collapsed",
                          on_change=lambda: st.session_state.update(cand_i=0),
                          format_func=lambda s: f"Todas ({len(lista)})" if s == "todas"
                          else f"{candidatos.SUGERENCIAS[s]} ({de_grupo.get(s, 0)})") or "todas"
        if filtro != "todas":
            lista = lista[lista["id"].map(lambda x: sugs.get(x, {}).get("sugerencia", "")) == filtro]
        # Primero los de la versión 1; dentro de cada versión, confianza alta, media, baja y sin dato
        conf = {"alta": 0, "media": 1, "baja": 2}
        lista = lista.assign(_p=lista["id"].map(lambda x: sugs.get(x, {}).get("prioridad", "v2")),
                             _c=lista["id"].map(lambda x: conf.get(sugs.get(x, {}).get("confianza", ""), 3))) \
            .sort_values(["_p", "_c", "id"], kind="stable").drop(columns=["_p", "_c"])
    lista = lista.reset_index(drop=True)
    if ir_a in set(lista["id"]):
        st.session_state.cand_i = int(lista.index[lista["id"] == ir_a][0])
    i = min(st.session_state.get("cand_i", 0), len(lista) - 1)
    c = lista.iloc[i]
    k = c["id"]

    nav_izq, nav_txt, nav_der = st.columns([1, 2, 1])
    if nav_izq.button("Anterior", icon=":material/arrow_back:", disabled=i == 0, width="stretch"):
        st.session_state.cand_i = i - 1
        st.rerun()
    nav_txt.markdown(f"<div style='text-align:center;padding-top:.45rem'>{i + 1} de {len(lista)}</div>",
                     unsafe_allow_html=True)
    if nav_der.button("Siguiente", icon=":material/arrow_forward:", icon_position="right",
                      disabled=i >= len(lista) - 1, width="stretch"):
        st.session_state.cand_i = i + 1
        st.rerun()

    st.html(f'<div style="margin:.6rem 0 .3rem"><span class="tc-chip tc-en" style="font-size:1.15rem;'
            f'padding:.25rem .8rem">{vista.e(c["en"])}</span> {insignias(c)}</div>')
    ya = candidatos.ya_en_glosario(c, tabla)
    if ya:
        st.warning(f"Este término ya está en tu glosario como {ya}. Lo normal es rechazarlo; si querés sumarle "
                   "variantes, hacelo desde su ficha.")

    sug = sugs.get(k)
    if sug:
        st.html(sugerencia_html(sug, pend))
    formas = candidatos.formas_revisadas(c, sug)
    origen = {f["forma"]: f["origen"] for f in formas}
    if not sug:
        inicial = candidatos.preferida_sugerida(c)
    else:
        inicial = next((t for t in origen if vista.plegar(t) == vista.plegar(sug["preferida"])), None) \
            if sug["preferida"] and sug["sugerencia"] in ("aceptar", "revisar") else None
    izq, der = st.columns([1.5, 1], gap="large")
    with izq:
        preferida = st.pills("¿Cuál es la traducción preferida?", list(origen), default=inicial,
                             key=f"pref_{k}", format_func=lambda t: f"{t}  ·  {origen[t]}", wrap=True,
                             help="La que querés ver en una buena traducción. Si en campo se dice en inglés, "
                                  "elegí la forma en inglés.")
        roles = {}
        catalogo, por_forma = candidatos.fuentes(), candidatos.citas(k)
        st.markdown("**Cada forma, con su fuente**")
        for t in origen:
            a, b = st.columns([1.25, 1], vertical_alignment="top")
            a.html(f'{vista.chip(t, "OK" if t == preferida else None)} <span class="tc-meta">{vista.e(origen[t])}</span>'
                   + fuentes_html(por_forma.get(vista.plegar(t), []), catalogo, origen[t]))
            if t == preferida:
                b.html('<div style="padding-top:.3rem">' + vista.etiqueta("OK") + ' <span class="tc-meta">preferida'
                       '</span></div>')
                continue
            rol = b.segmented_control(t, list(ROLES), format_func=ROLES.get, label_visibility="collapsed",
                                      default=candidatos.rol_sugerido(t, origen[t], sug), required=True,
                                      width="stretch", key=f"rol_{k}_{vista.plegar(t)}")
            roles[t] = rol or "no"
        st.caption("«Vale»: es correcta aunque no sea la preferida. «No se usa»: queda afuera; si una traducción la pone, "
                   "el verificador avisa para revisar. «Error»: marcala solo si estás seguro de que está mal. "
                   "La etiqueta AR es qué tan confiable es la fuente para el uso en Argentina; pasá el mouse para "
                   "ver por qué, o abrí la vista «Fuentes».")
        en = st.text_input("Inglés", value=(sug or {}).get("en") or c["en"], key=f"en_{k}",
                           help="Las formas en inglés que busca el verificador, separadas con |. La revisión previa "
                                "puede haber sumado siglas o las formas de un candidato que se une a este.")
        a, b = st.columns(2)
        codigos = list(datos.CATEGORIAS)
        pos_inicial = (sug or {}).get("pos") or "NOUN"
        pos = a.selectbox("Tipo de palabra", codigos, key=f"pos_{k}", format_func=lambda x: datos.CATEGORIAS[x],
                          index=codigos.index(pos_inicial) if pos_inicial in codigos else 0)
        area_inicial = (sug or {}).get("area") or c.get("area")
        areas = sorted(set(datos.AREAS) | ({area_inicial} if area_inicial else set()), key=str.lower)
        area = b.selectbox("Área", areas, index=areas.index(area_inicial) if area_inicial in areas else None,
                           key=f"area_{k}", accept_new_options=True, placeholder="Elegí o escribí una")
        nota = st.text_input("Aclaración (opcional)", key=f"nota_{k}",
                             placeholder="Uso en Argentina, contexto, por qué es error…")

    fila = candidatos.fila_decidida(c, preferida, roles, pos, area, nota, en)
    with der:
        st.markdown("**Así entra al glosario**")
        st.html(vista.ficha(dict(fila, id="nuevo")))
        st.markdown("**Qué marcaría el verificador** si la traducción dice…")
        st.html(vista.casos(fila))

    b1, b2, b3, b4 = st.columns(4)
    if b1.button("Aceptar", icon=":material/check:", type="secondary" if ya else "primary", key=f"ok_{k}",
                 shortcut="a", disabled=not preferida, width="stretch"):
        id_termino = datos.guardar_fila(fila)
        candidatos.marcar(k, "aprobado", id_termino)
        recordar(k, c["en"], "agregado", id_termino)
        st.rerun()
    if b2.button("Editar todo", icon=":material/edit:", key=f"ed_{k}", width="stretch"):
        agregar_candidato(k, fila)
    if b3.button("Rechazar", icon=":material/close:", type="primary" if ya else "secondary", key=f"no_{k}",
                 shortcut="x", width="stretch"):
        candidatos.marcar(k, "descartado")
        recordar(k, c["en"], "rechazado")
        st.rerun()
    if b4.button("Después", icon=":material/skip_next:", key=f"luego_{k}", shortcut="d", disabled=len(lista) < 2,
                 width="stretch"):
        st.session_state.cand_i = (i + 1) % len(lista)
        st.rerun()
    st.caption("Atajos de teclado: A acepta · X rechaza · D deja para después · Z deshace la última.")


# ─────────────── Fuentes ───────────────

CRITERIOS = [
    ("Autoría", "Quién lo escribió: una institución o especialistas identificables pesan más que un texto anónimo o "
                "generado por un modelo."),
    ("Tipo de fuente", "Primaria (texto técnico escrito por especialistas para trabajar), secundaria (glosario, "
                       "diccionario, manual) o intermediario (algo que resume otras fuentes, como glosariotest)."),
    ("Original o traducido", "Un texto escrito en castellano muestra el uso real. Uno traducido del inglés puede "
                             "arrastrar calcos (interferencia)."),
    ("Variedad", "El encargo es castellano técnico de Argentina: una fuente de otra variedad sirve para el concepto, "
                 "no para elegir la forma preferida."),
    ("Verificable", "Se puede ir a la página o al enlace y comprobar que la forma está ahí, con ese sentido."),
    ("Calidad del texto", "Errores de redacción, ortografía o extracción bajan la confianza en sus términos."),
]


def subir_originales():
    """Subir los documentos originales (CENOVA, YPF, manuales) para comprobar las citas contra ellos."""
    st.markdown("**Tus documentos originales**")
    st.caption("Subí la carpeta con los PDF y las presentaciones de donde salió glosariotest. Quedan en una carpeta "
               "privada del servidor (data/originales): no se publican ni se suben a git. Con ellos se comprueba "
               "cada cita de página y se vuelve a evaluar cada fuente. Si subís uno con el mismo nombre en el mismo "
               "lugar, reemplaza al anterior.")
    vuelta = st.session_state.get("subida_n", 0)
    modo = st.segmented_control("Qué subir", ["carpeta", "archivos"], key="subir_modo", required=True,
                                default="carpeta", label_visibility="collapsed",
                                format_func={"carpeta": "Una carpeta entera", "archivos": "Archivos sueltos"}.get)
    subidos = st.file_uploader("Documentos", type=originales.TIPOS, key=f"subir_{modo}_{vuelta}",
                               accept_multiple_files="directory" if modo == "carpeta" else True,
                               label_visibility="collapsed",
                               help="Con «Una carpeta entera» se suben también las subcarpetas, y se guarda cada "
                                    "archivo en su lugar. Solo entran los tipos de la lista; lo demás se saltea.")
    if subidos:
        hechos, reemplazos, fallas, tanda = [], [], [], set()
        for archivo in subidos:
            try:
                nombre, habia = originales.guardar(archivo, tanda)
                (reemplazos if habia else hechos).append(nombre)
            except (ValueError, OSError) as error:
                fallas.append(f"{archivo.name}: {error}")
        partes = []
        if hechos:
            partes.append(f"{len(hechos)} guardado{'s' if len(hechos) > 1 else ''}")
        if reemplazos:
            partes.append(f"{len(reemplazos)} reemplazado{'s' if len(reemplazos) > 1 else ''}")
        if partes:
            st.session_state.aviso_guardado = "Documentos: " + ", ".join(partes)
        st.session_state.fallas_subida = fallas
        st.session_state.subida_n = vuelta + 1  # vacía el cuadro para la próxima tanda
        st.rerun()
    for falla in st.session_state.pop("fallas_subida", []):
        st.error(f"No se pudo guardar {falla}")

    docs = originales.lista()
    if not docs:
        st.caption("Todavía no subiste ninguno.")
        return
    total = originales.tamaño_legible(sum(d["tamaño"] for d in docs))
    with st.expander(f"Subidos ({len(docs)} · {total})", expanded=len(docs) <= 8):
        for d in docs:
            a, b, c = st.columns([4, 1.6, 0.9], vertical_alignment="center")
            a.markdown(f"{d['nombre']}")
            b.caption(f"{originales.tamaño_legible(d['tamaño'])} · {d['fecha']:%d/%m %H:%M}")
            with c.popover("Borrar", type="tertiary"):
                st.caption("Se borra la copia del servidor. El archivo de tu compu no se toca.")
                if st.button("Sí, borrar", key=f"borrar_{d['nombre']}", type="primary"):
                    originales.borrar(d["nombre"])
                    st.session_state.aviso_guardado = f"«{d['nombre']}» borrado del servidor"
                    st.rerun()


def ver_fuentes():
    subir_originales()
    st.divider()
    st.caption("Cada fuente tiene dos notas, porque sirve para cosas distintas. **Concepto**: si es confiable para "
               "saber qué es el término y cómo se dice en inglés. **Uso en Argentina**: si es confiable para elegir "
               "la forma preferida en castellano de campo. La evaluación es una propuesta: corregila abajo si no "
               "estás de acuerdo.")
    with st.expander("Con qué criterios se evaluó"):
        st.html('<div class="tc-leyenda">' + "".join(
            f"<b>{vista.e(n)}</b><span>{vista.e(d)}</span>" for n, d in CRITERIOS) + "</div>")
        st.caption("La base teórica está en docs/fuentes-y-confiabilidad.md: Pinto (competencia documental), Nord "
                   "(el encargo y el destinatario fijan la norma), Even-Zohar (interferencia) y la práctica "
                   "terminológica (jerarquía de fuentes).")
    catalogo = candidatos.fuentes()
    if not catalogo:
        st.info("Todavía no hay catálogo de fuentes.")
        return
    usos = {}
    if candidatos.FORMAS_FUENTES.exists():
        conteo = datos.pd.read_csv(candidatos.FORMAS_FUENTES, dtype=str, keep_default_na=False)["fuente"].value_counts()
        usos = conteo.to_dict()
    colores = {n: c for n, c in candidatos.NIVELES.items()}
    orden = sorted(catalogo.values(), key=lambda f: -usos.get(f["id"], 0))
    columnas = st.columns(2, gap="medium")
    for n, f in enumerate(orden):
        confirmar = (f'<div class="tc-falta">Para confirmar: {vista.e(f["a_confirmar"])}</div>'
                     if f["a_confirmar"] else "")
        columnas[n % 2].html(
            f'<div class="tc-ficha"><div class="tc-ficha-cab"><b>{vista.e(f["nombre"])}</b>'
            f'<span class="tc-id">{usos.get(f["id"], 0)} citas</span></div>'
            f'<div style="margin:.2rem 0 .4rem">{vista.nivel("concepto " + f["para_concepto"], {"concepto " + k: v for k, v in colores.items()})}'
            f'{vista.nivel("uso en Argentina " + f["para_uso_ar"], {"uso en Argentina " + k: v for k, v in colores.items()})}</div>'
            f'<div class="tc-meta">{vista.e(f["tipo"])} · {vista.e(f["autoria"])}</div>'
            f'<div class="tc-meta">Idioma: {vista.e(f["idioma"])} · Variedad: {vista.e(f["variedad"])}</div>'
            f'<div class="tc-nota" style="font-style:normal">{vista.e(f["motivos"])}</div>{confirmar}</div>')

    with st.expander("Corregir la evaluación"):
        tabla = datos.pd.read_csv(candidatos.FUENTES, dtype=str, keep_default_na=False)
        niveles = ["alta", "media", "baja", "sin datos", "no aplica"]
        editado = st.data_editor(
            tabla, hide_index=True, width="stretch", key="editor_fuentes", disabled=["id"],
            column_config={"para_concepto": st.column_config.SelectboxColumn("concepto", options=niveles),
                           "para_uso_ar": st.column_config.SelectboxColumn("uso en Argentina", options=niveles)})
        if st.button("Guardar la evaluación", key="guardar_fuentes", type="primary"):
            candidatos.guardar_fuentes(editado)
            st.session_state.aviso_guardado = "Evaluación de fuentes guardada"
            st.rerun()

    doc = datos.RAIZ / "docs" / "fuentes-y-confiabilidad.pdf"
    reaud = datos.RAIZ / "docs" / "reauditoria-fuentes.pdf"
    a, b, _ = st.columns([1, 1.3, 1.5])
    if doc.exists():
        a.download_button("Criterios y teoría (PDF)", data=doc.read_bytes(), file_name="fuentes-y-confiabilidad.pdf",
                          mime="application/pdf", icon=":material/picture_as_pdf:", key="bajar_fuentes_pdf")
    if reaud.exists():
        b.download_button("Reauditoría contra los originales (PDF)", data=reaud.read_bytes(),
                          file_name="reauditoria-fuentes.pdf", mime="application/pdf",
                          icon=":material/picture_as_pdf:", key="bajar_reauditoria_pdf")


{"fichas": ver_fichas, "agregar": ver_agregar, "candidatos": ver_candidatos, "tabla": ver_tabla,
 "fuentes": ver_fuentes}[modo]()

st.divider()
ESTRUCTURA = datos.RAIZ / "docs" / "estructura-glosario.pdf"
csv_col, pdf_col, _ = st.columns([1, 1.4, 2])
csv_col.download_button("Bajar el CSV", data=datos.GLOSARIO.read_bytes() if datos.GLOSARIO.exists() else b"",
                        file_name="glossary_en_es.csv", mime="text/csv", icon=":material/download:")
if ESTRUCTURA.exists():
    pdf_col.download_button("Cómo está armado (PDF)", data=ESTRUCTURA.read_bytes(), file_name="estructura-glosario.pdf",
                            mime="application/pdf", icon=":material/picture_as_pdf:")
