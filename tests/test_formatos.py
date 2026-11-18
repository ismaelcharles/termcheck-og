"""Pruebas del lector de XLIFF y TMX (src/termcheck/formatos.py) y de su uso en la página Verificar.

Los archivos están armados a mano según la norma de cada formato. No son exportaciones reales de Trados ni
de memoQ. El contenido es inventado para probar el código.

Correr:  .venv/bin/python -m pytest tests/test_formatos.py -v
"""
import subprocess
import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from termcheck.formatos import ErrorDeFormato, es_de_traduccion, leer

RAIZ = Path(__file__).resolve().parent.parent

XLIFF_12 = """<?xml version="1.0" encoding="UTF-8"?>
<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">
  <file original="manual.docx" source-language="en-US" target-language="es-AR" datatype="plaintext">
    <body>
      <trans-unit id="1">
        <source>Inspect the <g id="1">wellhead</g> daily.</source>
        <target>Inspeccione la <g id="1">boca de pozo</g> todos los días.</target>
      </trans-unit>
      <trans-unit id="2">
        <source>Move the <bpt id="1">&lt;b&gt;</bpt>drilling rig<ept id="1">&lt;/b&gt;</ept>.<x id="2"/></source>
        <target>Mueva la <bpt id="1">&lt;b&gt;</bpt>plataforma de perforación<ept id="1">&lt;/b&gt;</ept>.</target>
      </trans-unit>
      <trans-unit id="3">
        <source>Run the casing.</source>
      </trans-unit>
      <trans-unit id="4">
        <source>Run the casing. Check the rig.</source>
        <seg-source><mrk mtype="seg" mid="1">Run the casing.</mrk> <mrk mtype="seg" mid="2">Check the rig.</mrk></seg-source>
        <target><mrk mtype="seg" mid="1">Baje el casing.</mrk> <mrk mtype="seg" mid="2">Revise el equipo.</mrk></target>
      </trans-unit>
      <trans-unit id="1">
        <source>Close the wellhead.</source>
        <target>   Cierre la
           boca de pozo. </target>
      </trans-unit>
    </body>
  </file>
</xliff>
"""

XLIFF_20 = """<?xml version="1.0" encoding="UTF-8"?>
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.0" srcLang="en" trgLang="es">
  <file id="f1">
    <unit id="u1">
      <segment>
        <source>Inspect the <pc id="1">wellhead</pc>.<ph id="2"/></source>
        <target>Inspeccione la <pc id="1">boca de pozo</pc>.</target>
      </segment>
    </unit>
    <unit id="u2">
      <segment id="a"><source>Run the casing.</source><target>Baje el casing.</target></segment>
      <ignorable><source> </source></ignorable>
      <segment id="b"><source>Check the rig.</source></segment>
    </unit>
  </file>
</xliff>
"""

TMX = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header creationtool="a mano" srclang="en-US" datatype="plaintext" segtype="sentence" adminlang="en" o-tmf="x"
          creationtoolversion="1"/>
  <body>
    <tu tuid="7">
      <tuv xml:lang="es-AR"><seg>Inspeccione la <hi>boca de pozo</hi>.</seg></tuv>
      <tuv xml:lang="en-US"><seg>Inspect the <hi>wellhead</hi>.</seg></tuv>
    </tu>
    <tu>
      <tuv xml:lang="en-US"><seg>Move the <bpt i="1">{b}</bpt>drilling rig<ept i="1">{/b}</ept>.</seg></tuv>
      <tuv xml:lang="es-AR"><seg>Mueva el equipo de perforación.</seg></tuv>
    </tu>
    <tu>
      <tuv xml:lang="en-US"><seg>Run the casing.</seg></tuv>
      <tuv xml:lang="pt-BR"><seg>Desça o revestimento.</seg></tuv>
    </tu>
  </body>
