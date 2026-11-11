"""Pruebas de scripts/actualizar_readme.py y de su botón en Resultados → Publicar.

Usan un README y una carpeta salida/ inventados, en una carpeta temporal. No tocan el README real.

Correr:  .venv/bin/python -m pytest tests/test_actualizar_readme.py -v
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

import actualizar_readme as ar
from conftest import ANOTACION_DEV, anotar

RAIZ = Path(__file__).resolve().parent.parent
README = f"# Proyecto\n\nTexto de arriba.\n\n{ar.INICIO}\nviejo\n{ar.FIN}\n\n## Después\n\nTexto de abajo.\n"
EVAL = "# Evaluación · conjunto de {c}\n\n9 términos.\n\n## Verificador frente al baseline\n\n| TermCheck | {n} |\n"


def armar(tmp_path, desarrollo=True, prueba=False):
    (tmp_path / "salida").mkdir()
    (tmp_path / "README.md").write_text(README, encoding="utf-8")
    if desarrollo:
        (tmp_path / "salida/eval_desarrollo.md").write_text(EVAL.format(c="desarrollo", n=3), encoding="utf-8")
    if prueba:
        (tmp_path / "salida/eval_prueba.md").write_text(EVAL.format(c="prueba", n=9), encoding="utf-8")
    return tmp_path / "README.md", tmp_path / "salida"


def test_copia_desarrollo_como_provisorio(tmp_path):
    readme, salida = armar(tmp_path)
    bien, mensaje = ar.actualizar(readme, salida)
    texto = readme.read_text(encoding="utf-8")
    assert bien and "desarrollo" in mensaje
    assert "Resultados provisorios" in texto and "| TermCheck | 3 |" in texto
    assert "### Verificador frente al baseline" in texto      # el subtítulo baja un nivel
    assert "# Evaluación" not in texto and "viejo" not in texto
    assert texto.startswith("# Proyecto\n\nTexto de arriba.") and texto.endswith("## Después\n\nTexto de abajo.\n")


def test_correrlo_dos_veces_deja_el_readme_igual(tmp_path):
    readme, salida = armar(tmp_path, prueba=True)
    ar.actualizar(readme, salida)
    primero = readme.read_text(encoding="utf-8")
    bien, mensaje = ar.actualizar(readme, salida)
    assert bien and "al día" in mensaje
    assert readme.read_text(encoding="utf-8") == primero


def test_la_evaluacion_final_reemplaza_a_la_de_desarrollo(tmp_path):
    readme, salida = armar(tmp_path)
    ar.actualizar(readme, salida)
    (salida / "eval_prueba.md").write_text(EVAL.format(c="prueba", n=9), encoding="utf-8")
    bien, mensaje = ar.actualizar(readme, salida)
    texto = readme.read_text(encoding="utf-8")
    assert bien and "evaluación final" in mensaje
    assert "| TermCheck | 9 |" in texto and "glosario v1 congelado" in texto
    assert "provisorios" not in texto and "| TermCheck | 3 |" not in texto


def test_sin_resultados_lo_dice(tmp_path):
    readme, salida = armar(tmp_path, desarrollo=False)
    assert ar.actualizar(readme, salida)[0]
    assert "Todavía no hay resultados" in readme.read_text(encoding="utf-8")


def test_sin_marcadores_no_cambia_nada(tmp_path):
    readme, salida = armar(tmp_path)
    readme.write_text("# Proyecto\n\nSin marcadores.\n", encoding="utf-8")
    bien, mensaje = ar.actualizar(readme, salida)
    assert not bien and "marcadores" in mensaje
    assert readme.read_text(encoding="utf-8") == "# Proyecto\n\nSin marcadores.\n"


def test_el_readme_del_proyecto_tiene_los_marcadores_y_los_huecos():
    texto = (RAIZ / "README.md").read_text(encoding="utf-8")
    assert texto.count(ar.INICIO) == 1 and texto.count(ar.FIN) == 1
    assert all(texto.count(m) == 1 for n in ar.AUTOR for m in ar.marcas_autor(n))


def test_el_boton_de_resultados_actualiza_el_readme(proyecto):
    """El botón recalcula desarrollo con la anotación inventada y escribe el README de la carpeta de prueba."""
    (proyecto / "README.md").write_text(README, encoding="utf-8")
    anotar(ANOTACION_DEV)
    at = AppTest.from_file(str(RAIZ / "app/paginas/resultados.py"), default_timeout=120)
    at.session_state["res_vista"] = "pub"
    at.run()
    [b for b in at.button if "Actualizar el README" in b.label][0].click().run()
    assert not at.exception, at.exception
    texto = (proyecto / "README.md").read_text(encoding="utf-8")
    assert "Resultados provisorios" in texto and "| TermCheck | 3 | 1 | 0 | 0 | 2 |" in texto
    assert any("README actualizado" in s.value for s in at.success)


# --- Los dos textos del autor (ejemplos y hallazgos) ---

def readme_con_lugares(tmp_path):
    partes = [f"## {n}\n\n{ar.marcas_autor(n)[0]}\n{ar.AUTOR[n][1]}\n{ar.marcas_autor(n)[1]}\n" for n in ar.AUTOR]
    ruta = tmp_path / "README.md"
    ruta.write_text("# Proyecto\n\n" + "\n".join(partes) + f"\n{ar.INICIO}\nviejo\n{ar.FIN}\n", encoding="utf-8")
    return ruta


def test_el_recuadro_pendiente_se_lee_como_vacio(tmp_path):
    readme = readme_con_lugares(tmp_path)
    assert ar.leer_autor(readme, "ejemplos") == "" and ar.leer_autor(readme, "hallazgos") == ""


def test_guardar_y_volver_a_leer_el_texto_del_autor(tmp_path):
    readme = readme_con_lugares(tmp_path)
    antes = readme.read_text(encoding="utf-8")
    bien, mensaje = ar.escribir_autor(readme, "ejemplos", "Texto inventado.\r\n\r\n- uno\n")
    assert bien and "guardado" in mensaje
    assert ar.leer_autor(readme, "ejemplos") == "Texto inventado.\n\n- uno"
    assert ar.leer_autor(readme, "hallazgos") == ""          # el otro lugar no se toca
    assert ar.escribir_autor(readme, "ejemplos", "Texto inventado.\n\n- uno")[1].endswith("ya estaba guardado así.")
    bien, mensaje = ar.escribir_autor(readme, "ejemplos", "   ")   # vacío: vuelve el recuadro
    assert bien and "Pendiente" in mensaje
    assert readme.read_text(encoding="utf-8") == antes


def test_el_texto_del_autor_no_puede_romper_los_marcadores(tmp_path):
    readme = readme_con_lugares(tmp_path)
    antes = readme.read_text(encoding="utf-8")
    bien, _ = ar.escribir_autor(readme, "hallazgos", "hola <!-- resultados:fin --> chau")
    assert not bien and readme.read_text(encoding="utf-8") == antes


def test_sin_el_lugar_en_el_readme_no_cambia_nada(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(README, encoding="utf-8")
    bien, mensaje = ar.escribir_autor(readme, "ejemplos", "algo")
    assert not bien and readme.read_text(encoding="utf-8") == README
    assert ar.leer_autor(readme, "ejemplos") == ""


def test_guardar_los_textos_desde_la_app(proyecto):
    readme_con_lugares(proyecto)
    at = AppTest.from_file(str(RAIZ / "app/paginas/resultados.py"), default_timeout=120)
    at.session_state["res_vista"] = "pub"
    at.run()
    [a for a in at.text_area if a.label == "Hallazgos"][0].set_value("Hallazgo inventado.")
    [b for b in at.button if "Guardar en el README" in b.label][0].click().run()
    assert not at.exception, at.exception
    assert ar.leer_autor(proyecto / "README.md", "hallazgos") == "Hallazgo inventado."
    assert ar.leer_autor(proyecto / "README.md", "ejemplos") == ""
    assert any("guardado" in s.value for s in at.success)
