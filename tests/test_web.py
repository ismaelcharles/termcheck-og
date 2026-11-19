"""Paridad y límites del adaptador público HTTP, independiente de Streamlit."""
import base64
import csv
import io
import re
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from termcheck import report
from termcheck.checker import verificar
from web.main import app
from web import servicio


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:
        yield c


def salida_html(cliente, en, es, **extra):
    r = cliente.post('/verificar', data={'en': en, 'es': es, **extra})
    assert r.status_code == 200
    return r.text


def csv_salida(html):
    datos = re.search(r'data-download="csv" data-content="([^"]+)"', html).group(1)
    return base64.b64decode(datos).decode()


@pytest.mark.parametrize('en,es', [
    ('Inspect the elevator.', 'Inspeccioná el elevador.'),
    ('Inspect the elevators.', 'Inspeccioná los elevadores.'),
    ('Choke manifold.', 'Colector de estrangulamiento.'),
    ('Cementing.', 'Hay que cementarlo.'),
    ('The rig floor.', 'El piso del equipo.'),
    ('Immediate well control.', 'Control inmediato del pozo.'),
    ('Surface casing.', 'Cañería guía.'),
    ('Hello everyone.', 'Hola a todos.'),
])
def test_paridad_csv_motor(cliente, en, es):
    terminos, _ = servicio.glosario()
    html = salida_html(cliente, en, es)
    assert 'data-result-ok' in html
    assert csv_salida(html) == report.a_csv_texto(verificar(en, es, terminos, 'L1', ''))


def test_html_incluye_documento_completo_y_huella(cliente):
    en, es = 'Casing.\nDrill pipe.', 'Casing.\nTubo de perforación.'
    html = salida_html(cliente, en, es)
    datos = re.search(r'data-download="html" data-content="([^"]+)"', html).group(1)
    reporte = base64.b64decode(datos).decode()
    assert 'L1' in reporte and 'L2' in reporte
    assert 'SHA-256' in reporte and 'glossary_v1_3.csv' in reporte
    assert len(list(csv.DictReader(io.StringIO(csv_salida(html))))) == 2


@pytest.mark.parametrize('en,es,mensaje', [
    ('', '', 'Completá'),
    ('Casing.\nWell.', 'Casing.', 'líneas'),
    ('Casing.\n\nWell.', 'Casing.\nExtra.\nPozo.', 'sin original'),
    ('x' * 20001, 'x', 'demasiado largo'),
])
def test_validacion_textos(cliente, en, es, mensaje):
    html = salida_html(cliente, en, es)
    assert 'data-validation-error' in html and mensaje in html
    assert 'data-result-ok' not in html


def test_sin_terminos_no_informa_exito(cliente):
    html = salida_html(cliente, 'Hello everyone.', 'Hola a todos.')
    assert 'No se encontraron términos' in html
    assert 'Sin observaciones' not in html


@pytest.mark.parametrize('nombre,datos', [
    ('prueba.csv', b'source_en;target_es\nCasing.;Casing.'),
    ('prueba.tsv', b'source_en\ttarget_es\nCasing.\tCasing.'),
    ('prueba.xlf', b'<xliff version="1.2"><file source-language="en" target-language="es"><body><trans-unit id="a"><source>Casing.</source><target>Casing.</target></trans-unit></body></file></xliff>'),
    ('prueba.tmx', b'<tmx version="1.4"><body><tu tuid="a"><tuv xml:lang="en"><seg>Casing.</seg></tuv><tuv xml:lang="es"><seg>Casing.</seg></tuv></tu></body></tmx>'),
])
def test_formatos(cliente, nombre, datos):
    r = cliente.post('/verificar', data={'modo': 'archivo'}, files={'archivo': (nombre, datos)})
    assert 'data-result-ok' in r.text
    filas = list(csv.DictReader(io.StringIO(csv_salida(r.text))))
    assert len(filas) == 1 and filas[0]['label'] == 'OK'


