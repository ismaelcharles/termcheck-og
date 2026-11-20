"""Pruebas del reporte (src/termcheck/report.py) y de scripts/run_check.py con --src y --tgt.

Correr:  .venv/bin/python -m pytest tests/test_report.py -v
"""
import csv
import io
import subprocess
import sys
from pathlib import Path

from termcheck.checker import verificar
from termcheck import VERSION
from termcheck.glossary import Termino
from termcheck.report import a_csv_texto, a_html, escribir_csv, resaltar

RAIZ = Path(__file__).resolve().parent.parent
GLOSARIO = [Termino(id="G1", en=["drilling rig", "rig"], pos="NOUN", es_preferred="equipo de perforación",
                    es_allowed=["equipo"], es_forbidden=["plataforma de perforación"]),
            Termino(id="G3", en=["wellhead"], pos="NOUN", es_preferred="boca de pozo")]
# Las columnas que pide el plan para el CSV (una fila por aparición)
COLUMNAS_DEL_PLAN = ["seg_id", "system", "term_id", "term_en", "label", "es_found", "start", "end"]


def test_csv_tiene_las_columnas_del_plan_y_una_fila_por_aparicion(tmp_path):
    oc = verificar("Move the rig to the wellhead.", "Mueva la plataforma de perforación a la boca de pozo.",
                   GLOSARIO, "S1", "mt")
    es = "Mueva la plataforma de perforación a la boca de pozo."
    contextos = {("S1", "mt"): ("Move the rig to the wellhead.", es)}
    filas = list(csv.DictReader(io.StringIO(a_csv_texto(oc, contextos))))
    assert list(filas[0])[:len(COLUMNAS_DEL_PLAN)] == COLUMNAS_DEL_PLAN
    assert [(f["term_id"], f["label"], f["es_found"]) for f in filas] == [
        ("G1", "PROHIBIDO", "plataforma de perforación"), ("G3", "OK", "boca de pozo")]
    # start y end dicen dónde está la forma en la traducción
    assert es[int(filas[0]["start"]):int(filas[0]["end"])] == "plataforma de perforación"
    assert filas[0]["source_en"] == filas[1]["source_en"] == "Move the rig to the wellhead."
    assert filas[0]["target_es"] == filas[1]["target_es"] == es
    assert filas[0]["target_es"][int(filas[0]["start"]):int(filas[0]["end"])] == filas[0]["es_found"]
    escribir_csv(oc, tmp_path / "r.csv", contextos)
    assert (tmp_path / "r.csv").read_text(encoding="utf-8") == a_csv_texto(oc, contextos)


def test_html_escapa_el_texto():
    en, es = "Move the <b>rig</b> & go.", 'Mueva el <script>alert("x")</script> equipo.'
    oc = verificar(en, es, GLOSARIO, "S1", "mt")
    html = a_html({"S1": en}, [{"seg_id": "S1", "system": "mt", "target_es": es}], oc)
    assert "<script>" not in html and "<b>rig" not in html
    assert "&lt;script&gt;" in html and "&amp; go." in html


def test_html_escapa_lo_que_viene_del_glosario():
    # Un glosario subido puede traer cualquier cosa en el id o en las formas: no tiene que llegar como HTML
    malo = [Termino(id='<img src=x onerror=alert(1)>', en=["rig"], pos="NOUN", es_preferred="<b>equipo</b>")]
    oc = verificar("Move the rig.", "Mueva la torre.", malo, "S1", "mt")
    html = a_html({"S1": "Move the rig."}, [{"seg_id": "S1", "system": "mt", "target_es": "Mueva la torre."}], oc)
    assert "<img" not in html and "<b>equipo" not in html
    assert "&lt;img" in html and "&lt;b&gt;equipo" in html


def test_html_resalta_los_tramos():
    en, es = "Move the rig.", "Mueva la plataforma de perforación."
    oc = verificar(en, es, GLOSARIO, "S1", "mt")
    html = a_html({"S1": en}, [{"seg_id": "S1", "system": "mt", "target_es": es}], oc)
    assert '<mark class="tc-prohibido"' in html
    assert ">plataforma de perforación</mark>" in html and ">rig</mark>" in html
    assert "1 prohibida" in html
    assert 'name="viewport"' in html and f"TermCheck {VERSION}" in html


def test_resaltar_no_pisa_tramos_y_saltea_los_no_encontrados():
    texto = "uno dos tres"
    salida = resaltar(texto, [(0, 7, "OK", "a"), (4, 7, "VARIANTE", "b"), (-1, -1, "NO_ENCONTRADO", "c")])
    import re
    from html import unescape
    assert unescape(re.sub(r"<[^>]+>", "", salida)) == texto
    assert 'title="a · b"' in salida


