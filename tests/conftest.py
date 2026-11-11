"""Lo que comparten las pruebas: un proyecto inventado, chico, en una carpeta temporal.

Las pruebas de la evaluación y el ensayo del camino final usan este proyecto y no los datos reales. Así nunca leen
la prueba verdadera ni tocan la anotación del dueño. El contenido es inventado para probar el código: no es
terminología revisada.
"""
import importlib
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for carpeta in ("app", "scripts"):
    if str(RAIZ / carpeta) not in sys.path:
        sys.path.insert(0, str(RAIZ / carpeta))

GLOSARIO = """id,en,pos,es_preferred,es_allowed,es_forbidden,subdomain,note,source
G1,drilling rig|rig,NOUN,equipo de perforación,equipo,plataforma de perforación,perforación,,inventado
G2,casing,NOUN,casing,cañería,,perforación,,inventado
G3,wellhead,NOUN,boca de pozo,,,producción,,inventado
G4,casing string,NOUN,sarta de casing,sarta de cañería,,perforación,,inventado
"""
SEGMENTOS = [("D1", "Move the drilling rig."), ("P1", "Inspect the wellhead."),
             ("P2", "Run the casing string near the rig.")]
TRADUCCIONES = {
    "D1": {"opusmt": "Mueva la plataforma de perforación.", "claude": "Mueva el equipo de perforación.",
           "deepl": "Mueva el equipo."},
    "P1": {"opusmt": "Inspeccione el wellhead.", "claude": "Inspeccione la boca de pozo.",
           "deepl": "Inspeccione la cabeza del pozo."},
    "P2": {"opusmt": "Baje la sarta de cañería cerca de la plataforma de perforación.",
           "claude": "Baje la sarta de casing cerca del equipo.",
           "deepl": "Baje la columna de revestimiento cerca del equipo de perforación."},
}
# La anotación inventada: (seg_id, sistema, término) → etiqueta. NO_VA: «casing» dentro de «casing string».
ANOTACION_DEV = {("D1", "opusmt", "G1"): "ERROR_TERMINO", ("D1", "claude", "G1"): "CORRECTO",
                 ("D1", "deepl", "G1"): "CORRECTO"}
ANOTACION_PRUEBA = {
    ("P1", "opusmt", "G3"): "SIN_TRADUCIR", ("P1", "claude", "G3"): "CORRECTO", ("P1", "deepl", "G3"): "CORRECTO",
    ("P2", "opusmt", "G4"): "CORRECTO", ("P2", "claude", "G4"): "CORRECTO", ("P2", "deepl", "G4"): "ERROR_TERMINO",
    ("P2", "opusmt", "G1"): "ERROR_TERMINO", ("P2", "claude", "G1"): "CORRECTO", ("P2", "deepl", "G1"): "CORRECTO",
    ("P2", "opusmt", "G2"): "NO_VA", ("P2", "claude", "G2"): "NO_VA", ("P2", "deepl", "G2"): "NO_VA",
}
# Con esa anotación, lo que tiene que dar la evaluación de la prueba (9 términos; los NO_VA no cuentan):
#   TermCheck: TP 3 (wellhead sin traducir, revestimiento, plataforma) · FP 1 («cabeza del pozo») · FN 0 · TN 5
#   Baseline:  TP 3 · FP 3 (no reconoce «sarta de cañería», «equipo» ni «cabeza del pozo») · FN 0 · TN 3


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    """Arma el proyecto inventado y hace que la app y la evaluación trabajen sobre él. Devuelve su carpeta."""
    for carpeta in ("glossary", "corpus", "mt", "splits", "annotations"):
        (tmp_path / "data" / carpeta).mkdir(parents=True)
    (tmp_path / "data/glossary/glossary_en_es.csv").write_text(GLOSARIO, encoding="utf-8")
    (tmp_path / "data/corpus/segments.tsv").write_text(
        "seg_id\tsource_en\turl\n" + "".join(f"{i}\t{t}\thttps://example.org\n" for i, t in SEGMENTOS),
        encoding="utf-8")
    (tmp_path / "data/mt/translations.tsv").write_text(
        "seg_id\tsystem\ttarget_es\n" + "".join(f"{i}\t{s}\t{t}\n" for i, d in TRADUCCIONES.items()
                                                for s, t in d.items()), encoding="utf-8")
    (tmp_path / "data/splits/dev_ids.txt").write_text("D1\n", encoding="utf-8")
    (tmp_path / "data/splits/test_ids.txt").write_text("P1\nP2\n", encoding="utf-8")
    (tmp_path / "data/splits/test_eval_ids.txt").write_text("P1\nP2\n", encoding="utf-8")

    monkeypatch.setenv("TERMCHECK_DATOS", str(tmp_path))
    monkeypatch.delenv("TERMCHECK_ANOTACIONES", raising=False)
    modulos = _recargar()
    yield tmp_path
    monkeypatch.undo()   # vuelve a los datos reales…
    _recargar()          # …y los módulos vuelven a apuntar a ellos


def _recargar():
    import anotacion
    import datos
    import evaluate
    return [importlib.reload(m) for m in (anotacion, datos, evaluate)]


def anotar(etiquetas):
    """Guarda una anotación inventada con las mismas funciones que usa la página Anotar."""
    import anotacion as an
    for (seg_id, sistema, term_id), etiqueta in etiquetas.items():
        an.guardar_uno(seg_id, sistema, term_id, etiqueta)
