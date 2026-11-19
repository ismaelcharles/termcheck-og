"""Los ejemplos públicos contrastan decisiones reales y la selección conserva la sesión."""
from pathlib import Path

from streamlit.testing.v1 import AppTest
import pytest

from presentacion import EJEMPLOS
from termcheck.checker import verificar
from termcheck.glossary import cargar

RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=lambda ej: ej["en"])
def test_contraste_con_glosario_publicado(ejemplo):
    terminos = cargar(RAIZ / "data/glossary/glossary_v1_3.csv")
    for campo, marcada in (("inicial", True), ("corregida", False)):
        ocurrencias = verificar(ejemplo["original"], ejemplo[campo], terminos)
        termino, = [o for o in ocurrencias if o.term_id == ejemplo["id"]]
        assert termino.marcada == marcada


def test_fichas_estables_al_interactuar_y_sin_repetidos(proyecto):
    at = AppTest.from_file(str(RAIZ / "app/demo.py"), default_timeout=120).run()
    ids = list(at.session_state.portada_fichas)
    assert len(ids) == len(set(ids)) == 3
    at.run()
    assert not at.exception
    assert list(at.session_state.portada_fichas) == ids
