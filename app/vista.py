"""Piezas visuales de la app: colores de las etiquetas, chips, fichas de términos y oraciones resaltadas.

Todo texto que viene del glosario pasa por html.escape antes de ir a la página.
"""
import html
from pathlib import Path
import unicodedata

import streamlit as st

from datos import CATEGORIAS, faltantes, variantes

from termcheck.etiquetas import ETIQUETAS as DEFINICIONES, INCONSISTENTE, NOMBRES
from termcheck.report import COLORES

# Compatibilidad con las páginas internas; nombres y significados vienen de una sola definición.
ETIQUETAS = {c: (COLORES[c][1] if et.nivel != "bien" else "var(--tc-muted, #4A453D)",
                 COLORES[c][0], et.significado) for c, et in DEFINICIONES.items()}
ETIQUETAS["INCONSISTENTE"] = ("var(--tc-warning, #7A5300)", "var(--tc-warning-bg, #F5E8C8)", INCONSISTENTE.significado)

CSS = "<style>" + (Path(__file__).parent / "static/termcheck.css").read_text(encoding="utf-8") + "</style>"


def estilos():
    st.html(CSS)


LINKEDIN = "https://www.linkedin.com/in/ismael-charles-546278264"


_LOGO_LINKEDIN = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%230A66C2' "
                  "d='M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05"
                  "c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 "
                  "0 4.12zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45"
                  "c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z'/%3E%3C/svg%3E")


def cabecera(titulo):
    st.html(f'''<style>.tc-cabecera a{{background:url("{_LOGO_LINKEDIN}") center/contain no-repeat}}</style><div class="tc-cabecera"><h1>{e(titulo)}</h1><span class="tc-autor">Ismael Charles</span>
<a href="{LINKEDIN}" target="_blank" rel="noopener" title="Ismael Charles en LinkedIn"
aria-label="Ismael Charles en LinkedIn"></a></div>''')


def e(texto):
    return html.escape(str(texto))


def plegar(texto):
    """Para comparar: minúsculas y sin tildes («Perforación» → «perforacion»)."""
    sin_tildes = unicodedata.normalize("NFD", str(texto).lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").strip()


def etiqueta(nombre):
    color, fondo, _ = ETIQUETAS[nombre]
    return f'<span class="tc-etiqueta" style="color:{color};background:{fondo}">{e(NOMBRES[nombre])}</span>'


def chip(texto, nombre=None, tachado=False):
    if nombre is None:
        return f'<span class="tc-chip tc-mute">{e(texto)}</span>'
    color, fondo, _ = ETIQUETAS[nombre]
    clase = "tc-chip tc-tachado" if tachado else "tc-chip"
    return f'<span class="{clase}" style="color:{color};background:{fondo}">{e(texto)}</span>'


def leyenda():
    filas = "".join(f"{etiqueta(n)}<span>{e(d)}</span>" for n, (_, _, d) in ETIQUETAS.items())
    return f'<div class="tc-leyenda">{filas}</div>'


def ficha(fila):
    """La ficha de un término: inglés arriba; abajo, qué traducción da cada etiqueta."""
    en = "".join(f'<span class="tc-chip tc-en">{e(v)}</span>' for v in variantes(fila["en"])) or chip("sin término")
    meta = " · ".join(x for x in [CATEGORIAS.get(fila["pos"], fila["pos"]), fila["subdomain"]] if x)
    renglones = []
    if fila["es_preferred"]:
        renglones.append(("✓", "var(--tc-accent, #1F6B43)", chip(fila["es_preferred"], "OK")))
    if variantes(fila["es_allowed"]):
        renglones.append(("≈", "var(--tc-link, #24527D)", "".join(chip(v, "VARIANTE") for v in variantes(fila["es_allowed"]))))
    if variantes(fila["es_forbidden"]):
        renglones.append(("✗", "var(--tc-error, #9C3324)",
                          "".join(chip(v, "PROHIBIDO", tachado=True) for v in variantes(fila["es_forbidden"]))))
    cuerpo = "".join(f'<div class="tc-fila"><span class="tc-signo" style="color:{c}">{s}</span><div>{h}</div></div>'
                     for s, c, h in renglones)
    nota = f'<div class="tc-nota">{e(fila["note"])}</div>' if fila["note"] else ""
    fuente = f'<div class="tc-fuente">Fuente: {e(fila["source"])}</div>' if fila["source"] else ""
    falta = faltantes(fila)
    aviso = f'<div class="tc-falta">Falta: {e(", ".join(falta))}</div>' if falta else ""
    return (f'<div class="tc-ficha"><div class="tc-ficha-cab"><div>{en}</div><span class="tc-id">{e(fila["id"])}</span>'
            f'</div><div class="tc-meta">{e(meta)}</div>{cuerpo}{nota}{fuente}{aviso}</div>')


def que_pasaria(fila):
    """Para cada traducción posible del término, qué etiqueta le pondría el verificador.
    Es la regla de la sección 3.2 del plan, aplicada a un solo término."""
    casos = []
    if fila["es_preferred"]:
        casos.append((fila["es_preferred"], "OK"))
    casos += [(v, "VARIANTE") for v in variantes(fila["es_allowed"])]
    casos += [(v, "PROHIBIDO") for v in variantes(fila["es_forbidden"])]
    aceptadas = {plegar(fila["es_preferred"])} | {plegar(v) for v in variantes(fila["es_allowed"])}
    for forma in variantes(fila["en"]):
        if plegar(forma) not in aceptadas:  # si está aceptada en inglés, es un préstamo: ya figura arriba
            casos.append((forma, "SIN_TRADUCIR"))
    return casos


def probar(fila, traduccion):
    """Qué etiqueta tendría una traducción escrita a mano. Compara sin tildes ni mayúsculas, pero todavía sin lemas
    (eso llega con el verificador de la Fase 3)."""
    buscada = plegar(traduccion)
    for texto, nombre in que_pasaria(fila):
        if plegar(texto) == buscada:
            return nombre
    return "NO_ENCONTRADO"


def nivel(texto, color_de):
    """Confiabilidad alta en gris, media en ocre y baja en rojo."""
    nombre = color_de.get(texto)
    if not nombre:
        return f'<span class="tc-nivel" style="background:transparent;color:var(--tc-muted, #4A453D)">{e(texto)}</span>'
    color, fondo, _ = ETIQUETAS[nombre]
    return f'<span class="tc-nivel" style="background:{fondo};color:{color}">{e(texto)}</span>'


def casos(fila):
    """Las filas «si la traducción dice X → etiqueta», más «cualquier otra cosa → NO_ENCONTRADO»."""
    filas = [(chip(t, n, tachado=n == "PROHIBIDO"), n) for t, n in que_pasaria(fila)]
    filas.append((chip("cualquier otra cosa"), "NO_ENCONTRADO"))
    return "".join(f'<div class="tc-fila tc-centro"><div style="flex:1">{c}</div>{etiqueta(n)}</div>' for c, n in filas)


def oracion(texto, nombre=None, apagado=None):
    """Resalta lo que está entre [[ ]] con el color de la etiqueta; lo que está entre (( )) va apagado."""
    salida = e(texto)
    if nombre:
        color, fondo, _ = ETIQUETAS[nombre]
        salida = salida.replace("[[", f'<span class="tc-marca" style="color:{color};background:{fondo};'
                                      f'border-color:{color}">').replace("]]", "</span>")
    salida = salida.replace("((", f'<span class="tc-apagado" title="{e(apagado or "")}">').replace("))", "</span>")
    return f'<div class="tc-oracion">{salida}</div>'
