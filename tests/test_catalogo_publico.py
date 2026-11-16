"""La consulta pública usa el glosario de la demo y no modifica datos ni ofrece edición."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

import catalogo
from termcheck.glossary import Termino

RAIZ = Path(__file__).resolve().parent.parent


def test_consulta_publica_usa_el_congelado_y_no_escribe(proyecto):
    trabajo = proyecto / "data/glossary/glossary_en_es.csv"
    congelado = trabajo.with_name("glossary_v1.csv")
    congelado.write_bytes(trabajo.read_bytes())
    trabajo.write_text(trabajo.read_text().replace("boca de pozo", "FORMA DE TRABAJO"))
    antes = {p: p.read_bytes() for p in (trabajo, congelado)}
    at = AppTest.from_file(str(RAIZ / "app/demo.py"), default_timeout=120).run()
    at.switch_page("paginas/glosario_publico.py").run()
    assert not at.exception, at.exception
    at.text_input[0].set_value("wellhead").run()
    html = "".join(m.proto.body for m in at.get("html"))
    assert "boca de pozo" in html and "FORMA DE TRABAJO" not in html
    assert all(b.label not in ("Editar", "Agregar término", "Borrar") for b in at.button)
    assert all(p.read_bytes() == contenido for p, contenido in antes.items())


def test_busqueda_sin_tildes_y_filtro_de_area(proyecto):
    terminos = catalogo.leer()
    assert [t.id for t in catalogo.buscar(terminos, "caneria")] == ["G2", "G4"]
    assert [t.id for t in catalogo.buscar(terminos, "", "producción")] == ["G3"]
    assert catalogo.buscar(terminos, "zzz-no-existe") == []


def test_la_ficha_escapa_todos_los_campos():
    t = Termino(id='<img src=x>', en=['<script>x</script>'], pos="NOUN", es_preferred='<b>forma</b>',
                note='<svg onload=alert(1)>', source='a & b')
    html = catalogo.ficha(t)
    assert '<script>' not in html and '<img' not in html and '<svg' not in html
    assert '&lt;script&gt;' in html and '&lt;b&gt;' in html and 'a &amp; b' in html


def test_navegacion_publica_y_ejemplos(proyecto):
    at = AppTest.from_file(str(RAIZ / "app/demo.py"), default_timeout=120).run()
    links = [p.proto.label for p in at.get("page_link")]
    assert all(nombre in links for nombre in ("Verificar", "Glosario", "Ejemplos"))
    at.switch_page("paginas/inicio.py").run()
    assert not at.exception, at.exception
    assert at.selectbox[0].options
    at.selectbox[0].select("Préstamo aceptado").run()
    html = "".join(m.proto.body for m in at.get("html"))
    assert 'casing' in html


def test_consultar_el_glosario_conserva_la_revision(proyecto):
    at = AppTest.from_file(str(RAIZ / "app/demo.py"), default_timeout=120).run()
    at.text_area[0].set_value("Inspect the wellhead.")
    at.text_area[1].set_value("Inspeccione la boca de pozo.")
    [b for b in at.button if b.label == "Verificar"][0].click().run()
    firma = at.session_state.vf_resultado[0]
    at.switch_page("paginas/glosario_publico.py").run()
    at.text_input[0].set_value("wellhead").run()
    at.switch_page("paginas/verificar.py").run()
    assert not at.exception, at.exception
    assert [t.value for t in at.text_area] == ["Inspect the wellhead.", "Inspeccione la boca de pozo."]
    assert at.session_state.vf_resultado[0] == firma
    assert any(s.value == "Revisión" for s in at.subheader)


def test_archivo_subido_se_conserva_al_consultar_glosario(proyecto):
    at = AppTest.from_file(str(RAIZ / "app/demo.py"), default_timeout=120).run()
    at.session_state.vf_modo = "tsv"
    at.run()
    subir = [f for f in at.get("file_uploader") if f.key == "vf_archivo"][0]
    subir.upload("ejemplo.tsv", b"source_en\ttarget_es\nInspect the wellhead.\tInspeccione la boca de pozo.\n", "text/tab-separated-values").run()
    [b for b in at.button if b.label == "Verificar"][0].click().run()
    firma = at.session_state.vf_resultado[0]
    at.switch_page("paginas/glosario_publico.py").run()
    at.switch_page("paginas/verificar.py").run()
    assert not at.exception, at.exception
    assert at.session_state.vf_resultado[0] == firma
    assert any(s.value == "Revisión" for s in at.subheader)
