"""Corre el verificador y escribe el reporte (CSV + HTML).

Sobre el corpus del proyecto (por defecto, el conjunto de desarrollo):
    .venv/bin/python scripts/run_check.py --translations data/mt/translations.tsv --ids data/splits/dev_ids.txt \
        --out salida/dev

Sobre un par de archivos de texto (una oración por línea, alineadas):
    .venv/bin/python scripts/run_check.py --src origen.txt --tgt traduccion.txt --out salida/mio

Sobre un archivo de una herramienta de traducción (XLIFF 1.2, XLIFF 2.0 o TMX):
    .venv/bin/python scripts/run_check.py --file proyecto.xliff --out salida/proyecto

Escribe <out>.csv (una fila por aparición de término) y <out>.html (resaltado por color). Muestra un resumen.
--system filtra un sistema (opusmt, claude, deepl).
"""
import argparse
import csv
import hashlib
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from termcheck.checker import verificar_tabla  # noqa: E402
from termcheck.consistency import inconsistencias  # noqa: E402
from termcheck.formatos import ErrorDeFormato, leer as leer_formato  # noqa: E402
from termcheck.glossary import ErrorDeGlosario, cargar_bytes, publicado, validar  # noqa: E402
from termcheck.report import a_html, escribir_csv  # noqa: E402


def leer_tsv(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def leer_ids(ruta):
    return {l.strip() for l in Path(ruta).read_text(encoding="utf-8").splitlines() if l.strip()}


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--glossary", help="CSV propio; por defecto, la misma edición publicada que usa la demo")
    p.add_argument("--translations", help="TSV con seg_id, system, target_es")
    p.add_argument("--segments", default=str(RAIZ / "data/corpus/segments.tsv"))
    p.add_argument("--ids", help="archivo con los seg_id a verificar (uno por línea)")
    p.add_argument("--src", help="texto en inglés, una oración por línea")
    p.add_argument("--tgt", help="traducción, una oración por línea")
    p.add_argument("--file", help="archivo XLIFF 1.2, XLIFF 2.0 o TMX con el inglés y la traducción")
    p.add_argument("--system", help="solo este sistema")
    p.add_argument("--out", required=True, help="ruta sin extensión para el .csv y el .html")
    a = p.parse_args()

    if "test_ids" in (a.ids or "") or "test_eval" in (a.ids or ""):
        print("Atención: estás verificando la PRUEBA. No ajustes glosario ni código mirando este resultado.")

    try:
        ruta_glosario = Path(a.glossary) if a.glossary else publicado(RAIZ / "data/glossary")
        bytes_glosario = ruta_glosario.read_bytes()
        terminos = cargar_bytes(bytes_glosario)
    except OSError as e:
        raise SystemExit(f"No se pudo leer el glosario: {e}")
    except ErrorDeGlosario as e:
        raise SystemExit(str(e))
    errores = [p for p in validar(terminos) if p.tipo == "error"]
    if errores or not terminos:
        raise SystemExit("No se puede verificar con este glosario: "
                         + ("; ".join(str(p) for p in errores) if errores else "no tiene términos."))
    if a.file:
        try:
            leidos, sin_traduccion = leer_formato(Path(a.file).read_bytes(), a.file)
        except ErrorDeFormato as e:
            raise SystemExit(str(e))
        if sin_traduccion:
            print(f"{sin_traduccion} sin traducción: se saltearon.")
        segmentos = {seg_id: en for seg_id, en, _ in leidos}
        traducciones = [{"seg_id": seg_id, "system": a.system or "mt", "target_es": es} for seg_id, _, es in leidos]
        ids = None
    elif a.src and a.tgt:
        en = Path(a.src).read_text(encoding="utf-8").splitlines()
        es = Path(a.tgt).read_text(encoding="utf-8").splitlines()
        if len(en) != len(es):
            raise SystemExit(f"Los archivos no tienen la misma cantidad de líneas ({len(en)} y {len(es)}).")
        segmentos = {f"L{i:04d}": t for i, t in enumerate(en, start=1)}
        traducciones = [{"seg_id": f"L{i:04d}", "system": a.system or "mt", "target_es": t}
                        for i, t in enumerate(es, start=1)]
        ids = None
    elif a.translations:
        segmentos = {f["seg_id"]: f["source_en"] for f in leer_tsv(a.segments)}
        traducciones = leer_tsv(a.translations)
        ids = leer_ids(a.ids) if a.ids else None
    else:
        raise SystemExit("Pasá --translations, --file, o --src y --tgt.")

    sistemas = {a.system} if a.system else None
    traducciones = [f for f in traducciones if (not sistemas or f["system"] in sistemas)
                    and (ids is None or f["seg_id"] in ids)]
    ocurrencias = verificar_tabla(segmentos, traducciones, terminos)
    advertencias = inconsistencias(ocurrencias)

    salida = Path(a.out)
    salida.parent.mkdir(parents=True, exist_ok=True)
    contextos = {(f["seg_id"], f["system"]): (segmentos[f["seg_id"]], f["target_es"])
                 for f in traducciones}
    escribir_csv(ocurrencias, salida.with_suffix(".csv"), contextos)
    referencia = ruta_glosario.name + " · SHA-256 " + hashlib.sha256(bytes_glosario).hexdigest()
    salida.with_suffix(".html").write_text(a_html(segmentos, traducciones, ocurrencias, advertencias,
                                                glosario=referencia),
                                           encoding="utf-8")

    print(f"{len(traducciones)} traducciones · {len(ocurrencias)} apariciones de términos · "
          f"{len(advertencias)} advertencias de consistencia")
    por = Counter((o.system, o.label) for o in ocurrencias)
    etiquetas = ["OK", "VARIANTE", "PROHIBIDO", "SIN_TRADUCIR", "NO_ENCONTRADO"]
    print(f"{'sistema':10}" + "".join(f"{e:>15}" for e in etiquetas))
    for s in sorted({o.system for o in ocurrencias}):
        print(f"{s:10}" + "".join(f"{por[(s, e)]:>15}" for e in etiquetas))
    print(f"→ {salida.with_suffix('.csv')} y {salida.with_suffix('.html')}")


if __name__ == "__main__":
    main()
