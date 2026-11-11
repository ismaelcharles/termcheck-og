"""Pruebas de la evaluación (plan 6.1 y 6.2): baseline.py y evaluate.py.

Usan el proyecto inventado de tests/conftest.py, en una carpeta temporal. No leen los datos reales.

Correr:  .venv/bin/python -m pytest tests/test_evaluacion.py -v
"""
import csv
import sys

import pytest

from conftest import ANOTACION_DEV, ANOTACION_PRUEBA, anotar


def test_baseline_solo_reconoce_la_preferida_exacta():
    from baseline import marca
    assert marca("Saque las tuberías de producción.", "tubería de producción")       # plural: no la reconoce
    assert not marca("Saque la Tubería de Producción.", "tubería de producción")      # mayúsculas: sí
    assert marca("", "pozo") and marca(None, "pozo")                                  # sin traducción: marca


def test_metricas_cuenta_los_cuatro_casos(proyecto):
    import evaluate as ev
    # (es error según la anotación, lo marcó la herramienta)
    pares = [(True, True)] * 3 + [(False, True)] * 1 + [(True, False)] * 2 + [(False, False)] * 4
    m = ev.metricas(pares)
    assert (m["TP"], m["FP"], m["FN"], m["TN"], m["n"]) == (3, 1, 2, 4, 10)
    assert m["precision"] == pytest.approx(3 / 4)
    assert m["recall"] == pytest.approx(3 / 5)
    assert m["f1"] == pytest.approx(2 * 0.75 * 0.6 / (0.75 + 0.6))


def test_metricas_sin_casos_no_divide_por_cero(proyecto):
    import evaluate as ev
    m = ev.metricas([])
    assert (m["precision"], m["recall"], m["f1"]) == (0.0, 0.0, 0.0)


def test_wilson(proyecto):
    import evaluate as ev
    assert ev.wilson(0, 0) == (0.0, 0.0)
    bajo, alto = ev.wilson(8, 10)                       # valores conocidos del intervalo de Wilson al 95 %
    assert bajo == pytest.approx(0.490, abs=0.002) and alto == pytest.approx(0.943, abs=0.002)
    bajo, alto = ev.wilson(10, 10)                      # con todo acertado, el techo es 1 y el piso no
    assert alto == pytest.approx(1.0) and 0.6 < bajo < 0.8


def test_evaluar_la_prueba_inventada(proyecto):
    import evaluate as ev
    anotar(ANOTACION_DEV)
    anotar(ANOTACION_PRUEBA)
    casos = ev.evaluar("prueba")
    assert len(casos) == 9                              # los tres «No va» no cuentan
    assert {c["seg_id"] for c in casos} == {"P1", "P2"}  # nada de desarrollo
    v = ev.metricas([(c["error_gold"], c["marca_verificador"]) for c in casos])
    b = ev.metricas([(c["error_gold"], c["marca_baseline"]) for c in casos])
    assert (v["TP"], v["FP"], v["FN"], v["TN"]) == (3, 1, 0, 5)
    assert (b["TP"], b["FP"], b["FN"], b["TN"]) == (3, 3, 0, 3)
    por_clave = {(c["seg_id"], c["system"], c["term_id"]): c for c in casos}
    assert por_clave[("P2", "opusmt", "G1")]["etiquetas_verificador"] == "PROHIBIDO"
    assert por_clave[("P1", "opusmt", "G3")]["etiquetas_verificador"] == "SIN_TRADUCIR"
    assert por_clave[("P2", "claude", "G1")]["etiquetas_verificador"] == "VARIANTE"


def test_evaluar_desarrollo_no_mezcla_la_prueba(proyecto):
    import evaluate as ev
    anotar(ANOTACION_DEV)
    anotar(ANOTACION_PRUEBA)
    assert {c["seg_id"] for c in ev.evaluar("desarrollo")} == {"D1"}


def test_escribir_guarda_tablas_y_casos(proyecto):
    import evaluate as ev
    anotar(ANOTACION_PRUEBA)
    texto, v, b = ev.escribir(ev.evaluar("prueba"), "prueba")
    md = (proyecto / "salida/eval_prueba.md").read_text(encoding="utf-8")
    assert md == texto
    assert "| TermCheck | 9 | 3 | 1 | 0 | 5 |" in md
    assert "| Baseline (texto exacto) | 9 | 3 | 3 | 0 | 3 |" in md
    with open(proyecto / "salida/eval_prueba_casos.csv", encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    assert [(f["tipo"], f["seg_id"], f["system"], f["term_id"]) for f in filas] == [("FP", "P1", "deepl", "G3")]
    assert filas[0]["target_es"] == "Inspeccione la cabeza del pozo."


def test_la_prueba_no_se_evalua_sin_glosario_congelado(proyecto, monkeypatch):
    import evaluate as ev
    anotar(ANOTACION_PRUEBA)
    monkeypatch.setattr(sys, "argv", ["evaluate.py", "--conjunto", "prueba"])
    with pytest.raises(SystemExit) as error:
        ev.main()
    assert "congelado" in str(error.value)
    assert not (proyecto / "salida").exists()


def test_evaluate_usa_la_misma_carpeta_de_anotacion_que_la_app(proyecto):
    import anotacion as an
    import evaluate as ev
    assert ev.ANOTACIONES == an.CARPETA
    assert str(ev.ANOTACIONES).startswith(str(proyecto))
