"""Datos de la anotación a ciegas (plan 5.4). Lo usa app/paginas/anotar.py.

- Dos conjuntos (decisión del dueño, 2026-11-11, para que la anotación entre en el tiempo): «desarrollo» son las
  15 oraciones de data/splits/dev_anotar_ids.txt y «prueba» las 40 de data/splits/test_eval_ids.txt
  (scripts/recortar_splits.py). La prueba se anota igual, a ciegas; el código del verificador nunca la lee.
- Qué se anota: cada término del glosario que aparece en la oración en inglés, en cada una de las tres traducciones.
- A ciegas: las traducciones se muestran como A, B y C, en un orden que depende de la oración (siempre el mismo
  para la misma oración). El sistema se guarda en el archivo pero no se muestra.
- data/annotations/gold.csv: seg_id, system, term_id, label, es_used, comment (formato del plan).
- data/annotations/descartes.csv: apariciones que el dueño marcó como «no va» (por ejemplo, un término detectado
  dentro de otro más largo). No son etiquetas del gold.
- Se guarda de una vez (archivo temporal + reemplazo), leyendo el archivo en el momento.
"""
import csv
import hashlib
import os
import random
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# TERMCHECK_DATOS: otra carpeta con data/ adentro, para pruebas y ensayos que no tocan los datos reales
DATOS = Path(os.environ.get("TERMCHECK_DATOS") or RAIZ)
SEGMENTOS = DATOS / "data" / "corpus" / "segments.tsv"
TRADUCCIONES = DATOS / "data" / "mt" / "translations.tsv"
DEV = DATOS / "data" / "splits" / "dev_ids.txt"
DEV_ANOTAR = DATOS / "data" / "splits" / "dev_anotar_ids.txt"
PRUEBA = DATOS / "data" / "splits" / "test_eval_ids.txt"
GLOSARIO = DATOS / "data" / "glossary" / "glossary_en_es.csv"
# TERMCHECK_ANOTACIONES: otra carpeta, para probar la página sin tocar la anotación real
CARPETA = Path(os.environ.get("TERMCHECK_ANOTACIONES") or DATOS / "data" / "annotations")
GOLD = CARPETA / "gold.csv"
DESCARTES = CARPETA / "descartes.csv"

SISTEMAS = ["opusmt", "claude", "deepl"]
COLUMNAS_GOLD = ["seg_id", "system", "term_id", "label", "es_used", "comment"]
COLUMNAS_DESCARTES = ["seg_id", "system", "term_id", "comment"]

# Las etiquetas del plan (5.4) con su definición
ETIQUETAS = {
    "CORRECTO": "La traducción del término es correcta, aunque no esté en el glosario.",
    "ERROR_TERMINO": "El término está mal traducido.",
    "OMISION": "El término desapareció de la traducción.",
    "SIN_TRADUCIR": "Quedó en inglés y no es un préstamo aceptado.",
}
NO_VA = "NO_VA"  # no es una etiqueta: la aparición no se anota (va a descartes.csv)

GUIONES = re.escape("-‐‑‒–—")


