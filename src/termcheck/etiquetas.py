"""Las etiquetas del verificador, definidas una sola vez.

El verificador le pone una etiqueta a cada aparición de un término (checker.py). Acá está, para cada una, el código
que sale en el CSV, el nombre con que se muestra a quien lee el reporte, qué significa y si hay que revisarla.
Lo usan el verificador, el reporte, los scripts y la app: lo que cambia acá cambia en todos lados.

    from termcheck.etiquetas import ETIQUETAS
    ETIQUETAS["PROHIBIDO"].nombre      # «Prohibida»
    ETIQUETAS["PROHIBIDO"].se_marca    # True
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Etiqueta:
    codigo: str        # como sale en el CSV: «PROHIBIDO»
    nombre: str        # como se muestra: «Prohibida»
    plural: str        # para contar: «2 prohibidas»
    significado: str   # una oración, para la tabla de etiquetas
    nivel: str         # «error», «aviso» o «bien»: decide el color en el reporte
    se_marca: bool     # True si hay que revisarla (en la evaluación cuenta como «marcada»)

    def contar(self, n):
        """«1 prohibida», «3 prohibidas»."""
        return f"{n} {self.nombre.lower() if n == 1 else self.plural}"


# En el orden en que se muestran: primero lo que hay que revisar.
ETIQUETAS = {e.codigo: e for e in [
    Etiqueta("PROHIBIDO", "Prohibida", "prohibidas", "Aparece una forma que el glosario da por incorrecta.",
             "error", True),
    Etiqueta("SIN_TRADUCIR", "Sin traducir", "sin traducir",
             "El término quedó en inglés y el glosario no lo acepta como préstamo.", "aviso", True),
    Etiqueta("NO_ENCONTRADO", "No encontrada", "no encontradas",
             "El término está en el inglés y ninguna forma conocida aparece en la traducción.", "aviso", True),
    Etiqueta("VARIANTE", "Variante aceptada", "variantes aceptadas",
             "Aparece una forma válida que no es la preferida.", "bien", False),
    Etiqueta("OK", "Preferida", "preferidas", "Aparece la traducción preferida.", "bien", False),
]}

# No es la etiqueta de una aparición: es una advertencia sobre el documento entero (consistency.py).
INCONSISTENTE = Etiqueta("INCONSISTENTE", "Inconsistente", "inconsistentes",
                         "En el mismo documento, el término se tradujo de más de una manera.", "aviso", False)

# Lo que se marca para revisar
MARCAN = frozenset(c for c, e in ETIQUETAS.items() if e.se_marca)
NOMBRES = {**{c: e.nombre for c, e in ETIQUETAS.items()}, INCONSISTENTE.codigo: INCONSISTENTE.nombre}


def orden(codigo):
    """Para ordenar apariciones: primero lo que hay que revisar (prohibida, sin traducir, no encontrada)."""
    return list(ETIQUETAS).index(codigo)
