"""Candidatos para el glosario (data/glossary/candidatos.csv): términos con fuente que el dueño revisa uno por uno.
Ver data/glossary/CANDIDATOS.md para de dónde sale cada columna. Aprobar uno lo pasa al glosario con el formulario;
este archivo solo guarda en qué quedó cada candidato."""
import re
from datetime import datetime

import pandas as pd

import datos
import vista

ARCHIVO = datos.GLOSARIO.parent / "candidatos.csv"
FUENTES = datos.GLOSARIO.parent / "fuentes.csv"              # catálogo de fuentes con su evaluación
FORMAS_FUENTES = datos.GLOSARIO.parent / "formas_fuentes.csv"  # de dónde sale cada forma (scripts/fuentes_formas.py)
AUDITORIA = datos.RAIZ / "data" / "auditoria" / "auditoria_citas.csv"  # citas comprobadas (scripts/auditar_citas.py)
REVISION = datos.GLOSARIO.parent / "revision_previa.csv"        # sugerencia de Claude por candidato (scripts/revision_previa.py)

# Qué sugiere la revisión previa, en el orden en que conviene verlas
SUGERENCIAS = {"aceptar": "Aceptar", "revisar": "Revisar", "fusionar": "Unir a otro", "sin fuente": "Sin fuente",
               "descartar": "Descartar"}

# Cómo se ve cada nivel de confiabilidad
NIVELES = {"alta": "OK", "media": "SIN_TRADUCIR", "baja": "PROHIBIDO"}

# En este orden se ofrecen: primero los rápidos (coinciden), después los que piden tu criterio.
GRUPOS = {
    "sí": "Coinciden",
    "no": "No coinciden",
    "slb": "Solo SLB",
    "docs": "Solo tus documentos",
    "nada": "Sin equivalente",
}


def leer():
    if not ARCHIVO.exists():
        return pd.DataFrame()
    return pd.read_csv(ARCHIVO, dtype=str, keep_default_na=False)


def fuentes():
    """id → fila del catálogo de fuentes."""
    if not FUENTES.exists():
        return {}
    return {f["id"]: f for f in pd.read_csv(FUENTES, dtype=str, keep_default_na=False).to_dict("records")}


def guardar_fuentes(tabla):
    temporal = FUENTES.with_suffix(".tmp")
    tabla.to_csv(temporal, index=False, encoding="utf-8")
    temporal.replace(FUENTES)


def revision():
    """id del candidato → su fila de la revisión previa. Vacío si no hay revisión."""
    if not REVISION.exists():
        return {}
    tabla = pd.read_csv(REVISION, dtype=str, keep_default_na=False)
    return {f["id"]: f for f in tabla.to_dict("records")}


def formas_revisadas(c, sug):
    """Las formas de las fuentes más las que trae la sugerencia y no estaban (por ejemplo, las dos mitades de
    «agente de sustentación o apuntalante», o una forma con fuente web citada en el motivo)."""
    formas = formas_con_origen(c)
    if not sug:
        return formas
    vistas = {vista.plegar(f["forma"]) for f in formas}
    for forma in [sug["preferida"]] + datos.variantes(sug["aceptadas"]) + datos.variantes(sug["no_se_usan"]):
        if forma and vista.plegar(forma) not in vistas:
            vistas.add(vista.plegar(forma))
            formas.append({"forma": forma, "origen": "revisión previa"})
    return formas


def rol_sugerido(forma, origen, sug):
    """«válida» o «no» para una forma que no es la preferida, según la revisión previa si la hay."""
    if sug:
        clave = vista.plegar(forma)
        if clave in {vista.plegar(f) for f in datos.variantes(sug["aceptadas"])}:
            return "válida"
        if clave in {vista.plegar(f) for f in datos.variantes(sug["no_se_usan"])}:
            return "no"
    return "no" if origen == "inglés" else "válida"


def citas(id_candidato):
    """forma plegada → lista de citas (fuente, cita, respaldo) de ese candidato."""
    if not FORMAS_FUENTES.exists():
        return {}
    tabla = pd.read_csv(FORMAS_FUENTES, dtype=str, keep_default_na=False)
    tabla = tabla[tabla["candidato"] == id_candidato]
    if AUDITORIA.exists():
        audit = pd.read_csv(AUDITORIA, dtype=str, keep_default_na=False)
        audit = audit[audit["candidato"] == id_candidato][["forma", "fuente", "cita", "respaldo", "resultado", "paginas"]]
        tabla = tabla.merge(audit.drop_duplicates(["forma", "fuente", "cita", "respaldo"]), how="left",
                            on=["forma", "fuente", "cita", "respaldo"]).fillna("")
    salida = {}
    for f in tabla.to_dict("records"):
        salida.setdefault(vista.plegar(f["forma"]), []).append(f)
    return salida


