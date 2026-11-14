"""Piezas visuales de la app: colores de las etiquetas, chips, fichas de términos y oraciones resaltadas.

Todo texto que viene del glosario pasa por html.escape antes de ir a la página.
"""
import html
import unicodedata

import streamlit as st

from datos import CATEGORIAS, faltantes, variantes

# Las etiquetas del verificador (sección 3.2 del plan): color de letra, color de fondo y qué quieren decir.
ETIQUETAS = {
    "OK": ("#1F6B43", "#DCEFE2", "Aparece la traducción preferida."),
    "VARIANTE": ("#24527D", "#DDE8F3", "Aparece una variante aceptada, no la preferida."),
    "PROHIBIDO": ("#9C3324", "#F6DCD6", "Aparece una traducción que el glosario marca como error."),
    "SIN_TRADUCIR": ("#7A5300", "#F5E8C8", "Quedó en inglés y no es un préstamo aceptado."),
    "NO_ENCONTRADO": ("#5E4682", "#E8E0F1", "No aparece ninguna traducción conocida: revisar."),
    "INCONSISTENTE": ("#8D4510", "#F4E2D1", "El mismo término se tradujo de dos formas en el documento."),
}

CSS = """
<style>
.tc-chip{display:inline-block;padding:.12rem .55rem;margin:.12rem .25rem .12rem 0;border-radius:999px;
  font-size:.86rem;line-height:1.5;border:1px solid transparent;white-space:nowrap}
.tc-en{background:#14120F;color:#F6F3ED;font-weight:500}
.tc-mute{background:#ECE6DB;color:#4A453D}
.tc-tachado{text-decoration:line-through;text-decoration-thickness:1.5px}
.tc-ficha{background:#FBF9F5;border:1px solid #D8D0C2;border-radius:.6rem;padding:.9rem 1rem .8rem;margin-bottom:.2rem}
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
.tc-idioma{font:600 .72rem Inter,sans-serif;letter-spacing:.06em;color:#7A7266;text-transform:uppercase}
.tc-marca{padding:.1rem .3rem;border-radius:.3rem;border-bottom:2px solid}
.tc-apagado{color:#9A9286;border-bottom:1px dashed #9A9286}
.tc-etiqueta{display:inline-block;font:600 .74rem ui-monospace,monospace;padding:.15rem .5rem;border-radius:.3rem;
  letter-spacing:.02em}
.tc-leyenda{display:grid;grid-template-columns:auto 1fr;gap:.35rem .8rem;align-items:center;font-size:.9rem}
.tc-flujo{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;font-size:.88rem;margin:.3rem 0 1rem}
.tc-paso{background:#FBF9F5;border:1px solid #D8D0C2;border-radius:.5rem;padding:.35rem .7rem}
.tc-paso b{font-weight:600}
.tc-flecha{color:#9A9286}
.tc-cita{font-size:.8rem;color:#4A453D;line-height:1.45;margin:.2rem 0 0 .2rem}
.tc-cita a{color:#24527D}
.tc-nivel{display:inline-block;font:600 .68rem Inter,sans-serif;padding:.05rem .4rem;border-radius:.3rem;margin-right:.3rem;
  white-space:nowrap}
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


def linkedin():
    """El logo de LinkedIn con el enlace al perfil del autor, arriba a la derecha. Va justo antes del título y
    queda en su mismo renglón (la caja mide 0 de alto). El logo va como fondo en la hoja de estilos porque st.html
    saca los SVG y los estilos escritos dentro de la etiqueta."""
    st.html(f'''<style>
.tc-li-caja{{display:flex;justify-content:flex-end;height:0;position:relative;z-index:5}}
.tc-li{{display:block;width:34px;height:34px;margin-top:.9rem;background:url("{_LOGO_LINKEDIN}") center/contain no-repeat}}
.tc-li:hover{{opacity:.8}}
@media (max-width:640px){{.tc-li{{width:28px;height:28px;margin-top:-1.9rem}}}}
</style>
<div class="tc-li-caja"><a class="tc-li" href="{LINKEDIN}" target="_blank" rel="noopener"
title="Ismael Charles en LinkedIn" aria-label="Ismael Charles en LinkedIn"></a></div>''')


def e(texto):
    return html.escape(str(texto))


def plegar(texto):
    """Para comparar: minúsculas y sin tildes («Perforación» → «perforacion»)."""
    sin_tildes = unicodedata.normalize("NFD", str(texto).lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").strip()


def etiqueta(nombre):
    color, fondo, _ = ETIQUETAS[nombre]
    return f'<span class="tc-etiqueta" style="color:{color};background:{fondo}">{nombre}</span>'


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
    """Etiqueta de confiabilidad: «uso AR alta» en verde, media en ámbar, baja en rojo; lo demás, gris."""
    nombre = color_de.get(texto)
    if not nombre:
        return f'<span class="tc-nivel" style="background:#ECE6DB;color:#4A453D">{e(texto)}</span>'
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
