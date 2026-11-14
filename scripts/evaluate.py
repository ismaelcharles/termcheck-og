"""Evaluación del verificador contra la anotación del dueño (plan 6.1–6.3).

    .venv/bin/python scripts/evaluate.py                    # desarrollo (lo que esté anotado)
    .venv/bin/python scripts/evaluate.py --conjunto prueba  # la evaluación final (20 oraciones)

Unidad: cada término anotado (seg_id, system, term_id) en gold.csv. Las filas «No va» (descartes.csv) no cuentan.
- «Error» según el dueño: ERROR_TERMINO, OMISION o SIN_TRADUCIR.
- El verificador «marca» si alguna aparición de ese término en esa traducción salió PROHIBIDO, SIN_TRADUCIR o
  NO_ENCONTRADO. Si el verificador no detectó el término (por ejemplo, porque quedó dentro de otro más largo),
  cuenta como no marcado y se informa aparte.
- Baseline: scripts/baseline.py (la preferida como texto exacto).

Escribe salida/eval_<conjunto>.md (tablas para el README) y salida/eval_<conjunto>_casos.csv (todos los FP y FN,
con el inglés y la traducción, para el análisis de errores).

En ese archivo, «causa_sugerida» es una pista automática, hecha con reglas simples (causa_sugerida(), más abajo).
No es el análisis: la causa la decide el dueño y la escribe en la columna «causa», que sale vacía. Las reglas para
los falsos negativos se probaron solo con casos inventados, porque en desarrollo no hubo ninguno.
"""
import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from baseline import marca as marca_baseline  # noqa: E402
from termcheck.checker import verificar  # noqa: E402
from termcheck.glossary import cargar  # noqa: E402
from termcheck.normalize import normalizar  # noqa: E402

ERRORES_GOLD = {"ERROR_TERMINO", "OMISION", "SIN_TRADUCIR"}
# Dónde están los datos. Normalmente, la carpeta del proyecto. Las pruebas automáticas y los ensayos usan otra
# carpeta (TERMCHECK_DATOS) para no tocar los datos reales; TERMCHECK_ANOTACIONES cambia solo la anotación, igual
# que en la app (app/anotacion.py).
DATOS = Path(os.environ.get("TERMCHECK_DATOS") or RAIZ)
ANOTACIONES = Path(os.environ.get("TERMCHECK_ANOTACIONES") or DATOS / "data" / "annotations")
GLOSARIO = DATOS / "data/glossary/glossary_en_es.csv"
CONGELADO = DATOS / "data/glossary/glossary_v1.csv"
SPLITS = {"desarrollo": DATOS / "data/splits/dev_ids.txt", "prueba": DATOS / "data/splits/test_eval_ids.txt"}


def leer(ruta, sep=","):
    if not Path(ruta).exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=sep))


def wilson(aciertos, total, z=1.96):
    """Intervalo de confianza del 95 % para una proporción (Wilson). Con pocos casos, el intervalo es ancho."""
    if total == 0:
        return (0.0, 0.0)
    p = aciertos / total
    centro = (p + z * z / (2 * total)) / (1 + z * z / total)
    margen = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return (max(0.0, centro - margen), min(1.0, centro + margen))


def metricas(pares):
    """pares: [(error_gold, marcado)] → dict con TP, FP, FN, TN, precisión, recall, F1 e intervalos."""
    c = Counter((g, m) for g, m in pares)
    tp, fp, fn, tn = c[(True, True)], c[(False, True)], c[(True, False)], c[(False, False)]
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn, "n": len(pares), "precision": prec, "recall": rec, "f1": f1,
            "precision_ic": wilson(tp, tp + fp), "recall_ic": wilson(tp, tp + fn)}


def fmt(x):
    return f"{x:.2f}".replace(".", ",")


def fila_md(nombre, m):
    return (f"| {nombre} | {m['n']} | {m['TP']} | {m['FP']} | {m['FN']} | {m['TN']} | "
            f"{fmt(m['precision'])} ({fmt(m['precision_ic'][0])}–{fmt(m['precision_ic'][1])}) | "
            f"{fmt(m['recall'])} ({fmt(m['recall_ic'][0])}–{fmt(m['recall_ic'][1])}) | {fmt(m['f1'])} |")


CABECERA = ("| Método | Términos | TP | FP | FN | TN | Precisión (IC 95 %) | Recall (IC 95 %) | F1 |\n"
            "|---|---:|---:|---:|---:|---:|---|---|---:|")


