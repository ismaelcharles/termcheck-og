"""Acuerdo entre dos anotadores (kappa de Cohen), plan 6.3, punto 4.

    .venv/bin/python scripts/kappa.py ruta/al/segundo_anotador.csv
    .venv/bin/python scripts/kappa.py segundo.csv --conjunto prueba

Compara data/annotations/gold.csv con el archivo de un segundo anotador. Ese archivo tiene las mismas columnas
que gold.csv: como mínimo seg_id, system, term_id y label. Solo cuentan los términos que anotaron los dos.

Da dos números:
- kappa con las cuatro etiquetas (Correcto, Error de término, Omisión, Sin traducir);
- kappa con dos (correcto o error), que es lo que usa la evaluación.

Kappa descuenta el acuerdo que saldría por azar. 1 es acuerdo total; 0, el que daría el azar. Con pocos casos, o
si casi todo es «Correcto», el número se mueve mucho: hay que informarlo junto con la cantidad de casos.
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate as ev  # noqa: E402


def kappa(pares):
    """pares: [(etiqueta del primero, etiqueta del segundo)] → (acuerdo observado, kappa).
    kappa es None si no se puede calcular: sin casos, o si los dos pusieron siempre la misma etiqueta."""
    n = len(pares)
    if n == 0:
        return 0.0, None
    observado = sum(a == b for a, b in pares) / n
    primero, segundo = Counter(a for a, _ in pares), Counter(b for _, b in pares)
    azar = sum(primero[e] * segundo[e] for e in primero) / (n * n)
    if azar == 1:
        return observado, None
    return observado, (observado - azar) / (1 - azar)


def comparar(gold, otro, ids=None):
    """gold y otro: filas con seg_id, system, term_id y label. ids: si se pasa, solo esas oraciones.
    Devuelve un dict con los pares en común, los dos kappas y cuántos términos anotó uno solo."""
    def por_clave(filas):
        return {(f["seg_id"], f["system"], f["term_id"]): f["label"] for f in filas
                if f.get("label") and (ids is None or f["seg_id"] in ids)}
    a, b = por_clave(gold), por_clave(otro)
    comunes = sorted(set(a) & set(b))
    pares = [(a[c], b[c]) for c in comunes]
    binario = [(x in ev.ERRORES_GOLD, y in ev.ERRORES_GOLD) for x, y in pares]
    return {"n": len(pares), "solo_primero": len(set(a) - set(b)), "solo_segundo": len(set(b) - set(a)),
            "cuatro": kappa(pares), "dos": kappa(binario),
            "desacuerdos": [(c, a[c], b[c]) for c in comunes if a[c] != b[c]]}


def texto(r):
    def linea(nombre, par):
        observado, k = par
        valor = ev.fmt(k) if k is not None else "no se puede calcular (los dos usaron una sola etiqueta)"
        return f"- {nombre}: acuerdo observado {ev.fmt(observado)} · kappa {valor}"
    lineas = [f"Términos anotados por los dos: {r['n']}",
              f"Solo en gold.csv: {r['solo_primero']} · solo en el segundo archivo: {r['solo_segundo']}"]
    if r["n"]:
        lineas += [linea("Cuatro etiquetas", r["cuatro"]), linea("Correcto o error", r["dos"]),
                   f"Desacuerdos: {len(r['desacuerdos'])}"]
        lineas += [f"  {s} · {sis} · {t}: gold {x} / segundo {y}" for (s, sis, t), x, y in r["desacuerdos"]]
    return "\n".join(lineas)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("segundo", help="CSV del segundo anotador, con las columnas de gold.csv")
    p.add_argument("--conjunto", choices=list(ev.SPLITS), help="comparar solo las oraciones de ese conjunto")
    a = p.parse_args()
    if not Path(a.segundo).exists():
        raise SystemExit(f"No existe {a.segundo}.")
    ids = None
    if a.conjunto:
        ids = {l.strip() for l in ev.SPLITS[a.conjunto].read_text(encoding="utf-8").splitlines() if l.strip()}
    r = comparar(ev.leer(ev.ANOTACIONES / "gold.csv"), ev.leer(a.segundo), ids)
    print(texto(r))
    if not r["n"]:
        raise SystemExit("No hay términos anotados por los dos: no se puede calcular el acuerdo.")


if __name__ == "__main__":
    main()
