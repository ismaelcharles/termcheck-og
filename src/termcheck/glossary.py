"""Cargar y validar el glosario (data/glossary/glossary_en_es.csv).

    from termcheck.glossary import cargar, validar
    terminos = cargar("data/glossary/glossary_en_es.csv")
    problemas = validar(terminos)

Desde la terminal, para revisar el glosario:

    python -m termcheck.glossary data/glossary/glossary_en_es.csv

Cada fila del CSV es un concepto. Las columnas con variantes (en, es_allowed, es_forbidden) separan las formas con «|».
"""
import csv
import io
import sys
from dataclasses import dataclass, field
from pathlib import Path

from termcheck.normalize import normalizar

COLUMNAS = ["id", "en", "pos", "es_preferred", "es_allowed", "es_forbidden", "subdomain", "note", "source"]
# Categorías gramaticales que entiende spaCy y que usa el glosario
CATEGORIAS = {"NOUN", "VERB", "ADJ", "ADV", "PROPN"}


class ErrorDeGlosario(Exception):
    """El archivo no se puede usar: no existe o le faltan columnas."""


@dataclass
class Termino:
    """Un concepto del glosario, con las variantes ya separadas en listas."""
    id: str
    en: list                      # formas en inglés: ["blowout preventer", "BOP"]
    pos: str                      # categoría gramatical: "NOUN"
    es_preferred: str             # la traducción preferida
    es_allowed: list = field(default_factory=list)    # otras traducciones que valen
    es_forbidden: list = field(default_factory=list)  # traducciones que son error
    subdomain: str = ""
    note: str = ""
    source: str = ""


@dataclass
class Problema:
    """Algo que está mal o que conviene mirar en una fila."""
    id: str        # el id del término (o la fila, si no tiene id)
    tipo: str      # "error" (hay que arreglarlo) o "aviso" (conviene mirarlo)
    mensaje: str

    def __str__(self):
        return f"[{self.tipo}] {self.id}: {self.mensaje}"


def separar(texto):
    """«wellhead | well-head |» → ["wellhead", "well-head"]. Sin espacios sobrantes ni partes vacías."""
    return [parte.strip() for parte in str(texto).split("|") if parte.strip()]


