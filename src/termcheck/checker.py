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
   Una forma de varias palabras también vale si va coordinada con otra y comparten el principio: «pozo de
   petróleo o gas» por «pozo de gas» (matcher.buscar_coordinada, desde la versión 0.2).
3. Una prohibida que es parte estricta de una forma completa admitida del mismo término no compite con ella.
   Las demás coincidencias se etiquetan con prioridad PROHIBIDO > OK > VARIANTE > SIN_TRADUCIR > NO_ENCONTRADO.
   Lo que en la traducción ya usó un término no lo puede usar otro (así «pozo» dentro de «boca de pozo» no vale
   dos veces). Se resuelven primero los términos más largos.
   De las formas libres se toma la más larga y, a igual largo, la que está más a la izquierda. Hay una excepción:
   cuando el término también aparece dentro de un término más largo que no se encontró («casing» dentro de
   «casing string»), esa mención compite por las mismas palabras de la traducción. Ahí se alinean por posición,
   respetando el orden: cada mención con la aparición que le cae más cerca. Si no alcanzan para todas, la que
   queda sin pareja es NO_ENCONTRADO.
4. Si no se encontró nada, rapidfuzz SUGIERE lo más parecido a la preferida (nunca cambia la etiqueta).
"""
from dataclasses import dataclass

from termcheck.etiquetas import MARCAN  # lo que se marca para revisar: PROHIBIDO, SIN_TRADUCIR, NO_ENCONTRADO
from termcheck.matcher import analizar, analizar_forma, buscar, buscar_coordinada, es_sigla, pos_aceptable
from termcheck.normalize import normalizar

# El orden en que se decide la etiqueta (no es el orden en que se muestran: ese está en etiquetas.py)
PRIORIDAD = ["PROHIBIDO", "OK", "VARIANTE", "SIN_TRADUCIR"]


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
    es_allowed: tuple = ()  # las otras formas que el glosario acepta (para que el reporte pueda nombrarlas)

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


def _tramos_es(t, palabras_es):
    """Coincidencias por etiqueta, con los tokens propios de cada tramo."""
    tramos = {label: [] for label in PRIORIDAD}
    for label, forma, sigla in _formas_es(t):
        palabras_forma = analizar_forma(forma, "es")
        tramos[label] += [(a, b, forma, b-a, frozenset(range(a, b)))
                          for a, b in buscar(palabras_es, palabras_forma, "es", sigla)]
        tramos[label] += [(a, b, forma, len(palabras_forma), frozenset(propias))
                          for a, b, propias in buscar_coordinada(palabras_es, palabras_forma)]
    return tramos


def detectar(palabras_en, terminos):
    """Los términos del glosario en el inglés: [(i, j, termino)] sin superposiciones, en orden de aparición."""
    return _detectar(palabras_en, terminos)[0]


def _detectar(palabras_en, terminos):
    """Devuelve (apariciones, anidadas). anidadas: las menciones que perdieron contra un término más largo que las
    contiene enteras, como [(i, j, termino, k)], donde k es el lugar del término largo en «apariciones»."""
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
    salida.sort(key=lambda c: c[0])
    anidadas, vistas = [], set()
    for i, j, t in candidatos:
        for k, (a, b, largo) in enumerate(salida):
            if a <= i and j <= b and (j - i) < (b - a) and largo.id != t.id and (i, j, t.id) not in vistas:
                vistas.add((i, j, t.id))
                anidadas.append((i, j, t, k))
    return salida, anidadas


def _centro(palabras, i, j, largo_texto):
    """Dónde cae el tramo palabras[i:j] dentro de su texto, de 0 (al principio) a 1 (al final)."""
    return (palabras[i].inicio + palabras[j - 1].fin) / 2 / max(1, largo_texto)


def _alinear(cortos, largos):
    """Empareja en orden dos listas de posiciones ya ordenadas, len(cortos) <= len(largos).

    Cada elemento de «cortos» recibe uno de «largos», sin cruzarse, de modo que la suma de distancias sea la menor
    posible. Devuelve los índices de «largos» elegidos, uno por cada elemento de «cortos».
    """
    n, m = len(cortos), len(largos)
    INF = float("inf")
    # costo[a][b]: lo mejor para emparejar los primeros a de «cortos» usando solo los primeros b de «largos»
    costo = [[0.0] * (m + 1)] + [[INF] * (m + 1) for _ in range(n)]
    for a in range(1, n + 1):
        for b in range(a, m + 1):
            costo[a][b] = min(costo[a][b - 1], costo[a - 1][b - 1] + abs(cortos[a - 1] - largos[b - 1]))
    elegidos, b = [], m
    for a in range(n, 0, -1):
        while costo[a][b] == costo[a][b - 1]:
            b -= 1
        elegidos.append(b - 1)
        b -= 1
    return elegidos[::-1]


def _con_pareja(menciones, tramos):
    """Qué tramos de la traducción quedan para las menciones propias cuando hay rivales.

    menciones: [(posición en el inglés, es_propia)]. tramos: [(posición en la traducción, tramo)].
    Devuelve los tramos que la alineación les da a las menciones propias.
    """
    menciones, tramos = sorted(menciones), sorted(tramos)
    pm, pt = [m[0] for m in menciones], [t[0] for t in tramos]
    if len(pm) <= len(pt):
        parejas = list(zip(range(len(pm)), _alinear(pm, pt)))
    else:
        parejas = list(zip(_alinear(pt, pm), range(len(pt))))
    return [tramos[x][1] for n, x in parejas if menciones[n][1]]


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
    apariciones, anidadas = _detectar(palabras_en, terminos)
    largo_en, largo_es = len(texto_en), len(texto_es or "")
    resultado = {}
    usadas = set()  # palabras de la traducción ya asignadas a algún término

    # Primero los términos más largos en inglés (suelen tener la traducción más larga)
    orden = sorted(range(len(apariciones)), key=lambda k: -(apariciones[k][1] - apariciones[k][0]))
    for k in orden:
        i, j, t = apariciones[k]
        encontrado = None
        por_etiqueta = _tramos_es(t, palabras_es)
        # «Revestimiento» aislado puede ser prohibido para liner, aunque la variante completa
        # «tubería de revestimiento corta» esté admitida. La excepción es por aparición y tokens:
        # no elimina otras prohibidas separadas ni formas ya reservadas para otro término.
        admitidos = [tramo for label in ("OK", "VARIANTE") for tramo in por_etiqueta[label]
                     if not usadas & tramo[4]]
        por_etiqueta["PROHIBIDO"] = [p for p in por_etiqueta["PROHIBIDO"]
                                      if not any(a[0] <= p[0] and p[1] <= a[1] and p[4] < a[4]
                                                 for a in admitidos)]
        for label in PRIORIDAD:
            # Un tramo es (a, b, forma, largo, propias): la forma ocupa palabras_es[a:b], tiene «largo» palabras y
            # «propias» son las que usa solo ella. En una coincidencia seguida son todas; en una coordinada
            # («pozo de petróleo o gas»), las del final: el principio lo comparte con la otra alternativa.
            tramos = por_etiqueta[label]
            # Solo los tramos libres; de dos que se pisan queda el más largo
            libres = []
            for tramo in sorted(tramos, key=lambda x: (-x[3], x[0])):
                if not usadas & tramo[4] and not any(tramo[4] & otro[4] for otro in libres):
                    libres.append(tramo)
            if not libres:
                continue
            # Menciones del término dentro de un término más largo que no se encontró: compiten por los tramos
            rivales = [(_centro(palabras_en, a, b, largo_en), False) for a, b, t2, n in anidadas
                       if t2.id == t.id and resultado[n].label == "NO_ENCONTRADO"]
            if rivales:
                propias = [(_centro(palabras_en, a, b, largo_en), True) for n, (a, b, t2) in enumerate(apariciones)
                           if t2.id == t.id and (n == k or n not in resultado)]
                libres = _con_pareja(propias + rivales,
                                     [(_centro(palabras_es, tramo[0], tramo[1], largo_es), tramo) for tramo in libres])
            if libres:
                # la más larga primero, después la que está más a la izquierda
                encontrado = (label, min(libres, key=lambda x: (-x[3], x[0])))
            if encontrado:
                break
        o = Ocurrencia(seg_id, system, t.id, texto_en[palabras_en[i].inicio:palabras_en[j - 1].fin], "NO_ENCONTRADO",
                       "", -1, -1, palabras_en[i].inicio, palabras_en[j - 1].fin, t.es_preferred,
                       es_allowed=tuple(t.es_allowed))
        if encontrado:
            label, (a, b, forma, _, propias) = encontrado
            usadas |= propias
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
