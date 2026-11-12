"""Pruebas de la prueba de coherencia con errores sintéticos (plan 6.4): scripts/inject_errors.py.

Usan el proyecto inventado de tests/conftest.py, en una carpeta temporal. No leen los datos reales.

Correr:  .venv/bin/python -m pytest tests/test_inject_errors.py -v
"""
import importlib

from conftest import ANOTACION_DEV, anotar


def _modulo():
    import inject_errors
    return importlib.reload(inject_errors)   # para que tome la carpeta del proyecto inventado


def _glosario(proyecto):
    from termcheck.glossary import cargar
    return cargar(proyecto / "data/glossary/glossary_en_es.csv")


def test_reemplazar_y_borrar():
    ie = _modulo()
    assert ie.reemplazar("Mueva el equipo de perforación.", [(9, 30)], "rig") == "Mueva el rig."
    assert ie.reemplazar("Mueva el equipo de perforación.", [(9, 30)], "") == "Mueva el."
    assert ie.reemplazar("El equipo y el equipo.", [(3, 9), (15, 21)], "X") == "El X y el X."


def test_detecta_los_tres_errores_puestos(proyecto):
    ie = _modulo()
    anotar(ANOTACION_DEV)   # D1: claude y deepl «Correcto» (parten de ahí); opusmt es un error real y no se usa
    casos, salteados = ie.inyectar(_glosario(proyecto))
    assert len(casos) == 6 and salteados == {"prohibida": 0, "inglés": 0, "borrado": 0}
    assert {c["system"] for c in casos} == {"claude", "deepl"}
    assert all(c["detectado"] == "sí" for c in casos)
    assert all(c["etiqueta_verificador"] == c["etiqueta_esperada"] for c in casos)
    claude = {c["tipo"]: c["target_modificado"] for c in casos if c["system"] == "claude"}
    assert claude == {"prohibida": "Mueva el plataforma de perforación.", "inglés": "Mueva el drilling rig.",
                      "borrado": "Mueva el."}


def test_saltea_lo_que_no_seria_un_error(proyecto):
    """«casing» acepta la forma inglesa y no tiene prohibidas: solo se le puede borrar."""
    ie = _modulo()
    with open(proyecto / "data/corpus/segments.tsv", "a", encoding="utf-8") as f:
        f.write("D2\tRun the casing.\thttps://example.org\n")
    with open(proyecto / "data/mt/translations.tsv", "a", encoding="utf-8") as f:
        f.write("D2\tclaude\tBaje la cañería.\n")
    (proyecto / "data/splits/dev_ids.txt").write_text("D1\nD2\n", encoding="utf-8")
    anotar({("D2", "claude", "G2"): "CORRECTO"})
    casos, salteados = ie.inyectar(_glosario(proyecto))
    assert [(c["tipo"], c["detectado"], c["etiqueta_verificador"]) for c in casos] == [("borrado", "sí", "NO_ENCONTRADO")]
    assert salteados == {"prohibida": 1, "inglés": 1, "borrado": 0}


def test_no_usa_la_prueba(proyecto):
    ie = _modulo()
    from conftest import ANOTACION_PRUEBA
    anotar(ANOTACION_PRUEBA)   # solo hay anotación de prueba: no hay de dónde partir
    assert ie.inyectar(_glosario(proyecto)) == ([], {"prohibida": 0, "inglés": 0, "borrado": 0})


def test_el_informe_va_marcado_como_sintetico(proyecto):
    ie = _modulo()
    anotar(ANOTACION_DEV)
    texto = ie.escribir(*ie.inyectar(_glosario(proyecto)))
    assert "Resultado sintético" in texto and "No mide el recall real" in texto
    assert "| prohibida (PROHIBIDO) | 2 | 2 |" in texto
    assert (proyecto / "salida/estres.md").read_text(encoding="utf-8") == texto
    assert len((proyecto / "salida/estres_casos.csv").read_text(encoding="utf-8").splitlines()) == 7
