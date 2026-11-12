"""Los 10 casos difíciles del plan (3.3), con un glosario mínimo de prueba propio (no el real).

Correr:  .venv/bin/python -m pytest tests/test_hard_cases.py -v
"""
import pytest

from termcheck.checker import verificar
from termcheck.consistency import inconsistencias
from termcheck.glossary import Termino


def T(id, en, preferida, validas="", prohibidas=""):
    sep = lambda s: [x for x in s.split("|") if x]  # noqa: E731
    return Termino(id=id, en=sep(en), pos="NOUN", es_preferred=preferida, es_allowed=sep(validas),
                   es_forbidden=sep(prohibidas))


GLOSARIO = [
    T("G01", "production tubing", "tubería de producción", "tubing"),
    T("G02", "drilling mud|mud", "lodo de perforación", "fluido de perforación|lodo"),
    T("G03", "well", "pozo"),
    T("G04", "drill pipe", "tubería de perforación", "barra de sondeo"),
    T("G05", "pipe", "caño", "tubería"),
    T("G06", "casing", "casing", "cañería de entubación"),
    T("G07", "drilling rig|rig", "equipo de perforación", "equipo", "plataforma de perforación"),
    T("G08", "blowout preventer|BOP", "preventor de reventones", "BOP"),
    T("G09", "wellhead|well-head|well head", "boca de pozo", "cabeza de pozo"),
    T("G10", "choke manifold", "manifold de estranguladores", "manifold"),
]


def etiquetas(en, es):
    return [(o.term_id, o.label) for o in verificar(en, es, GLOSARIO)]


def test_1_plural_y_genero():
    oc = verificar("Pull the production tubing.", "Saque las tuberías de producción.", GLOSARIO)
    assert [(o.term_id, o.label, o.es_found) for o in oc] == [("G01", "OK", "tuberías de producción")]


def test_2_tildes_y_mayusculas():
    assert etiquetas("Check the drilling mud.", "Revise el Lodo de Perforacion.") == [("G02", "OK")]


def test_3_as_well_as_no_es_pozo():
    ids = [t for t, _ in etiquetas("Check the BOP as well as the choke manifold.",
                                   "Revise el BOP y el manifold de estranguladores.")]
    assert "G03" not in ids
    assert ids == ["G08", "G10"]


def test_3b_well_sustantivo_si():
    assert etiquetas("Shut in the well.", "Cierre el pozo.") == [("G03", "OK")]


def test_4_superposicion_gana_el_largo():
    assert etiquetas("Inspect the drill pipe.", "Inspeccione la tubería de perforación.") == [("G04", "OK")]


def test_5_prestamo_aceptado():
    assert etiquetas("Run the casing.", "Se bajó el casing.") == [("G06", "OK")]
    assert etiquetas("Pull the production tubing.", "Saque el tubing.") == [("G01", "VARIANTE")]


def test_6_prohibido():
    assert etiquetas("Move the drilling rig.", "Mueva la plataforma de perforación.") == [("G07", "PROHIBIDO")]


def test_7_repeticion_dos_filas():
    oc = verificar("The rig and the rig crew.", "El equipo de perforación y la cuadrilla del equipo.", GLOSARIO)
    assert [(o.term_id, o.label) for o in oc] == [("G07", "OK"), ("G07", "VARIANTE")]


def test_8_inconsistencia_entre_segmentos():
    oc = verificar("Mix the drilling mud.", "Mezcle el lodo de perforación.", GLOSARIO, "S3", "x")
    oc += verificar("Pump the drilling mud.", "Bombee el fluido de perforación.", GLOSARIO, "S7", "x")
    adv = inconsistencias(oc)
    assert len(adv) == 1 and adv[0].term_id == "G02"
    assert sorted(s for segs in adv[0].formas.values() for s in segs) == ["S3", "S7"]


