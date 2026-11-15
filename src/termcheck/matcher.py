"""Buscar formas del glosario dentro de un texto, palabra por palabra (plan 3.1, pasos 2 y 3).

Un texto se convierte en una lista de «palabras» (Palabra): el texto tal cual, su forma normalizada y su lema.
Una forma del glosario («tubería de producción») se convierte en otra lista igual y se busca como secuencia
seguida dentro del texto.

Dos palabras coinciden si coincide la forma o el lema. En español, como respaldo, también si solo cambian el
número o el género:
    «tuberías» ~ «tubería»   (lema)        «Perforacion» ~ «perforación»   (forma normalizada)
    «rigs» ~ «rig»           (lema)        «drilling» ~ «drilling» aunque spaCy diga «drill» (forma)
    «packers» ~ «packer»     (número)      «repararse» ≠ «reparación»      (otra palabra de la misma familia)

Una palabra escrita con guion cuenta como sus partes: «gas-lift» = «gas lift», «well-head» = «well head».

En español una forma de varias palabras también se reconoce cuando va coordinada con otra y comparten el
principio (buscar_coordinada): «pozo de petróleo o gas» vale por «pozo de gas».

Ejemplo:
    from termcheck.matcher import analizar, analizar_forma, buscar
    texto = analizar("Las tuberías de producción", "es")
    buscar(texto, analizar_forma("tubería de producción", "es"), "es")   # → [(1, 4)]  (palabras 1 a 3)
"""
import re
from dataclasses import dataclass
from functools import lru_cache

from termcheck.normalize import GUIONES, normalizar

# Un término en español es una unidad fija: «cabeza del pozo» no es «cabeza de pozo» (anotación del dueño, S118
# de desarrollo, 2026-11-11). Por eso no se igualan «de» y «del» ni se saltean artículos en el medio.
# Categorías que un sustantivo de una sola palabra no puede tener (en «as well as», «well» es ADV).
NO_SUSTANTIVO = {"ADV", "ADP", "AUX", "CCONJ", "SCONJ", "DET", "PRON", "PART", "NUM", "PUNCT", "SYM", "INTJ"}
# Los tramos de una palabra separados por guiones: «gas-lift» → «gas», «lift». Un guion suelto no deja ninguno.
_PARTES = re.compile(f"[^{re.escape(GUIONES)}]+")

# Coordinación (buscar_coordinada). Lo que une dos alternativas; la coma sola no alcanza (ver más abajo).
COORDINAN = {"o", "u", "y", "e", "ni", "/"}
MAX_ALTERNATIVA = 3   # palabras de cada alternativa: «petróleo», «de petróleo», «de agua dulce»
MAX_ALTERNATIVAS = 3  # cuántas alternativas puede haber antes del final de la forma: «petróleo, agua o gas»


@dataclass
class Palabra:
    texto: str      # tal cual en el original: «Tuberías»
    norma: str      # minúsculas y sin tildes: «tuberias»
    lema: str       # lema normalizado: «tuberia»
    pos: str        # categoría gramatical de spaCy
    inicio: int     # posición del primer carácter en el texto original
    fin: int        # posición siguiente al último carácter


# Partes de spaCy que el verificador no usa: el reconocedor de nombres propios (ner) y, en español, el analizador
# sintáctico (parser). Sin ellas analiza en la mitad del tiempo y los lemas y las categorías salen iguales
# (comprobado palabra por palabra sobre todo el corpus y el glosario). En inglés el analizador sintáctico se queda:
# la categoría de algunas palabras («after», «that») depende de él.
SIN_USAR = {"en": ["ner"], "es": ["parser", "ner"]}


@lru_cache(maxsize=None)
def modelo(idioma):
    """El modelo de spaCy del idioma ("en" o "es"). Se carga una sola vez."""
    import spacy
    return spacy.load("en_core_web_sm" if idioma == "en" else "es_core_news_sm", exclude=SIN_USAR[idioma])