def comprobacion(cita, catalogo):
    """Qué dio la comprobación contra el documento original: (texto corto, "bien" | "dudosa" | "mal" | "")."""
    res, pags = cita.get("resultado", ""), cita.get("paginas", "")
    if not res:
        return "", ""
    if cita["fuente"] == "opus":
        if res == "no está":
            return "no aparece en ningún documento", "mal"
        lugares = []
        for parte in pags.split("; "):
            fuente, _, pagina = parte.partition(" ")
            nombre = catalogo.get(fuente, {}).get("nombre", fuente)
            lugares.append(f"{nombre} {pagina}".strip())
        return "aparece en " + "; ".join(lugares[:4]) + (" …" if len(lugares) > 4 else ""), "bien"
    if res.startswith("en la página"):
        return "comprobada en el original" + (" (leída con OCR)" if "parecido" in res else ""), "bien"
    if res in ("página vecina", "en otra página") or res.startswith("página vecina"):
        return f"no está en esa página; está en p. {pags.replace('~', '')}", "dudosa"
    if res == "no está":
        return "no está en el documento original", "mal"
    if res == "sin documento":
        return "sin comprobar: el documento no se subió", ""
    return res, ""


def cita_corta(cita, catalogo):
    """«Programa Pozo NOC p. 8» o «SLB Energy Glossary (español) https://…». Si la comprobación contra el original
    dio que no está, lo dice: «Programa Pozo NOC p. 15 (no está en el original)»."""
    nombre = catalogo.get(cita["fuente"], {}).get("nombre", cita["fuente"] or "sin fuente")
    nota = " (no está en el original)" if cita.get("resultado") == "no está" and cita["fuente"] != "opus" else ""
    return f"{nombre} {cita['cita']}".strip() + nota


def grupo(c):
    if c["coinciden"] in ("sí", "no"):
        return c["coinciden"]
    return "slb" if c["es_slb"] else "docs" if c["es_docs"] else "nada"


def marcar(id_candidato, estado, id_glosario=""):
    tabla = leer()
    tabla.loc[tabla["id"] == id_candidato, ["estado", "id_glosario"]] = [estado, id_glosario]
    temporal = ARCHIVO.with_suffix(".tmp")
    tabla.to_csv(temporal, index=False, encoding="utf-8")
    temporal.replace(ARCHIVO)


def formas_slb(texto):
    """«portamecha (lastrabarrenas)» o «espacio anular; anillo» → cada forma por separado."""
    return [p.strip() for p in re.split(r"[;()]", texto) if p.strip()]


def formas_docs(c):
    return [c["es_docs"]] + [p.strip() for p in re.split(r"[;|]", c["es_docs_variantes"]) if p.strip()]


def ya_en_glosario(c, glosario):
    """El id del glosario que ya tiene este término en inglés, o ""."""
    buscado = vista.plegar(c["en"])
    for _, fila in glosario.iterrows():
        if buscado in {vista.plegar(v) for v in datos.variantes(fila["en"])}:
            return fila["id"]
    return ""


def fuente(c):
    fuentes = []
    if c["url_slb"]:
        fuentes.append(f"SLB Energy Glossary {c['url_slb']}")
    if c["es_docs"]:
        fuentes.append(f"docs: {c['fuente_docs']}")
    if c["en_osha"]:
        fuentes.append("en: OSHA O&G eTool glossary")
    return "; ".join(fuentes)


def formas_con_origen(c):
    """Todas las traducciones que traen las fuentes, sin repetir, con de dónde sale cada una. Al final va el término
    en inglés, por si en campo se usa así (préstamo, como casing o liner)."""
    salida, vistas = [], {}
    pares = [(f, "SLB") for f in formas_slb(c["es_slb"])]
    if c["es_docs"]:
        pares += [(f, "tus documentos") for f in formas_docs(c) if f]
    pares += [(f, "inglés") for f in datos.variantes(c["en"])]
    for forma, origen in pares:
        clave = vista.plegar(forma)
        if clave in vistas:
            if origen not in vistas[clave]["origen"] and origen != "inglés":
                vistas[clave]["origen"] += f" y {origen}"
            continue
        vistas[clave] = {"forma": forma, "origen": origen}
        salida.append(vistas[clave])
    return salida


def preferida_sugerida(c):
    """La forma que aparece marcada al abrir el candidato. Solo es un punto de partida: si las fuentes no
    coinciden y tus documentos la tienen tal cual, va la de tus documentos (uso argentino); si no, la de SLB."""
    docs = [f for f in formas_docs(c) if f] if c["es_docs"] else []
    slb = formas_slb(c["es_slb"])
    if docs and (not slb or (c["coinciden"] == "no" and "propuesto" not in c["fuente_docs"])):
        return docs[0]
    return slb[0] if slb else (docs[0] if docs else None)


