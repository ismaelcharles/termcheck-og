"""Regresiones con frases inventadas tras probar traducciones públicas externas al corpus."""
import pytest

from termcheck.checker import verificar
from termcheck.glossary import Termino


def termino(id, en, es, prohibidas=()):
    return Termino(id=id, en=[en], pos='NOUN', es_preferred=es,
                   es_allowed=[], es_forbidden=list(prohibidas))


CASING = termino('P1', 'casing', 'cañería')
TUBING = termino('P2', 'tubing', 'tubería de producción')
WELL_CONTROL = termino('P3', 'well control', 'control de pozo')
WELLHEAD = termino('P4', 'wellhead', 'cabeza de pozo', ['boca de pozo'])


@pytest.mark.parametrize('en', [
    'In this case, stop the test.', 'These cases require a review.',
    'CASE MANAGEMENT', 'The case was closed.',
])
def test_case_no_es_casing(en):
    assert verificar(en, 'En este caso, revise la situación.', [CASING]) == []


def test_tube_no_es_tubing():
    assert verificar('The tube is clean.', 'El tubo está limpio.', [TUBING]) == []


@pytest.mark.parametrize('en', ['Inspect the casing.', 'Inspect the casings.'])
def test_casing_y_su_plural_se_conservan(en):
    [o] = verificar(en, 'Inspeccione la cañería.', [CASING])
    assert (o.term_en.lower(), o.label) == (en.split()[2].rstrip('.').lower(), 'OK')


def test_case_junto_a_casing_no_agrega_otra_aparicion():
    en = 'In this case, inspect the casing.'
    [o] = verificar(en, 'En este caso, inspeccione la cañería.', [CASING])
    assert o.term_en == 'casing' and en[o.src_start:o.src_end] == 'casing'


@pytest.mark.parametrize('es,found', [
    ('Compruebe el control de un pozo.', 'control de un pozo'),
    ('Compruebe el control de unos pozos.', 'control de unos pozos'),
    ('Compruebe los controles de un pozo.', 'controles de un pozo'),
])
def test_articulo_indefinido_entre_de_y_sustantivo(es, found):
    [o] = verificar('Check well control.', es, [WELL_CONTROL])
    assert (o.label, o.es_found) == ('OK', found)
    assert es[o.start:o.end] == found


def test_articulo_femenino():
    mud = termino('P5', 'mud pump', 'bomba de lodo')
    casing_shoe = termino('P6', 'casing shoe', 'zapata de cañería')
    [o] = verificar('Inspect the casing shoe.', 'Inspeccione la zapata de una cañería.', [casing_shoe, mud])
    assert (o.label, o.es_found) == ('OK', 'zapata de una cañería')


@pytest.mark.parametrize('es', [
    'El control de otro pozo.', 'El control de ningún pozo.',
    'El control de un nuevo pozo.', 'El control. De un pozo.',
    'El control del pozo.', 'El control de el pozo.',
])
def test_no_se_omiten_otras_palabras_ni_se_iguala_del(es):
    [o] = verificar('Check well control.', es, [WELL_CONTROL])
    assert o.label == 'NO_ENCONTRADO'


def test_forma_prohibida_tambien_reconoce_articulo():
    es = 'Inspeccione la boca de un pozo.'
    [o] = verificar('Inspect the wellhead.', es, [WELLHEAD])
    assert (o.label, o.es_found) == ('PROHIBIDO', 'boca de un pozo')


def test_el_tramo_con_articulo_no_vale_para_dos_terminos():
    well = termino('P7', 'well', 'pozo')
    oc = verificar('Check well control near the well.', 'Compruebe el control de un pozo.', [WELL_CONTROL, well])
    assert [(o.term_id, o.label) for o in oc] == [('P3', 'OK'), ('P7', 'NO_ENCONTRADO')]