</tmx>
"""


def test_xliff_12():
    pares, sin_traduccion = leer(XLIFF_12.encode("utf-8"), "a.xliff")
    assert pares == [
        ("1", "Inspect the wellhead daily.", "Inspeccione la boca de pozo todos los días."),
        ("2", "Move the drilling rig.", "Mueva la plataforma de perforación."),   # sin el código de <bpt> y <ept>
        ("4#1", "Run the casing.", "Baje el casing."),                              # unidad partida en segmentos
        ("4#2", "Check the rig.", "Revise el equipo."),
        ("1-2", "Close the wellhead.", "Cierre la boca de pozo."),                  # id repetido; espacios acomodados
    ]
    assert sin_traduccion == 1


def test_xliff_20():
    pares, sin_traduccion = leer(XLIFF_20.encode("utf-8"), "a.xlf")
    assert pares == [("u1", "Inspect the wellhead.", "Inspeccione la boca de pozo."),
                     ("u2#a", "Run the casing.", "Baje el casing.")]
    assert sin_traduccion == 1


def test_tmx_con_doctype_simple_y_variantes_en_cualquier_orden():
    pares, sin_traduccion = leer(TMX.encode("utf-8"), "a.tmx")
    assert pares == [("7", "Inspect the wellhead.", "Inspeccione la boca de pozo."),
                     ("2", "Move the drilling rig.", "Mueva el equipo de perforación.")]
    assert sin_traduccion == 1    # la unidad que no tiene español


def test_utf16_con_marca_de_orden():
    datos = TMX.replace('encoding="UTF-8"', 'encoding="UTF-16"').encode("utf-16")
    assert len(leer(datos, "a.tmx")[0]) == 2


@pytest.mark.parametrize("malo", [
    '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><xliff version="1.2"><file><body><trans-unit id="1">'
    '<source>&a;</source><target>x</target></trans-unit></body></file></xliff>',
    '<!DOCTYPE tmx [ <!ELEMENT tmx ANY> ]><tmx version="1.4"><body/></tmx>',
])
def test_rechaza_entidades_y_doctype_con_definiciones(malo):
    with pytest.raises(ErrorDeFormato, match="seguridad"):
        leer(malo.encode("utf-8"), "a.xliff")


@pytest.mark.parametrize("malo, mensaje", [
    ("esto no es xml", "XML válido"),
    ("<html><body/></html>", "no es XLIFF ni TMX"),
    ('<xliff version="3.0"/>', "versión"),
    ('<xliff version="1.2"><file><body/></file></xliff>', "No encontré segmentos"),
])
def test_errores_claros(malo, mensaje):
    with pytest.raises(ErrorDeFormato, match=mensaje):
        leer(malo.encode("utf-8"), "a.xliff")


def test_extensiones():
    assert es_de_traduccion("Proyecto.XLIFF") and es_de_traduccion("a.xlf") and es_de_traduccion("memoria.tmx")
    assert not es_de_traduccion("a.tsv") and not es_de_traduccion("a.sdlxliff")


def test_run_check_con_archivo(tmp_path):
    archivo = tmp_path / "proyecto.xliff"
    archivo.write_text(XLIFF_12, encoding="utf-8")
    glosario = tmp_path / "glosario.csv"
    glosario.write_text("id,en,pos,es_preferred,es_allowed,es_forbidden,subdomain,note,source\n"
                        "G1,drilling rig|rig,NOUN,equipo de perforación,equipo,plataforma de perforación,,,inventado\n"
                        "G3,wellhead,NOUN,boca de pozo,,,,,inventado\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(RAIZ / "scripts/run_check.py"), "--file", str(archivo),
                        "--glossary", str(glosario), "--out", str(tmp_path / "salida")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "5 traducciones" in r.stdout and "1 sin traducción" in r.stdout
    filas = (tmp_path / "salida.csv").read_text(encoding="utf-8")
    assert "PROHIBIDO" in filas and "4#2" in filas


def test_la_pagina_verificar_procesa_un_xliff(monkeypatch):
    monkeypatch.setenv("TERMCHECK_DEMO", "1")
    monkeypatch.delenv("TERMCHECK_SIN_LOGIN", raising=False)
    at = AppTest.from_file(str(RAIZ / "app/demo.py"), default_timeout=120)
    at.run()
    at.session_state["vf_modo"] = "tsv"
    at.run()
    assert not at.exception, at.exception
    subir = [f for f in at.get("file_uploader") if f.key == "vf_archivo"][0]
    subir.upload("proyecto.xliff", XLIFF_12.encode("utf-8"), "application/xml").run()
    assert not at.exception, at.exception
    [b for b in at.button if b.label == "Verificar"][0].click().run()
    assert not at.exception, at.exception
    assert any("Revisión" in s.value for s in at.subheader)
    assert any("· 5 segmentos" in m.proto.body for m in at.get("html"))
    assert any("Se salteó 1 segmento sin traducción" in c.value for c in at.caption)
