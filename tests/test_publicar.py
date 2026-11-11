"""Pruebas de scripts/publicar.py con un repositorio de juguete y un «GitHub» local (una carpeta), sin red.

Correr:  .venv/bin/python -m pytest tests/test_publicar.py -v
"""
import subprocess

import pytest

import publicar as pub


def git(carpeta, *orden):
    r = subprocess.run(["git", "-C", str(carpeta), *orden], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture
def repo(tmp_path):
    """Un proyecto con un commit, conectado a un remoto local."""
    remoto, local = tmp_path / "remoto.git", tmp_path / "proyecto"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(remoto)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(local)], check=True)
    git(local, "config", "user.name", "Prueba")
    git(local, "config", "user.email", "prueba@example.org")
    (local / "data/annotations").mkdir(parents=True)
    (local / "data/glossary").mkdir(parents=True)
    (local / "README.md").write_text("# Proyecto\n", encoding="utf-8")
    (local / "data/annotations/gold.csv").write_text("seg_id,system,term_id,label,es_used,comment\n", encoding="utf-8")
    (local / "data/glossary/glossary_en_es.csv").write_text("id,en\nG1,rig\n", encoding="utf-8")
    git(local, "add", ".")
    git(local, "commit", "-q", "-m", "inicio")
    git(local, "remote", "add", "origin", str(remoto))
    git(local, "push", "-q", "-u", "origin", "main")
    return local, remoto


def test_sin_cambios_no_hace_nada(repo):
    local, remoto = repo
    antes = git(remoto, "rev-parse", "main")
    assert pub.pendientes(local) == []
    assert pub.publicar(local) == (True, "No hay cambios para publicar.")
    assert git(remoto, "rev-parse", "main") == antes


def test_sube_la_anotacion_y_el_readme(repo):
    local, remoto = repo
    (local / "data/annotations/gold.csv").write_text("seg_id,system,term_id,label,es_used,comment\nP1,deepl,G1,CORRECTO,,\n",
                                                     encoding="utf-8")
    (local / "README.md").write_text("# Proyecto\n\nResultados.\n", encoding="utf-8")
    assert sorted(pub.pendientes(local)) == ["README.md", "data/annotations/gold.csv"]
    bien, texto = pub.publicar(local)
    assert bien and "Subido a GitHub" in texto
    assert git(remoto, "rev-parse", "main") == git(local, "rev-parse", "HEAD")
    assert "P1,deepl,G1,CORRECTO" in git(remoto, "show", "main:data/annotations/gold.csv")
    assert pub.pendientes(local) == []


def test_no_sube_archivos_fuera_de_la_lista(repo):
    local, remoto = repo
    (local / "privado.txt").write_text("no publicar", encoding="utf-8")
    (local / "data/glossary/candidatos.csv").write_text("x", encoding="utf-8")
    (local / "README.md").write_text("# Otro\n", encoding="utf-8")
    bien, _ = pub.publicar(local)
    assert bien
    subidos = git(remoto, "ls-tree", "-r", "--name-only", "main").splitlines()
    assert "privado.txt" not in subidos and "data/glossary/candidatos.csv" not in subidos
    assert "README.md" in subidos


def test_al_publicar_el_glosario_congelado_pone_la_etiqueta_una_vez(repo):
    local, remoto = repo
    (local / "data/glossary/glossary_v1.csv").write_text("id,en\nG1,rig\n", encoding="utf-8")
    (local / "data/glossary/glossary_v1.txt").write_text("glossary-v1 · 1 término\n", encoding="utf-8")
    bien, texto = pub.publicar(local)
    assert bien and "Etiqueta glossary-v1 puesta" in texto
    marcado = git(remoto, "rev-parse", "glossary-v1")
    assert marcado == git(local, "rev-parse", "HEAD")
    # Un cambio posterior se sube, pero la etiqueta se queda donde estaba
    (local / "README.md").write_text("# Con resultados\n", encoding="utf-8")
    bien, texto = pub.publicar(local)
    assert bien and "Etiqueta" not in texto
    assert git(remoto, "rev-parse", "glossary-v1") == marcado
    assert git(remoto, "rev-parse", "main") != marcado


def test_si_no_se_puede_subir_lo_dice(repo):
    local, _ = repo
    git(local, "remote", "set-url", "origin", str(local / "no-existe.git"))
    (local / "README.md").write_text("# Otro\n", encoding="utf-8")
    bien, texto = pub.publicar(local)
    assert not bien and "no se pudo subir" in texto
    # el commit quedó guardado: la próxima vez que haya conexión, se sube sin perder nada
    git(local, "remote", "set-url", "origin", str(local.parent / "remoto.git"))
    bien, texto = pub.publicar(local)
    assert bien and "al día" in texto