def test_run_check_con_src_y_tgt(tmp_path):
    (tmp_path / "g.csv").write_text(
        "id,en,pos,es_preferred,es_allowed,es_forbidden,subdomain,note,source\n"
        "G1,drilling rig|rig,NOUN,equipo de perforación,equipo,plataforma de perforación,,,inventado\n",
        encoding="utf-8")
    (tmp_path / "en.txt").write_text("Move the rig.\nStop the rig.\n", encoding="utf-8")
    (tmp_path / "es.txt").write_text("Mueva el equipo.\nDetenga la plataforma de perforación.\n", encoding="utf-8")
    orden = [sys.executable, str(RAIZ / "scripts/run_check.py"), "--glossary", str(tmp_path / "g.csv"),
             "--src", str(tmp_path / "en.txt"), "--tgt", str(tmp_path / "es.txt"), "--out", str(tmp_path / "rep")]
    r = subprocess.run(orden, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "2 traducciones · 2 apariciones" in r.stdout
    with open(tmp_path / "rep.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert [(f["seg_id"], f["label"]) for f in filas] == [("L0001", "VARIANTE"), ("L0002", "PROHIBIDO")]
    assert [(f["source_en"], f["target_es"]) for f in filas] == [
        ("Move the rig.", "Mueva el equipo."),
        ("Stop the rig.", "Detenga la plataforma de perforación.")]
    assert "<mark" in (tmp_path / "rep.html").read_text(encoding="utf-8")


def test_run_check_avisa_si_las_lineas_no_coinciden(tmp_path):
    (tmp_path / "g.csv").write_text(
        "id,en,pos,es_preferred,es_allowed,es_forbidden,subdomain,note,source\nG1,rig,NOUN,equipo,,,,,x\n",
        encoding="utf-8")
    (tmp_path / "en.txt").write_text("Move the rig.\nStop the rig.\n", encoding="utf-8")
    (tmp_path / "es.txt").write_text("Mueva el equipo.\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(RAIZ / "scripts/run_check.py"), "--glossary", str(tmp_path / "g.csv"),
                        "--src", str(tmp_path / "en.txt"), "--tgt", str(tmp_path / "es.txt"),
                        "--out", str(tmp_path / "rep")], capture_output=True, text=True)
    assert r.returncode != 0 and "misma cantidad de líneas" in r.stderr
    assert not (tmp_path / "rep.csv").exists()


def test_superposicion_conserva_la_advertencia_y_el_texto():
    import re
    from html import unescape
    texto = "pozo de petróleo o gas"
    salida = resaltar(texto, [(0, 16, "OK", "oil well"), (0, len(texto), "PROHIBIDO", "gas well")])
    assert unescape(re.sub(r"<[^>]+>", "", salida)) == texto
    assert 'class="tc-prohibido"' in salida and "oil well · gas well" in salida


def test_reporte_agrupa_repeticiones_sin_perder_las_filas_csv():
    from termcheck.report import bloque_segmento
    oc = verificar("Move the rig and stop the rig.", "Mueva el equipo y detenga el equipo.", GLOSARIO)
    pieza = bloque_segmento("Move the rig and stop the rig.", "Mueva el equipo y detenga el equipo.", oc)
    assert "rig, 2 veces" in pieza
    assert len(list(csv.DictReader(io.StringIO(a_csv_texto(oc))))) == 2


def test_csv_asocia_contextos_por_segmento_y_sistema():
    pares = [("S1", "mt-a", "Move the rig.", "Mueva el equipo."),
             ("S1", "mt-b", "Move the rig.", "Mueva la plataforma de perforación.")]
    ocurrencias = [o for seg, system, en, es in pares for o in verificar(en, es, GLOSARIO, seg, system)]
    contextos = {(seg, system): (en, es) for seg, system, en, es in pares}
    filas = list(csv.DictReader(io.StringIO(a_csv_texto(ocurrencias, contextos))))
    assert [(f["system"], f["target_es"]) for f in filas] == [
        ("mt-a", "Mueva el equipo."), ("mt-b", "Mueva la plataforma de perforación.")]
    html = a_html({"S1": pares[0][2]},
                  [{"seg_id": seg, "system": system, "target_es": es} for seg, system, _, es in pares],
                  ocurrencias)
    import re
    from html import unescape
    texto_html = unescape(re.sub(r"<[^>]+>", "", html))
    assert "Mueva el equipo." in texto_html and "Mueva la plataforma de perforación." in texto_html
    assert 'tc-variante' in html and 'tc-prohibido' in html


def test_filtro_muestra_solo_los_detalles_para_revisar():
    from termcheck.report import bloque_segmento
    en, es = "Move the rig to the wellhead.", "Mueva la plataforma de perforación a la boca de pozo."
    oc = verificar(en, es, GLOSARIO)
    pieza = bloque_segmento(en, es, oc, solo=True)
    assert "Prohibida. Preferida:" in pieza
    assert "Preferida.</td>" not in pieza
