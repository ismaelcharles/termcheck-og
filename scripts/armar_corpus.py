"""Arma el corpus de origen (data/corpus/segments.tsv) con oraciones en inglés de textos de dominio público.

Fuentes:
- OSHA eTool (páginas guardadas como PDF por el dueño en data/originales/osha/): fuente principal.
- Reglamentos y guías federales de EE. UU. (BLM, BSEE, EPA) en data/corpus/fuentes/: para los términos que OSHA no trae.

Qué se descarta, para que cada oración sea texto original, completo y publicable:
- los recuadros de definición marcados con † (vienen del diccionario de Petex, con copyright) y el glosario de OSHA;
- encabezados, pies de página, títulos, rótulos de figuras y viñetas que no son oraciones;
- oraciones sin verbo conjugado ni imperativo («Being struck by…»: es un rótulo de riesgo, no una oración);
- oraciones con citas entre corchetes o de normas API, con «§», o que empiezan con «See»;
- oraciones repetidas o contenidas dentro de otra ya elegida;
- en los reglamentos, oraciones con una palabra partida con guion al final de línea (no se adivina cómo se unía).

Cómo se eligen (siempre igual: no hay azar):
1. Se cubre cada término del glosario al menos una vez, eligiendo primero la oración que cubre más términos todavía
   no cubiertos; ante empate, OSHA antes que los reglamentos y la oración más corta.
2. Se completa hasta TOTAL con oraciones de OSHA que suman términos con menos apariciones.

Correr:  .venv/bin/python scripts/armar_corpus.py
Escribe data/corpus/segments.tsv y data/corpus/COBERTURA.md.
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

import spacy  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
from termcheck.glossary import cargar  # noqa: E402
from termcheck.normalize import normalizar  # noqa: E402

TOTAL = 120
MIN_PALABRAS, MAX_PALABRAS = 6, 45
OSHA = RAIZ / "data" / "originales" / "osha"
FUENTES = RAIZ / "data" / "corpus" / "fuentes"
SALIDA = RAIZ / "data" / "corpus" / "segments.tsv"
COBERTURA = RAIZ / "data" / "corpus" / "COBERTURA.md"

# Página del navegador: fecha y hora, título, número de página, menú
RUIDO_OSHA = re.compile(r"^(\d+/\d+/\d+, \d+:\d+|eTool : .*|\d+/\d+|U\.S\. DEPARTMENT OF LABOR|"
                        r"Occupational Safety and Health Administration|Oil and Gas Well Drilling and Servicing eTool|"
                        r"Oil and Gas Menu|https?://\S+)$")
# Marcas de imprenta de govinfo y encabezados de página de los reglamentos
RUIDO_CFR = re.compile(r"(VerDate|Jkt \d|Frm \d|Sfmt|PsN:|Y:\\SGML|^\d+$|^§ \d|Interior\s+§|"
                       r"Environmental Protection Agency\s+§|^\d+ CFR Ch\.|^Pt\. \d+)")
FIN = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")
CORTE = "\x01"  # marca dónde había una palabra partida con guion al final de línea
ANCHO = 105  # las líneas que el navegador corta por ancho miden entre 110 y 134 caracteres
NLP = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
ABREVIATURAS = ("e.g.", "i.e.", "No.", "U.S.", "O.D.", "I.D.", "ft.", "in.", "Fig.", "approx.", "etc.", "vs.")


def texto_pdf(ruta):
    return subprocess.run(["pdftotext", str(ruta), "-"], capture_output=True, text=True, check=True).stdout


def url_osha(texto):
    m = re.search(r"https://www\.osha\.gov/etools/oil-and-gas\S*", texto)
    return m.group(0) if m else ""


def parrafos_osha(texto):
    """Líneas de la página impresa → párrafos. Una línea larga sin punto final sigue en la siguiente."""
    lineas = [l.rstrip() for l in texto.splitlines() if not RUIDO_OSHA.match(l.strip())]
    bloques, actual = [], []
    for l in lineas + [""]:
        if l.strip():
            actual.append(l.strip())
        else:
            if actual:
                bloques.append(actual)
            actual = []
    parrafos = []
    for bloque in bloques:
        if any("†" in l for l in bloque):
            continue  # recuadro de definición del diccionario de Petex
        pedazo = ""
        for n, l in enumerate(bloque):
            pedazo = f"{pedazo} {l}".strip()
            sigue_en_minuscula = n + 1 < len(bloque) and bloque[n + 1][:1].islower()
            if (len(l) < ANCHO and not sigue_en_minuscula) or l[-1] in ".:?!":
                parrafos.append((pedazo, False))
                pedazo = ""
        if pedazo:
            parrafos.append((pedazo, False))
    return parrafos


def parrafos_cfr(texto):
    """Reglamentos a dos columnas: se juntan las líneas de cada párrafo. Donde una palabra quedó partida con guion
    se deja la marca CORTE: la oración que la tenga se descarta."""
    lineas = [l.strip() for l in texto.splitlines() if not RUIDO_CFR.search(l.strip())]
    parrafos, actual = [], []
    for l in lineas + [""]:
        nuevo_inciso = re.match(r"^\(([a-z]|\d+|[ivx]+)\)\s", l)
        if not l or nuevo_inciso:
            if actual:
                parrafos.append((" ".join(actual), False))
            actual = [l] if l else []
            continue
        if actual and actual[-1].endswith("-") and l[:1].islower():
            actual[-1] += CORTE
        actual.append(l)
    return parrafos


def oraciones(parrafo):
    protegido = parrafo
    for a in ABREVIATURAS:  # solo como palabra entera: «in.» no tiene que encontrarse dentro de «chain.»
        protegido = re.sub(r"(?<![A-Za-z])" + re.escape(a), a.replace(".", "\x00"), protegido)
    partes = FIN.split(protegido)
    # «(1) Your composite…»: el número de inciso no es parte de la oración
    return [re.sub(r"^\(([a-z]|\d+|[ivx]+)\)\s+", "", o.replace("\x00", ".")).strip() for o in partes]


def tiene_verbo(o):
    """El verbo principal está conjugado («is», «could cause») o es un imperativo al principio («Inspect…»).
    «Being struck by debris if the block runs…» no sirve: «runs» está conjugado, pero dentro del «if»."""
    doc = NLP(o)
    raiz = next(t for t in doc if t.dep_ == "ROOT")
    conjugado = "Fin" in raiz.morph.get("VerbForm") or any(
        h.dep_ in ("aux", "auxpass") and (h.tag_ == "MD" or "Fin" in h.morph.get("VerbForm")) for h in raiz.children)
    imperativo = raiz.tag_ == "VB" and raiz.i == doc[0].i
    sin_sujeto = doc[0].tag_ == "VBZ"  # «Covers such items as…»: descripción de un documento, sin sujeto
    return (conjugado or imperativo) and not sin_sujeto


def sirve(o):
    palabras = re.findall(r"[A-Za-z0-9']+", o)
    return (MIN_PALABRAS <= len(palabras) <= MAX_PALABRAS and o[:1].isupper() and o[-1] == "."
            and not re.search(r"[\[\]§†\x01]|More\.\.\.|^See |^Note:|^Figure|^Fig\.|https?:|RP \d|"
                              r"American Petroleum Institute|illustration:| - |\(Specify\)|\d\.$", o)
            and not o.isupper() and tiene_verbo(o))


def patron(termino):
    formas = sorted((re.escape(normalizar(f)) for f in termino.en), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(formas) + r")(?:s|es)?\b")


def juntar_candidatas():
    """Todas las oraciones que sirven, con su fuente y URL. Sin repetidas."""
    candidatas, vistas = [], set()

    def agregar(texto_oracion, url, origen):
        clave = normalizar(texto_oracion).rstrip(".")
        if not any(clave in v or v in clave for v in vistas):  # repetida o contenida en otra
            vistas.add(clave)
            candidatas.append({"texto": texto_oracion, "url": url, "origen": origen})

    for pdf in sorted(OSHA.glob("*.pdf")):
        if "Glossary" in pdf.name:
            continue  # el glosario de OSHA es el diccionario de Petex (con copyright)
        texto = texto_pdf(pdf)
        url = url_osha(texto)
        for parrafo, _ in parrafos_osha(texto):
            for o in oraciones(parrafo):
                if sirve(o):
                    agregar(o, url, "OSHA")

    urls = dict(re.findall(r"\| (\S+\.pdf) \| [^|]+ \| (\S+) \|", (FUENTES / "README.md").read_text()))
    for pdf in sorted(FUENTES.glob("*.pdf")):
        for parrafo, cortado in parrafos_cfr(texto_pdf(pdf)):
            if cortado:
                continue
            for o in oraciones(re.sub(r"^\(([a-z]|\d+|[ivx]+)\)\s+", "", parrafo)):
                if sirve(o):
                    agregar(o, urls.get(pdf.name, pdf.name), pdf.name.split("_")[0].upper())
    return candidatas


def elegir(candidatas, terminos):
    patrones = {t.id: patron(t) for t in terminos}
    for c in candidatas:
        texto = normalizar(c["texto"])
        c["terminos"] = {i for i, p in patrones.items() if p.search(texto)}
        c["palabras"] = len(c["texto"].split())
    candidatas = [c for c in candidatas if c["terminos"]]
    elegidas, cuenta = [], {t.id: 0 for t in terminos}

    def tomar(c):
        elegidas.append(c)
        candidatas.remove(c)
        for i in c["terminos"]:
            cuenta[i] += 1

    # 1. Cubrir cada término al menos una vez
    while True:
        faltan = {i for i, n in cuenta.items() if n == 0}
        utiles = [c for c in candidatas if c["terminos"] & faltan]
        if not utiles:
            break
        tomar(max(utiles, key=lambda c: (len(c["terminos"] & faltan), c["origen"] == "OSHA", -c["palabras"])))
    # 2. Completar con OSHA, sumando los términos que menos aparecen
    while len(elegidas) < TOTAL:
        osha = [c for c in candidatas if c["origen"] == "OSHA"] or candidatas
        if not osha:
            break
        tomar(max(osha, key=lambda c: (sum(1 / (1 + cuenta[i]) for i in c["terminos"]), -c["palabras"])))
    return elegidas, cuenta


def main():
    terminos = cargar(RAIZ / "data" / "glossary" / "glossary_en_es.csv")
    candidatas = juntar_candidatas()
    elegidas, cuenta = elegir(candidatas, terminos)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["seg_id", "source_en", "url"])
        for n, c in enumerate(elegidas, start=1):
            w.writerow([f"S{n:03d}", c["texto"], c["url"]])
    nombres = {t.id: t.en[0] for t in terminos}
    sin = [f"{i} {nombres[i]}" for i, n in cuenta.items() if n == 0]
    origenes = {}
    for c in elegidas:
        origenes[c["origen"]] = origenes.get(c["origen"], 0) + 1
    lineas = [
        "# Cobertura del corpus", "",
        f"Generado por `scripts/armar_corpus.py`. {len(elegidas)} oraciones de {len(candidatas)} candidatas.", "",
        "Oraciones por fuente: " + ", ".join(f"{k} {v}" for k, v in sorted(origenes.items())) + ".", "",
        f"Términos cubiertos: {len(terminos) - len(sin)} de {len(terminos)}.", "",
        "## Términos sin ninguna oración", "", *([f"- {s}" for s in sin] or ["Ninguno."]), "",
        "## Apariciones por término", "", "| Término | Inglés | Oraciones |", "|---|---|---|",
        *[f"| {i} | {nombres[i]} | {n} |" for i, n in cuenta.items()], "",
    ]
    COBERTURA.write_text("\n".join(lineas), encoding="utf-8")
    print(f"{len(elegidas)} oraciones · {len(terminos) - len(sin)} de {len(terminos)} términos cubiertos · "
          f"por fuente: {origenes}")
    if sin:
        print("Sin cubrir:", "; ".join(sin))


if __name__ == "__main__":
    main()