def evaluar(conjunto, glosario_ruta=None):
    glosario_ruta = glosario_ruta or GLOSARIO
    ids = {l.strip() for l in SPLITS[conjunto].read_text(encoding="utf-8").splitlines() if l.strip()}
    terminos = cargar(glosario_ruta)
    por_id = {t.id: t for t in terminos}
    segmentos = {f["seg_id"]: f["source_en"] for f in leer(DATOS / "data/corpus/segments.tsv", "\t")}
    trad = {(f["seg_id"], f["system"]): f["target_es"] for f in leer(DATOS / "data/mt/translations.tsv", "\t")}
    gold = [g for g in leer(ANOTACIONES / "gold.csv") if g["seg_id"] in ids]

    # El verificador, una vez por traducción anotada
    ocurrencias = {}
    for clave in sorted({(g["seg_id"], g["system"]) for g in gold}):
        for o in verificar(segmentos[clave[0]], trad.get(clave, ""), terminos, *clave):
            ocurrencias.setdefault((o.seg_id, o.system, o.term_id), []).append(o)

    casos = []
    for g in gold:
        clave = (g["seg_id"], g["system"], g["term_id"])
        oc = ocurrencias.get(clave, [])
        t = por_id.get(g["term_id"])
        casos.append({
            **g, "error_gold": g["label"] in ERRORES_GOLD,
            "detectado": bool(oc),
            "etiquetas_verificador": "|".join(o.label for o in oc),
            "es_found": "|".join(o.es_found for o in oc),
            "marca_verificador": any(o.marcada for o in oc),
            "marca_baseline": marca_baseline(trad.get(clave[:2], ""), t.es_preferred) if t else True,
            "source_en": segmentos[g["seg_id"]], "target_es": trad.get(clave[:2], ""),
            "es_preferred": t.es_preferred if t else "",
            "sugerencia": "|".join(o.suggestion for o in oc if o.suggestion),
            "causa_sugerida": "", "causa": "",
        })
        if casos[-1]["error_gold"] != casos[-1]["marca_verificador"]:
            casos[-1]["causa_sugerida"] = causa_sugerida(casos[-1], terminos)
    return casos


def _dentro_de_otro(t, texto_en, terminos):
    """Si una forma inglesa del término está dentro de otra más larga de otro término que aparece en la oración,
    devuelve (forma, forma más larga). Si no, None."""
    oracion = f" {normalizar(texto_en)} "
    for otro in terminos:
        if otro.id == t.id:
            continue
        for larga in otro.en:
            for corta in t.en:
                c, l = f" {normalizar(corta)} ", f" {normalizar(larga)} "
                if c != l and c in l and l.rstrip() in oracion:
                    return corta, larga
    return None


def _parecida(caso, t):
    """La forma de la traducción que se parece a una forma válida del glosario sin ser igual, o "".
    Mira lo que el dueño marcó como usado (es_used) y lo que el verificador encontró más parecido a la preferida."""
    from rapidfuzz import fuzz
    validas = [normalizar(f) for f in [t.es_preferred] + list(t.es_allowed) if f]
    for usada in [caso.get("es_used", "")] + caso.get("sugerencia", "").split("|"):
        n = normalizar(usada)
        if n and n not in validas and any(fuzz.ratio(n, v) >= 70 for v in validas):
            return usada
    return ""


def causa_sugerida(caso, terminos):
    """Una pista sobre por qué el verificador y la anotación no coinciden en este caso (plan 6.3).

    Reglas simples, en este orden. Falso positivo (anotado Correcto, el verificador marcó):
      quedó en inglés → préstamo · forma prohibida → ambigüedad · se parece a una forma válida → morfología ·
      si no → sinónimo que falta.
    Falso negativo (anotado como error, el verificador no marcó):
      término no detectado en el inglés → dentro de otro o no detectado · el glosario acepta la forma inglesa →
      préstamo · si no → ambigüedad o error de la anotación.
    """
    t = next((x for x in terminos if x.id == caso["term_id"]), None)
    if t is None:
        return "el término ya no está en el glosario"
    etiquetas = set(caso["etiquetas_verificador"].split("|")) - {""}
    if not caso["error_gold"]:                                        # falso positivo
        if "SIN_TRADUCIR" in etiquetas:
            return "préstamo: quedó en inglés y se anotó Correcto; la forma inglesa no figura como válida"
        if "PROHIBIDO" in etiquetas:
            return (f"ambigüedad: apareció la forma prohibida «{caso['es_found'].strip('|')}» y se anotó Correcto; "
                    "puede tener otro sentido en esta oración")
        parecida = _parecida(caso, t)
        if parecida:
            return f"morfología: «{parecida}» se parece a una forma válida y no se reconoció"
        if caso.get("es_used"):
            return f"sinónimo que falta: se usó «{caso['es_used']}» y el glosario no lo lista"
        return "sinónimo que falta: la traducción usó una forma que el glosario no lista"
    if not caso["detectado"]:                                         # falso negativo
        dentro = _dentro_de_otro(t, caso["source_en"], terminos)
        if dentro:
            return f"término dentro de otro: «{dentro[0]}» quedó dentro de «{dentro[1]}»"
        return "término no detectado en el inglés: la forma del texto no coincide con las del glosario"
    encontrada = caso["es_found"].strip("|")
    if caso["label"] == "SIN_TRADUCIR":
        return f"préstamo: el glosario acepta «{encontrada}» y se anotó Sin traducir"
    return (f"ambigüedad: el verificador encontró la forma válida «{encontrada}» y se anotó "
            f"{'Omisión' if caso['label'] == 'OMISION' else 'Error de término'}; puede estar en otra parte de la "
            "oración o con otro sentido, o es un error de la anotación")