def leer_tsv(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def leer_csv(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _ids(ruta):
    if not ruta.exists():
        return []
    return [l.strip() for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def ids_dev():
    return _ids(DEV)


def ids_conjunto(nombre):
    """Los seg_id que se anotan en un conjunto: «desarrollo» (si no hay recorte, todo dev) o «prueba»."""
    if nombre == "prueba":
        return _ids(PRUEBA)
    return _ids(DEV_ANOTAR) or ids_dev()


def ids_anotables():
    """Dónde se permite guardar: todo desarrollo y la prueba recortada."""
    return set(ids_dev()) | set(_ids(PRUEBA))


def oraciones(nombre):
    """Las oraciones de un conjunto, en orden: [{seg_id, source_en, url}]."""
    ids = set(ids_conjunto(nombre))
    return [s for s in leer_tsv(SEGMENTOS) if s["seg_id"] in ids]


def oraciones_dev():
    """Las oraciones de desarrollo, en orden: [{seg_id, source_en, url}]."""
    dev = set(ids_dev())
    return [s for s in leer_tsv(SEGMENTOS) if s["seg_id"] in dev]


def traducciones(ids):
    """seg_id → {system: target_es}, solo para los ids pedidos."""
    ids = set(ids)
    salida = {}
    for f in leer_tsv(TRADUCCIONES):
        if f["seg_id"] in ids:
            salida.setdefault(f["seg_id"], {})[f["system"]] = f["target_es"]
    return salida


def orden_ciego(seg_id):
    """Los tres sistemas en un orden que depende solo del seg_id: [(letra, sistema)]."""
    semilla = int(hashlib.sha256(seg_id.encode()).hexdigest(), 16)
    sistemas = SISTEMAS[:]
    random.Random(semilla).shuffle(sistemas)
    return list(zip("ABC", sistemas))


def patron(forma):
    """Regex para una forma en inglés en el texto original: sin distinguir mayúsculas, con guion o espacio entre
    palabras, y plural en -s/-es."""
    partes = [re.escape(p) for p in re.split(rf"[\s{GUIONES}]+", forma.strip()) if p]
    return r"\b" + rf"[\s{GUIONES}]+".join(partes) + r"(?:s|es)?\b"


def terminos():
    """Los términos del glosario: [{id, en: [formas]}]."""
    return [{"id": f["id"], "en": [p.strip() for p in f["en"].split("|") if p.strip()]} for f in leer_csv(GLOSARIO)]


def apariciones(texto, lista):
    """Qué términos del glosario aparecen en la oración en inglés.

    Devuelve [{id, forma, inicio, fin}] ordenado por posición; un término cuenta una vez por oración (formato del
    plan: una fila por oración, sistema y término), en su primera aparición. Si un término está dentro de otro más
    largo (casing dentro de casing shoe) se listan los dos: el dueño decide con «No va».
    """
    salida = []
    for t in lista:
        mejor, lugares = None, set()
        for forma in sorted(t["en"], key=len, reverse=True):
            for m in re.finditer(patron(forma), texto, flags=re.IGNORECASE):
                if not any(a <= m.start() < b for a, b in lugares):
                    lugares.add((m.start(), m.end()))
                if mejor is None or m.start() < mejor.start():
                    mejor = m
        if mejor:
            salida.append({"id": t["id"], "forma": mejor.group(0), "inicio": mejor.start(), "fin": mejor.end(),
                           "veces": len(lugares)})
    return sorted(salida, key=lambda a: (a["inicio"], -a["fin"]))


def dentro_de_otro(a, todas):
    """True si la aparición a está dentro de otra más larga de la misma oración."""
    return any(b is not a and b["inicio"] <= a["inicio"] and a["fin"] <= b["fin"] and (b["fin"] - b["inicio"]) >
               (a["fin"] - a["inicio"]) for b in todas)


def _escribir(ruta, columnas, filas):
    CARPETA.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(".tmp")
    with open(temporal, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(filas, key=lambda x: (x["seg_id"], x["system"], x["term_id"])))
    temporal.replace(ruta)


def anotadas():
    """(seg_id, system, term_id) → fila, de gold.csv y de descartes.csv (estas con label NO_VA)."""
    salida = {(f["seg_id"], f["system"], f["term_id"]): f for f in leer_csv(GOLD)}
    for f in leer_csv(DESCARTES):
        salida[(f["seg_id"], f["system"], f["term_id"])] = dict(f, label=NO_VA, es_used="")
    return salida


def guardar(seg_id, system, filas):
    """Reemplaza todo lo anotado para (seg_id, system) por filas [{term_id, label, es_used, comment}].

    Se niega a guardar oraciones que no son de desarrollo, sistemas desconocidos o etiquetas fuera del plan.
    """
    if seg_id not in ids_anotables():
        raise ValueError(f"{seg_id} no está en un conjunto que se anote")
    if system not in SISTEMAS:
        raise ValueError(f"sistema desconocido: {system}")
    for f in filas:
        if f["label"] not in ETIQUETAS and f["label"] != NO_VA:
            raise ValueError(f"etiqueta desconocida: {f['label']}")
    mismo = lambda x: x["seg_id"] == seg_id and x["system"] == system  # noqa: E731
    gold = [f for f in leer_csv(GOLD) if not mismo(f)]
    desc = [f for f in leer_csv(DESCARTES) if not mismo(f)]
    for f in filas:
        base = {"seg_id": seg_id, "system": system, "term_id": f["term_id"], "comment": f.get("comment", "").strip()}
        if f["label"] == NO_VA:
            desc.append(base)
        else:
            gold.append(dict(base, label=f["label"], es_used=f.get("es_used", "").strip()))
    _escribir(GOLD, COLUMNAS_GOLD, gold)
    _escribir(DESCARTES, COLUMNAS_DESCARTES, desc)


def guardar_uno(seg_id, system, term_id, label, es_used="", comment=""):
    """Guarda una sola etiqueta (seg_id, system, term_id). label None la borra. Lo usa la página al elegir cada
    etiqueta, para que no haga falta un botón de guardar."""
    if seg_id not in ids_anotables():
        raise ValueError(f"{seg_id} no está en un conjunto que se anote")
    if system not in SISTEMAS:
        raise ValueError(f"sistema desconocido: {system}")
    if label is not None and label not in ETIQUETAS and label != NO_VA:
        raise ValueError(f"etiqueta desconocida: {label}")
    mismo = lambda x: (x["seg_id"], x["system"], x["term_id"]) == (seg_id, system, term_id)  # noqa: E731
    gold = [f for f in leer_csv(GOLD) if not mismo(f)]
    desc = [f for f in leer_csv(DESCARTES) if not mismo(f)]
    base = {"seg_id": seg_id, "system": system, "term_id": term_id, "comment": (comment or "").strip()}
    if label == NO_VA:
        desc.append(base)
    elif label:
        gold.append(dict(base, label=label, es_used=(es_used or "").strip()))
    _escribir(GOLD, COLUMNAS_GOLD, gold)
    _escribir(DESCARTES, COLUMNAS_DESCARTES, desc)


def completar_correcto(seg_id, celdas):
    """Pone CORRECTO en las celdas [(system, term_id)] que todavía no tienen nada. Lo ya anotado no se toca.
    Una sola escritura. Devuelve cuántas completó."""
    if seg_id not in ids_anotables():
        raise ValueError(f"{seg_id} no está en un conjunto que se anote")
    hechas = anotadas()
    faltan = [(s, t) for s, t in celdas if s in SISTEMAS and not hechas.get((seg_id, s, t), {}).get("label")]
    if not faltan:
        return 0
    gold = leer_csv(GOLD) + [{"seg_id": seg_id, "system": s, "term_id": t, "label": "CORRECTO", "es_used": "",
                              "comment": ""} for s, t in faltan]
    _escribir(GOLD, COLUMNAS_GOLD, gold)
    return len(faltan)


PALABRA = re.compile(r"[^\W_]+(?:[-'’][^\W_]+)*")


def palabras(texto):
    """Las palabras de una traducción, en orden (sin signos de puntuación). Para marcar la forma usada con clics."""
    return PALABRA.findall(texto)


def forma(lista, indices):
    """Las palabras elegidas (por posición), en el orden de la oración: [3, 1] → «lista[1] lista[3]»."""
    return " ".join(lista[i] for i in sorted(indices))


def indices_de(es_used, lista):
    """Al revés que forma(): dónde está una forma ya guardada dentro de la traducción. [] si no se encuentra."""
    buscada = [p.lower() for p in palabras(es_used)]
    if not buscada:
        return []
    bajas = [p.lower() for p in lista]
    for i in range(len(bajas) - len(buscada) + 1):
        if bajas[i:i + len(buscada)] == buscada:
            return list(range(i, i + len(buscada)))
    return []
