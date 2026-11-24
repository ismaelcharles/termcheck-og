"""Controles inventados: offsets del texto original frente al HTML y al CSV reales."""
import csv
import io
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

import pytest

from termcheck.checker import verificar
from termcheck.etiquetas import NOMBRES, orden
from termcheck.glossary import Termino
from termcheck.report import a_csv_texto, a_html, bloque_segmento, escribir_csv


class Parrafos(HTMLParser):
    """Reconstruye texto y marcas desde el HTML, sin usar el algoritmo de resaltado."""
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.parrafos = []
        self.actual = None
        self.marca = None
        # El parser HTML del navegador normaliza CRLF/CR literales antes de resolver entidades.
        self.feed(html.replace("\r\n", "\n").replace("\r", "\n"))

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.actual = {"texto": "", "marcas": []}
        elif tag == "mark" and self.actual is not None:
            self.marca = (len(self.actual["texto"]), dict(attrs))

    def handle_data(self, data):
        if self.actual is not None:
            self.actual["texto"] += data

    def handle_endtag(self, tag):
        if tag == "mark" and self.marca is not None:
            inicio, attrs = self.marca
            self.actual["marcas"].append((inicio, len(self.actual["texto"]), attrs))
            self.marca = None
        elif tag == "p" and self.actual is not None:
            self.parrafos.append(self.actual)
            self.actual = None


GLOSARIO = [
    Termino(id="P1", en=["drilling rig", "rig"], pos="NOUN", es_preferred="equipo de perforación",
            es_allowed=["equipo"], es_forbidden=["plataforma de perforación"]),
    Termino(id="P2", en=["oil well"], pos="NOUN", es_preferred="pozo de petróleo"),
    Termino(id="P3", en=["gas well"], pos="NOUN", es_preferred="pozo de gas"),
]


CASOS = [
    ("Move the rig.", "Mueva el equipo de perforación.", [("OK", "equipo de perforación")]),
    ('“Move the rig!”', '«Mueva el equipo de perforación»; & <fin>.', [("OK", "equipo de perforación")]),
    ("Move the rig.", "Mueva el equipo de PERFORACION.", [("OK", "equipo de PERFORACION")]),
    ("Move the rig.", unicodedata.normalize("NFD", "Mueva el equipo de perforación."),
     [("OK", unicodedata.normalize("NFD", "equipo de perforación"))]),
    ("  Move the rig.  ", "\t Mueva el equipo de perforación.  ", [("OK", "equipo de perforación")]),
    ("🛢️ Move the rig; stop the rig.", "🛠️ Mueva el equipo; detenga el equipo.",
     [("VARIANTE", "equipo"), ("VARIANTE", "equipo")]),
    ("Move the rig.\nStop the rig.", "Mueva el equipo de\nperforación.\nDetenga el equipo.",
     [("OK", "equipo de\nperforación"), ("VARIANTE", "equipo")]),
    ("First line.\r\nMove the rig.", "Primera línea.\r\nMueva el equipo de perforación.",
     [("OK", "equipo de perforación")]),
    ("First line.\rMove the rig.", "Primera línea.\rMueva el equipo de perforación.",
     [("OK", "equipo de perforación")]),
    ("Move the drilling\r\nrig.", "Mueva el equipo de\r\nperforación.",
     [("OK", "equipo de\r\nperforación")]),
    ("Move the drilling\rrig.", "Mueva el equipo de\rperforación.",
     [("OK", "equipo de\rperforación")]),
    ("Move the rig; stop the rig; inspect the rig.",
     "Mueva el equipo; detenga la plataforma de perforación; inspeccione el rig.",
     [("PROHIBIDO", "plataforma de perforación"), ("VARIANTE", "equipo"), ("SIN_TRADUCIR", "rig")]),
    ("Move the rig and stop the rig.", "Mueva el equipo.", [("VARIANTE", "equipo"), ("NO_ENCONTRADO", "")]),
    ("Move the rig.", "Mueva la torre.", [("NO_ENCONTRADO", "")]),
    ("Inspect the oil well and the gas well.", "Revise el pozo de petróleo o gas.",
     [("OK", "pozo de petróleo"), ("OK", "pozo de petróleo o gas")]),
    ("Move the rig.", "", [("NO_ENCONTRADO", "")]),
]
CASOS += [(f"Move the drilling{g}rig.", f"Mueva el equipo{g}de{g}perforación.",
           [("OK", f"equipo{g}de{g}perforación")]) for g in "-‐‑‒–—"]


def comprobar_parrafo(parrafo, texto, ocurrencias, original=False):
    assert parrafo["texto"] == texto
    tramos = [(o.src_start, o.src_end, o) if original else (o.start, o.end, o) for o in ocurrencias]
    for i in range(len(texto)):
        activos = [o for a, b, o in tramos if a <= i < b]
        marcas = [attrs for a, b, attrs in parrafo["marcas"] if a <= i < b]
        assert len(marcas) == bool(activos), (i, texto, activos, marcas)
        if activos:
            assert marcas[0]["class"] == "tc-" + min((o.label for o in activos), key=orden).lower()
            for o in activos:
                assert f"{o.term_id} · {NOMBRES[o.label]}" in marcas[0]["title"]


