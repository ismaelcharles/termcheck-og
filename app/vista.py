"""Piezas visuales de la app: colores de las etiquetas, chips, fichas de términos y oraciones resaltadas.

Todo texto que viene del glosario pasa por html.escape antes de ir a la página.
"""
import html
import unicodedata

import streamlit as st

from datos import CATEGORIAS, faltantes, variantes

from termcheck.etiquetas import ETIQUETAS as DEFINICIONES, INCONSISTENTE, NOMBRES
from termcheck.report import COLORES

# Compatibilidad con las páginas internas; nombres y significados vienen de una sola definición.
ETIQUETAS = {c: (COLORES[c][1] if et.nivel != "bien" else "#4A453D",
                 COLORES[c][0], et.significado) for c, et in DEFINICIONES.items()}
ETIQUETAS["INCONSISTENTE"] = ("#7A5300", "#F5E8C8", INCONSISTENTE.significado)

CSS = """
<style>
[data-testid="stMainBlockContainer"]{max-width:1120px;padding-top:2rem;padding-bottom:2rem}
.st-key-public_nav{border-bottom:1px solid #DED8CC;padding:.2rem 0 1rem;margin-bottom:1.15rem}
.st-key-public_nav [data-testid="stPageLink"]{font-size:.95rem}
.tc-brand-description{color:#766D60;margin:.45rem 0 .6rem;font-size:.92rem}
.tc-page-intro{margin:.25rem 0 1.25rem}
.tc-page-intro h2{font:500 2rem/1.25 Newsreader,Georgia,serif!important;letter-spacing:-.02em}
.tc-page-intro p{color:#766D60;margin:.55rem 0 0}
.tc-dict-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;margin:.7rem 0 1.25rem}
.tc-dict-preview{grid-template-columns:repeat(3,minmax(0,1fr))}
.tc-dict-card{background:#FFFDF9;border:1px solid #DED8CC;border-radius:10px;padding:1.1rem 1.25rem;min-width:0;overflow-wrap:anywhere}
.tc-dict-top{display:flex;justify-content:space-between;gap:.5rem;font-size:.73rem;color:#7A7266;margin-bottom:.65rem}
.tc-dict-card h3{font:500 1.6rem/1.2 Newsreader,Georgia,serif!important;letter-spacing:-.02em;margin:0}
.tc-dict-alias{color:#7A7266;font-size:.79rem;margin:.3rem 0}
.tc-dict-preferred{color:#285C53;font-weight:600;font-size:1rem;line-height:1.5;margin:.7rem 0 .6rem}
.tc-dict-row{font-size:.83rem;line-height:1.6;margin:.5rem 0}
.tc-dict-row>span{font-size:.72rem;color:#7A7266}
.tc-dict-row p{margin:.05rem 0;color:#554F45}
.tc-dict-avoid p{color:#9C3324}
.tc-dict-card details{border-top:1px solid #EAE4D9;margin-top:.9rem;padding-top:.65rem;font-size:.8rem;color:#6A6257}
.tc-dict-card summary{font-size:.76rem;color:#7A7266}
.tc-dict-card details p{margin:.55rem 0;line-height:1.6}
.tc-dict-source{font-size:.74rem}
@media(max-width:760px){.tc-dict-grid,.tc-dict-preview{grid-template-columns:minmax(0,1fr)}
 .tc-dict-card{padding:1.1rem}.tc-dict-card h3{font-size:1.5rem!important}}
h1{font-size:1.8rem!important;letter-spacing:-.035em}
h2{font-size:1.2rem!important;letter-spacing:-.02em}
h3{font-size:1.05rem!important}
.st-key-vf_editor,.st-key-vf_revision{background:#FFFFFF}
.st-key-vf_editor [data-testid="stTextArea"] textarea{background:#FAFBF9;line-height:1.6}
.st-key-vf_editor [data-testid="stForm"]{padding:0}
.tc-descripcion{color:#65716A;margin:.35rem 0 1.4rem;font-size:.95rem}
.tc-result-summary{font-size:.92rem;color:#65716A;margin:0 0 .5rem}
.tc-result-summary strong{color:#202824;font-weight:600}
.tc-empty{padding:1.75rem 0;text-align:center;color:#65716A;font-size:.9rem}
@media(max-width:640px){[data-testid="stMainBlockContainer"]{padding-top:1.1rem;padding-left:1rem;padding-right:1rem}}
.tc-chip{display:inline-block;padding:.12rem .55rem;margin:.12rem .25rem .12rem 0;border-radius:0;
  font-size:.86rem;line-height:1.5;border:1px solid transparent;white-space:normal;overflow-wrap:anywhere}
.tc-en{background:transparent;color:#14120F;font-weight:500}
.tc-mute{background:transparent;color:#4A453D}
.tc-tachado{text-decoration:line-through;text-decoration-thickness:1.5px}
.tc-ficha{background:#FFFDF9;border:1px solid #DED8CC;border-radius:10px;padding:1.05rem 1rem;margin-bottom:.25rem}
.tc-ficha-cab{display:flex;justify-content:space-between;align-items:baseline;gap:.5rem;margin-bottom:.45rem}
.tc-id{font:500 .78rem ui-monospace,monospace;color:#7A7266}
.tc-meta{font-size:.78rem;color:#7A7266}
.tc-fila{display:flex;gap:.5rem;align-items:flex-start;margin:.15rem 0}
.tc-centro{align-items:center}
.tc-signo{width:1.1rem;flex:none;text-align:center;font-weight:600;line-height:1.9}
.tc-nota{font-size:.84rem;color:#4A453D;margin-top:.45rem;font-style:italic}
.tc-fuente{font-size:.76rem;color:#7A7266;margin-top:.25rem}
.tc-falta{font-size:.78rem;color:#7A5300;background:#F5E8C8;border-radius:.3rem;padding:.1rem .45rem;margin-top:.45rem;
  display:inline-block}
.tc-oracion{font-size:1.06rem;line-height:2.1;margin:.1rem 0 .5rem}
.tc-idioma{font:500 .82rem Inter,sans-serif;color:#6A6257}
.tc-marca{padding:.1rem .3rem;border-radius:.3rem;border-bottom:2px solid}
.tc-apagado{color:#9A9286;border-bottom:1px dashed #9A9286}
.tc-etiqueta{display:inline-block;font:500 .82rem Inter,sans-serif;padding:.15rem .5rem;border-radius:.3rem;
  letter-spacing:.02em}
.tc-leyenda{display:grid;grid-template-columns:auto 1fr;gap:.35rem .8rem;align-items:center;font-size:.9rem}
.tc-flujo{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;font-size:.88rem;margin:.3rem 0 1rem}
.tc-paso{background:#FBF9F5;border:1px solid #D8D0C2;border-radius:.5rem;padding:.35rem .7rem}
.tc-paso b{font-weight:600}
.tc-flecha{color:#9A9286}
.tc-cita{font-size:.8rem;color:#4A453D;line-height:1.45;margin:.2rem 0 0 .2rem}
.tc-cita a{color:#24527D}
.tc-nivel{display:inline-block;font:600 .68rem Inter,sans-serif;padding:.05rem .4rem;border-radius:.3rem;margin-right:.3rem;
  white-space:normal;overflow-wrap:anywhere}
</style>
"""