def test_8b_plural_no_es_inconsistencia():
    oc = verificar("Pull the production tubing.", "Saque la tubería de producción.", GLOSARIO, "S1", "x")
    oc += verificar("Pull the production tubing.", "Saque las tuberías de producción.", GLOSARIO, "S2", "x")
    assert inconsistencias(oc) == []


def test_9_siglas():
    assert etiquetas("Test the BOP.", "Pruebe el preventor de reventones.") == [("G08", "OK")]
    assert etiquetas("Test the BOPs.", "Pruebe los BOP.") == [("G08", "VARIANTE")]
    # «bop» en minúscula no es la sigla, y nunca dentro de otra palabra
    assert etiquetas("The bop sound and the bopper.", "El sonido.") == []


@pytest.mark.parametrize("forma", ["wellhead", "well-head", "well head", "Well-Head"])
def test_10_variantes_de_escritura(forma):
    assert etiquetas(f"Inspect the {forma}.", "Inspeccione la boca de pozo.") == [("G09", "OK")]


def test_sin_traducir_y_no_encontrado():
    assert etiquetas("Inspect the drill pipe.", "Inspeccione el drill pipe.") == [("G04", "SIN_TRADUCIR")]
    oc = verificar("Inspect the drill pipe.", "Inspeccione la tubería de perforar.", GLOSARIO)
    assert [o.label for o in oc] == ["NO_ENCONTRADO"]
    assert oc[0].suggestion  # rapidfuzz sugiere algo parecido, sin cambiar la etiqueta


def test_una_palabra_de_la_traduccion_no_vale_dos_veces():
    # «pozo» dentro de «boca de pozo» ya lo usó wellhead: well queda sin traducción encontrada
    oc = verificar("The wellhead of the well.", "La boca de pozo.", GLOSARIO)
    assert [(o.term_id, o.label) for o in oc] == [("G09", "OK"), ("G03", "NO_ENCONTRADO")]


def test_del_no_es_de():
    # Decisión del dueño (S118 de desarrollo): «cabeza del pozo» es error para wellhead; el término es fijo
    assert etiquetas("Inspect the wellhead.", "Inspeccione la boca del pozo.") == [("G09", "NO_ENCONTRADO")]


def test_mencion_dentro_de_un_termino_largo_no_encontrado():
    # «pipe» aparece dos veces en el inglés: suelto y dentro de «drill pipe». Si «drill pipe» no se encontró, la
    # «tubería» que está en su lugar es de él y no vale como traducción del «pipe» suelto.
    en = "Check the drill pipe and then inspect the pipe."
    oc = verificar(en, "Revise la tubería de sondeo y después inspeccione la tubería.", GLOSARIO)
    assert [(o.term_id, o.label) for o in oc] == [("G04", "NO_ENCONTRADO"), ("G05", "VARIANTE")]
    assert oc[1].start > 40  # tomó la segunda «tubería», la que está en el lugar del «pipe» suelto
    oc = verificar(en, "Revise la tubería de sondeo y después inspecciónela.", GLOSARIO)
    assert [(o.term_id, o.label) for o in oc] == [("G04", "NO_ENCONTRADO"), ("G05", "NO_ENCONTRADO")]
    # Una sola «tubería», en el lugar del «pipe» suelto: es de él
    oc = verificar(en, "Revise las barras y después inspeccione la tubería.", GLOSARIO)
    assert [(o.term_id, o.label) for o in oc] == [("G04", "NO_ENCONTRADO"), ("G05", "VARIANTE")]


def test_sin_menciones_anidadas_gana_la_forma_mas_larga_y_la_primera():
    # Sin términos largos sin encontrar, se mantiene la regla de siempre
    oc = verificar("Inspect the mast before raising the mast.", "Inspeccione el caño antes de izarlo.", GLOSARIO[4:5]
                   + [T("G11", "mast", "caño")])
    assert [(o.term_id, o.label, o.start) for o in oc][0][1:] == ("OK", 15)
    assert oc[1].label == "NO_ENCONTRADO"
