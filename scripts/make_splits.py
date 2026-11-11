"""Divide el corpus en desarrollo (40) y prueba (80) al azar, con semilla fija.

Lee los seg_id de data/corpus/segments.tsv y escribe data/splits/dev_ids.txt y test_ids.txt (un seg_id por línea,
ordenados). Con la misma semilla y el mismo corpus, la división sale siempre igual.

Si los archivos ya existen no los pisa: cambiar la división después de mirar resultados contaminaría la prueba.
Para rehacerla a propósito: --forzar.

No imprime el contenido de prueba, solo cuántos hay.
"""
import argparse
import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SEGMENTOS = RAIZ / "data" / "corpus" / "segments.tsv"
CARPETA = RAIZ / "data" / "splits"
SEMILLA = 20261109
N_DEV = 40


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--forzar", action="store_true", help="rehacer aunque ya exista la división")
    args = p.parse_args()

    dev, test = CARPETA / "dev_ids.txt", CARPETA / "test_ids.txt"
    if (dev.exists() or test.exists()) and not args.forzar:
        raise SystemExit("La división ya existe; no se toca. Usá --forzar solo si sabés por qué.")

    with open(SEGMENTOS, encoding="utf-8", newline="") as f:
        ids = [fila["seg_id"] for fila in csv.DictReader(f, delimiter="\t")]
    if len(ids) != len(set(ids)):
        raise SystemExit("Hay seg_id repetidos en segments.tsv.")
    if len(ids) <= N_DEV:
        raise SystemExit(f"El corpus tiene {len(ids)} oraciones; hacen falta más de {N_DEV}.")

    mezcla = sorted(ids)
    random.Random(SEMILLA).shuffle(mezcla)
    ids_dev, ids_test = sorted(mezcla[:N_DEV]), sorted(mezcla[N_DEV:])

    CARPETA.mkdir(parents=True, exist_ok=True)
    dev.write_text("\n".join(ids_dev) + "\n", encoding="utf-8")
    test.write_text("\n".join(ids_test) + "\n", encoding="utf-8")
    print(f"Semilla {SEMILLA}: {len(ids_dev)} de desarrollo, {len(ids_test)} de prueba (total {len(ids)}).")


if __name__ == "__main__":
    main()
