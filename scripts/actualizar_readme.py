"""Copia las tablas de resultados al README, entre dos marcadores.

    .venv/bin/python scripts/actualizar_readme.py
    (o el botón «Actualizar el README» de la app, en Resultados → Publicar)

Qué copia:
- Si ya existe la evaluación final (salida/eval_prueba.md), copia esas tablas.
- Si todavía no existe, vuelve a calcular las de desarrollo y las copia con el aviso de que son provisorias.

Nunca calcula la evaluación de la prueba: eso se hace una sola vez, con el botón «Calcular la evaluación final».
Solo cambia lo que está entre los marcadores; el resto del README no se toca. Correrlo dos veces deja el archivo
igual.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INICIO = "<!-- resultados:inicio (lo escribe scripts/actualizar_readme.py; no editar a mano) -->"
FIN = "<!-- resultados:fin -->"


def carpeta_datos():
    """La carpeta del proyecto, o la de TERMCHECK_DATOS en pruebas y ensayos (igual que evaluate.py y la app)."""
    return Path(os.environ.get("TERMCHECK_DATOS") or RAIZ)


def _tablas(ruta):
    """El archivo de evaluación sin su título, con los subtítulos un nivel más abajo (van dentro de una sección)."""
    lineas = ruta.read_text(encoding="utf-8").strip("\n").split("\n")
    if lineas and lineas[0].startswith("# "):
        lineas = lineas[1:]
    return "\n".join("#" + l if l.startswith("## ") else l for l in lineas).strip("\n")


def bloque(salida):
    """El texto que va entre los marcadores, según lo que haya en la carpeta salida/."""
    final, desarrollo = Path(salida) / "eval_prueba.md", Path(salida) / "eval_desarrollo.md"
    if final.exists():
        fecha = datetime.fromtimestamp(final.stat().st_mtime)
        return (f"Evaluación final sobre el conjunto de prueba, con el glosario v1 congelado. "
                f"Calculada el {fecha:%Y-%m-%d}.\n\n" + _tablas(final))
    if desarrollo.exists():
        return ("> **Resultados provisorios.** Son del conjunto de desarrollo, que se usó para ajustar el código y "
                "el glosario. Sirven para ver que el verificador funciona, no para decir cuánto acierta. La "
                "evaluación final se calcula sobre el conjunto de prueba, que todavía no está anotado entero.\n\n"
                + _tablas(desarrollo))
    return "Todavía no hay resultados: falta la anotación."


def actualizar(readme, salida):
    """Reemplaza lo que hay entre los marcadores del README. Devuelve (salió bien, texto para mostrar)."""
    readme = Path(readme)
    if not readme.exists():
        return False, f"No existe {readme.name}."
    texto = readme.read_text(encoding="utf-8")
    if texto.count(INICIO) != 1 or texto.count(FIN) != 1 or texto.index(INICIO) > texto.index(FIN):
        return False, "El README no tiene los marcadores de resultados (o están repetidos). No se cambió nada."
    antes, resto = texto.split(INICIO)
    _, despues = resto.split(FIN)
    nuevo = f"{antes}{INICIO}\n{bloque(salida)}\n{FIN}{despues}"
    cual = "la evaluación final" if (Path(salida) / "eval_prueba.md").exists() else "los resultados de desarrollo"
    if nuevo == texto:
        return True, f"El README ya tenía {cual} al día."
    readme.write_text(nuevo, encoding="utf-8")
    return True, f"README actualizado con {cual}."


def refrescar_desarrollo():
    """Si todavía no hay evaluación final, recalcula las tablas de desarrollo con la anotación de hoy."""
    sys.path.insert(0, str(RAIZ / "scripts"))
    import evaluate as ev
    if (ev.DATOS / "salida" / "eval_prueba.md").exists():
        return
    casos = ev.evaluar("desarrollo")
    if casos:
        ev.escribir(casos, "desarrollo")


if __name__ == "__main__":
    refrescar_desarrollo()
    bien, mensaje = actualizar(carpeta_datos() / "README.md", carpeta_datos() / "salida")
    print(mensaje)
    sys.exit(0 if bien else 1)
