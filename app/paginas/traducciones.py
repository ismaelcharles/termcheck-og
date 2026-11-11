"""Página de traducciones: estado de los 3 sistemas y carga de DeepL por tandas.

DeepL se usa desde su página web gratuita (no hay API). La web acepta hasta 1.500 caracteres por vez, así que el
corpus se corta en tandas. Cada tanda se copia con un botón, se pega en DeepL y la traducción se pega de vuelta acá.
Cuando están todas, se unen en data/mt/translations.tsv con el sistema «deepl».
"""
import csv
from datetime import date

import streamlit as st

import datos
import vista

SEGMENTOS = datos.RAIZ / "data" / "corpus" / "segments.tsv"
TRADUCCIONES = datos.RAIZ / "data" / "mt" / "translations.tsv"
VERSIONES = datos.RAIZ / "data" / "mt" / "versiones.csv"
CARPETA_DEEPL = datos.RAIZ / "data" / "mt" / "deepl"
LIMITE = 1400  # caracteres por tanda (DeepL web acepta 1.500)
SISTEMAS = {"opusmt": "Opus-MT", "claude": "Claude (sin glosario)", "deepl": "DeepL"}


def leer(ruta, separador="\t"):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=separador))


def tandas(segmentos):
    """Corta el corpus en tandas de hasta LIMITE caracteres, sin partir oraciones."""
    lista, actual, largo = [], [], 0
    for s in segmentos:
        if actual and largo + len(s["source_en"]) + 1 > LIMITE:
            lista.append(actual)
            actual, largo = [], 0
        actual.append(s)
        largo += len(s["source_en"]) + 1
    if actual:
        lista.append(actual)
    return lista


def lineas(texto):
    return [l.strip() for l in texto.splitlines() if l.strip()]


def archivo_tanda(n):
    return CARPETA_DEEPL / f"tanda_{n:02d}.txt"


def unir(lista):
    """Escribe las filas de DeepL en translations.tsv (conserva las de los otros sistemas) y anota la fecha."""
    nuevas = []
    for n, tanda in enumerate(lista, start=1):
        for s, t in zip(tanda, lineas(archivo_tanda(n).read_text(encoding="utf-8"))):
            nuevas.append({"seg_id": s["seg_id"], "system": "deepl", "target_es": t})
    otras = [f for f in leer(TRADUCCIONES) if f["system"] != "deepl"]
    with open(TRADUCCIONES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["seg_id", "system", "target_es"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(otras + nuevas, key=lambda x: (x["seg_id"], x["system"])))
    versiones = [v for v in leer(VERSIONES, ",") if v["system"] != "deepl"]
    versiones.append({"system": "deepl", "fecha": date.today().isoformat(), "version": "DeepL Translator web gratuita",
                      "como": "pegado a mano por tandas, inglés → español, sin opciones ni glosario"})
    with open(VERSIONES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["system", "fecha", "version", "como"], lineterminator="\n")
        w.writeheader()
        w.writerows(versiones)
    return len(nuevas)


vista.estilos()
st.title("Traducciones")
segmentos = leer(SEGMENTOS)
if not segmentos:
    st.info("Todavía no hay corpus (data/corpus/segments.tsv).")
    st.stop()

hechas = leer(TRADUCCIONES)
columnas = st.columns(len(SISTEMAS))
for col, (clave, nombre) in zip(columnas, SISTEMAS.items()):
    cuantas = sum(1 for f in hechas if f["system"] == clave)
    col.metric(nombre, f"{cuantas} de {len(segmentos)}")

st.subheader("DeepL")
lista = tandas(segmentos)
listas = [n for n in range(1, len(lista) + 1) if archivo_tanda(n).exists()]
st.markdown(
    f"1. Abrí [DeepL](https://www.deepl.com/translator) en otra pestaña, con **inglés → español**. No hace falta cuenta "
    f"y no cambies ninguna opción.\n"
    f"2. En cada tanda, copiá el texto con el botón de la esquina del recuadro, pegalo en DeepL, copiá la traducción "
    f"y pegala en el campo de abajo.\n"
    f"3. Guardá la tanda. La app controla que vuelvan tantas líneas como oraciones mandaste.\n\n"
    f"Van **{len(listas)} de {len(lista)}** tandas guardadas.")
st.progress(len(listas) / len(lista))

CARPETA_DEEPL.mkdir(parents=True, exist_ok=True)
for n, tanda in enumerate(lista, start=1):
    guardada = archivo_tanda(n).exists()
    titulo = f"Tanda {n}: {tanda[0]['seg_id']} a {tanda[-1]['seg_id']} ({len(tanda)} oraciones)"
    with st.expander(titulo, expanded=not guardada and n == min(set(range(1, len(lista) + 1)) - set(listas),
                                                                     default=0),
                     icon=":material/check_circle:" if guardada else ":material/radio_button_unchecked:"):
        st.code("\n".join(s["source_en"] for s in tanda), language=None, wrap_lines=True)
        previo = archivo_tanda(n).read_text(encoding="utf-8") if guardada else ""
        pegado = st.text_area("Traducción de DeepL", value=previo, key=f"deepl_{n}", height=220,
                              placeholder="Pegá acá lo que devolvió DeepL")
        recibidas = lineas(pegado)
        if pegado and len(recibidas) != len(tanda):
            st.warning(f"Llegaron {len(recibidas)} líneas y la tanda tiene {len(tanda)} oraciones. Revisá que DeepL "
                       "no haya unido o partido alguna.")
        if st.button("Guardar tanda", key=f"guardar_{n}", type="primary", icon=":material/save:",
                     disabled=len(recibidas) != len(tanda)):
            archivo_tanda(n).write_text("\n".join(recibidas) + "\n", encoding="utf-8")
            st.rerun()

if len(listas) == len(lista):
    if st.button("Unir las tandas en el archivo de traducciones", type="primary", icon=":material/merge:"):
        st.success(f"Listo: {unir(lista)} traducciones de DeepL en data/mt/translations.tsv.")
