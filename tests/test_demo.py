"""Pruebas de la demo pública (app/demo.py): abre sin login, verifica el ejemplo y respeta los límites.

El ejemplo usa tres oraciones del conjunto de desarrollo. No se lee la prueba.

Correr:  .venv/bin/python -m pytest tests/test_demo.py -v
"""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

DEMO = str(Path(__file__).resolve().parent.parent / "app/demo.py")


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setenv("TERMCHECK_DEMO", "1")      # al terminar la prueba, la variable se borra
    monkeypatch.delenv("TERMCHECK_SIN_LOGIN", raising=False)
    at = AppTest.from_file(DEMO, default_timeout=120)
    at.run()
    assert not at.exception, at.exception
    return at


def test_abre_sin_login_y_sin_corpus(demo):
    assert not [b for b in demo.button if "Google" in b.label]
    assert any("Demo pública" in c.value for c in demo.caption)
    assert any("Reporte" in s.value for s in demo.subheader)  # ejemplo precargado
    assert demo.text_area[0].proto.max_chars == 20000


def test_el_ejemplo_muestra_un_reporte(demo):
    [b for b in demo.button if "ejemplo" in b.label][0].click().run()
    assert not demo.exception, demo.exception
    assert any("Reporte" in s.value for s in demo.subheader)
    assert any("términos encontrados en 3 segmentos" in m.value for m in demo.markdown)


def test_corta_en_el_maximo_de_segmentos(demo):
    demo.text_area[0].set_value("\n".join(["Check the wellhead."] * 201))
    demo.text_area[1].set_value("\n".join(["Revise la boca de pozo."] * 201))
    [b for b in demo.button if b.label == "Verificar"][0].click().run()
    assert not demo.exception, demo.exception
    assert any("verifica los primeros 200" in w.value for w in demo.warning)
    assert any("en 200 segmentos" in m.value for m in demo.markdown)


def test_el_cuadro_de_texto_corta_en_el_maximo_de_letras(demo):
    largo = "\n".join(["The drilling rig was moved to the new location near the wellhead again. " * 3] * 150)
    demo.text_area[0].set_value(largo)
    demo.text_area[1].set_value(largo)
    [b for b in demo.button if b.label == "Verificar"][0].click().run()
    assert not demo.exception, demo.exception
    assert len(largo) > 20000 and len(demo.text_area[0].value) == 20000


def test_limites_de_un_archivo():
    """Un archivo no pasa por el cuadro de texto: el largo total se revisa aparte."""
    import limites
    cortos = [(f"F{i}", "", "Check the wellhead.", "Revise la boca de pozo.") for i in range(250)]
    pares, aviso, seguir = limites.aplicar(cortos)
    assert len(pares) == 200 and "primeros 200" in aviso and seguir
    largos = [(f"F{i}", "", "x" * 500, "y" * 500) for i in range(50)]
    pares, aviso, seguir = limites.aplicar(largos)
    assert pares == [] and "demasiado largo" in aviso and not seguir
    assert limites.aplicar(cortos[:3]) == (cortos[:3], "", True)


def test_vaciar_y_verificar_solo_al_pedirlo(demo, monkeypatch):
    import termcheck.checker as checker
    llamadas = []
    original = checker.verificar
    def contar(*args, **kwargs):
        llamadas.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(checker, "verificar", contar)
    [b for b in demo.button if b.label == "Vaciar"][0].click().run()
    assert not any("Reporte" in s.value for s in demo.subheader)
    demo.text_area[0].set_value("Check the wellhead.")
    demo.text_area[1].set_value("Revise la boca de pozo.")
    assert not llamadas
    [b for b in demo.button if b.label == "Verificar"][0].click().run()
    assert len(llamadas) == 1 and not demo.exception
    demo.checkbox[0].check().run()
    assert len(llamadas) == 1 and not demo.exception
