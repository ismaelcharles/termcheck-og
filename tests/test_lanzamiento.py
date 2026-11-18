"""Casos de entrada y cobertura que pueden dar una falsa impresión de revisión completa."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from termcheck.formatos import ErrorDeFormato, leer
from termcheck.glossary import ErrorDeGlosario, cargar_bytes, publicado
from termcheck.report import a_html
from entrada import leer_tabla

RAIZ = Path(__file__).resolve().parent.parent


def demo():
    return AppTest.from_file(str(RAIZ / "app/demo.py"), default_timeout=120).run()


def test_sin_terminos_no_se_presenta_como_revision_correcta(proyecto):
    at = demo()
    at.text_area[0].set_value("The document is ready.")
    at.text_area[1].set_value("El documento está listo.")
    [b for b in at.button if b.label == "Verificar"][0].click().run()
    assert not at.exception
    assert not at.success
    assert any("No se encontraron términos del glosario" in i.value for i in at.info)
    html = "".join(m.proto.body for m in at.get("html"))
    assert "documento está listo" in html


def test_glosario_invalido_impide_verificar(proyecto):
    at = demo()
    datos = (proyecto / "data/glossary/glossary_en_es.csv").read_text()
    datos += "G1,new term,NOUN,otra forma,,,,,inventado\n"
    subir = [f for f in at.get("file_uploader") if f.key == "vf_glosario"][0]
    subir.upload("duplicado.csv", datos.encode(), "text/csv").run()
    assert not at.exception
    assert at.error
    assert not [b for b in at.button if b.label == "Verificar"]


def test_csv_con_fila_incompleta_no_se_verifica_parcialmente(proyecto):
    at = demo()
    at.session_state.vf_modo = "tsv"
    at.run()
    subir = [f for f in at.get("file_uploader") if f.key == "vf_archivo"][0]
    subir.upload("incompleto.csv", b"source_en,target_es\nInspect the wellhead.,Revise la boca de pozo.\nRun the casing.\n", "text/csv").run()
    assert not at.exception
    assert any("fila 3" in w.value.lower() for w in at.warning)
    assert not [b for b in at.button if b.label == "Verificar"]


def test_identificadores_xml_repetidos_no_pisan_segmentos_en_el_reporte():
    xml = '<xliff version="1.2"><file><body>' + ''.join(
        f'<trans-unit id="{i}"><source>English {n}</source><target>Español {n}</target></trans-unit>'
        for n, i in enumerate(["x", "x", "x-2", "x"], 1)) + '</body></file></xliff>'
    pares, _ = leer(xml.encode())
    assert len({p[0] for p in pares}) == len(pares)
    assert [p[1] for p in pares] == [f"English {i}" for i in range(1, 5)]


@pytest.mark.parametrize("datos", [b"\xef\xbb\xbf\xff", b"\xff\xfe\x00"])
def test_xml_con_bom_y_codificacion_rota_da_error_legible(datos):
    with pytest.raises(ErrorDeFormato, match="codificación"):
        leer(datos)


def test_tmx_de_otro_par_de_idiomas_no_se_etiqueta_como_ingles_espanol():
    xml = ('<tmx version="1.4"><header srclang="fr"/><body><tu>'
           '<tuv xml:lang="fr"><seg>bonjour</seg></tuv>'
           '<tuv xml:lang="de"><seg>hallo</seg></tuv></tu></body></tmx>')
    with pytest.raises(ErrorDeFormato, match="inglés|español"):
        leer(xml.encode())


@pytest.mark.parametrize("separador", [",", ";", "\t"])
def test_tabla_preserva_omisiones_y_comillas(separador):
    texto = (f"source_en{separador}target_es\n"
             f'"Inspect the rig, then the casing."{separador}"Revise el equipo, luego el casing."\n'
             f"Inspect the wellhead.{separador}\n")
    assert leer_tabla(texto.encode()) == [
        ("Inspect the rig, then the casing.", "Revise el equipo, luego el casing."),
        ("Inspect the wellhead.", "")]


@pytest.mark.parametrize("texto", [
    'source_en,target_es\n"Inspect the wellhead.,Sin cierre\n',
    'source_en,target_es\n,Sin original\n',
    'source_en,target_es\nInspect the wellhead.,Revise,otro campo\n',
])
def test_tabla_rota_no_produce_un_reporte_parcial(texto):
    with pytest.raises(ValueError):
        leer_tabla(texto.encode())


def test_glosario_con_comillas_rotas_da_error_legible():
    texto = ('id,en,pos,es_preferred,es_allowed,es_forbidden,subdomain,note,source\n'
             'G1,"wellhead,NOUN,boca de pozo,,,,,inventado\n')
    with pytest.raises(ErrorDeGlosario, match="CSV"):
        cargar_bytes(texto.encode())


def test_xliff_con_idiomas_explicitos_incompatibles_se_rechaza():
    texto = ('<xliff version="2.0" srcLang="fr" trgLang="de"><file id="1"><unit id="1">'
             '<segment><source>bonjour</source><target>hallo</target></segment>'
             '</unit></file></xliff>')
    with pytest.raises(ErrorDeFormato, match="inglés|español"):
        leer(texto.encode())


@pytest.mark.parametrize("destino", ["Inspeccione la boca de pozo.\nBaje el casing.\n",
                                     "Inspeccione la boca de pozo.\nBaje el casing.\n\n"])
def test_lineas_vacias_no_cambian_la_pareja_de_traducciones(proyecto, destino):
    at = demo()
    at.text_area[0].set_value("Inspect the wellhead.\n\nRun the casing.")
    at.text_area[1].set_value(destino)
    [b for b in at.button if b.label == "Verificar"][0].click().run()
    assert not at.exception
    assert "vf_resultado" not in at.session_state
    assert any("Alineá los textos" in w.value for w in at.warning)


def test_demo_y_catalogo_usan_la_edicion_publicada(proyecto):
    import catalogo
    carpeta = proyecto / "data/glossary"
    base = (carpeta / "glossary_en_es.csv").read_text()
    (carpeta / "glossary_v1.csv").write_text(base)
    nueva = carpeta / "glossary_v1_1.csv"
    nueva.write_text(base.replace("boca de pozo", "cabezal"))
    assert publicado(carpeta) == nueva == catalogo.archivo()
    at = demo()
    at.text_area[0].set_value("Inspect the wellhead.")
    at.text_area[1].set_value("Inspeccione el cabezal.")
    [b for b in at.button if b.label == "Verificar"][0].click().run()
    assert not at.exception
    assert [o.label for o in at.session_state.vf_resultado[2]] == ["OK"]


def test_reporte_sin_terminos_explicita_cobertura_y_escapa_identidad_glosario():
    html = a_html({"1": "Hello."}, [{"seg_id": "1", "system": "", "target_es": "Hola."}], [],
                  glosario='<img src=x>.csv · SHA-256 abc')
    assert "No se encontraron términos del glosario" in html
    assert "<img" not in html and "&lt;img src=x&gt;.csv" in html


@pytest.mark.parametrize("separador", [",", ";", "\t"])
def test_csv_sin_encabezado_con_separadores_dentro_de_las_comillas(separador):
    texto = f'"Check the well, casing, and tubing."{separador}"Revise el pozo, el casing y el tubing."\n'
    assert leer_tabla(texto.encode()) == [("Check the well, casing, and tubing.",
                                         "Revise el pozo, el casing y el tubing.")]