def cargar(ruta):
    """Lee el CSV y devuelve la lista de términos, en el orden del archivo.

    Acepta el archivo con o sin BOM (Excel lo agrega al guardar en UTF-8). Si falta alguna columna, avisa cuál.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise ErrorDeGlosario(f"No existe el archivo {ruta}")
    return cargar_bytes(ruta.read_bytes())


def publicado(carpeta):
    """Última edición publicada; el glosario histórico de evaluación permanece disponible."""
    carpeta = Path(carpeta)
    for nombre in ("glossary_v1_3.csv", "glossary_v1_1.csv", "glossary_v1.csv", "glossary_en_es.csv"):
        ruta = carpeta / nombre
        if ruta.exists():
            return ruta
    raise ErrorDeGlosario("No hay un glosario publicado en esta carpeta.")


def cargar_bytes(datos):
    """Lo mismo que cargar(), con el contenido del archivo ya leído (por ejemplo, un glosario subido desde la app).

    Las columnas pueden venir separadas por coma, por punto y coma (así guarda Excel en castellano) o por tabulación.
    """
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ErrorDeGlosario("El archivo no está en UTF-8. En Excel: Guardar como → «CSV UTF-8 (delimitado por "
                              "comas)».")
    encabezado = texto.split("\n", 1)[0]
    separador = max(",;\t", key=encabezado.count)  # el que más aparece en la primera línea; si empatan, la coma
    try:
        lector = csv.DictReader(io.StringIO(texto, newline=""), delimiter=separador, strict=True)
        nombres = [(n or "").strip() for n in (lector.fieldnames or [])]
        lector.fieldnames = nombres
        filas = list(lector)
    except csv.Error as e:
        raise ErrorDeGlosario("No se pudo leer el CSV: revisá las comillas y el separador de columnas.") from e
    faltan = [c for c in COLUMNAS if c not in nombres]
    if faltan:
        raise ErrorDeGlosario(f"Al archivo le faltan columnas: {', '.join(faltan)}")
    if len(nombres) != len(set(nombres)):
        raise ErrorDeGlosario("El CSV tiene nombres de columna repetidos.")
    terminos = []
    for numero, fila in enumerate(filas, start=2):  # la fila 1 es el encabezado
        if None in fila:
            raise ErrorDeGlosario(f"La fila {numero} del CSV tiene más campos que el encabezado.")
        fila = {c: (fila.get(c) or "").strip() for c in COLUMNAS}
        if not any(fila.values()):
            continue  # fila vacía al final del archivo
        terminos.append(Termino(
            id=fila["id"] or f"fila {numero}",
            en=separar(fila["en"]),
            pos=fila["pos"],
            es_preferred=fila["es_preferred"],
            es_allowed=separar(fila["es_allowed"]),
            es_forbidden=separar(fila["es_forbidden"]),
            subdomain=fila["subdomain"],
            note=fila["note"],
            source=fila["source"],
        ))
    return terminos


def validar(terminos):
    """Revisa el glosario y devuelve la lista de problemas. Lista vacía = todo bien.

    Errores (el verificador daría resultados equivocados):
    - id repetido;
    - sin término en inglés, sin traducción preferida o con una categoría que no existe;
    - la misma forma en dos papeles dentro de un término (por ejemplo, válida y prohibida a la vez);
    - la misma forma en inglés en dos términos: el verificador no sabría a cuál corresponde.
    Avisos (conviene mirarlos):
    - sin fuente;
    - una forma en inglés repetida dentro del mismo término («screen-out» y «screen out» se buscan igual).
    """
    problemas = []
    vistos = set()
    duenio_en = {}  # forma en inglés normalizada → id del término que la tiene

    for t in terminos:
        def error(mensaje):
            problemas.append(Problema(t.id, "error", mensaje))

        if t.id in vistos:
            error("el id está repetido")
        vistos.add(t.id)

        if not t.en:
            error("falta el término en inglés")
        if not t.es_preferred:
            error("falta la traducción preferida")
        if t.pos not in CATEGORIAS:
            error(f"la categoría «{t.pos}» no existe (tiene que ser una de: {', '.join(sorted(CATEGORIAS))})")
        if not t.source:
            problemas.append(Problema(t.id, "aviso", "no tiene fuente"))

        # Cada forma en español puede tener un solo papel dentro del término
        papeles = {}
        for papel, formas in (("preferida", [t.es_preferred] if t.es_preferred else []),
                              ("válida", t.es_allowed), ("prohibida", t.es_forbidden)):
            for forma in formas:
                clave = normalizar(forma)
                if clave in papeles:
                    error(f"«{forma}» figura como {papeles[clave]} y como {papel}")
                else:
                    papeles[clave] = papel

        # Cada forma en inglés pertenece a un solo término
        for forma in t.en:
            clave = normalizar(forma)
            if clave in duenio_en and duenio_en[clave] != t.id:
                error(f"la forma en inglés «{forma}» ya está en {duenio_en[clave]}")
            elif clave in duenio_en:  # dentro del mismo término no rompe nada, pero sobra
                problemas.append(Problema(t.id, "aviso", f"la forma en inglés «{forma}» está repetida (con guion o "
                                                         "sin guion se busca igual)"))
            else:
                duenio_en[clave] = t.id
    return problemas


def main(ruta):
    try:
        terminos = cargar(ruta)
    except ErrorDeGlosario as e:
        print(f"No se pudo leer el glosario: {e}")
        return 2
    problemas = validar(terminos)
    errores = [p for p in problemas if p.tipo == "error"]
    print(f"{len(terminos)} términos · {len(errores)} errores · {len(problemas) - len(errores)} avisos")
    for p in problemas:
        print(f"  {p}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "data/glossary/glossary_en_es.csv"))
