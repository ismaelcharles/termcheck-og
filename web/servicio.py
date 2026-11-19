"""Adaptador HTTP sin estado: reutiliza el motor y no guarda textos ni cargas."""
import base64
import csv
import hashlib
from io import StringIO
from pathlib import Path

from app.entrada import leer_tabla
from app.limites import MAX_TERMINOS, aplicar
from termcheck.checker import verificar
from termcheck.consistency import inconsistencias
from termcheck.formatos import ErrorDeFormato, es_de_traduccion, leer
from termcheck.glossary import ErrorDeGlosario, cargar_bytes, publicado, validar
from termcheck import report

RAIZ = Path(__file__).resolve().parents[1]
MAX_ARCHIVO = 1024 * 1024


def glosario(datos=None, nombre=""):
    if datos is None:
        ruta = publicado(RAIZ / "data/glossary")
        datos, nombre = ruta.read_bytes(), ruta.name
    if len(datos) > MAX_ARCHIVO:
        raise ValueError("El glosario supera el máximo de 1 MB.")
    terminos = cargar_bytes(datos)
    errores = [p for p in validar(terminos) if p.tipo == "error"]
    if errores:
        raise ValueError("No se puede verificar con este glosario: " + "; ".join(map(str, errores[:5])))
    if not terminos:
        raise ValueError("El glosario no tiene términos. Agregá al menos uno para verificar.")
    if len(terminos) > MAX_TERMINOS:
        raise ValueError(f"El máximo es {MAX_TERMINOS} términos por glosario.")
    return terminos, nombre + " · SHA-256 " + hashlib.sha256(datos).hexdigest()


def pares_texto(en, es):
    if not en.strip() or not es.strip():
        raise ValueError("Completá el inglés y la traducción para verificar.")
    a, b = en.splitlines(), es.splitlines()
    if len(a) != len(b):
        raise ValueError(f"El inglés tiene {len(a)} líneas y la traducción {len(b)}. Alineá los textos: una pareja por línea.")
    if any(not x.strip() and y.strip() for x, y in zip(a, b)):
        raise ValueError("Hay una línea con traducción pero sin original en inglés.")
    return [(f"L{i}", "", x, y) for i, (x, y) in enumerate(zip(a, b), 1) if x.strip()]


def pares_archivo(datos, nombre):
    if len(datos) > MAX_ARCHIVO:
        raise ValueError("El archivo supera el máximo de 1 MB.")
    if es_de_traduccion(nombre):
        filas, omitidos = leer(datos, nombre)
        if not filas:
            raise ValueError("Ningún segmento del archivo tiene traducción.")
        return [(i, "", en, es) for i, en, es in filas], (
            f"Se saltearon {omitidos} segmentos sin traducción." if omitidos else "")
    if Path(nombre).suffix.lower() not in {".csv", ".tsv", ".txt"}:
        raise ValueError("Usá CSV, TSV, XLIFF o TMX.")
    return [(f"F{i}", "", a, b) for i, (a, b) in enumerate(leer_tabla(datos), 1)], ""


def analizar(pares, terminos, referencia, aviso=""):
    pares, limite, seguir = aplicar(pares)
    if not seguir:
        raise ValueError(limite)
    resultado = [(p, verificar(p[2], p[3], terminos, p[0], p[1])) for p in pares]
    todas = [o for _, oc in resultado for o in oc]
    advertencias = inconsistencias(todas)
    segmentos = {p[0]: p[2] for p in pares}
    traducciones = [{"seg_id": p[0], "system": p[1], "target_es": p[3]} for p in pares]
    codificar = lambda texto: base64.b64encode(texto.encode()).decode()
    return dict(resultado=resultado, todas=todas, marcadas=sum(o.marcada for o in todas),
                aviso=" ".join(filter(None, (aviso, limite))), terminos=terminos,
                consistencia=report.avisos_html(advertencias), leyenda=report.leyenda(),
                html_b64=codificar(report.a_html(segmentos, traducciones, todas, advertencias, glosario=referencia)),
                csv_b64=codificar(report.a_csv_texto(todas)))


def ejemplo_desarrollo():
    def tabla(nombre):
        return list(csv.DictReader(StringIO((RAIZ / nombre).read_text()), delimiter="\t"))
    originales = {f["seg_id"]: f["source_en"] for f in tabla("data/corpus/segments.tsv")}
    traducciones = {f["seg_id"]: f["target_es"] for f in tabla("data/mt/translations.tsv") if f["system"] == "opusmt"}
    ids = ["S004", "S078", "S079"]
    return "\n".join(originales[i] for i in ids), "\n".join(traducciones[i] for i in ids)