def _palabras(doc):
    salida = []
    for tok in doc:
        if tok.is_space:
            continue
        partes = list(_PARTES.finditer(tok.text))
        for parte in partes:
            norma = normalizar(parte.group(0))
            if not norma:
                continue
            # El lema de spaCy es de la palabra entera. Si se partió por un guion, cada parte queda con su forma.
            lema = (normalizar(tok.lemma_) or norma) if len(partes) == 1 else norma
            salida.append(Palabra(parte.group(0), norma, lema, tok.pos_, tok.idx + parte.start(),
                                  tok.idx + parte.end()))
    return salida


def analizar(texto, idioma):
    """Texto → lista de Palabra, con spaCy en contexto (así el lema y la categoría dependen de la oración)."""
    return _palabras(modelo(idioma)(texto))


@lru_cache(maxsize=4096)
def _forma_cache(forma, idioma):
    return tuple(_palabras(modelo(idioma)(forma)))


def analizar_forma(forma, idioma):
    """Una forma del glosario, analizada aislada (se guarda en caché: el glosario se repite mucho)."""
    return list(_forma_cache(forma, idioma))


def es_sigla(forma):
    """«BOP», «ESP», «AIB»: una sola palabra, toda en mayúsculas. Se compara respetando mayúsculas."""
    return forma.isupper() and " " not in forma.strip() and len(forma.strip()) >= 2


@lru_cache(maxsize=None)
def _flexiones(norma):
    """Las formas de una palabra española sin el plural, y con el género tapado («@» en lugar de la -o o la -a).

        «tuberias» → tuberias, tuberia, tuberi@       «viajeros» → viajeros, viajero, viajer@
        «luces»    → luces, luce, luc, luz            «reparacion» → reparacion

    Dos palabras son la misma con otro número o género si comparten alguna. No se toca nada más: «reparada»
    (reparada, reparad@) y «reparacion» no comparten ninguna, así que un verbo no pasa por el sustantivo de su
    familia. Hasta la versión 0.1 esto se hacía con la raíz Snowball, que sí las igualaba.

    El género se tapa, no se quita: si se quitara, «línea» quedaría igual a la palabra inglesa «line».
    Las formas de menos de tres letras no cuentan («las» no es «la» ni «los»).
    """
    formas = {norma}
    if norma.endswith("s"):
        formas.add(norma[:-1])                      # tuberias → tuberia
        if norma.endswith("es"):
            formas.add(norma[:-2])                  # preventores → preventor
            if norma.endswith("ces"):
                formas.add(norma[:-3] + "z")        # luces → luz
    formas = {f for f in formas if len(f) >= 3}
    return frozenset(formas | {f[:-1] + "@" for f in formas if len(f) >= 4 and f[-1] in "ao"})


def _coincide(p, q, idioma):
    """¿La palabra del texto p coincide con la palabra de la forma q?"""
    if p.norma == q.norma or p.lema == q.norma or p.lema == q.lema or p.norma == q.lema:
        return True
    if idioma == "en":
        return p.norma in (q.norma + "s", q.norma + "es")  # plural simple si spaCy no lo lematizó
    # Respaldo para cuando spaCy no acierta el lema: mismo vocablo con otro número o género.
    return not _flexiones(p.norma).isdisjoint(_flexiones(q.norma))


def buscar(texto, forma, idioma, sigla=None):
    """Dónde aparece la forma (lista de Palabra) dentro del texto (lista de Palabra).

    Devuelve [(i, j)]: la coincidencia ocupa las palabras texto[i:j]. Las coincidencias no se pisan entre sí.
    sigla: el texto de la sigla si hay que respetar mayúsculas («BOP» sí, «bop» no; «BOPs» sí).
    """
    if not forma:
        return []
    salida, i = [], 0
    while i < len(texto):
        j = _intentar(texto, forma, i, idioma, sigla)
        if j:
            salida.append((i, j))
            i = j
        else:
            i += 1
    return salida


