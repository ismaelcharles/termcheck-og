"""Buscar formas del glosario dentro de un texto, palabra por palabra (plan 3.1, pasos 2 y 3).

Un texto se convierte en una lista de «palabras» (Palabra): el texto tal cual, su forma normalizada, su lema y,
en español, su raíz. Una forma del glosario («tubería de producción») se convierte en otra lista igual y se busca
como secuencia seguida dentro del texto.

Dos palabras coinciden si coincide la forma, el lema o (solo en español) la raíz Snowball:
    «tuberías» ~ «tubería»   (lema)        «Perforacion» ~ «perforación»   (forma normalizada)
    «rigs» ~ «rig»           (lema)        «drilling» ~ «drilling» aunque spaCy diga «drill» (forma)

Ejemplo:
    from termcheck.matcher import analizar, buscar
    texto = analizar("Las tuberías de producción", "es")
    buscar(texto, analizar_forma("tubería de producción", "es"))   # → [(1, 4)]  (palabras 1 a 3)
"""
import re
from dataclasses import dataclass
from functools import lru_cache

from termcheck.normalize import normalizar

# Guiones sueltos («well-head» → well, -, head): no cuentan como palabra; así «well-head» = «well head».
GUIONES = set("-‐‑‒–—")
# Un término en español es una unidad fija: «cabeza del pozo» no es «cabeza de pozo» (anotación del dueño, S118
# de desarrollo, 2026-11-11). Por eso no se igualan «de» y «del» ni se saltean artículos en el medio.
# Categorías que un sustantivo de una sola palabra no puede tener (en «as well as», «well» es ADV).
NO_SUSTANTIVO = {"ADV", "ADP", "AUX", "CCONJ", "SCONJ", "DET", "PRON", "PART", "NUM", "PUNCT", "SYM", "INTJ"}


@dataclass
class Palabra:
    texto: str      # tal cual en el original: «Tuberías»
    norma: str      # minúsculas y sin tildes: «tuberias»
    lema: str       # lema normalizado: «tuberia»
    raiz: str       # raíz Snowball (solo español; en inglés queda igual a norma)
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


@lru_cache(maxsize=None)
def _stemmer():
    from nltk.stem.snowball import SnowballStemmer
    return SnowballStemmer("spanish")


def _palabras(doc, idioma):
    salida = []
    for tok in doc:
        if tok.is_space or tok.text in GUIONES:
            continue
        norma = normalizar(tok.text)
        if not norma:
            continue
        lema = normalizar(tok.lemma_) or norma
        if idioma == "es":
            raiz = _stemmer().stem(norma)
        else:
            raiz = norma
        salida.append(Palabra(tok.text, norma, lema, raiz, tok.pos_, tok.idx, tok.idx + len(tok.text)))
    return salida


def analizar(texto, idioma):
    """Texto → lista de Palabra, con spaCy en contexto (así el lema y la categoría dependen de la oración)."""
    return _palabras(modelo(idioma)(texto), idioma)


@lru_cache(maxsize=4096)
def _forma_cache(forma, idioma):
    return tuple(_palabras(modelo(idioma)(forma), idioma))


def analizar_forma(forma, idioma):
    """Una forma del glosario, analizada aislada (se guarda en caché: el glosario se repite mucho)."""
    return list(_forma_cache(forma, idioma))


def es_sigla(forma):
    """«BOP», «ESP», «AIB»: una sola palabra, toda en mayúsculas. Se compara respetando mayúsculas."""
    return forma.isupper() and " " not in forma.strip() and len(forma.strip()) >= 2


def _coincide(p, q, idioma):
    """¿La palabra del texto p coincide con la palabra de la forma q?"""
    if p.norma == q.norma or p.lema == q.norma or p.lema == q.lema or p.norma == q.lema:
        return True
    if idioma == "en":
        return p.norma in (q.norma + "s", q.norma + "es")  # plural simple si spaCy no lo lematizó
    # Raíz: solo como respaldo para flexión de género y número («tuberías» ~ «tubería»). Con más de 2 letras de
    # diferencia ya es otra palabra de la misma familia («perforar» ≠ «perforación», las dos dan «perfor»).
    return p.raiz == q.raiz and len(q.raiz) >= 3 and abs(len(p.norma) - len(q.norma)) <= 2


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