@pytest.mark.parametrize("en,es,esperado", CASOS)
def test_posiciones_csv_pantalla_y_html(en, es, esperado, tmp_path):
    oc = verificar(en, es, GLOSARIO, "S1", "control")
    assert [(o.label, o.es_found) for o in oc] == esperado
    fuentes = list(re.finditer(r"\b(?:drilling[-‐‑‒–—\s]+rig|oil well|gas well|rig)\b", en, re.I))
    assert [(o.src_start, o.src_end) for o in oc] == [m.span() for m in fuentes]
    elegidos = []
    for o, (_, literal) in zip(oc, esperado):
        if literal:
            inicio = es.index(literal)
            # No reutilizar «equipo» dentro de una preferida completa ya asignada.
            while any(a <= inicio and inicio + len(literal) <= b for a, b in elegidos):
                inicio = es.index(literal, inicio + 1)
            assert (o.start, o.end) == (inicio, inicio + len(literal))
            elegidos.append((inicio, inicio + len(literal)))
    for o in oc:
        assert 0 <= o.src_start < o.src_end <= len(en)
        assert en[o.src_start:o.src_end] == o.term_en
        if o.label == "NO_ENCONTRADO":
            assert (o.start, o.end, o.es_found) == (-1, -1, "")
        else:
            assert 0 <= o.start < o.end <= len(es)
            assert es[o.start:o.end] == o.es_found
    encontrados = [(o.start, o.end) for o in oc if o.start >= 0]
    assert len(set(encontrados)) == len(encontrados)

    contextos = {("S1", "control"): (en, es)}
    csv_texto = a_csv_texto(oc, contextos)
    escribir_csv(oc, tmp_path / "reporte.csv", contextos)
    assert (tmp_path / "reporte.csv").read_bytes() == csv_texto.encode("utf-8")
    filas = list(csv.DictReader(io.StringIO(csv_texto, newline="")))
    assert len(filas) == len(oc)
    for fila, o in zip(filas, oc):
        assert (fila["source_en"], fila["target_es"]) == (en, es)
        assert (int(fila["start"]), int(fila["end"]), fila["es_found"]) == (o.start, o.end, o.es_found)
        if o.start >= 0:
            assert fila["target_es"][int(fila["start"]):int(fila["end"])] == fila["es_found"]

    completo = a_html({"S1": en}, [{"seg_id": "S1", "system": "control", "target_es": es}], oc)
    descarga = Parrafos(completo).parrafos
    # La pantalla usa bloque_segmento; su filtro solo afecta la tabla de detalles.
    for solo in (False, True):
        pantalla = Parrafos(bloque_segmento(en, es, oc, solo=solo)).parrafos
        for indice, texto in enumerate((en, es), start=1):
            comprobar_parrafo(pantalla[indice], texto, oc, original=indice == 1)
            assert pantalla[indice] in descarga


def test_pagina_real_descarga_los_mismos_textos_y_posiciones(monkeypatch):
    import streamlit as st
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("TERMCHECK_DEMO", "1")
    descargados = {}
    descargar = st.download_button

    def capturar(label, data, *args, **kwargs):
        descargados[label] = data
        return descargar(label, data, *args, **kwargs)

    monkeypatch.setattr(st, "download_button", capturar)
    pagina = Path(__file__).resolve().parents[1] / "app/demo.py"
    app = AppTest.from_file(str(pagina), default_timeout=120).run()
    pares = [
        ("  🛢️ Move the rig; stop the rig.  ",
         "  🛠️ Mueva el equipo; detenga la plataforma de perforacio\u0301n.  "),
        ("Inspect the wellhead.", "Revise la válvula."),
    ]
    app.text_area[0].set_value("\n".join(p[0] for p in pares))
    app.text_area[1].set_value("\n".join(p[1] for p in pares))
    [b for b in app.button if b.label == "Verificar"][0].click().run()
    assert not app.exception, app.exception
    resultado = app.session_state.vf_resultado[1]
    assert [(p[2], p[3]) for p, _ in resultado] == pares
    assert [[o.label for o in oc] for _, oc in resultado] == [["PROHIBIDO", "VARIANTE"], ["NO_ENCONTRADO"]]
    filas = list(csv.DictReader(io.StringIO(descargados["Tabla CSV"])))
    assert len(filas) == 3
    for fila in filas:
        if int(fila["start"]) >= 0:
            assert fila["target_es"][int(fila["start"]):int(fila["end"])] == fila["es_found"]
    for fila, (p, o) in zip(filas, [(p, o) for p, oc in resultado for o in oc]):
        assert (fila["seg_id"], fila["system"], fila["source_en"], fila["target_es"]) == p
        assert (int(fila["start"]), int(fila["end"]), fila["es_found"], fila["label"]) == (
            o.start, o.end, o.es_found, o.label)
    html = Parrafos(descargados["Reporte HTML"]).parrafos
    for i, ((_, _, en, es), oc) in enumerate(resultado):
        if i:
            app.selectbox[0].select(i).run()
        bloques = [m.proto.body for m in app.get("html") if 'class="tc-seg"' in m.proto.body]
        assert len(bloques) == 1
        parrafos = Parrafos(bloques[0]).parrafos
        for indice, texto in enumerate((en, es), start=1):
            comprobar_parrafo(parrafos[indice], texto, oc, original=indice == 1)
            assert parrafos[indice] in html
