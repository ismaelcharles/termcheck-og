"""Ensayo del camino que le queda al dueño, de punta a punta, con el proyecto inventado de tests/conftest.py:

    anotar la prueba → congelar el glosario v1 → «Calcular la evaluación final» → tablas y casos guardados

Corre la página Resultados de verdad (AppTest de Streamlit), sobre una carpeta temporal. No toca la anotación
real ni lee la prueba real.

Correr:  .venv/bin/python -m pytest tests/test_camino_final.py -v
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from conftest import ANOTACION_DEV, ANOTACION_PRUEBA, anotar

PAGINA = str(Path(__file__).resolve().parent.parent / "app/paginas/resultados.py")


def abrir(vista):
    at = AppTest.from_file(PAGINA, default_timeout=120)
    at.session_state["res_vista"] = vista
    at.run()
    assert not at.exception, at.exception
    return at


def boton(at, texto):
    return [b for b in at.button if texto in b.label]


def test_camino_final_completo(proyecto):
    congelado = proyecto / "data/glossary/glossary_v1.csv"
    anotar(ANOTACION_DEV)

    # 1. Sin glosario congelado, la prueba no se puede evaluar
    at = abrir("prueba")
    assert any("congelá el glosario" in w.value for w in at.warning)
    assert not boton(at, "Calcular la evaluación final")

    # 2. Congelar: primero la casilla, después el botón
    at = abrir("sug")
    assert boton(at, "Congelar glosario v1")[0].disabled
    at.checkbox[0].check().run()
    boton(at, "Congelar glosario v1")[0].click().run()
    assert not at.exception, at.exception
    assert congelado.read_bytes() == (proyecto / "data/glossary/glossary_en_es.csv").read_bytes()
    assert "4 términos" in (proyecto / "data/glossary/glossary_v1.txt").read_text(encoding="utf-8")

    # 3. Con la prueba a medio anotar, el botón final todavía no aparece
    mitad = dict(list(ANOTACION_PRUEBA.items())[:5])
    anotar(mitad)
    at = abrir("prueba")
    assert not boton(at, "Calcular la evaluación final")

    # 4. Con la prueba entera (los «No va» cuentan como anotados), aparece y calcula
    anotar(ANOTACION_PRUEBA)
    at = abrir("prueba")
    boton(at, "Calcular la evaluación final")[0].click().run()
    assert not at.exception, at.exception
    md = (proyecto / "salida/eval_prueba.md").read_text(encoding="utf-8")
    assert "| TermCheck | 9 | 3 | 1 | 0 | 5 |" in md
    assert "| Baseline (texto exacto) | 9 | 3 | 3 | 0 | 3 |" in md
    casos = (proyecto / "salida/eval_prueba_casos.csv").read_text(encoding="utf-8")
    assert casos.count("\n") == 2 and "FP,P1,deepl,G3" in casos       # encabezado + el único falso positivo
    assert any("TermCheck" in m.value for m in at.markdown)           # la tabla se ve en la página


def test_la_evaluacion_final_usa_el_glosario_congelado(proyecto):
    """Si el glosario de trabajo cambia después de congelar, el resultado de la prueba no cambia."""
    import evaluate as ev
    anotar(ANOTACION_PRUEBA)
    at = abrir("sug")
    at.checkbox[0].check().run()
    boton(at, "Congelar glosario v1")[0].click().run()
    trabajo = proyecto / "data/glossary/glossary_en_es.csv"
    # después de congelar, alguien agrega «cabeza del pozo» como válida en el glosario de trabajo
    trabajo.write_text(trabajo.read_text(encoding="utf-8").replace("G3,wellhead,NOUN,boca de pozo,,",
                                                                   "G3,wellhead,NOUN,boca de pozo,cabeza del pozo,"),
                       encoding="utf-8")
    at = abrir("prueba")
    boton(at, "Calcular la evaluación final")[0].click().run()
    assert not at.exception, at.exception
    assert "| TermCheck | 9 | 3 | 1 | 0 | 5 |" in (proyecto / "salida/eval_prueba.md").read_text(encoding="utf-8")
    # con el glosario de trabajo, en cambio, ese falso positivo desaparece
    v = ev.metricas([(c["error_gold"], c["marca_verificador"]) for c in ev.evaluar("prueba", trabajo)])
    assert v["FP"] == 0


def test_las_vistas_de_resultados_abren_sin_errores(proyecto):
    anotar(ANOTACION_DEV)
    for vista in ("sug", "dev", "prueba", "pub"):
        abrir(vista)