def fila_decidida(c, preferida, roles, pos, area, nota, en=None):
    """La fila del glosario según lo que elegiste. `roles` dice, para cada otra forma, "válida", "no" o "error".
    La fuente lleva la cita de cada forma que queda en la fila."""
    usadas = [preferida] + [f for f, r in roles.items() if r in ("válida", "error")] if preferida else []
    return {"id": "", "en": (en or "").strip() or c["en"], "pos": pos or "NOUN", "es_preferred": preferida or "",
            "es_allowed": datos.juntar([f for f, r in roles.items() if r == "válida"]),
            "es_forbidden": datos.juntar([f for f, r in roles.items() if r == "error"]),
            "subdomain": (area or "").strip(), "note": (nota or "").strip(), "source": fuente_por_forma(c, usadas)}


def fuente_por_forma(c, formas):
    """«revestimiento: Programa Pozo NOC p. 8, Programa Pozo NOC p. 5; tubería de revestimiento: SLB … | en: OSHA…»"""
    catalogo, por_forma = fuentes(), citas(c["id"])
    partes, sin_cita = [], []
    for forma in formas:
        lista = por_forma.get(vista.plegar(forma), [])
        if lista:
            partes.append(f"{forma}: " + ", ".join(cita_corta(x, catalogo) for x in lista))
        elif forma:
            sin_cita.append(forma)
    if sin_cita:  # formas que trajo la revisión previa; la fuente está en su motivo
        partes.append(f"{', '.join(sin_cita)}: revisión previa {c['id']} (data/glossary/revision_previa.csv)")
    if c["en_osha"]:
        partes.append("en: OSHA O&G eTool glossary")
    return "; ".join(partes) or fuente(c)


def markdown_sugerencia(sug):
    if not sug:
        return []
    que = SUGERENCIAS.get(sug["sugerencia"], sug["sugerencia"])
    if sug["destino"]:
        que += f" ({sug['destino']})"
    lineas = [f"> **Revisión previa:** {que} · confianza {sug['confianza']} · {sug['prioridad']}"]
    if sug["preferida"]:
        lineas.append(f"> Preferida: **{sug['preferida']}**"
                      + (f" · vale: {sug['aceptadas'].replace('|', ', ')}" if sug["aceptadas"] else "")
                      + (f" · no se usa: {sug['no_se_usan'].replace('|', ', ')}" if sug["no_se_usan"] else ""))
    if sug["en"]:
        lineas.append(f"> Inglés: {sug['en'].replace('|', ' / ')}")
    lineas.append(f"> Por qué: {sug['motivo']}")
    if sug["para_vos"]:
        lineas.append(f"> Para vos: {sug['para_vos']}")
    return lineas + [""]


def markdown_pendientes():
    """Los candidatos pendientes en Markdown, agrupados como en la app. Se arma en el momento con lo que queda."""
    tabla = leer()
    pend = tabla[tabla["estado"] == "pendiente"].copy() if not tabla.empty else tabla
    hoy = datetime.now().strftime("%Y-%m-%d %H:%M")
    lineas = [f"# Candidatos pendientes ({len(pend)})", "",
              f"TermCheck O&G · generado el {hoy} desde `data/glossary/candidatos.csv`.", "",
              "No son parte del glosario: entran solo si los aceptás en la app (Glosario → Candidatos). "
              "«SLB» es el SLB Energy Glossary en español; «Tus documentos» sale de glosariotest (CENOVA, YPF). "
              "Cada forma lleva su fuente, la página o el enlace, y qué tan confiable es esa fuente (ver "
              "docs/fuentes-y-confiabilidad.md).", ""]
    if pend.empty:
        return "\n".join(lineas + ["No quedan candidatos pendientes.", ""])
    pend["grupo"] = pend.apply(grupo, axis=1)

    catalogo, sugs = fuentes(), revision()
    for clave, nombre in GRUPOS.items():
        filas = pend[pend["grupo"] == clave]
        if filas.empty:
            continue
        lineas += [f"## {nombre} ({len(filas)})", ""]
        for _, c in filas.iterrows():
            area = f" · {c['area']}" if c.get("area") else ""
            lineas += [f"### {c['id']} · {c['en'].replace('|', ' / ')}{area}", ""]
            lineas += markdown_sugerencia(sugs.get(c["id"]))
            por_forma = citas(c["id"])
            formas = formas_con_origen(c)
            formas = [f for f in formas if f["origen"] != "inglés"]
            if not formas:
                lineas += ["- Sin traducción en las fuentes.", ""]
                continue
            for f in formas:
                lineas.append(f"- **{f['forma']}**")
                for x in por_forma.get(vista.plegar(f["forma"]), []):
                    ficha = catalogo.get(x["fuente"], {})
                    cita = f"[{ficha.get('nombre', x['fuente'])}]({x['cita']})" if x["cita"].startswith("http") \
                        else cita_corta(x, catalogo)
                    nivel = (f" · confiabilidad: concepto {ficha['para_concepto']}, uso en Argentina "
                             f"{ficha['para_uso_ar']}") if ficha else ""
                    texto, _ = comprobacion(x, catalogo)
                    lineas.append(f"  - {cita}: {x['respaldo']}{nivel}" + (f" · **{texto}**" if texto else ""))
            lineas.append("")
    return "\n".join(lineas)
