"""Regresiones de las decisiones del autor en la revisión de noviembre de 2026."""
from pathlib import Path

import pytest

from termcheck.checker import verificar
from termcheck.glossary import cargar, publicado, validar


@pytest.fixture(scope="module")
def glosario_trabajo():
    return cargar(Path(__file__).resolve().parents[1] / "data/glossary/glossary_en_es.csv")


@pytest.mark.parametrize("traduccion", [
    "Hay que cementar el pozo.",
    "El pozo se cementa.",
    "El pozo se cementó.",
    "Cementaron el pozo.",
    "El pozo fue cementado.",
    "Hay que cementarlo.",
    "Hay que cementarse.",
    "Se está cementando el pozo.",
    "El pozo se cementará.",
    "El pozo se cementaría.",
])
def test_cementacion_verbal(glosario_trabajo, traduccion):
    resultado = verificar("Cementing the well.", traduccion, glosario_trabajo)
    cemento = next(o for o in resultado if o.term_id == "T064")
    assert not cemento.marcada
    assert cemento.es_form == "cementar"


@pytest.mark.parametrize("ingles, traduccion, termino", [
    ("The rig floor.", "El piso del equipo.", "T011"),
    ("Immediate well control.", "Control inmediato del pozo.", "T096"),
    ("Surface casing.", "Cañería guía.", "T055"),
    ("Intermediate casing.", "Cañería intermedia.", "T056"),
    ("The traveling block.", "El aparejo.", "T026"),
    ("Drill pipe.", "Barras de sondeo.", "T035"),
    ("Choke manifold.", "Manifold de surgencia.", "T032"),
    ("Coiled tubing.", "Tubería enrollada.", "T089"),
    ("Christmas tree.", "Christmas tree.", "T006"),
    ("Casing.", "Entubado.", "T031"),
    ("Drill string.", "Sarta.", "T104"),
    ("Fishing tool.", "Herramienta de pesca.", "T100"),
    ("Kelly.", "Vástago.", "T037"),
])
def test_formas_aceptadas_por_el_autor(glosario_trabajo, ingles, traduccion, termino):
    resultado = verificar(ingles, traduccion, glosario_trabajo)
    ocurrencia = next(o for o in resultado if o.term_id == termino)
    assert not ocurrencia.marcada


@pytest.mark.parametrize("ingles, traduccion, termino", [
    ("Drill pipe.", "Tubo de perforación.", "T035"),
    ("Surface casing.", "Entubado de superficie.", "T055"),
    ("Choke manifold.", "Colector de estrangulamiento.", "T032"),
    ("Workover.", "Hay que reparar el pozo.", "T098"),
    ("Cementing.", "El cemento está listo.", "T064"),
    ("Wellhead.", "Boca del pozo.", "T019"),
])
def test_correcciones_y_limites(glosario_trabajo, ingles, traduccion, termino):
    resultado = verificar(ingles, traduccion, glosario_trabajo)
    assert next(o for o in resultado if o.term_id == termino).marcada


def test_glosario_revisado_valido(glosario_trabajo):
    assert not [p for p in validar(glosario_trabajo) if p.tipo == "error"]


def test_edicion_publicada_incluye_la_revision():
    carpeta = Path(__file__).resolve().parents[1] / "data/glossary"
    ruta = publicado(carpeta)
    assert ruta.name == "glossary_v1_3.csv"
    assert ruta.read_bytes() == (carpeta / "glossary_en_es.csv").read_bytes()
    terminos = cargar(ruta)
    assert len(terminos) == 104
    assert next(t for t in terminos if t.id == "T032").es_preferred == "manifold de surgencia"


@pytest.mark.parametrize("ingles,espanol", [
    ("Inspect the elevator.", "Inspeccioná el elevador."),
    ("Inspect the elevators.", "Inspeccioná los elevadores."),
])
def test_elevator_singular_y_plural(glosario_trabajo, ingles, espanol):
    termino = next(t for t in glosario_trabajo if t.id == "T091")
    assert termino.en == ["elevator"]
    ocurrencias = verificar(ingles, espanol, [termino])
    assert len(ocurrencias) == 1
    assert ocurrencias[0].label == "OK"
