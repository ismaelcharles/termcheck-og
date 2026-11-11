"""Normalizar texto para comparar formas: «Lodo de Perforacion» y «lodo de perforación» tienen que ser iguales.

Solo sirve para comparar. Lo que se muestra al usuario es siempre el texto original.
"""
import re
import unicodedata

# Guiones de distintos tipos que aparecen en textos copiados de PDF o Word
GUIONES = "-‐‑‒–—"


def sin_tildes(texto):
    """«perforación» → «perforacion». También «ñ» → «n»: para comparar alcanza.

    Antes pasa por NFKC, que convierte los subíndices y similares: «H₂S» → «H2S».
    """
    descompuesto = unicodedata.normalize("NFD", unicodedata.normalize("NFKC", texto))
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def normalizar(texto):
    """Minúsculas, sin tildes, guiones como espacio y un solo espacio entre palabras.

    «Well-Head » → «well head»   ·   «Lodo de  Perforación» → «lodo de perforacion»
    """
    texto = sin_tildes(str(texto).lower())
    for guion in GUIONES:
        texto = texto.replace(guion, " ")
    return re.sub(r"\s+", " ", texto).strip()
