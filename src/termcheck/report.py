"""Reportes del verificador: CSV (una fila por aparición) y HTML con los términos resaltados por color.

    escribir_csv(ocurrencias, "salida/reporte.csv")
    html = a_html(segmentos, traducciones, ocurrencias, advertencias)
"""
import csv
import html as _html

COLUMNAS = ["seg_id", "system", "term_id", "term_en", "label", "es_found", "start", "end", "es_expected",
            "suggestion"]

# Colores por etiqueta (fondo, texto). Los que se marcan para revisar en tonos cálidos.
COLORES = {  # los mismos de la app (app/vista.py)
    "OK": ("#DCEFE2", "#1F6B43"),
    "VARIANTE": ("#DDE8F3", "#24527D"),
    "PROHIBIDO": ("#F6DCD6", "#9C3324"),
    "SIN_TRADUCIR": ("#F5E8C8", "#7A5300"),
    "NO_ENCONTRADO": ("#E8E0F1", "#5E4682"),
}
NOMBRES = {"OK": "Preferida", "VARIANTE": "Variante aceptada", "PROHIBIDO": "Prohibida",
           "SIN_TRADUCIR": "Sin traducir", "NO_ENCONTRADO": "No encontrada", "INCONSISTENTE": "Inconsistente"}


def filas(ocurrencias):
    return [{c: getattr(o, c) for c in COLUMNAS} for o in ocurrencias]


def escribir_csv(ocurrencias, ruta):
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas(ocurrencias))


def a_csv_texto(ocurrencias):
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNAS, lineterminator="\n")
    w.writeheader()
    w.writerows(filas(ocurrencias))
    return buf.getvalue()


def resaltar(texto, tramos):
    """Texto con <mark> en los tramos [(inicio, fin, label, titulo)]. Los tramos no se pisan."""
    partes, pos = [], 0
    for inicio, fin, label, titulo in sorted(t for t in tramos if t[0] >= 0):
        if inicio < pos:
            continue
        fondo, letra = COLORES[label]
        partes.append(_html.escape(texto[pos:inicio]))
        partes.append(f'<mark class="tc-{label.lower()}" style="background:{fondo};color:{letra};border-radius:3px;'
                      f'padding:0 2px" title="{_html.escape(titulo)}">{_html.escape(texto[inicio:fin])}</mark>')
        pos = fin
    partes.append(_html.escape(texto[pos:]))
    return "".join(partes)


def bloque_segmento(texto_en, texto_es, ocurrencias):
    """HTML de un segmento: inglés y español resaltados, y la lista de términos."""
    en = resaltar(texto_en, [(o.src_start, o.src_end, o.label, f"{o.term_id} · {NOMBRES[o.label]}")
                             for o in ocurrencias])
    es = resaltar(texto_es, [(o.start, o.end, o.label, f"{o.term_id} · {NOMBRES[o.label]}") for o in ocurrencias])
    items = []
    for o in ocurrencias:
        fondo, letra = COLORES[o.label]
        detalle = f"«{_html.escape(o.es_found)}»" if o.es_found else "nada"
        if o.label != "OK":
            detalle += f" · preferida: «{_html.escape(o.es_expected)}»"
        if o.suggestion:
            detalle += f" · ¿quizás «{_html.escape(o.suggestion)}»?"
        items.append(f'<li><span style="background:{fondo};color:{letra};border-radius:3px;padding:0 4px;'
                     f'font-size:.8em">{NOMBRES[o.label]}</span> <b>{_html.escape(o.term_en)}</b> '
                     f'<code>{o.term_id}</code> → {detalle}</li>')
    return (f'<div class="tc-seg"><p class="tc-en">{en}</p><p class="tc-es">{es}</p>'
            f'<ul class="tc-items">{"".join(items)}</ul></div>')


def a_html(segmentos, traducciones, ocurrencias, advertencias=(), titulo="Reporte de TermCheck"):
    """Reporte completo. segmentos: {seg_id: en}. traducciones: [{seg_id, system, target_es}]."""
    por_clave = {}
    for o in ocurrencias:
        por_clave.setdefault((o.seg_id, o.system), []).append(o)
    cuenta = {}
    for o in ocurrencias:
        cuenta[o.label] = cuenta.get(o.label, 0) + 1
    resumen = " · ".join(f"{NOMBRES[k]}: {cuenta[k]}" for k in COLORES if k in cuenta)
    cuerpo = []
    for f in traducciones:
        oc = por_clave.get((f["seg_id"], f["system"]), [])
        cuerpo.append(f'<h3>{_html.escape(f["seg_id"])} · {_html.escape(f["system"])}</h3>'
                      + bloque_segmento(segmentos[f["seg_id"]], f["target_es"], oc))
    avisos = "".join(f"<li>{_html.escape(str(a))}</li>" for a in advertencias)
    return f"""<!doctype html><html lang="es"><meta charset="utf-8"><title>{_html.escape(titulo)}</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem;color:#14120F;
background:#FBF9F5}} .tc-es{{border-left:3px solid #D8D0C2;padding-left:.8rem}} h3{{margin-top:2rem;font-size:1rem}}
code{{color:#7A7266}}</style>
<h1>{_html.escape(titulo)}</h1><p>{resumen}</p>
{"<h2>Advertencias de consistencia</h2><ul>" + avisos + "</ul>" if avisos else ""}
{"".join(cuerpo)}</html>"""
