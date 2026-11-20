"""Un mismo reporte para la pantalla y el archivo HTML; CSV por aparición."""
import csv
import html as _html
from collections import Counter
from datetime import datetime, timezone

from termcheck import VERSION
from termcheck.etiquetas import ETIQUETAS, INCONSISTENTE, NOMBRES, orden

COLUMNAS = ["seg_id", "system", "term_id", "term_en", "label", "es_found", "start", "end", "es_expected",
            "suggestion", "source_en", "target_es"]
COLORES = {c: (("var(--tc-error-bg, #F6DCD6)", "var(--tc-error, #9C3324)") if e.nivel == "error" else
               ("var(--tc-warning-bg, #F5E8C8)", "var(--tc-warning, #7A5300)") if e.nivel == "aviso" else ("transparent", "inherit"))
           for c, e in ETIQUETAS.items()}
e = _html.escape

CSS = """
.tc-report{color:var(--tc-text, #202824);font:inherit;line-height:1.8;overflow-wrap:break-word}
.tc-report .tc-seg{border-top:1px solid var(--tc-border, #DCE1DA);padding:1rem 0;margin-top:.5rem;break-inside:avoid}
.st-key-vf_revision .tc-seg{border-top:0;padding:0;margin:0}
.tc-report .tc-seg-id{font-size:.82rem;color:var(--tc-muted, #6A6257);margin:0 0 .65rem}
.tc-report .tc-par{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:2rem}
.tc-report .tc-par p{margin:.25rem 0 .9rem;white-space:pre-wrap}
.tc-report .tc-lengua{font-size:.8rem;color:var(--tc-muted, #65716A);font-weight:500}
.tc-report mark{background:transparent;color:inherit;padding:0;border-radius:0;text-decoration:underline;
 text-decoration-color:var(--tc-muted, #AAA296);text-underline-offset:3px;text-decoration-thickness:1px}
.tc-report mark.tc-prohibido{background:var(--tc-error-bg, #F6DCD6);color:var(--tc-error, #9C3324);text-decoration:none}
.tc-report mark.tc-sin_traducir,.tc-report mark.tc-no_encontrado{background:var(--tc-warning-bg, #F5E8C8);color:var(--tc-warning, #7A5300);text-decoration:none}
.tc-report table{width:100%;table-layout:fixed;border-collapse:collapse;font-size:.9rem;line-height:1.55;margin:.6rem 0 0}
.tc-report td{overflow-wrap:anywhere}
.tc-report th,.tc-report td{text-align:left;vertical-align:top;padding:.75rem .65rem;border-bottom:1px solid var(--tc-rule, #E5E9E2)}
.tc-report th{font-weight:500;color:var(--tc-muted, #65716A);font-size:.78rem}
.tc-report th:first-child,.tc-report td:first-child{padding-left:0;width:22%}
.tc-report td:nth-child(2){width:25%}
.tc-report .tc-error{color:var(--tc-error, #9C3324)}.tc-report .tc-aviso{color:var(--tc-warning, #7A5300)}
.tc-report .tc-report-note{font-size:.84rem;color:var(--tc-muted, #6A6257)}
.tc-report code{font-size:.78rem;background:transparent;color:var(--tc-muted, #6A6257)}
@media(max-width:640px){.tc-report .tc-par{grid-template-columns:minmax(0,1fr);gap:.4rem}
 .tc-report table{font-size:.9rem}.tc-report table thead{display:none}
 .tc-report table tr{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:.25rem .75rem;
 padding:.8rem 0;border-bottom:1px solid var(--tc-rule, #E5E9E2)}
 .tc-report table td{padding:0;border:0;width:auto!important;overflow-wrap:anywhere}
 .tc-report table td:last-child{grid-column:1/-1}
 .tc-report table td[data-label]::before{content:attr(data-label);display:block;font-size:.75rem;color:var(--tc-muted, #65716A);margin-bottom:.15rem}}
@media print{.tc-report .tc-seg{break-inside:auto}.tc-report mark{print-color-adjust:exact;-webkit-print-color-adjust:exact}
 body{background:white!important;margin:0!important}details{display:block}}
"""


