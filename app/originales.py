"""Los documentos originales del dueño (PDF, presentaciones) de donde salió glosariotest. Se suben desde la app
(Glosario → Fuentes) y quedan en data/originales/, una carpeta privada: no se publica ni se sube a git.
Sirven para comprobar contra el original las citas de página de cada candidato."""
from datetime import datetime
from pathlib import Path

import datos

CARPETA = datos.RAIZ / "data" / "originales"
TIPOS = ["pdf", "pptx", "ppt", "docx", "doc", "odp", "odt", "xlsx", "xls", "txt", "md"]


def nombre_seguro(nombre):
    """La ruta relativa del archivo, sin nada que salga de la carpeta: «CENOVA/Gas/x.pdf» queda igual,
    «../../x.pdf» → «x.pdf» (nunca sale de la carpeta). Se descartan las partes vacías, «.», «..» y las ocultas."""
    partes = [p.strip() for p in str(nombre).replace("\\", "/").split("/")]
    partes = [p for p in partes if p and p not in (".", "..") and not p.startswith(".")]
    return "/".join(partes)


def guardar(archivo, tanda=None):
    """Guarda un archivo subido. Devuelve (nombre, si reemplazó a uno que ya estaba).
    `tanda` son los nombres ya guardados en esta misma subida: si se repite uno (dos «Programa.pdf» de subcarpetas
    distintas que llegaron sin la ruta), el segundo se guarda como «Programa (2).pdf» en vez de pisar al primero."""
    nombre = nombre_seguro(archivo.name)
    if not nombre:
        raise ValueError(f"Nombre de archivo no válido: {archivo.name!r}")
    if tanda is not None:
        base, punto, ext = nombre.rpartition(".") if "." in Path(nombre).name else (nombre, "", "")
        n = 2
        while nombre in tanda:
            nombre = f"{base} ({n}){punto}{ext}"
            n += 1
        tanda.add(nombre)
    CARPETA.mkdir(parents=True, exist_ok=True)
    CARPETA.chmod(0o700)
    destino = CARPETA / nombre
    if CARPETA.resolve() not in destino.resolve().parents:
        raise ValueError(f"Ruta no válida: {archivo.name!r}")
    destino.parent.mkdir(parents=True, exist_ok=True)
    for carpeta in [destino.parent, *destino.parent.parents]:
        if carpeta == CARPETA:
            break
        carpeta.chmod(0o700)
    habia = destino.exists()
    temporal = destino.with_name(destino.name + ".subiendo")
    temporal.write_bytes(archivo.getvalue())
    temporal.chmod(0o600)
    temporal.replace(destino)
    return nombre, habia


def lista():
    """Los documentos subidos, por orden alfabético de ruta: [{nombre, tamaño, fecha}]."""
    if not CARPETA.exists():
        return []
    salida = []
    for f in CARPETA.rglob("*"):
        if f.is_file() and not f.name.endswith(".subiendo"):
            st = f.stat()
            salida.append({"nombre": f.relative_to(CARPETA).as_posix(), "tamaño": st.st_size,
                           "fecha": datetime.fromtimestamp(st.st_mtime)})
    return sorted(salida, key=lambda x: x["nombre"].lower())


def borrar(nombre):
    f = CARPETA / nombre_seguro(nombre)
    if f.is_file() and CARPETA.resolve() in f.resolve().parents:
        f.unlink()
        # Si la subcarpeta quedó vacía, se va también
        for carpeta in f.parents:
            if carpeta == CARPETA or any(carpeta.iterdir()):
                break
            carpeta.rmdir()


def tamaño_legible(n):
    for unidad in ("bytes", "KB", "MB"):
        if n < 1024 or unidad == "MB":
            return f"{n:.0f} {unidad}" if unidad == "bytes" else f"{n:.1f} {unidad}"
        n /= 1024
