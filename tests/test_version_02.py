"""Los tres arreglos de la versión 0.2 del verificador, con oraciones inventadas y un glosario mínimo propio.

1. Guion: «gas-lift» y «gas lift» son la misma forma.
2. Coordinación: «pozo de petróleo o gas» vale por «pozo de gas».
3. Familia de palabras: «repararse» no es «reparación». El respaldo solo iguala número y género.

Los tres salieron de leer los errores de la evaluación final (docs/findings.md). Ninguna prueba usa oraciones del
corpus.

Correr:  .venv/bin/python -m pytest tests/test_version_02.py -v
"""
import pytest

from termcheck.checker import verificar
from termcheck.glossary import Termino
from termcheck.matcher import _flexiones, analizar, analizar_forma, buscar, buscar_coordinada


def T(id, en, preferida, validas="", prohibidas=""):
    sep = lambda s: [x for x in s.split("|") if x]  # noqa: E731
    return Termino(id=id, en=sep(en), pos="NOUN", es_preferred=preferida, es_allowed=sep(validas),
                   es_forbidden=sep(prohibidas))


GAS_LIFT = T("V01", "gas lift", "gas lift", "levantamiento artificial por gas")
SCREEN_OUT = T("V02", "screen-out|screenout", "arenamiento", "screen-out")
OIL_WELL = T("V03", "oil well", "pozo de petróleo")
GAS_WELL = T("V04", "gas well", "pozo de gas")
OIL = T("V05", "oil", "petróleo")
WORKOVER = T("V06", "workover", "workover", "reparación")
CASING_INT = T("V07", "intermediate casing", "casing intermedio")
CASING_PROD = T("V08", "production casing", "casing de producción")
PACKER = T("V09", "packer", "packer", "empacador")
RIG = T("V10", "drilling rig|rig", "equipo de perforación", "equipo", "plataforma de perforación")
TRAVELING = T("V11", "traveling block", "bloque viajero")
WELL = T("V12", "well", "pozo")


def etiquetas(en, es, glosario):
    return [(o.term_id, o.label) for o in verificar(en, es, glosario)]


# ───────── 1. Guion ─────────

def test_guion_en_la_traduccion():
    es = "Instale el sistema de gas-lift."
    [o] = verificar("Install the gas lift system.", es, [GAS_LIFT])
    assert (o.label, o.es_found) == ("OK", "gas-lift")
    assert es[o.start:o.end] == "gas-lift"


def test_guion_en_el_glosario_y_no_en_la_traduccion():
    assert etiquetas("A screen-out occurred.", "Quedó como screen out.", [SCREEN_OUT]) == [("V02", "VARIANTE")]
    assert etiquetas("A screen-out occurred.", "Quedó como screen-out.", [SCREEN_OUT]) == [("V02", "VARIANTE")]


@pytest.mark.parametrize("texto", ["gas-lift", "gas–lift", "Gas-Lift"])
def test_una_palabra_con_guion_son_sus_partes(texto):
    palabras = analizar(f"El {texto} funciona.", "es")
    assert [p.norma for p in palabras][1:3] == ["gas", "lift"]
    assert buscar(palabras, analizar_forma("gas lift", "es"), "es") == [(1, 3)]


def test_un_guion_suelto_no_es_una_palabra():
    assert [p.texto for p in analizar("pozo - gas", "es")] == ["pozo", "gas"]


# ───────── 2. Coordinación ─────────

@pytest.mark.parametrize("es, encontrada", [
    ("Un pozo de petróleo o gas produce fluidos.", "pozo de petróleo o gas"),
    ("Un pozo de petróleo o de gas produce fluidos.", "pozo de petróleo o de gas"),
    ("Un pozo de petróleo/gas produce fluidos.", "pozo de petróleo/gas"),
    ("Un pozo de petróleo y/o gas produce fluidos.", "pozo de petróleo y/o gas"),
    ("Los pozos de petróleo y gas producen fluidos.", "pozos de petróleo y gas"),
    ("Los pozos de petróleo, gas y agua producen fluidos.", "pozos de petróleo, gas"),
    ("Los pozos de agua, petróleo o gas producen fluidos.", "pozos de agua, petróleo o gas"),
])
def test_forma_coordinada(es, encontrada):
    [o] = verificar("An oil or gas well produces fluids.", es, [GAS_WELL])
    assert (o.label, o.es_found) == ("OK", encontrada)
    assert es[o.start:o.end] == encontrada


@pytest.mark.parametrize("es", [
    "Un pozo de petróleo. El gas se ventea.",           # otro signo en el medio
    "El pozo produce petróleo y gas.",                  # «pozo … gas» sin «de»
    "Un pozo de petróleo, gas natural licuado.",        # solo una coma: no se sabe si es una enumeración
    "El pozo de petróleo que se perforó ayer o gas.",   # la alternativa es demasiado larga
    "Un pozo y gas.",                                   # no hay alternativa
])
def test_no_es_una_forma_coordinada(es):
    assert etiquetas("An oil or gas well produces fluids.", es, [GAS_WELL]) == [("V04", "NO_ENCONTRADO")]


def test_la_coordinada_puede_ser_prohibida():
    assert etiquetas("Move the drilling rig.", "Mueva la plataforma de producción o perforación.", [RIG]) == [
        ("V10", "PROHIBIDO")]