def filas(ocurrencias, contextos=None):
    """Filas por aparición; contextos asocia (seg_id, system) al par de textos original/traducción."""
    contextos = contextos or {}
    resultado = []
    for o in ocurrencias:
        fila = {c: getattr(o, c) for c in COLUMNAS if c not in ("source_en", "target_es")}
        fila["source_en"], fila["target_es"] = contextos.get((o.seg_id, o.system), ("", ""))
        resultado.append(fila)
    return resultado


def escribir_csv(ocurrencias, ruta, contextos=None):
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas(ocurrencias, contextos))


def a_csv_texto(ocurrencias, contextos=None):
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNAS, lineterminator="\n")
    w.writeheader()
    w.writerows(filas(ocurrencias, contextos))
    return buf.getvalue()


def resaltar(texto, tramos):
    """Divide las superposiciones sin repetir ni perder texto. Gana la etiqueta de mayor aviso.

    Las formas coordinadas pueden compartir el principio. Los títulos conservan ambas lecturas.
    """
    tramos = [(a, min(b, len(texto)), c, t) for a, b, c, t in tramos if 0 <= a < b and a < len(texto)]
    bordes = sorted({0, len(texto)} | {p for a, b, _, _ in tramos for p in (a, b)})
    piezas = []
    for a, b in zip(bordes, bordes[1:]):
        activos = [t for t in tramos if t[0] < b and a < t[1]]
        label = min((t[2] for t in activos), key=orden) if activos else None
        titulo = " · ".join(dict.fromkeys(t[3] for t in activos))
        if piezas and piezas[-1][2:] == (label, titulo):
            piezas[-1] = (piezas[-1][0], b, label, titulo)
        else:
            piezas.append((a, b, label, titulo))
    return "".join(f'<mark class="tc-{c.lower()}" title="{e(t)}">{e(texto[a:b])}</mark>' if c else e(texto[a:b])
                   for a, b, c, t in piezas)


def detalle(o):
    if not o.es_expected:
        return NOMBRES[o.label] + "."
    preferida = f"«{o.es_expected}»"
    if o.label == "OK":
        return "Preferida."
    if o.label == "VARIANTE":
        return f"Variante aceptada. Preferida: {preferida}."
    if o.label == "PROHIBIDO":
        return f"Prohibida. Preferida: {preferida}."
    if o.label == "SIN_TRADUCIR":
        return f"Sin traducir. Preferida: {preferida}."
    conocidas = ", ".join(f"«{x}»" for x in dict.fromkeys((o.es_expected, *o.es_allowed)) if x)
    texto = f"No encontrada. Formas: {conocidas}."
    if o.suggestion:
        texto += f" Por parecido: «{o.suggestion}»."
    return texto


def resumen(ocurrencias, segmentos):
    n = len(ocurrencias)
    return (f"{n} {'término encontrado' if n == 1 else 'términos encontrados'} en {segmentos} "
            f"{'segmento' if segmentos == 1 else 'segmentos'}; {sum(o.marcada for o in ocurrencias)} para revisar.")


def recuento(ocurrencias):
    cuenta = Counter(o.label for o in ocurrencias)
    return " · ".join(et.contar(cuenta[c]) for c, et in ETIQUETAS.items() if cuenta[c])


