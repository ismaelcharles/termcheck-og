"""Pruebas de app/anotacion.py: detección de términos en inglés, orden a ciegas y guardado.

Usan archivos propios en una carpeta temporal: no tocan los datos reales.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))
import anotacion as an  # noqa: E402

TERMINOS = [{"id": "T1", "en": ["casing"]}, {"id": "T2", "en": ["casing shoe"]},
            {"id": "T3", "en": ["blowout preventer", "BOP"]}, {"id": "T4", "en": ["flowline", "flow line"]}]


def test_detecta_plural_mayusculas_y_guion():
    aps = an.apariciones("Inspect the Flow-Lines and the BOPs.", TERMINOS)
    assert [(a["id"], a["forma"]) for a in aps] == [("T4", "Flow-Lines"), ("T3", "BOPs")]


def test_no_detecta_dentro_de_palabra():
    assert an.apariciones("The encasing was fine.", TERMINOS) == []


def test_termino_dentro_de_otro_se_lista_y_se_marca():
    aps = an.apariciones("Set the casing shoe.", TERMINOS)
    assert [a["id"] for a in aps] == ["T2", "T1"]
    corto = next(a for a in aps if a["id"] == "T1")
    assert an.dentro_de_otro(corto, aps) and not an.dentro_de_otro(aps[0], aps)


def test_cuenta_veces_sin_repetir_formas():
    aps = an.apariciones("The BOP and the blowout preventer; the BOP again.", TERMINOS)
    assert aps[0]["id"] == "T3" and aps[0]["veces"] == 3


def test_orden_ciego_estable_y_completo():
    assert an.orden_ciego("S001") == an.orden_ciego("S001")
    assert sorted(s for _, s in an.orden_ciego("S001")) == sorted(an.SISTEMAS)
    ordenes = {tuple(s for _, s in an.orden_ciego(f"S{i:03d}")) for i in range(1, 30)}
    assert len(ordenes) > 1


@pytest.fixture
def carpeta(tmp_path, monkeypatch):
    (tmp_path / "dev.txt").write_text("S001\nS002\n")
    monkeypatch.setattr(an, "DEV", tmp_path / "dev.txt")
    monkeypatch.setattr(an, "DEV_ANOTAR", tmp_path / "no-existe.txt")
    (tmp_path / "prueba.txt").write_text("S050\n")
    monkeypatch.setattr(an, "PRUEBA", tmp_path / "prueba.txt")
    monkeypatch.setattr(an, "CARPETA", tmp_path / "ann")
    monkeypatch.setattr(an, "GOLD", tmp_path / "ann" / "gold.csv")
    monkeypatch.setattr(an, "DESCARTES", tmp_path / "ann" / "descartes.csv")
    return tmp_path


def test_guardar_reemplaza_y_separa_descartes(carpeta):
    an.guardar("S001", "deepl", [{"term_id": "T1", "label": "CORRECTO", "es_used": "casing"},
                                 {"term_id": "T2", "label": an.NO_VA, "comment": "dentro de otro"}])
    an.guardar("S001", "deepl", [{"term_id": "T1", "label": "ERROR_TERMINO", "es_used": "carcasa"},
                                 {"term_id": "T2", "label": an.NO_VA}])
    gold = an.leer_csv(an.GOLD)
    assert gold == [{"seg_id": "S001", "system": "deepl", "term_id": "T1", "label": "ERROR_TERMINO",
                     "es_used": "carcasa", "comment": ""}]
    assert [f["term_id"] for f in an.leer_csv(an.DESCARTES)] == ["T2"]
    assert an.anotadas()[("S001", "deepl", "T2")]["label"] == an.NO_VA


def test_guardar_rechaza_fuera_de_desarrollo(carpeta):
    with pytest.raises(ValueError):
        an.guardar("S099", "deepl", [{"term_id": "T1", "label": "CORRECTO"}])
    with pytest.raises(ValueError):
        an.guardar("S001", "deepl", [{"term_id": "T1", "label": "OK"}])
    with pytest.raises(ValueError):
        an.guardar("S001", "google", [{"term_id": "T1", "label": "CORRECTO"}])


def test_palabras_y_forma_ida_y_vuelta():
    lista = an.palabras("Lubricar el bloque de la corona, y la unión giratoria.")
    assert lista[:3] == ["Lubricar", "el", "bloque"] and "," not in lista
    idx = an.indices_de("bloque de la corona", lista)
    assert an.forma(lista, idx) == "bloque de la corona"
    assert an.forma(lista, [9, 8]) == "unión giratoria"
    assert an.indices_de("bloque móvil", lista) == []


def test_guardar_uno_cambia_solo_esa_celda(carpeta):
    an.guardar("S001", "deepl", [{"term_id": "T1", "label": "CORRECTO", "es_used": "casing"},
                                 {"term_id": "T2", "label": "CORRECTO", "es_used": "zapato"}])
    an.guardar_uno("S001", "deepl", "T2", "ERROR_TERMINO", "zapato", "mal")
    an.guardar_uno("S001", "claude", "T2", an.NO_VA)
    hechas = an.anotadas()
    assert hechas[("S001", "deepl", "T1")]["label"] == "CORRECTO"
    assert hechas[("S001", "deepl", "T2")]["label"] == "ERROR_TERMINO"
    assert hechas[("S001", "deepl", "T2")]["comment"] == "mal"
    assert hechas[("S001", "claude", "T2")]["label"] == an.NO_VA
    an.guardar_uno("S001", "claude", "T2", None)
    assert ("S001", "claude", "T2") not in an.anotadas()
    with pytest.raises(ValueError):
        an.guardar_uno("S099", "deepl", "T1", "CORRECTO")


def test_conjuntos_y_prueba_se_puede_anotar(carpeta):
    assert an.ids_conjunto("desarrollo") == ["S001", "S002"]  # sin recorte: todo dev
    assert an.ids_conjunto("prueba") == ["S050"]
    an.guardar_uno("S050", "deepl", "T1", "CORRECTO")
    assert an.anotadas()[("S050", "deepl", "T1")]["label"] == "CORRECTO"


def test_completar_correcto_no_pisa_lo_anotado(carpeta):
    an.guardar_uno("S001", "deepl", "T1", "ERROR_TERMINO", "carcasa")
    an.guardar_uno("S001", "claude", "T1", an.NO_VA)
    n = an.completar_correcto("S001", [(s, "T1") for s in an.SISTEMAS] + [("deepl", "T2")])
    hechas = an.anotadas()
    assert n == 2
    assert hechas[("S001", "deepl", "T1")]["label"] == "ERROR_TERMINO"
    assert hechas[("S001", "claude", "T1")]["label"] == an.NO_VA
    assert hechas[("S001", "opusmt", "T1")]["label"] == "CORRECTO"
    assert hechas[("S001", "deepl", "T2")]["label"] == "CORRECTO"
    assert an.completar_correcto("S001", [("deepl", "T2")]) == 0
    with pytest.raises(ValueError):
        an.completar_correcto("S099", [("deepl", "T1")])
