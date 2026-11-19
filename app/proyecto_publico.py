"""Método y resultados publicados, en lenguaje de consulta para la portada."""
from pathlib import Path
import re

import streamlit as st

from vista import e

README = Path(__file__).resolve().parent.parent / "README.md"
FUENTE = "https://github.com/ismaelcharles/termcheck-og#4-resultados"


def resultados_publicados():
    """Lee la comparación histórica de 0.1, sin mezclarla con la nueva medición de 0.2."""
    texto = README.read_text(encoding="utf-8")
    tabla = texto.split("### Verificador frente al baseline", 1)[1].split("### Por sistema", 1)[0]
    resultados = {}
    for metodo in ("Baseline (texto exacto)", "TermCheck"):
        fila = re.search(r"^\| " + re.escape(metodo) + r" \| (.+)$", tabla, re.M)
        columnas = [c.strip() for c in fila.group(1).split("|")]
        n, tp, fp, fn, tn = map(int, columnas[:5])
        resultados[metodo] = dict(n=n, tp=tp, fp=fp, fn=fn, tn=tn)
    return resultados


def mostrar():
    datos = resultados_publicados()
    tc, base = datos["TermCheck"], datos["Baseline (texto exacto)"]
    errores = tc["tp"] + tc["fn"]
    avisos = tc["tp"] + tc["fp"]
    precision = round(100 * tc["tp"] / avisos)
    st.html(f"""
    <section class="tc-project-section" aria-labelledby="tc-por-que">
      <div class="tc-project-heading">
        <h2 id="tc-por-que">¿Por qué uso TermCheck y no solo un LLM?</h2>
        <p>Para revisar terminología necesito un criterio que pueda consultar y volver a aplicar.
        Diseñé TermCheck para contrastar cada término reconocido con mi glosario de español petrolero argentino:
        cada decisión tiene una ficha detrás.</p>
      </div>
      <div class="tc-benefits">
        <article><h3>Mi criterio, explícito</h3><p>En mi glosario defino qué forma prefiero,
        qué variantes acepto y cuáles conviene evitar. La herramienta también permite cargar otro glosario.</p></article>
        <article><h3>Una revisión repetible</h3><p>El mismo texto, con la misma edición del glosario
        y del motor, recibe las mismas marcas. Así puedo repetir la revisión sin redactar un prompt cada vez.</p></article>
        <article><h3>Resultados comprobables</h3><p>Puedo consultar el término señalado, la forma esperada
        y su ficha. El reporte HTML y la tabla CSV permiten revisar y compartir los hallazgos.</p></article>
      </div>
      <div class="tc-evidence">
        <h3>Qué mostró la evaluación</h3>
        <p class="tc-evidence-context">Versión 0.1 · Glosario v1 · Anotación humana a ciegas</p>
        <div class="tc-metrics">
          <div><strong>{tc['tp']} de {errores}</strong><span>errores detectados</span>
            <p>De los errores que identifiqué en mi revisión, detectó el {round(100 * tc['tp'] / errores)} %.</p></div>
          <div><strong>{precision} %</strong><span>de los avisos eran errores reales</span>
            <p>{tc['tp']} de sus {avisos} avisos coincidieron con mi revisión.</p></div>
          <div><strong>{tc['fp']} frente a {base['fp']}</strong><span>falsas alarmas</span>
            <p>Menos avisos innecesarios que buscar solo la traducción preferida como texto exacto.</p></div>
        </div>
        <div class="tc-evidence-table"><table>
          <caption>Comparé dos maneras de revisar los mismos {tc['n']} casos de término en traducción</caption>
          <thead><tr><th scope="col">Resultado</th><th scope="col">Búsqueda exacta</th><th scope="col">TermCheck</th></tr></thead>
          <tbody>
            <tr><th scope="row">Errores detectados, de {errores}</th><td>{base['tp']}</td><td>{tc['tp']}</td></tr>
            <tr><th scope="row">Falsas alarmas</th><td>{base['fp']}</td><td>{tc['fp']}</td></tr>
            <tr><th scope="row">Errores que quedaron sin marcar</th><td>{base['fn']}</td><td>{tc['fn']}</td></tr>
          </tbody>
        </table></div>
        <p>TermCheck redujo las falsas alarmas al reconocer variantes y plurales,
        aunque dejó pasar más errores que la búsqueda exacta.</p>
        <details class="tc-project-details"><summary>Cómo leer estos resultados</summary>
          <p>La muestra reúne {tc['n']} casos: 40 unidades de término y oración traducidas por tres sistemas,
          en 20 oraciones. No son {tc['n']} contextos distintos. Anoté las traducciones sin ver
          qué sistema las produjo ni qué decía el verificador, con mi criterio de uso argentino.</p>
          <p>Comparé TermCheck con una búsqueda exacta; no lo evalué contra un LLM usado como revisor.
          Estos números corresponden a la versión 0.1 y al glosario v1, no estiman el rendimiento
          de la edición actual. La muestra es pequeña y los resultados tienen incertidumbre.</p>
          <p>En la publicación, el intervalo de confianza del 95 % es 76–94 % para la precisión
          y 82–97 % para la detección de errores.</p>
        </details>
        <p class="tc-evidence-note">Resultados históricos de 0.1 con glosario v1.
        Todavía no hice una evaluación independiente equivalente de la edición actual.
        <a href="{e(FUENTE)}" target="_blank" rel="noopener">Consultar el método y los resultados completos</a>.</p>
      </div>
    </section>
    <section class="tc-project-section" aria-labelledby="tc-como-funciona">
      <div class="tc-project-heading">
        <h2 id="tc-como-funciona">Cómo funciona por dentro</h2>
        <p>Organicé el proyecto en cuatro pasos: del texto de entrada a una marca que puedo revisar.</p>
      </div>
      <ol class="tc-architecture">
        <li><h3>Recibe los textos y el glosario</h3><p>La interfaz, hecha con Streamlit,
        recibe el original en inglés y su traducción. También lee CSV, TSV, XLIFF y TMX.
        El glosario aporta las equivalencias y las decisiones de uso.</p></li>
        <li><h3>Reconoce los términos</h3><p>Python y spaCy separan las palabras y analizan
        sus formas y categorías. Así puede reconocer un plural y distinguir el sustantivo
        <i lang="en">well</i> de la expresión <i lang="en">as well as</i>.</p></li>
        <li><h3>Aplica las reglas del glosario</h3><p>Busca la forma preferida, las variantes
        admitidas y las formas a evitar. También señala términos que quedaron en inglés sin
        estar aceptados y traducciones que no pudo encontrar.</p></li>
        <li><h3>Devuelve una revisión trazable</h3><p>Resalta las apariciones, vincula sus fichas
        y comprueba si un término cambia de traducción dentro del documento.
        El mismo motor genera la vista y los reportes descargables.</p></li>
      </ol>
      <details class="tc-project-details"><summary>Las técnicas, en simple</summary>
        <dl class="tc-techniques">
          <div><dt>Normalización</dt><dd>Unifica mayúsculas, tildes y guiones para comparar;
          conserva el texto original en el reporte.</dd></div>
          <div><dt>Lematización y morfología</dt><dd>Relaciona formas como «lodos» y «lodo».
          También aplica reglas de número, género y algunas formas verbales.</dd></div>
          <div><dt>Coincidencia de términos</dt><dd>Busca secuencias de palabras y da prioridad a los términos
          más largos cuando se superponen. Reconoce ciertas coordinaciones, como «pozo de petróleo o gas».</dd></div>
          <div><dt>Reglas explícitas</dt><dd>Clasifica cada aparición según el glosario.
          Las sugerencias por parecido, calculadas con RapidFuzz, ayudan a revisar;
          no convierten una coincidencia aproximada en una forma aceptada.</dd></div>
          <div><dt>Capas separadas</dt><dd>La interfaz recibe los datos; el motor lingüístico los analiza;
          el glosario fija el criterio y el generador de reportes presenta las marcas.
          El motor también se puede usar desde la línea de comandos.</dd></div>
        </dl>
      </details>
      <p class="tc-evidence-note">El alcance es terminológico: revisa los términos que reconoce en el glosario.
      No encontrar avisos no garantiza que toda la traducción esté bien. Por eso mantengo la interpretación del contexto
      y la decisión final en manos de quien revisa.</p>
    </section>
    """)
