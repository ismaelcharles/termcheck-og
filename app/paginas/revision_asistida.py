import html
import json
import re
import sqlite3
from pathlib import Path

import streamlit as st
import vista

base = Path(__file__).resolve().parents[3] / "termcheck-evaluacion-60" / "revision-ia"
vista.estilos()
st.title("Revisión asistida")
if not (base / "cola.json").exists():
    st.info("La primera lectura está en curso.")
    st.stop()
casos = json.loads((base / "cola.json").read_text())
opciones = ["La dejaría así", "Cambiaría el término", "El término no corresponde", "Necesito otra opinión"]
etiquetas = {
    "La dejaría así": "La traducción del término es aceptable",
    "Cambiaría el término": "La traducción del término necesita corrección",
    "El término no corresponde": "En el original, lo resaltado no tiene el sentido técnico que se evalúa",
    "Necesito otra opinión": "Tengo dudas sobre cómo evaluarlo",
}
def conectar():
    con = sqlite3.connect(base / "respuestas.sqlite")
    con.execute("CREATE TABLE IF NOT EXISTS revision (id TEXT PRIMARY KEY, decision TEXT NOT NULL, nota TEXT NOT NULL)")
    return con

with conectar() as con:
    hechas = {k:(d,n) for k,d,n in con.execute("SELECT id,decision,nota FROM revision")}
st.caption("Leé la frase y decidí si cambiarías el término para este encargo. Se incluyen discrepancias y una muestra aleatoria de coincidencias.")
st.progress(len(hechas)/len(casos), text=f"{len(hechas)} de {len(casos)} decisiones guardadas")
if len(hechas)==len(casos):
    st.success("Completaste la revisión asistida.")
ids=[c["id"] for c in casos]
pendientes=[k for k in ids if k not in hechas]
if "ra_actual" not in st.session_state:
    st.session_state.ra_actual=(pendientes or ids)[0]
k=st.selectbox("Caso",ids,key="ra_actual",format_func=lambda i:f"{ids.index(i)+1} · {casos[ids.index(i)]['termino']}"+(" ✓" if i in hechas else ""))
c=casos[ids.index(k)]
st.subheader(c["termino"])
st.caption("Inglés")
partes = re.split("(" + re.escape(c["termino"]) + ")", c["en"], flags=re.IGNORECASE)
st.html('<p lang="en">' + "".join(
    "<strong>" + html.escape(palabra) + "</strong>" if i % 2 else html.escape(palabra)
    for i, palabra in enumerate(partes)) + "</p>")
st.caption("Traducción")
st.write(c["es"])
with st.popover("Consultar glosario"):
    st.write(c["preferida"])
    if c["variantes"]:
        st.write("También se acepta · "+" · ".join(c["variantes"]))
def guardar():
    decision=st.session_state.get("dec_"+k)
    if decision is None:
        st.session_state.ra_sin_decision = True
        return
    st.session_state.pop("ra_sin_decision", None)
    with conectar() as con:
        con.execute("INSERT OR REPLACE INTO revision VALUES (?,?,?)",(k,decision,st.session_state["nota_"+k]))
    st.session_state.ra_ultima = k
    faltan=[i for i in pendientes if i!=k]
    if faltan:
        st.session_state.ra_actual=faltan[0]

prev,nota=hechas.get(k,(None,""))
with st.form("rev_"+k):
    st.radio("¿Cómo evaluarías este caso?", opciones, index=opciones.index(prev) if prev else None, format_func=etiquetas.get, key="dec_"+k, help="Si la traducción está mal, elegí que necesita corrección. La tercera opción se refiere al sentido de lo resaltado en el original inglés. Podés indicar un error sin proponer una alternativa.")
    st.text_input("Comentario o traducción sugerida (opcional)",value=nota,key="nota_"+k)
    st.form_submit_button("Guardar y continuar",type="primary",on_click=guardar)
if st.session_state.pop("ra_sin_decision", False):
    st.warning("Elegí una opción para guardar tu decisión.")
comparar = k if k in hechas else st.session_state.get("ra_ultima")
if comparar in hechas:
    anterior = casos[ids.index(comparar)]
    with st.expander(f"Ver las dos lecturas del caso {ids.index(comparar)+1} · {anterior['termino']}"):
        st.write("Tu decisión · "+etiquetas.get(hechas[comparar][0], hechas[comparar][0]))
        st.write("GPT-6.2 Astra Max · "+anterior["motivo"])
        st.write("TermCheck · "+(", ".join(anterior["marcas"]) or "Término sin detectar"))
