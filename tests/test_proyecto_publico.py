"""La portada informa la prueba histórica sin atribuirla a la edición actual."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

from proyecto_publico import resultados_publicados

RAIZ = Path(__file__).resolve().parent.parent


def test_metricas_usan_la_evaluacion_independiente_de_01():
    datos = resultados_publicados()
    assert datos['TermCheck'] == dict(n=120, tp=49, fp=7, fn=4, tn=60)
    assert datos['Baseline (texto exacto)'] == dict(n=120, tp=52, fp=18, fn=1, tn=49)


def test_resultados_y_metodo_siguen_visibles_despues_de_verificar(proyecto):
    at = AppTest.from_file(str(RAIZ / 'app/demo.py'), default_timeout=120).run()
    for revisar in (False, True):
        if revisar:
            at.text_area[0].set_value('Inspect the wellhead.')
            at.text_area[1].set_value('Inspeccione la boca de pozo.')
            next(b for b in at.button if b.label == 'Verificar').click().run()
        assert not at.exception
        html = ''.join(m.proto.body for m in at.get('html'))
        assert '49 de 53' in html and '88 %' in html
        assert 'Cómo funciona por dentro' in html
        assert 'no se evaluó contra un LLM usado como revisor' in html
        assert 'no estiman el rendimiento' in html
        assert 'edición actual todavía no tiene una evaluación independiente' in html
