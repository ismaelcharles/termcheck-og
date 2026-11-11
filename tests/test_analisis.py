"""Pruebas de las herramientas para el análisis de errores: la causa sugerida de cada FP y FN (evaluate.py) y el
acuerdo entre anotadores (scripts/kappa.py).

Todos los casos son inventados. Las reglas para los falsos negativos solo se probaron así: en la anotación de
desarrollo no hubo ninguno.

Correr:  .venv/bin/python -m pytest tests/test_analisis.py -v
"""
import csv
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ANOTACION_PRUEBA, anotar

RAIZ = Path(__file__).resolve().parent.parent


def caso(**cambios):
    base = {"term_id": "G1", "label": "CORRECTO", "error_gold": False, "detectado": True, "es_used": "",
            "etiquetas_verificador": "NO_ENCONTRADO", "es_found": "", "sugerencia": "",
            "source_en": "Move the drilling rig.", "target_es": ""}
    return {**base, **cambios}


@pytest.fixture
def terminos(proyecto):
    import evaluate as ev
    return ev.cargar(ev.GLOSARIO)


def causa(terminos, **cambios):
    import evaluate as ev
    return ev.causa_sugerida(caso(**cambios), terminos)


# --- Falsos positivos: anotado Correcto, el verificador marcó ---

def test_fp_que_quedo_en_ingles_es_prestamo(terminos):
    assert causa(terminos, term_id="G3", etiquetas_verificador="SIN_TRADUCIR", es_found="wellhead").startswith(
        "préstamo")


def test_fp_con_forma_prohibida_es_ambiguedad(terminos):
    c = causa(terminos, etiquetas_verificador="PROHIBIDO", es_found="plataforma de perforación")
    assert c.startswith("ambigüedad") and "«plataforma de perforación»" in c


def test_fp_parecido_a_una_forma_valida_es_morfologia(terminos):
    assert causa(terminos, sugerencia="equipos de perforacion").startswith("morfología: «equipos de perforacion»")
    assert causa(terminos, term_id="G3", es_used="bocas de pozo").startswith("morfología: «bocas de pozo»")


def test_fp_sin_parecido_es_sinonimo_que_falta(terminos):
    assert causa(terminos, term_id="G3", es_used="cabezal") == (
        "sinónimo que falta: se usó «cabezal» y el glosario no lo lista")
    assert causa(terminos, term_id="G3").startswith("sinónimo que falta: la traducción usó")


# --- Falsos negativos: anotado como error, el verificador no marcó ---

def test_fn_de_un_termino_dentro_de_otro(terminos):
    c = causa(terminos, term_id="G2", label="ERROR_TERMINO", error_gold=True, detectado=False,
              etiquetas_verificador="", source_en="Run the casing string near the rig.")
    assert c == "término dentro de otro: «casing» quedó dentro de «casing string»"


def test_fn_no_detectado_en_el_ingles(terminos):
    c = causa(terminos, term_id="G3", label="OMISION", error_gold=True, detectado=False, etiquetas_verificador="",
              source_en="Inspect the well head assembly.")
    assert c.startswith("término no detectado en el inglés")


def test_fn_con_la_forma_inglesa_aceptada_es_prestamo(terminos):
    c = causa(terminos, term_id="G2", label="SIN_TRADUCIR", error_gold=True, etiquetas_verificador="OK",
              es_found="casing")
    assert c == "préstamo: el glosario acepta «casing» y se anotó Sin traducir"


def test_fn_con_forma_valida_es_ambiguedad_o_error_de_anotacion(terminos):
    c = causa(terminos, label="ERROR_TERMINO", error_gold=True, etiquetas_verificador="VARIANTE", es_found="equipo")
    assert c.startswith("ambigüedad") and "Error de término" in c and "error de la anotación" in c
    assert "Omisión" in causa(terminos, label="OMISION", error_gold=True, etiquetas_verificador="OK",
                              es_found="equipo de perforación")


def test_termino_que_ya_no_esta_en_el_glosario(terminos):
    assert causa(terminos, term_id="NOEXISTE") == "el término ya no está en el glosario"


def test_el_archivo_de_casos_trae_la_pista_y_la_columna_causa_vacia(proyecto):
    import evaluate as ev
    anotar(ANOTACION_PRUEBA)
    casos = ev.evaluar("prueba")
    ev.escribir(casos, "prueba")
    with open(proyecto / "salida/eval_prueba_casos.csv", encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        filas = list(lector)
    assert lector.fieldnames[-2:] == ["causa_sugerida", "causa"]
    assert len(filas) == 1 and filas[0]["causa_sugerida"] and filas[0]["causa"] == ""
    # Los casos en que el verificador y la anotación coinciden no llevan pista
    assert all(not c["causa_sugerida"] for c in casos if c["error_gold"] == c["marca_verificador"])


# --- Kappa ---

def fila(seg, etiqueta, sistema="claude", termino="G1"):
    return {"seg_id": seg, "system": sistema, "term_id": termino, "label": etiqueta}


def test_kappa_con_un_ejemplo_hecho_a_mano(proyecto):
    import kappa as k
    # 10 casos: 4 sí-sí, 1 sí-no, 1 no-sí, 4 no-no → observado 0,8; azar 0,5; kappa 0,6
    pares = [(True, True)] * 4 + [(True, False)] + [(False, True)] + [(False, False)] * 4
    observado, valor = k.kappa(pares)
    assert observado == pytest.approx(0.8) and valor == pytest.approx(0.6)


def test_kappa_acuerdo_total_y_casos_sin_calculo(proyecto):
    import kappa as k
    assert k.kappa([("A", "A"), ("B", "B")]) == (1.0, 1.0)
    assert k.kappa([]) == (0.0, None)
    assert k.kappa([("A", "A"), ("A", "A")]) == (1.0, None)     # una sola etiqueta: no se puede calcular


def test_comparar_usa_solo_lo_que_anotaron_los_dos(proyecto):
    import kappa as k
    gold = [fila("S1", "CORRECTO"), fila("S2", "ERROR_TERMINO"), fila("S3", "OMISION"), fila("S4", "CORRECTO")]
    otro = [fila("S1", "CORRECTO"), fila("S2", "SIN_TRADUCIR"), fila("S3", "CORRECTO"), fila("S9", "CORRECTO")]
    r = k.comparar(gold, otro)
    assert (r["n"], r["solo_primero"], r["solo_segundo"]) == (3, 1, 1)
    assert [d[0][0] for d in r["desacuerdos"]] == ["S2", "S3"]
    # Con dos etiquetas, S2 pasa a ser acuerdo (los dos dicen que es un error)
    assert r["cuatro"][0] == pytest.approx(1 / 3) and r["dos"][0] == pytest.approx(2 / 3)
    assert k.comparar(gold, otro, ids={"S1"})["n"] == 1
    assert "Términos anotados por los dos: 3" in k.texto(r)


def test_kappa_desde_la_terminal(proyecto):
    anotar(ANOTACION_PRUEBA)
    segundo = proyecto / "segundo.csv"
    segundo.write_text((proyecto / "data/annotations/gold.csv").read_text(encoding="utf-8"), encoding="utf-8")
    r = subprocess.run([sys.executable, str(RAIZ / "scripts/kappa.py"), str(segundo), "--conjunto", "prueba"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "Términos anotados por los dos: 9" in r.stdout and "kappa 1,00" in r.stdout
    r = subprocess.run([sys.executable, str(RAIZ / "scripts/kappa.py"), str(proyecto / "noexiste.csv")],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "No existe" in r.stderr