def test_dos_terminos_comparten_el_principio():
    # «casing intermedio y de producción»: los dos términos están, y el segundo comparte «casing» con el primero
    en = "Run the intermediate casing and the production casing."
    assert etiquetas(en, "Baje el casing intermedio y de producción.", [CASING_INT, CASING_PROD]) == [
        ("V07", "OK"), ("V08", "OK")]
    en = "Oil wells and gas wells are inspected."
    assert etiquetas(en, "Se inspeccionan los pozos de petróleo y gas.", [OIL_WELL, GAS_WELL]) == [
        ("V03", "OK"), ("V04", "OK")]
    # Si falta la segunda, se marca
    assert etiquetas(en, "Se inspeccionan los pozos de petróleo.", [OIL_WELL, GAS_WELL]) == [
        ("V03", "OK"), ("V04", "NO_ENCONTRADO")]


def test_la_otra_alternativa_queda_libre():
    # «petróleo» está en el medio de «pozo de petróleo o gas» y sigue valiendo como traducción de «oil»
    oc = verificar("Oil flows from an oil or gas well.", "Sale petróleo de un pozo de agua o gas, y petróleo.",
                   [OIL, GAS_WELL])
    assert [(o.term_id, o.label) for o in oc] == [("V05", "OK"), ("V05", "OK"), ("V04", "OK")]


def test_el_final_coordinado_no_vale_dos_veces():
    # «gas» ya lo usó «gas well»: no queda para otro término que también lo necesite
    gas = T("V13", "gas", "gas")
    oc = verificar("The gas well vents gas.", "El pozo de petróleo o gas ventea.", [GAS_WELL, gas])
    assert [(o.term_id, o.label) for o in oc] == [("V04", "OK"), ("V13", "NO_ENCONTRADO")]


def test_buscar_coordinada_devuelve_el_tramo_y_el_final():
    texto = analizar("Un pozo de petróleo o gas.", "es")
    assert buscar_coordinada(texto, analizar_forma("pozo de gas", "es")) == [(1, 6, (5,))]
    assert buscar_coordinada(texto, analizar_forma("pozo", "es")) == []          # una sola palabra: no hay qué partir
    assert buscar_coordinada(texto, analizar_forma("pozo de agua", "es")) == []
    texto = analizar("Un pozo de petróleo o de gas.", "es")
    assert buscar_coordinada(texto, analizar_forma("pozo de gas", "es")) == [(1, 7, (5, 6))]


def test_seguida_y_coordinada_en_la_misma_oracion():
    # Con una forma seguida más a la izquierda no hace falta la coordinada: se toma la primera
    oc = verificar("A gas well and an oil or gas well.", "Un pozo de gas y un pozo de petróleo o gas.", [GAS_WELL])
    assert [(o.label, o.es_found) for o in oc] == [("OK", "pozo de gas"), ("OK", "pozo de petróleo o gas")]


# ───────── 3. Familia de palabras ─────────

@pytest.mark.parametrize("es", [
    "El pozo necesita una intervención porque no puede repararse.",
    "El pozo necesita una intervención porque no puede ser reparado.",
    "La bomba fue reparada antes de la intervención.",
    "Hay que reparar el pozo.",
])
def test_un_verbo_no_vale_por_el_sustantivo(es):
    assert etiquetas("The well needs a workover.", es, [WORKOVER]) == [("V06", "NO_ENCONTRADO")]


@pytest.mark.parametrize("es, etiqueta", [
    ("El pozo necesita una reparación.", "VARIANTE"),
    ("El pozo necesita dos reparaciones.", "VARIANTE"),
    ("El pozo necesita un workover.", "OK"),
    ("El pozo necesita dos workovers.", "OK"),
])
def test_el_plural_sigue_valiendo(es, etiqueta):
    assert etiquetas("The well needs a workover.", es, [WORKOVER]) == [("V06", etiqueta)]


def test_plural_de_un_prestamo():
    assert etiquetas("Set the packers.", "Fije los packers.", [PACKER]) == [("V09", "OK")]
    assert etiquetas("Set the packers.", "Fije los empacadores.", [PACKER]) == [("V09", "VARIANTE")]


def test_numero_y_genero():
    assert etiquetas("Check the traveling blocks.", "Revise los bloques viajeros.", [TRAVELING]) == [("V11", "OK")]
    assert etiquetas("Move the rigs.", "Mueva los equipos de perforación.", [RIG]) == [("V10", "OK")]


@pytest.mark.parametrize("a, b, iguales", [
    ("tuberias", "tuberia", True), ("viajeros", "viajera", True), ("preventores", "preventor", True),
    ("luces", "luz", True), ("gases", "gas", True), ("bases", "base", True), ("packers", "packer", True),
    ("ciegas", "ciego", True), ("intermedia", "intermedio", True),
    ("repararse", "reparacion", False), ("reparada", "reparacion", False), ("perforar", "perforacion", False),
    ("perforado", "perforador", False), ("terminado", "terminacion", False), ("de", "del", False),
    ("estrangulacion", "estrangulador", False), ("ahogo", "ahogar", False), ("cementarse", "cementacion", False),
    # Ni con otra palabra que se le parece, ni con una palabra inglesa
    ("perforadora", "perforador", False), ("liner", "line", False), ("linea", "line", False),
    ("casos", "cased", False), ("tabla", "table", False), ("las", "los", False), ("una", "uno", False),
])
def test_flexiones(a, b, iguales):
    assert (not _flexiones(a).isdisjoint(_flexiones(b))) is iguales


def test_palabras_cortas_no_se_igualan_por_flexion():
    # «as» y «a», «os» y «o»: con menos de tres letras solo vale la forma exacta
    assert _flexiones("as") == frozenset() and _flexiones("la") == frozenset()
    assert _flexiones("las") == {"las"} and _flexiones("gas") == {"gas"}


def test_well_sigue_sin_valer_dos_veces():
    # Nada de lo anterior cambia la regla de siempre
    assert etiquetas("The well.", "El pozo.", [WELL]) == [("V12", "OK")]