def _intentar(texto, forma, i, idioma, sigla):
    """Si la forma empieza en texto[i], devuelve dónde termina; si no, None."""
    k = i
    for q in forma:
        if k >= len(texto):
            return None
        p = texto[k]
        if sigla:
            if not re.fullmatch(re.escape(sigla) + r"s?", p.texto):
                return None
        elif not _coincide(p, q, idioma):
            return None
        k += 1
    return k


def _une(p):
    """True si la palabra une dos alternativas: una conjunción, la barra o la coma."""
    return p.norma in COORDINAN or p.texto == ","


def _es_palabra(p):
    return not _une(p) and any(c.isalnum() for c in p.texto)


def buscar_coordinada(texto, forma):
    """Dónde aparece una forma española de varias palabras cuando va coordinada con otra y comparten el principio.

        «pozo de petróleo o gas»              vale por «pozo de gas»            (principio «pozo de», final «gas»)
        «pozo de petróleo o de gas»           vale por «pozo de gas»            (principio «pozo», final «de gas»)
        «casing intermedio y de producción»   vale por «casing de producción»

    La forma se parte en un principio y un final. Entre los dos tiene que haber una o más alternativas, cada una
    de hasta MAX_ALTERNATIVA palabras y seguida de una conjunción, una barra o una coma. Si lo único que las une
    son comas, después del final tiene que venir una conjunción («petróleo, gas y agua»): una coma sola no alcanza
    para decir que es una enumeración. Cualquier otro signo en el medio corta la búsqueda.

    Devuelve [(i, j, propias)]: la coincidencia va de texto[i] a texto[j - 1] y «propias» son los índices de las
    palabras del final, las únicas que son solo de esta forma (el principio lo comparte con la otra alternativa).
    No mira la coordinación del otro lado («lodo o fluido de perforación» por «lodo de perforación»).
    """
    salida = []
    for corte in range(1, len(forma)):
        principio, final = forma[:corte], forma[corte:]
        for i in range(len(texto)):
            k = _intentar(texto, principio, i, "es", None)
            if not k:
                continue
            hay_conjuncion = False
            for _ in range(MAX_ALTERNATIVAS):
                # una alternativa: palabras hasta lo que la une con lo que sigue
                n = k
                while n < len(texto) and _es_palabra(texto[n]):
                    n += 1
                if n == k or n - k > MAX_ALTERNATIVA or n >= len(texto) or not _une(texto[n]):
                    break
                while n < len(texto) and _une(texto[n]):
                    hay_conjuncion = hay_conjuncion or texto[n].texto != ","
                    n += 1
                k = n
                j = _intentar(texto, final, k, "es", None)
                if j and (hay_conjuncion or (j < len(texto) and texto[j].norma in COORDINAN)):
                    salida.append((i, j, tuple(range(k, j))))
                    break
    # La misma coincidencia puede salir con dos cortes; queda una sola (la de final más largo)
    unicas = {}
    for i, j, propias in salida:
        if (i, j) not in unicas or len(propias) > len(unicas[(i, j)]):
            unicas[(i, j)] = propias
    return [(i, j, propias) for (i, j), propias in sorted(unicas.items())]


def pos_aceptable(pos_glosario, palabras):
    """Filtro gramatical (plan 3.3, caso 3). Solo para términos de una palabra: en los de varias, la secuencia ya
    alcanza (y spaCy a veces etiqueta mal: «manifold» como adjetivo, «well» de «well-head» como adjetivo).

    Un sustantivo no puede ser adverbio, preposición, etc. Tampoco verbo, salvo en -ing: spaCy etiqueta como verbo
    muchos sustantivos en -ing de esta área («casing», «tubing»).
    """
    if len(palabras) != 1 or pos_glosario not in ("NOUN", "PROPN"):
        return True
    p = palabras[0]
    if p.pos in NO_SUSTANTIVO:
        return False
    if p.pos == "VERB" and not p.norma.endswith("ing"):
        return False
    return True