def estilos():
    st.html(CSS)


LINKEDIN = "https://www.linkedin.com/in/ismael-charles-546278264"


_LOGO_LINKEDIN = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%230A66C2' "
                  "d='M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05"
                  "c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 "
                  "0 4.12zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45"
                  "c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z'/%3E%3C/svg%3E")


def cabecera(titulo):
    st.html(f'''<style>
.tc-cabecera{{display:flex;align-items:center;gap:.65rem;flex-wrap:wrap}}
.tc-cabecera h1{{font-family:Newsreader,Georgia,serif;font-size:2.25rem!important;font-weight:500;margin:0;line-height:1.2;letter-spacing:-.035em}}
.tc-autor{{font-size:.78rem;color:#65716A;margin-left:auto}}
.tc-cabecera a{{align-self:center;width:19px;height:19px;flex-shrink:0;
background:url("{_LOGO_LINKEDIN}") center/contain no-repeat}}
@media(max-width:640px){{.tc-cabecera h1{{font-size:1.8rem!important}}.tc-autor{{font-size:.72rem}}}}
</style><div class="tc-cabecera"><h1>{e(titulo)}</h1><span class="tc-autor">Ismael Charles</span>
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
        renglones.append(("✓", "#1F6B43", chip(fila["es_preferred"], "OK")))
    if variantes(fila["es_allowed"]):
        renglones.append(("≈", "#24527D", "".join(chip(v, "VARIANTE") for v in variantes(fila["es_allowed"]))))
    if variantes(fila["es_forbidden"]):
        renglones.append(("✗", "#9C3324",
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
        return f'<span class="tc-nivel" style="background:transparent;color:#4A453D">{e(texto)}</span>'
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
