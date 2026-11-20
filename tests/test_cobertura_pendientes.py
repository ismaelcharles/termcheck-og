"""Controles dirigidos de los 18 conceptos sin contexto en las muestras naturales.

Las traducciones son inventadas; se prueban detección, omisiones y confusiones de
conceptos explícitos. No son una medición de calidad en textos nuevos.
"""
from pathlib import Path
import json

import pytest

from termcheck.checker import verificar
from termcheck.glossary import cargar

ROOT=Path(__file__).resolve().parents[1]
CASOS=json.loads((ROOT/'data/checks/cobertura_18_v1_4.json').read_text())['casos']


@pytest.fixture(scope='module')
def glosario():return cargar(ROOT/'data/glossary/glossary_v1_4.csv')


@pytest.mark.parametrize('caso',CASOS,ids=lambda r:r['id'])
@pytest.mark.parametrize('tipo',['es_valido','es_error'])
def test_contextos_dirigidos(caso,tipo,glosario):
    target=caso[tipo]
    result=verificar(caso['en'],target,glosario)
    own=[o for o in result if o.term_id==caso['term_id']]
    assert len(own)==1
    [o]=own
    assert o.marcada==(tipo=='es_error')
    assert caso['en'][o.src_start:o.src_end]==o.term_en
    if o.start>=0:assert target[o.start:o.end]==o.es_found


def test_inventario_coincide_con_huecos_identificados():
    audit=json.loads((ROOT/'docs/cobertura-1-4.json').read_text())
    assert len(CASOS)==len({r['term_id'] for r in CASOS})==18
    assert {r['term_id'] for r in CASOS}==set(audit['resumen']['conceptos_sin_deteccion'])
