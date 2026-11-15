"""Las páginas abren sin notas locales ni material privado del glosario.

Usa solo el proyecto inventado de conftest, nunca la prueba real.
"""
from pathlib import Path
import importlib
import pytest
from streamlit.testing.v1 import AppTest
from conftest import ANOTACION_DEV, anotar

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("pagina", ["inicio", "verificar", "glosario", "traducciones", "anotar", "resultados"])
def test_paginas_sin_archivos_privados(proyecto, monkeypatch, pagina):
    import candidatos
    import originales
    importlib.reload(candidatos)
    monkeypatch.setenv("TERMCHECK_DEMO", "0")
    monkeypatch.setenv("TERMCHECK_SIN_LOGIN", "1")
    monkeypatch.setattr(originales, "CARPETA", proyecto / "data/originales")
    anotar(ANOTACION_DEV)
    at = AppTest.from_file(str(RAIZ / "app/streamlit_app.py"), default_timeout=120)
    at.run()
    if pagina != "inicio":
        at.switch_page(f"paginas/{pagina}.py").run()
    assert not at.exception, at.exception


@pytest.mark.parametrize("modo", ["candidatos", "fuentes", "tabla", "agregar"])
def test_glosario_sin_catalogos_privados(proyecto, monkeypatch, modo):
    import candidatos
    import originales
    importlib.reload(candidatos)
    monkeypatch.setattr(originales, "CARPETA", proyecto / "data/originales")
    at = AppTest.from_file(str(RAIZ / "app/paginas/glosario.py"), default_timeout=120)
    at.session_state["vista_glosario"] = modo
    at.run()
    assert not at.exception, at.exception
