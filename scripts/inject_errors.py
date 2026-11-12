"""Prueba de coherencia con errores sintéticos (plan 6.4). Solo sobre el conjunto de DESARROLLO.

    .venv/bin/python scripts/inject_errors.py

Qué hace:
1. Toma los términos que el dueño anotó «Correcto» en desarrollo y que el verificador también dio por buenos
   (OK o VARIANTE). Esos son los casos de partida.
2. De cada uno hace hasta tres copias de la traducción, cada una con un error puesto a propósito:
   - prohibida: cambia el término por la primera forma prohibida del glosario (si el término no tiene, se saltea);
   - inglés:    cambia el término por el inglés tal como está en el original (si el glosario acepta la forma
                inglesa como válida para ese término, se saltea: no sería un error);
   - borrado:   saca el término de la traducción.
3. Pasa cada copia por el verificador y mira si marca el término.

Qué mide y qué no: mide si el verificador es coherente con su propio glosario (si ve los errores más simples que
se le pueden poner). NO mide el recall real: los errores que comete la traducción automática son otros, y esos se
miden con la anotación (scripts/evaluate.py). Por eso el resultado va en un archivo aparte y marcado como sintético.

Escribe salida/estres.md (el resumen por tipo) y salida/estres_casos.csv (todos los casos, uno por fila).
Se puede volver a correr cuando haya más anotación o cuando el glosario tenga formas prohibidas.
"""
import csv
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

import evaluate as ev  # noqa: E402
from termcheck.checker import verificar  # noqa: E402
from termcheck.glossary import cargar  # noqa: E402
from termcheck.normalize import normalizar  # noqa: E402

TIPOS = ["prohibida", "inglés", "borrado"]
ESPERADA = {"prohibida": "PROHIBIDO", "inglés": "SIN_TRADUCIR", "borrado": "NO_ENCONTRADO"}
COLUMNAS = ["tipo", "seg_id", "system", "term_id", "detectado", "etiqueta_esperada", "etiqueta_verificador",
            "forma_original", "forma_puesta", "otros_terminos_cambiados", "source_en", "target_original",
            "target_modificado"]


def acepta_ingles(t):
    """True si el glosario lista alguna forma inglesa del término como preferida o válida en castellano."""
    aceptadas = {normalizar(f) for f in [t.es_preferred] + list(t.es_allowed) if f}
    return any(normalizar(f) in aceptadas for f in t.en)


def reemplazar(texto, tramos, nuevo):
    """Cambia cada tramo (inicio, fin) del texto por «nuevo». Si «nuevo» es vacío, borra y acomoda los espacios."""
    for inicio, fin in sorted(tramos, reverse=True):
        texto = texto[:inicio] + nuevo + texto[fin:]
    if not nuevo:
        texto = re.sub(r"\s+([.,;:)])", r"\1", re.sub(r"\s{2,}", " ", texto)).strip()
    return texto


def _marcas(ocurrencias):
    """{term_id: lo marcó} para una lista de ocurrencias del verificador."""
    marcas = {}
    for o in ocurrencias:
        marcas[o.term_id] = marcas.get(o.term_id, False) or o.marcada
    return marcas


def casos_de_partida(terminos):
    """Los (anotación, término, ocurrencias, todas las ocurrencias de la traducción) de donde salen las copias."""
    ids = {l.strip() for l in ev.SPLITS["desarrollo"].read_text(encoding="utf-8").splitlines() if l.strip()}
    por_id = {t.id: t for t in terminos}
    segmentos = {f["seg_id"]: f["source_en"] for f in ev.leer(ev.DATOS / "data/corpus/segments.tsv", "\t")}
    trad = {(f["seg_id"], f["system"]): f["target_es"] for f in ev.leer(ev.DATOS / "data/mt/translations.tsv", "\t")}
    partida, verificadas = [], {}
    for g in ev.leer(ev.ANOTACIONES / "gold.csv"):
        clave = (g["seg_id"], g["system"])
        t = por_id.get(g["term_id"])
        if g["seg_id"] not in ids or g["label"] != "CORRECTO" or t is None or clave not in trad:
            continue
        if clave not in verificadas:
            verificadas[clave] = verificar(segmentos[g["seg_id"]], trad[clave], terminos, *clave)
        propias = [o for o in verificadas[clave] if o.term_id == t.id]
        if propias and all(o.label in ("OK", "VARIANTE") for o in propias):
            partida.append({"seg_id": g["seg_id"], "system": g["system"], "termino": t, "ocurrencias": propias,
                            "todas": verificadas[clave], "source_en": segmentos[g["seg_id"]],
                            "target_es": trad[clave]})
    return partida