def bloque_segmento(texto_en, texto_es, ocurrencias, solo=False, cabecera=""):
    """Pieza compartida por Inicio, Verificar y la descarga. Agrupa filas iguales, conserva cada resaltado."""
    en = resaltar(texto_en, [(o.src_start, o.src_end, o.label, f"{o.term_id} · {NOMBRES[o.label]}") for o in ocurrencias])
    es = resaltar(texto_es, [(o.start, o.end, o.label, f"{o.term_id} · {NOMBRES[o.label]}") for o in ocurrencias])
    grupos = {}
    for o in sorted(ocurrencias, key=lambda o: orden(o.label)):
        if solo and not o.marcada:
            continue
        clave = (o.term_id, o.term_en.casefold(), o.es_found, o.label, o.es_expected, o.es_allowed, o.suggestion)
        if clave not in grupos:
            grupos[clave] = [o, 0]
        grupos[clave][1] += 1
    rows = []
    for o, n in grupos.values():
        veces = f", {n} veces" if n > 1 else ""
        rows.append(f'<tr><td data-label="Término" title="{e(o.term_id)}">{e(o.term_en)}{veces}</td>'
                    f'<td data-label="En la traducción">{e(o.es_found) if o.es_found else "—"}</td>'
                    f'<td class="tc-{ETIQUETAS[o.label].nivel}">{e(detalle(o))}</td></tr>')
    tabla = ('<table><thead><tr><th>Término</th><th>En la traducción</th><th>Resultado</th></tr></thead>'
             f'<tbody>{"".join(rows)}</tbody></table>' if rows else
             '<p class="tc-report-note">Ningún término para revisar en este segmento.</p>' if solo else
             '<p class="tc-report-note">Ningún término del glosario en este segmento.</p>')
    return (f'<section class="tc-report"><div class="tc-seg"><p class="tc-seg-id">{e(cabecera)}</p>'
            f'<div class="tc-par"><div><span class="tc-lengua">Inglés</span><p>{en}</p></div>'
            f'<div><span class="tc-lengua">Traducción</span><p>{es}</p></div></div>{tabla}</div></section>')


def avisos_html(advertencias):
    items = []
    for a in advertencias:
        formas = "; ".join(f"«{f}» en {', '.join(s)}" for f, s in a.formas.items())
        items.append(f'<li><b>{e(a.term_en or a.term_id)}</b>{" · " + e(a.system) if a.system else ""}: {e(formas)}</li>')
    return ('<section class="tc-report"><h3>El mismo término, traducido de formas distintas</h3><ul>'
            + "".join(items) + '</ul></section>') if items else ""


def leyenda():
    rows = "".join(f'<tr><td>{e(et.nombre)}</td><td><code>{et.codigo}</code></td><td>{e(et.significado)}</td></tr>'
                   for et in (*ETIQUETAS.values(), INCONSISTENTE))
    return ('<section class="tc-report"><table><thead><tr><th>Resultado</th><th>Código del CSV</th>'
            f'<th>Qué significa</th></tr></thead><tbody>{rows}</tbody></table></section>')


def a_html(segmentos, traducciones, ocurrencias, advertencias=(), titulo="Reporte de TermCheck", glosario=""):
    por_clave = {}
    for o in ocurrencias:
        por_clave.setdefault((o.seg_id, o.system), []).append(o)
    cuerpo = []
    for f in traducciones:
        oc = por_clave.get((f["seg_id"], f["system"]), [])
        cuerpo.append(bloque_segmento(segmentos[f["seg_id"]], f["target_es"], oc,
                                     cabecera=" · ".join(x for x in (f["seg_id"], f["system"]) if x)))
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(titulo)}</title>
<style>body{{font:16px/1.65 Inter,system-ui,sans-serif;max-width:68rem;margin:2rem auto;padding:0 1rem;
color:#202824;background:#FFFFFF;color-scheme:light}}h1,h2,h3{{font-family:Inter,system-ui,sans-serif;font-weight:600}}
footer{{overflow-wrap:anywhere}}{CSS}</style></head>
<body><h1>{e(titulo)}</h1><p>{e(resumen(ocurrencias, len(traducciones)))}</p><p>{e(recuento(ocurrencias))}</p>
<p>La revisión solo cubre los términos reconocidos del glosario. Una coincidencia no valida la traducción completa.
{"No se encontraron términos del glosario en el original." if not ocurrencias else ""}</p>
{avisos_html(advertencias)}{"".join(cuerpo)}<h2>Qué significa cada resultado</h2>{leyenda()}
<p>Las sugerencias se basan en el parecido de letras. Nunca cambian la etiqueta.</p>
<footer>TermCheck {VERSION} · {fecha} UTC{f'<p>Glosario: {e(glosario)}</p>' if glosario else ''}</footer></body></html>'''
