"""Copia las tablas de resultados al README, entre dos marcadores.

    .venv/bin/python scripts/actualizar_readme.py
    (o el botón «Actualizar el README» de la app, en Resultados → Publicar)

Qué copia:
- Si ya existe la evaluación final (salida/eval_prueba.md), copia esas tablas.
- Si todavía no existe, vuelve a calcular las de desarrollo y las copia con el aviso de que son provisorias.

Nunca calcula la evaluación de la prueba: eso se hace una sola vez, con el botón «Calcular la evaluación final».
Solo cambia lo que está entre los marcadores; el resto del README no se toca. Correrlo dos veces deja el archivo
igual.

Cuando la evaluación final ya se publicó, sus tablas quedan fijas: el marcador de inicio del README pasa a ser
«<!-- resultados:fijos …» y este script ya no las cambia. Así, lo que se mida después con otra versión del
verificador no reemplaza a lo publicado; va en su propia sección del README.

También guarda los dos textos que escribe el autor (los ejemplos de errores reales y los hallazgos), cada uno entre
sus propios marcadores. Los usa la app (Resultados → Publicar → «Tus textos del README»), para que el autor no
tenga que editar el archivo a mano. Este script nunca escribe el contenido de esos textos.
"""
import os
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INICIO = "<!-- resultados:inicio (lo escribe scripts/actualizar_readme.py; no editar a mano) -->"
FIN = "<!-- resultados:fin -->"
# El marcador de inicio cuando las tablas ya no se vuelven a escribir (alcanza con que empiece así)
FIJOS = "<!-- resultados:fijos"

# Los textos que escribe el autor: nombre → (título para la app, recuadro que queda mientras no haya texto)
AUTOR = {
    "ejemplos": ("Dos ejemplos de errores reales",
                 "> **Pendiente, lo completa el autor.** Dos ejemplos reales del corpus: la oración en inglés, lo "
                 "que tradujo el\n> sistema y la forma que se usa en Argentina."),
    "hallazgos": ("Hallazgos",
                  "> **Pendiente, lo completa el autor** cuando esté la evaluación final: qué sistema maneja mejor "
                  "la terminología,\n> qué tipos de error aparecen más y por qué falla el verificador cuando falla."),
}


def marcas_autor(nombre):
    return f"<!-- autor:{nombre}:inicio -->", f"<!-- autor:{nombre}:fin -->"


def _partes_autor(readme, nombre):
    """(lo de antes, lo que hay entre los marcadores, lo de después), o None si el README no tiene ese lugar."""
    readme = Path(readme)
    if not readme.exists():
        return None
    texto = readme.read_text(encoding="utf-8")
    ini, fin = marcas_autor(nombre)
    if texto.count(ini) != 1 or texto.count(fin) != 1 or texto.index(ini) > texto.index(fin):
        return None
    antes, resto = texto.split(ini)
    medio, despues = resto.split(fin)
    return antes, medio.strip("\n"), despues


def leer_autor(readme, nombre):
    """El texto que el autor ya escribió en ese lugar del README. "" si todavía está el recuadro «Pendiente»."""
    partes = _partes_autor(readme, nombre)
    if not partes or partes[1] == AUTOR[nombre][1]:
        return ""
    return partes[1]


def escribir_autor(readme, nombre, texto):
    """Guarda el texto del autor en su lugar del README. Vacío → vuelve el recuadro «Pendiente».
    Devuelve (salió bien, texto para mostrar)."""
    titulo = AUTOR[nombre][0]
    partes = _partes_autor(readme, nombre)
    if not partes:
        return False, f"El README no tiene el lugar para «{titulo}» (o está repetido). No se cambió nada."
    texto = (texto or "").replace("\r\n", "\n").strip()
    if "<!--" in texto or "-->" in texto:
        return False, f"«{titulo}»: el texto no puede tener «<!--» ni «-->». No se cambió nada."
    antes, medio, despues = partes
    nuevo = texto or AUTOR[nombre][1]
    if nuevo == medio:
        return True, f"«{titulo}» ya estaba guardado así."
    ini, fin = marcas_autor(nombre)
    Path(readme).write_text(f"{antes}{ini}\n{nuevo}\n{fin}{despues}", encoding="utf-8")
    return True, (f"«{titulo}» guardado en el README." if texto else
                  f"«{titulo}» quedó vacío: volvió el recuadro «Pendiente».")


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


def fijos(readme):
    """True si los resultados del README quedaron fijos (ya se publicó la evaluación final)."""
    readme = Path(readme)
    return readme.exists() and FIJOS in readme.read_text(encoding="utf-8")


def actualizar(readme, salida):
    """Reemplaza lo que hay entre los marcadores del README. Devuelve (salió bien, texto para mostrar)."""
    readme = Path(readme)
    if not readme.exists():
        return False, f"No existe {readme.name}."
    texto = readme.read_text(encoding="utf-8")
    if FIJOS in texto:
        return True, ("Los resultados del README son los de la evaluación final que se publicó y quedaron fijos. "
                      "No se cambió nada.")
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
