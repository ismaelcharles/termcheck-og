"""Sube a GitHub lo que cambia cuando el dueño trabaja: anotación, glosario, README y documentos del informe.

    .venv/bin/python scripts/publicar.py                 # desde la terminal
    (o el botón «Publicar en GitHub» de la app, en Resultados → Publicar)

Qué hace:
1. Agrega solo los archivos de la lista ARCHIVOS (nunca «todo»: así no sube por accidente algo privado).
2. Hace un commit con la fecha.
3. Si el glosario v1 ya está congelado y guardado, pone la etiqueta `glossary-v1` (una sola vez).
4. Sube el commit y la etiqueta.

Si no hay nada nuevo, no hace nada y lo dice.
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVOS = ["README.md", "data/annotations", "data/glossary/glossary_en_es.csv", "data/glossary/glossary_v1.csv",
            "data/glossary/glossary_v1.txt", "data/glossary/SOURCES.md", "docs/annotation_guidelines.md",
            "docs/findings.md", "docs/validation.md"]
ETIQUETA = "glossary-v1"


def git(repo, *orden):
    """Corre git en la carpeta del proyecto. Devuelve (salió bien, texto)."""
    r = subprocess.run(["git", "-C", str(repo), *orden], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip("\n")


def existentes(repo):
    return [a for a in ARCHIVOS if (Path(repo) / a).exists()]


def pendientes(repo=RAIZ):
    """Los archivos de la lista que cambiaron desde el último commit: ["data/annotations/gold.csv", ...]."""
    ok, texto = git(repo, "status", "--porcelain", "--untracked-files=all", "--", *existentes(repo))
    return [linea[3:].strip().strip('"') for linea in texto.splitlines()] if ok else []


def _falta_etiqueta(repo):
    """True si el glosario v1 ya está guardado en git y la etiqueta todavía no existe."""
    hay_v1, _ = git(repo, "cat-file", "-e", "HEAD:data/glossary/glossary_v1.csv")
    hay_etiqueta, _ = git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{ETIQUETA}")
    return hay_v1 and not hay_etiqueta


def _sin_subir(repo):
    """Cuántos commits locales todavía no están en GitHub."""
    ok, texto = git(repo, "rev-list", "--count", "@{u}..HEAD")
    return int(texto) if ok and texto.isdigit() else 0


def publicar(repo=RAIZ, mensaje=None):
    """Guarda y sube los cambios. Devuelve (salió bien, texto para mostrar)."""
    cambios = pendientes(repo)
    pasos = []
    if cambios:
        ok, texto = git(repo, "add", "--", *existentes(repo))
        if not ok:
            return False, f"No se pudieron agregar los archivos: {texto}"
        mensaje = mensaje or f"Datos y resultados al {datetime.now():%Y-%m-%d %H:%M}"
        ok, texto = git(repo, "commit", "-m", mensaje, "--", *existentes(repo))
        if not ok:
            return False, f"No se pudo guardar el commit: {texto}"
        pasos.append(f"Guardado: {', '.join(cambios)}.")
    if _falta_etiqueta(repo):
        ok, texto = git(repo, "tag", ETIQUETA)
        if not ok:
            return False, f"No se pudo poner la etiqueta {ETIQUETA}: {texto}"
        pasos.append(f"Etiqueta {ETIQUETA} puesta.")
    etiqueta_local, _ = git(repo, "rev-parse", "-q", "--verify", f"refs/tags/{ETIQUETA}")
    if not pasos and not _sin_subir(repo) and not etiqueta_local:
        return True, "No hay cambios para publicar."
    ok, texto = git(repo, "push", "origin", "HEAD")
    if not ok:
        return False, " ".join(pasos) + f" Pero no se pudo subir a GitHub: {texto}"
    if etiqueta_local:
        ok, texto = git(repo, "push", "origin", ETIQUETA)
        if not ok:
            return False, " ".join(pasos) + f" El commit se subió, pero la etiqueta no: {texto}"
    if not pasos:
        return True, "No había cambios nuevos; GitHub está al día."
    return True, " ".join(pasos) + " Subido a GitHub."


if __name__ == "__main__":
    bien, salida = publicar()
    print(salida)
    sys.exit(0 if bien else 1)
