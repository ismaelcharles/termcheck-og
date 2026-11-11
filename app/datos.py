"""Leer y guardar el glosario desde la app. Lo usan la tabla, las fichas y el formulario.

Reglas de guardado:
- Se escribe de una vez (archivo temporal + reemplazo): nunca queda un CSV a medio escribir.
- La primera vez que se guarda en cada visita, se deja una copia del archivo anterior en data/glossary/historial/.
"""
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent
# TERMCHECK_DATOS: otra carpeta con data/ adentro, para pruebas y ensayos que no tocan los datos reales
DATOS = Path(os.environ.get("TERMCHECK_DATOS") or RAIZ)
GLOSARIO = DATOS / "data" / "glossary" / "glossary_en_es.csv"
HISTORIAL = GLOSARIO.parent / "historial"

COLUMNAS = ["id", "en", "pos", "es_preferred", "es_allowed", "es_forbidden", "subdomain", "note", "source"]
COLUMNAS_CON_VARIANTES = ["en", "es_allowed", "es_forbidden"]
# Las que cuentan para saber si una fila tiene algo escrito (id y pos se llenan solos)
COLUMNAS_DE_CONTENIDO = [c for c in COLUMNAS if c not in ("id", "pos")]

# Categorías gramaticales: el código que espera spaCy y cómo se dice en castellano
CATEGORIAS = {"NOUN": "Sustantivo", "VERB": "Verbo", "ADJ": "Adjetivo", "ADV": "Adverbio", "PROPN": "Nombre propio"}
# Áreas que nombra el plan (sección 2). Se pueden agregar otras al escribir.
AREAS = ["perforación", "terminación", "producción", "intervención de pozos", "control de pozo", "geología", "HSE",
         "general"]


def fecha_archivo():
    """Momento de la última modificación del CSV (para saber si alguien lo cambió por otro lado)."""
    return GLOSARIO.stat().st_mtime_ns if GLOSARIO.exists() else 0


def leer():
    if not GLOSARIO.exists():
        return pd.DataFrame(columns=COLUMNAS)
    tabla = pd.read_csv(GLOSARIO, dtype=str, keep_default_na=False)
    for columna in COLUMNAS:  # si falta alguna columna, se agrega vacía
        if columna not in tabla.columns:
            tabla[columna] = ""
    return tabla[COLUMNAS]


def guardar(tabla):
    if GLOSARIO.exists() and not st.session_state.get("copia_hecha"):
        HISTORIAL.mkdir(exist_ok=True)
        copia = HISTORIAL / f"glossary_{datetime.now():%Y%m%d-%H%M%S}.csv"
        copia.write_bytes(GLOSARIO.read_bytes())
        st.session_state.copia_hecha = True
    temporal = GLOSARIO.with_suffix(".tmp")
    tabla.to_csv(temporal, index=False, encoding="utf-8")
    temporal.replace(GLOSARIO)


def variantes(texto):
    """«wellhead | well-head |» → ["wellhead", "well-head"]"""
    return [p.strip() for p in str(texto).split("|") if p.strip()]


def juntar(lista):
    """["wellhead", "well-head"] → «wellhead|well-head»"""
    return "|".join(p.strip() for p in lista if p and p.strip())


def siguiente_id(ids):
    """El próximo id libre con la forma T001, T002…"""
    numeros = [int(i[1:]) for i in ids if len(i) > 1 and i[0] == "T" and i[1:].isdigit()]
    return f"T{max(numeros, default=0) + 1:03d}"


def ordenar(tabla):
    """Deja la tabla lista para guardar: sin filas vacías, sin espacios sobrantes y con id en cada fila."""
    tabla = tabla.fillna("").astype(str)
    for columna in COLUMNAS:
        tabla[columna] = tabla[columna].str.strip()
    for columna in COLUMNAS_CON_VARIANTES:
        tabla[columna] = tabla[columna].map(lambda t: juntar(variantes(t)))
    con_algo = (tabla[COLUMNAS_DE_CONTENIDO] != "").any(axis=1)
    tabla = tabla[con_algo].reset_index(drop=True)
    ids = list(tabla["id"])
    for i, valor in enumerate(ids):
        if valor == "":
            ids[i] = siguiente_id(ids)
    tabla["id"] = ids
    return tabla


def faltantes(fila):
    """Qué le falta a una fila para estar completa (no impide guardar)."""
    return [nombre for nombre, columna in
            [("inglés", "en"), ("categoría", "pos"), ("traducción preferida", "es_preferred"), ("fuente", "source")]
            if str(fila.get(columna, "")).strip() == ""]


def avisos(tabla):
    """Los problemas del glosario, con las mismas reglas que src/termcheck/glossary.py (validar)."""
    from termcheck.glossary import Termino, separar, validar
    terminos, nombres = [], {}
    for _, f in tabla.iterrows():
        id_ = f["id"] or "(sin id)"
        nombres[id_] = f["en"] or "sin término"
        terminos.append(Termino(id=id_, en=separar(f["en"]), pos=f["pos"], es_preferred=f["es_preferred"],
                                es_allowed=separar(f["es_allowed"]), es_forbidden=separar(f["es_forbidden"]),
                                subdomain=f["subdomain"], note=f["note"], source=f["source"]))
    return [f"**{p.id}** ({nombres.get(p.id, '')}): {p.mensaje}" + (" (aviso)" if p.tipo == "aviso" else "") + "."
            for p in validar(terminos)]


def guardar_fila(fila):
    """Agrega o reemplaza un término (por id) leyendo el archivo en el momento: no pisa cambios hechos en otro lado.
    Devuelve el id con que quedó guardado."""
    tabla = leer()
    if fila.get("id") and (tabla["id"] == fila["id"]).any():
        for columna in COLUMNAS:
            tabla.loc[tabla["id"] == fila["id"], columna] = fila.get(columna, "")
    else:
        fila = dict(fila, id=siguiente_id(list(tabla["id"])))
        tabla = pd.concat([tabla, pd.DataFrame([{c: fila.get(c, "") for c in COLUMNAS}])], ignore_index=True)
    guardar(ordenar(tabla))
    avisar_cambio_externo()
    return fila["id"]


def borrar_fila(id_termino):
    tabla = leer()
    guardar(tabla[tabla["id"] != id_termino].reset_index(drop=True))
    avisar_cambio_externo()


def avisar_cambio_externo():
    """Después de guardar desde las fichas o el formulario, la tabla tiene que volver a leer el archivo."""
    for clave in ("base", "guardado", "fecha"):
        st.session_state.pop(clave, None)
    st.session_state.vuelta = st.session_state.get("vuelta", 0) + 1
