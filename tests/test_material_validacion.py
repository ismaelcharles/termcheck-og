"""Preparación y cotejo con archivos inventados; no simula una sesión ni exportación real."""
from pathlib import Path
import csv,hashlib,json,zipfile
import xml.etree.ElementTree as E

import pytest

from scripts.preparar_prueba_uso import preparar,ROWS
from scripts.comprobar_exportacion_cat import comprobar
from termcheck.formatos import leer


def tmx(path,rows=ROWS,creator='memoQ',encoding='utf-8'):
    root=E.Element('tmx',version='1.4');E.SubElement(root,'header',creationtool=creator,creationtoolversion='control-inventado')
    body=E.SubElement(root,'body')
    # El orden de una memoria no tiene que coincidir con el archivo de origen.
    for sid,en,es in reversed(rows):
        tu=E.SubElement(body,'tu',tuid=sid)
        for lang,text in [('en-US',en),('es-AR',es)]:
            E.SubElement(E.SubElement(tu,'tuv',{'{http://www.w3.org/XML/1998/namespace}lang':lang}),'seg').text=text
    path.write_bytes(E.tostring(root,encoding=encoding,xml_declaration=True))
    return path


def test_material_no_inventa_participantes_ni_procedencia(tmp_path):
    m=preparar(tmp_path)
    assert m['participantes_reales']==m['exportaciones_cat_reales']==0
    assert len(leer((tmp_path/'muestra.xlf').read_bytes(),'muestra.xlf')[0])==8
    with zipfile.ZipFile(tmp_path/'material-prueba.zip') as z:
        assert 'respuestas.json' not in z.namelist()
        assert z.read('referencia.tsv')==(tmp_path/'referencia.tsv').read_bytes()
    with (tmp_path/'registro-uso.csv').open() as f:
        assert all(not r['participante_anonimo'] and not r['completada_sin_ayuda'] for r in csv.DictReader(f))
    with pytest.raises(ValueError,match='no sobrescribir'):preparar(tmp_path)


@pytest.mark.parametrize('creator,tool,encoding',[('memoQ','memoq','utf-8'),('SDL Language Platform','trados','utf-16')])
def test_cotejo_en_es_por_pares_y_no_por_orden(tmp_path,creator,tool,encoding):
    preparar(tmp_path)
    path=tmx(tmp_path/'sintetico.tmx',creator=creator,encoding=encoding)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    r=comprobar(path,tmp_path/'referencia.tsv',tool,'test')
    assert r['coincide_con_referencia'] and r['pares']==8
    assert r['coincide_con_lectura_independiente'] and r['original_intacto']
    assert r['sha256']==before==hashlib.sha256(path.read_bytes()).hexdigest()
    assert 'declaración' in r['procedencia']  # La cabecera de un control no prueba una exportación real.


def test_no_da_por_bueno_un_archivo_local_como_exportacion(tmp_path):
    preparar(tmp_path);path=tmx(tmp_path/'sintetico.tmx',creator='TermCheck control local')
    with pytest.raises(ValueError,match='cabecera'):comprobar(path,tmp_path/'referencia.tsv','memoq','test')


def test_pares_perdidos_o_modificados_no_se_ocultan(tmp_path):
    preparar(tmp_path);path=tmx(tmp_path/'sintetico.tmx',rows=ROWS[:-1]+[('OTRO','Wrong source.','Origen cambiado.')])
    r=comprobar(path,tmp_path/'referencia.tsv','memoq','test')
    assert not r['coincide_con_referencia']
    assert r['faltantes']==r['adicionales']==1


def test_destino_vacio_no_se_cuenta_como_importacion_completa(tmp_path):
    preparar(tmp_path);path=tmx(tmp_path/'sintetico.tmx',rows=ROWS[:-1]+[(ROWS[-1][0],ROWS[-1][1],'')])
    r=comprobar(path,tmp_path/'referencia.tsv','memoq','test')
    assert not r['coincide_con_referencia'] and r['omitidos_sin_es']==1 and r['faltantes']==1


def test_control_tmx_no_habilita_formatos_nativos(tmp_path):
    preparar(tmp_path)
    with pytest.raises(ValueError,match='TMX original'):
        comprobar(tmp_path/'muestra.xlf',tmp_path/'referencia.tsv','memoq','test')
