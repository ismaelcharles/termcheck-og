"""Recorta lo que se anota, para que la anotación entre en el tiempo que hay (decisión del dueño, 2026-11-11).

- data/splits/dev_anotar_ids.txt: 15 oraciones de desarrollo. Primero las que ya tienen alguna etiqueta en
  gold.csv, después las siguientes de dev_ids.txt en orden, hasta 15.
- data/splits/test_eval_ids.txt: 40 de las 80 de prueba, al azar con semilla fija. Es la prueba con la que se
  evalúa. Se elige sin mirar el contenido: el script no lee las oraciones ni las traducciones, solo los ids, y no
  los imprime.

dev_ids.txt y test_ids.txt no se tocan. Si los archivos nuevos ya existen, no los pisa (--forzar para rehacer).
"""
import argparse
import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SPLITS = RAIZ / "data" / "splits"
GOLD = RAIZ / "data" / "annotations" / "gold.csv"
SEMILLA = 20261111
N_DEV, N_TEST = 15, 40


def leer_ids(ruta):
    return [l.strip() for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--forzar", action="store_true")
    args = p.parse_args()
    dev_out, test_out = SPLITS / "dev_anotar_ids.txt", SPLITS / "test_eval_ids.txt"
    if (dev_out.exists() or test_out.exists()) and not args.forzar:
        raise SystemExit("Los recortes ya existen; no se tocan.")

    dev = leer_ids(SPLITS / "dev_ids.txt")
    test = leer_ids(SPLITS / "test_ids.txt")

    con_etiqueta = set()
    if GOLD.exists():
        with open(GOLD, encoding="utf-8-sig", newline="") as f:
            con_etiqueta = {r["seg_id"] for r in csv.DictReader(f)}
    elegidas = [i for i in dev if i in con_etiqueta]
    elegidas += [i for i in dev if i not in con_etiqueta][: max(0, N_DEV - len(elegidas))]
    dev_out.write_text("\n".join(sorted(elegidas)) + "\n", encoding="utf-8")

    muestra = sorted(random.Random(SEMILLA).sample(sorted(test), N_TEST))
    test_out.write_text("\n".join(muestra) + "\n", encoding="utf-8")
    print(f"Desarrollo a anotar: {len(elegidas)} ({len(con_etiqueta & set(dev))} ya empezadas). "
          f"Prueba a evaluar: {len(muestra)} de {len(test)} (semilla {SEMILLA}).")


if __name__ == "__main__":
    main()
