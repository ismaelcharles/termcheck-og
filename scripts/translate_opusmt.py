"""Traduce el corpus con Opus-MT (Helsinki-NLP/opus-mt-en-es), en este servidor y sin GPU.

Correr:  .venv/bin/python scripts/translate_opusmt.py

Lee data/corpus/segments.tsv y escribe las filas del sistema «opusmt» en data/mt/translations.tsv
(seg_id, system, target_es). Las filas de los otros sistemas que ya estén en el archivo se conservan.
Anota la versión exacta del modelo en data/mt/versiones.csv.
"""
import csv
from datetime import date
from pathlib import Path

import torch
from huggingface_hub import model_info
from transformers import MarianMTModel, MarianTokenizer

RAIZ = Path(__file__).resolve().parent.parent
SEGMENTOS = RAIZ / "data" / "corpus" / "segments.tsv"
SALIDA = RAIZ / "data" / "mt" / "translations.tsv"
VERSIONES = RAIZ / "data" / "mt" / "versiones.csv"
MODELO = "Helsinki-NLP/opus-mt-en-es"
SISTEMA = "opusmt"
TANDA = 8  # oraciones por vez: con 2 núcleos y poca memoria conviene ir de a poco


def leer_tsv(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def traducir(textos):
    revision = model_info(MODELO).sha  # el commit exacto del modelo, para poder repetir la prueba
    tok = MarianTokenizer.from_pretrained(MODELO, revision=revision)
    modelo = MarianMTModel.from_pretrained(MODELO, revision=revision).eval()
    salida = []
    with torch.no_grad():
        for i in range(0, len(textos), TANDA):
            lote = tok(textos[i:i + TANDA], return_tensors="pt", padding=True, truncation=True)
            # Decodificación fija (sin azar): el mismo texto da siempre la misma traducción
            ids = modelo.generate(**lote, num_beams=4, max_new_tokens=256, do_sample=False)
            salida += tok.batch_decode(ids, skip_special_tokens=True)
            print(f"  {min(i + TANDA, len(textos))}/{len(textos)}")
    return salida, revision


def guardar(filas_nuevas, revision):
    otras = [f for f in leer_tsv(SALIDA) if f["system"] != SISTEMA]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["seg_id", "system", "target_es"], delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(otras + filas_nuevas, key=lambda x: (x["seg_id"], x["system"])))
    versiones = [v for v in leer_tsv_coma(VERSIONES) if v["system"] != SISTEMA]
    versiones.append({"system": SISTEMA, "fecha": date.today().isoformat(), "version": f"{MODELO}@{revision}",
                      "como": "transformers, beam 4, sin muestreo, CPU"})
    with open(VERSIONES, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["system", "fecha", "version", "como"], lineterminator="\n")
        w.writeheader()
        w.writerows(versiones)


def leer_tsv_coma(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    segmentos = leer_tsv(SEGMENTOS)
    traducciones, revision = traducir([s["source_en"] for s in segmentos])
    filas = [{"seg_id": s["seg_id"], "system": SISTEMA, "target_es": t} for s, t in zip(segmentos, traducciones)]
    guardar(filas, revision)
    print(f"{len(filas)} traducciones de {MODELO}@{revision[:8]} en {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
