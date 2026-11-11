"""El verificador: dado un segmento en inglés, su traducción y el glosario, etiqueta cada término (plan 3.1 y 3.2).

    from termcheck.glossary import cargar
    from termcheck.checker import verificar
    terminos = cargar("data/glossary/glossary_en_es.csv")
    for o in verificar("Run the casing.", "Se bajó el casing.", terminos):
        print(o.term_id, o.label, o.es_found)        # T005 OK casing

Pasos:
1. Detectar los términos en el inglés (matcher.buscar). Si dos se superponen («drill pipe» y «pipe»), gana el más
   largo. Cada aparición cuenta aparte (el mismo término dos veces = dos filas).
2. Para cada aparición, buscar en la traducción la preferida, las válidas, las prohibidas y las formas en inglés.
3. Etiquetar con esta prioridad: PROHIBIDO > OK > VARIANTE > SIN_TRADUCIR > NO_ENCONTRADO.
   Lo que en la traducción ya usó un término no lo puede usar otro (así «pozo» dentro de «boca de pozo» no vale
   dos veces). Se resuelven primero los términos más largos.
4. Si no se encontró nada, rapidfuzz SUGIERE lo más parecido a la preferida (nunca cambia la etiqueta).
"""
from dataclasses import dataclass

from termcheck.matcher import analizar, analizar_forma, buscar, es_sigla, pos_aceptable
from termcheck.normalize import normalizar

PRIORIDAD = ["PROHIBIDO", "OK", "VARIANTE", "SIN_TRADUCIR"]
MARCAN = {"PROHIBIDO", "SIN_TRADUCIR", "NO_ENCONTRADO"}  # lo que se marca para revisar (plan 6.1)


@dataclass
class Ocurrencia:
    """Una aparición de un término del glosario en un segmento, ya etiquetada."""
    seg_id: str
    system: str
    term_id: str
    term_en: str       # cómo aparece en el inglés: «drilling rigs»
    label: str         # OK, VARIANTE, PROHIBIDO, SIN_TRADUCIR, NO_ENCONTRADO
    es_found: str      # cómo aparece en la traducción (vacío si NO_ENCONTRADO)
    start: int         # posición en la traducción (-1 si no se encontró)
    end: int
    src_start: int     # posición en el inglés
    src_end: int
    es_expected: str = ""  # la preferida del glosario
    es_form: str = ""      # la forma del glosario que coincidió (para la consistencia)
    suggestion: str = ""   # solo en NO_ENCONTRADO: lo más parecido a la preferida, para revisar

    @property
    def marcada(self):
        return self.label in MARCAN


def _formas_es(t):
    """Las formas a buscar en la traducción, con su etiqueta: [(label, forma, sigla)]."""
    formas = [("PROHIBIDO", f) for f in t.es_forbidden] + [("OK", t.es_preferred)]
    formas += [("VARIANTE", f) for f in t.es_allowed]
    # El término en inglés en la traducción. Si además figura como préstamo aceptado, ya quedó como OK o VARIANTE.
    aceptadas = {normalizar(f) for f in [t.es_preferred] + t.es_allowed}
    formas += [("SIN_TRADUCIR", f) for f in t.en if normalizar(f) not in aceptadas]
    return [(label, f, f if es_sigla(f) else None) for label, f in formas if f]


def detectar(palabras_en, terminos):
    """Los términos del glosario en el inglés: [(i, j, termino)] sin superposiciones, en orden de aparición."""
    candidatos = []
    for t in terminos:
        for forma in t.en:
            sigla = forma if es_sigla(forma) else None
            for i, j in buscar(palabras_en, analizar_forma(forma, "en"), "en", sigla):
                if pos_aceptable(t.pos, palabras_en[i:j]):
                    candidatos.append((i, j, t))
    # Gana el más largo (en palabras; a igual largo, el que empieza antes)
    candidatos.sort(key=lambda c: (-(c[1] - c[0]), c[0]))
    tomadas, salida = set(), []
    for i, j, t in candidatos:
        if not tomadas & set(range(i, j)):
            tomadas |= set(range(i, j))
            salida.append((i, j, t))
    return sorted(salida, key=lambda c: c[0])


def _sugerir(texto_es, palabras_es, preferida, usadas):
    """La secuencia de palabras libres más parecida a la preferida (rapidfuzz), si se parece bastante."""
    from rapidfuzz import fuzz
    n = max(1, len(preferida.split()))
    mejor, puntaje = "", 0
    for largo in {max(1, n - 1), n, n + 1}:
        for i in range(len(palabras_es) - largo + 1):
            if usadas & set(range(i, i + largo)):
                continue
            tramo = texto_es[palabras_es[i].inicio:palabras_es[i + largo - 1].fin]
            p = fuzz.ratio(normalizar(tramo), normalizar(preferida))
            if p > puntaje:
                mejor, puntaje = tramo, p
    return mejor if puntaje >= 70 else ""


def verificar(texto_en, texto_es, terminos, seg_id="", system=""):
    """Etiqueta cada aparición de un término del glosario. Devuelve [Ocurrencia] en el orden del inglés."""
    palabras_en = analizar(texto_en, "en")
    palabras_es = analizar(texto_es or "", "es")
    apariciones = detectar(palabras_en, terminos)
    resultado = {}
    usadas = set()  # palabras de la traducción ya asignadas a algún término

    # Primero los términos más largos en inglés (suelen tener la traducción más larga)
    orden = sorted(range(len(apariciones)), key=lambda k: -(apariciones[k][1] - apariciones[k][0]))
    for k in orden:
        i, j, t = apariciones[k]
        encontrado = None
        for label in PRIORIDAD:
            tramos = []
            for lab, forma, sigla in _formas_es(t):
                if lab == label:
                    tramos += [(a, b, forma) for a, b in buscar(palabras_es, analizar_forma(forma, "es"), "es", sigla)]
            # la más larga primero, después la que está más a la izquierda
            for a, b, forma in sorted(tramos, key=lambda x: (-(x[1] - x[0]), x[0])):
                if not usadas & set(range(a, b)):
                    encontrado = (label, a, b, forma)
                    break
            if encontrado:
                break
        o = Ocurrencia(seg_id, system, t.id, texto_en[palabras_en[i].inicio:palabras_en[j - 1].fin], "NO_ENCONTRADO",
                       "", -1, -1, palabras_en[i].inicio, palabras_en[j - 1].fin, t.es_preferred)
        if encontrado:
            label, a, b, forma = encontrado
            usadas |= set(range(a, b))
            o.label, o.start, o.end, o.es_form = label, palabras_es[a].inicio, palabras_es[b - 1].fin, forma
            o.es_found = texto_es[o.start:o.end]
        resultado[k] = o
    # Sugerencias al final, cuando ya se sabe qué palabras quedaron libres
    for o in resultado.values():
        if o.label == "NO_ENCONTRADO":
            o.suggestion = _sugerir(texto_es or "", palabras_es, o.es_expected, usadas)
    return [resultado[k] for k in range(len(apariciones))]


def verificar_tabla(segmentos, traducciones, terminos, sistemas=None, ids=None):
    """Verifica muchas traducciones.

    segmentos: {seg_id: texto_en}. traducciones: [{seg_id, system, target_es}].
    sistemas, ids: si se dan, solo esos. Devuelve [Ocurrencia].
    """
    salida = []
    for fila in traducciones:
        if sistemas and fila["system"] not in sistemas:
            continue
        if ids is not None and fila["seg_id"] not in ids:
            continue
        salida += verificar(segmentos[fila["seg_id"]], fila["target_es"], terminos, fila["seg_id"], fila["system"])
    return salida