def inyectar(terminos):
    """Devuelve (casos, salteados). casos: una fila por copia con error. salteados: {tipo: cuántos}."""
    casos, salteados = [], {tipo: 0 for tipo in TIPOS}
    for p in casos_de_partida(terminos):
        t, propias = p["termino"], p["ocurrencias"]
        puestas = {"prohibida": t.es_forbidden[0] if t.es_forbidden else None,
                   "inglés": None if acepta_ingles(t) else propias[0].term_en,
                   "borrado": ""}
        antes = _marcas(p["todas"])
        for tipo in TIPOS:
            if puestas[tipo] is None:
                salteados[tipo] += 1
                continue
            modificado = reemplazar(p["target_es"], [(o.start, o.end) for o in propias], puestas[tipo])
            despues = verificar(p["source_en"], modificado, terminos, p["seg_id"], p["system"])
            marcas = _marcas(despues)
            casos.append({
                "tipo": tipo, "seg_id": p["seg_id"], "system": p["system"], "term_id": t.id,
                "detectado": "sí" if marcas.get(t.id, False) else "no",
                "etiqueta_esperada": ESPERADA[tipo],
                "etiqueta_verificador": "|".join(o.label for o in despues if o.term_id == t.id),
                "forma_original": "|".join(o.es_found for o in propias), "forma_puesta": puestas[tipo],
                # Otros términos de la oración que antes estaban bien y ahora salen marcados, o al revés
                "otros_terminos_cambiados": "|".join(sorted(k for k in antes if k != t.id
                                                            and antes[k] != marcas.get(k, False))),
                "source_en": p["source_en"], "target_original": p["target_es"], "target_modificado": modificado,
            })
    return casos, salteados


def informe(casos, salteados):
    partida = len({(c["seg_id"], c["system"], c["term_id"]) for c in casos})
    lineas = ["# Prueba de coherencia con errores sintéticos · conjunto de desarrollo", "",
              "**Resultado sintético.** Los errores de esta tabla se pusieron a propósito sobre traducciones que "
              "estaban bien. Mide si el verificador es coherente con su glosario. No mide el recall real: ese sale "
              "de la anotación (`salida/eval_*.md`) y no se mezcla con este.", "",
              f"Casos de partida: {partida} términos anotados «Correcto» que el verificador también dio por buenos.",
              "", "| Error puesto | Casos | Detectados | % (IC 95 %) | Con la etiqueta esperada | Salteados |",
              "|---|---:|---:|---|---:|---:|"]
    for tipo in TIPOS:
        cs = [c for c in casos if c["tipo"] == tipo]
        det = sum(c["detectado"] == "sí" for c in cs)
        esperada = sum(ESPERADA[tipo] in c["etiqueta_verificador"].split("|") for c in cs)
        if cs:
            ic = ev.wilson(det, len(cs))
            pct = f"{ev.fmt(100 * det / len(cs))} ({ev.fmt(100 * ic[0])}–{ev.fmt(100 * ic[1])})"
        else:
            pct = "—"
        lineas.append(f"| {tipo} ({ESPERADA[tipo]}) | {len(cs)} | {det} | {pct} | {esperada} | {salteados[tipo]} |")
    lineas += ["", "Salteados: en «prohibida», términos sin forma prohibida en el glosario; en «inglés», términos "
               "cuya forma inglesa el glosario acepta como válida."]
    no_det = [c for c in casos if c["detectado"] == "no"]
    lineas += ["", f"## Errores puestos que el verificador no marcó ({len(no_det)})", ""]
    if no_det:
        lineas += ["| Error | Oración | Sistema | Término | Etiqueta que dio | Traducción modificada |",
                   "|---|---|---|---|---|---|"]
        lineas += [f"| {c['tipo']} | {c['seg_id']} | {c['system']} | {c['term_id']} | "
                   f"{c['etiqueta_verificador'] or '(no detectado)'} | {c['target_modificado']} |" for c in no_det]
    else:
        lineas.append("Ninguno.")
    colaterales = [c for c in casos if c["otros_terminos_cambiados"]]
    lineas += ["", f"Copias donde cambió la marca de otro término de la misma oración: {len(colaterales)} "
               f"de {len(casos)}. El detalle está en `salida/estres_casos.csv`."]
    return "\n".join(lineas) + "\n"


def escribir(casos, salteados):
    salida = ev.DATOS / "salida"
    salida.mkdir(exist_ok=True)
    texto = informe(casos, salteados)
    (salida / "estres.md").write_text(texto, encoding="utf-8")
    with open(salida / "estres_casos.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(casos)
    return texto


def main():
    casos, salteados = inyectar(cargar(ev.GLOSARIO))
    if not casos:
        raise SystemExit("No hay de dónde partir: hace falta al menos un término anotado «Correcto» en desarrollo "
                         "que el verificador también dé por bueno.")
    print(escribir(casos, salteados))


if __name__ == "__main__":
    main()