def informe(casos, conjunto):
    v = metricas([(c["error_gold"], c["marca_verificador"]) for c in casos])
    b = metricas([(c["error_gold"], c["marca_baseline"]) for c in casos])
    lineas = [f"# Evaluación · conjunto de {conjunto}", "",
              f"{len(casos)} términos anotados en {len({c['seg_id'] for c in casos})} oraciones "
              f"({sum(c['error_gold'] for c in casos)} errores según la anotación). "
              f"El verificador no detectó {sum(not c['detectado'] for c in casos)} de ellos (cuentan como no marcados).",
              "", "## Verificador frente al baseline", "", CABECERA, fila_md("Baseline (texto exacto)", b),
              fila_md("TermCheck", v), "",
              "## Por sistema de traducción (TermCheck)", "", CABECERA.replace("Método", "Sistema")]
    sistemas = sorted({c["system"] for c in casos})
    for s in sistemas:
        lineas.append(fila_md(s, metricas([(c["error_gold"], c["marca_verificador"]) for c in casos
                                           if c["system"] == s])))
    lineas += ["", "## Errores de terminología según la anotación, por sistema", "",
               "| Sistema | Términos | Errores | % | Error de término | Omisión | Sin traducir |",
               "|---|---:|---:|---:|---:|---:|---:|"]
    for s in sistemas:
        cs = [c for c in casos if c["system"] == s]
        e = Counter(c["label"] for c in cs)
        n_err = sum(c["error_gold"] for c in cs)
        lineas.append(f"| {s} | {len(cs)} | {n_err} | {fmt(100 * n_err / len(cs) if cs else 0)} | "
                      f"{e['ERROR_TERMINO']} | {e['OMISION']} | {e['SIN_TRADUCIR']} |")
    lineas += ["", "## Recall por tipo de error (TermCheck)", "", "| Etiqueta del dueño | Casos | Detectados |",
               "|---|---:|---:|"]
    for lab in ["ERROR_TERMINO", "OMISION", "SIN_TRADUCIR"]:
        cs = [c for c in casos if c["label"] == lab]
        lineas.append(f"| {lab} | {len(cs)} | {sum(c['marca_verificador'] for c in cs)} |")
    lineas += ["", "## Qué etiqueta dio el verificador según la anotación", "",
               "| Anotación \\ Verificador | " + " | ".join(ETIQ) + " |", "|---|" + "---:|" * len(ETIQ)]
    for lab in ["CORRECTO", "ERROR_TERMINO", "OMISION", "SIN_TRADUCIR"]:
        cs = [c for c in casos if c["label"] == lab]
        cuenta = Counter((c["etiquetas_verificador"].split("|")[0] or "(no detectado)") for c in cs)
        lineas.append(f"| {lab} | " + " | ".join(str(cuenta[e]) for e in ETIQ) + " |")
    lineas += ["", "IC 95 %: intervalo de Wilson. Con pocos casos es ancho: los números son orientativos."]
    return "\n".join(lineas) + "\n", v, b


ETIQ = ["OK", "VARIANTE", "PROHIBIDO", "SIN_TRADUCIR", "NO_ENCONTRADO", "(no detectado)"]


COLUMNAS_CASOS = ["tipo", "seg_id", "system", "term_id", "label", "es_used", "comment", "etiquetas_verificador",
                  "es_found", "es_preferred", "source_en", "target_es", "causa_sugerida", "causa"]


def escribir(casos, conjunto):
    """Guarda salida/eval_<conjunto>.md (tablas) y salida/eval_<conjunto>_casos.csv (los FP y FN).
    Lo usan este script y el botón de la app. Devuelve (texto, métricas del verificador, métricas del baseline)."""
    texto, v, b = informe(casos, conjunto)
    salida = DATOS / "salida"
    salida.mkdir(exist_ok=True)
    (salida / f"eval_{conjunto}.md").write_text(texto, encoding="utf-8")
    with open(salida / f"eval_{conjunto}_casos.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS_CASOS, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        for c in casos:
            if c["error_gold"] != c["marca_verificador"]:
                w.writerow({**c, "tipo": "FN" if c["error_gold"] else "FP"})
    return texto, v, b


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--conjunto", choices=list(SPLITS), default="desarrollo")
    a = p.parse_args()
    glosario = GLOSARIO
    if a.conjunto == "prueba":
        glosario = CONGELADO
        if not glosario.exists():
            raise SystemExit("La prueba se evalúa con el glosario congelado (glossary_v1.csv). Congelalo antes, "
                             "desde la app: Resultados → Sugerencias para el glosario.")
        print("Evaluación sobre la PRUEBA, con el glosario v1 congelado.")
    casos = evaluar(a.conjunto, glosario)
    if not casos:
        raise SystemExit(f"No hay anotaciones en el conjunto de {a.conjunto}.")
    texto, _, _ = escribir(casos, a.conjunto)
    print(texto)


if __name__ == "__main__":
    main()