def test_fila_rota_y_glosario_invalido(cliente):
    r = cliente.post('/verificar', data={'modo': 'archivo'}, files={'archivo': ('x.csv', b'source_en,target_es\nCasing.')})
    assert 'data-validation-error' in r.text
    r = cliente.post('/verificar', data={'en': 'Casing.', 'es': 'Casing.'}, files={'glosario': ('g.csv', b'id,en\nX,foo')})
    assert 'data-validation-error' in r.text
    assert 'data-result-ok' not in r.text


def test_glosario_propio_y_escape(cliente):
    datos = ('id,en,pos,es_preferred,es_allowed,es_forbidden,subdomain,note,source\n'
             'X,widget,NOUN,artefacto,,,,,criterio propio\n').encode()
    r = cliente.post('/verificar', data={'en': 'The widget.', 'es': 'El artefacto. <script>alert(1)</script>'}, files={'glosario': ('g.csv', datos)})
    assert 'data-result-ok' in r.text
    assert '<script>alert(1)</script>' not in r.text
    assert '&lt;script&gt;' in r.text
    assert 'X' in csv_salida(r.text)


def test_limites_y_origen(cliente):
    r = cliente.post('/verificar', files={'archivo': ('x.csv', b'x' * (servicio.MAX_ARCHIVO + 1))}, data={'modo': 'archivo'})
    assert 'data-validation-error' in r.text
    assert cliente.post('/verificar', content=b'x' * (3 * servicio.MAX_ARCHIVO)).status_code == 413
    assert cliente.post('/verificar', data={'en': 'x'}, headers={'Origin': 'https://ajeno.example'}).status_code == 403
    r = cliente.get('/')
    assert r.headers['cache-control'] == 'no-store'
    assert 'set-cookie' not in r.headers


def test_catalogo_y_descarga(cliente):
    html = cliente.get('/glosario?q=elevator').text
    assert '<h3 lang="en">elevator</h3>' in html
    assert '<span>91</span>' in html
    assert cliente.get('/glosario.csv').content == (servicio.RAIZ / 'data/glossary/glossary_v1_3.csv').read_bytes()
    assert 'No encontré términos' in cliente.get('/glosario?q=zzzzzz').text
    assert 'Página 1 de' in cliente.get('/glosario?pagina=-1', headers={'HX-Request':'true'}).text


def test_sesiones_simultaneas_sin_cruces(cliente):
    def caso(i):
        texto = f'Casing. Visitante {i}.'
        html = salida_html(cliente, 'Casing.', texto)
        assert f'Visitante {i}.' in html
        assert all(f'Visitante {j}.' not in html for j in range(3) if j != i)
    with ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(caso, range(3)))


@pytest.fixture(scope="module")
def cliente_publico():
    from web.main import publica
    with TestClient(publica) as c:
        yield c


def test_montaje_demo_y_fuentes(cliente_publico):
    r = cliente_publico.get('/demo/')
    assert r.status_code == 200
    assert '<base href="http://testserver/demo/">' in r.text
    for archivo in ['static/web.css', 'static/web.js', 'static/tema.js', 'static/vendor/htmx.min.js', 'fonts/inter-normal-latin.woff2']:
        assert cliente_publico.get('/demo/' + archivo).status_code == 200
    assert "url('../fonts/" in cliente_publico.get('/demo/static/web.css').text
    assert cliente_publico.get('/demo/salud').json()['estado'] == 'ok'
    html = cliente_publico.post('/demo/verificar', data={'en':'Inspect the elevator.', 'es':'Inspeccioná el elevador.'}).text
    assert 'Sin observaciones' in html


@pytest.mark.parametrize('ruta,selector', [
    ('glosario?q=elevator', '<h3 lang="en">elevator</h3>'),
    ('ejemplos', 'Probar traducción'),
])
def test_secciones_directas_y_fragmentos(cliente_publico, ruta, selector):
    completo = cliente_publico.get('/demo/' + ruta).text
    assert '<!doctype html>' in completo and selector in completo
    assert 'id="workspace" hidden' in completo
    parcial = cliente_publico.get('/demo/' + ruta, headers={'HX-Request':'true'}).text
    assert '<!doctype html>' not in parcial and selector in parcial
