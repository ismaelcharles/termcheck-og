"""Consulta pública del mismo glosario que usa la demo. No escribe datos."""
import random

import streamlit as st

import datos
import vista
from termcheck.glossary import cargar, publicado


def archivo():
    return publicado(datos.GLOSARIO.parent)


def leer():
    return cargar(archivo())


def buscar(terminos, texto="", area="Todas las áreas"):
    consulta = vista.plegar(texto.strip())
    return [t for t in terminos if (area == "Todas las áreas" or t.subdomain == area)
            and (not consulta or consulta in vista.plegar(" ".join(
                [*t.en, t.es_preferred, *t.es_allowed, *t.es_forbidden, t.note])))]


def ficha(t):
    e = vista.e
    alternativas = (f'<p class="tc-dict-alias">{e(" · ".join(t.en[1:]))}</p>' if len(t.en) > 1 else "")
    formas = (f'<div class="tc-dict-row"><span>También</span><p>{e(" · ".join(t.es_allowed))}</p></div>'
              if t.es_allowed else "")
    evitar = (f'<div class="tc-dict-row tc-dict-avoid"><span>Evitar</span><p>{e(" · ".join(t.es_forbidden))}</p></div>'
              if t.es_forbidden else "")
    detalle = ((f'<p>{e(t.note)}</p>' if t.note else "")
               + (f'<p class="tc-dict-source">{e(t.source)}</p>' if t.source else ""))
    return (f'<article class="tc-dict-card"><div class="tc-dict-top"><span>{e(t.subdomain)}</span>'
            f'<span>{e(vista.numero_termino(t.id))}</span></div><h3>{e(t.en[0])}</h3>{alternativas}'
            f'<div class="tc-dict-preferred">{e(t.es_preferred)}</div>{formas}{evitar}'
            + (f'<details><summary>Nota y fuentes</summary>{detalle}</details>' if detalle else "")
            + '</article>')


def fichas(terminos, compactas=False):
    clase = " tc-dict-preview" if compactas else ""
    return f'<div class="tc-dict-grid{clase}">' + "".join(ficha(t) for t in terminos) + '</div>'


def destacados(terminos):
    por_id = {t.id: t for t in terminos}
    ids = st.session_state.get("portada_fichas", [])
    cantidad = min(3, len(por_id))
    if len(ids) != cantidad or any(i not in por_id for i in ids):
        ids = random.sample(list(por_id), cantidad)
        st.session_state.portada_fichas = ids
    return [por_id[i] for i in ids]
