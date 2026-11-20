"""Método y resultados publicados, en lenguaje de consulta para la portada."""
from pathlib import Path
import json
import re

from html import escape as e
from termcheck import VERSION
from termcheck.glossary import cargar, edicion_publicada, publicado

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"
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


def estado_actual():
    """Datos publicados de la edición actual; no sustituye la evaluación histórica."""
    comparacion = json.loads((RAIZ / "docs/cierre-comparacion-2026-11.json").read_text(encoding="utf-8"))
    auditoria = json.loads((RAIZ / "docs/auditoria-base-validacion.json").read_text(encoding="utf-8"))
    cobertura = json.loads((RAIZ / "docs/cobertura-1-4.json").read_text(encoding="utf-8"))
    carpeta = RAIZ / "data/glossary"
    return dict(version=VERSION, glosario=edicion_publicada(carpeta), conceptos=len(cargar(publicado(carpeta))),
                antes=comparacion["resultados"]["congelado-12"]["reserva"],
                despues=comparacion["resultados"]["actual-14"]["reserva"],
                motor_antes=comparacion["resultados"]["congelado-12"]["version_motor"],
                motor_despues=comparacion["resultados"]["actual-14"]["version_motor"],
                version_comprobada=auditoria["version"],
                referencia=comparacion["referencias"]["reserva"],
                formas=auditoria["contrato_glosario"]["formas"],
                controles=auditoria["controles_18"], cobertura=cobertura["resumen"])


def contenido(interfaz="Streamlit"):
    datos = resultados_publicados()
    actual = estado_actual()
    antes, despues, referencia = actual["antes"], actual["despues"], actual["referencia"]
    precision_antes = f"{100 * antes['precision']:.1f}".replace(".", ",")
    precision_despues = f"{100 * despues['precision']:.1f}".replace(".", ",")
    tc, base = datos["TermCheck"], datos["Baseline (texto exacto)"]
    # Desempeño del verificador específicamente sobre los 40 casos traducidos con DeepL,
    # tomado de la tabla «Por sistema» de la evaluación 0.1/v1.
    deepl = {"n": 40, "errores": 23, "tp": 21, "fp": 2, "fn": 2}
    errores = tc["tp"] + tc["fn"]
    avisos = tc["tp"] + tc["fp"]
    precision = round(100 * tc["tp"] / avisos)
    return f"""
    <section class="tc-project-section" aria-labelledby="tc-por-que">
      <div class="tc-project-heading">
        <h2 id="tc-por-que">¿Por qué usar TermCheck además de DeepL o un LLM?</h2>
        <p>Cuando traducís con DeepL o un LLM, podés usar TermCheck para revisar la terminología con criterios
        explícitos. Compara cada término reconocido con un glosario de español petrolero argentino y muestra
        la ficha que respalda cada marca.</p>
      </div>
      <div class="tc-benefits">
        <article><h3>Tu criterio, explícito</h3><p>El glosario define qué forma se prefiere,
        qué variantes se aceptan y cuáles conviene evitar. También podés cargar tu propio glosario.</p></article>
        <article><h3>Una revisión repetible</h3><p>El mismo texto, con la misma edición del glosario
        y del motor, recibe las mismas marcas. Así podés repetir la revisión sin redactar un prompt cada vez.</p></article>
        <article><h3>Resultados comprobables</h3><p>Podés consultar el término señalado, la forma esperada
        y su ficha. El reporte HTML y la tabla CSV permiten revisar y compartir los hallazgos.</p></article>
      </div>
      <div class="tc-evidence" aria-labelledby="tc-estado-actual">
        <h3 id="tc-estado-actual">Estado actual de TermCheck</h3>
        <p><strong>Motor {e(actual['version'])} · Glosario {e(actual['glosario'])} · {actual['conceptos']} conceptos</strong></p>
        <p>La revisión funciona con reglas lingüísticas y el glosario; no usa un LLM para decidir las marcas.
        En la versión {e(actual['version'])}, «tubería de revestimiento corta» se reconoce como variante de
        <i lang="en">liner</i>, aunque contenga «revestimiento», que se desaconseja cuando aparece aislado.</p>
        <details class="tc-project-details"><summary>Qué está comprobado y qué queda fuera</summary>
          <p>Comprobé las {actual['formas']} formas declaradas en el glosario y los flujos de entrada, revisión,
          consulta y descarga en PC y teléfono. En el corpus y las muestras públicas aparecen
          {actual['cobertura']['conceptos_con_deteccion']} de los {actual['conceptos']} conceptos.
          Para los otros {actual['controles']['conceptos']} preparé {actual['controles']['pares']} pares inventados,
          con traducciones válidas y omisiones o confusiones. Son controles técnicos de IA, no traducciones
          publicadas ni una evaluación humana independiente.</p>
          <p>No hice pruebas con otros traductores. Esta etapa se centra en comprobaciones automatizadas y
          revisión de IA. Lee XLIFF 1.2, XLIFF 2.0 y TMX; los formatos nativos de Trados y memoQ quedan fuera
          del soporte anunciado.</p>
          <p>La búsqueda dentro del segmento puede atribuir una palabra al referente equivocado. Por ejemplo,
          «equipo» puede corresponder a otro componente y hacer que una traducción de <i lang="en">rig</i>
          quede sin aviso. El análisis contextual con un único LLM está en estudio y sigue en pausa.</p>
        </details>
      </div>
      <div class="tc-evidence" aria-labelledby="tc-comparacion-reciente">
        <h3 id="tc-comparacion-reciente">Comparación reciente sobre ejemplos conocidos</h3>
        <p class="tc-evidence-context">Referencia mixta humana/IA · {referencia['evaluables']} casos evaluables
        en {referencia['oraciones']} oraciones, traducidas por tres sistemas.</p>
        <p>Volví a revisar los mismos casos con el glosario 1.2 y con el glosario 1.4.
        En esta muestra, las reformas del glosario redujeron las falsas alarmas:</p>
        <div class="tc-metrics">
          <div><strong>{antes['FP']} → {despues['FP']}</strong><span>falsas alarmas</span>
            <p>{antes['FP'] - despues['FP']} avisos innecesarios menos según la referencia.</p></div>
          <div><strong>{antes['FN']} → {despues['FN']}</strong><span>errores sin señalar</span>
            <p>De {antes['TP'] + antes['FN']} errores de la referencia, ahora quedan {despues['FN']} sin marcar.</p></div>
          <div><strong class="tc-metric-comparison">{precision_antes} % → {precision_despues} %</strong><span>precisión observada</span>
            <p>Proporción de avisos que coinciden con errores de esa referencia.</p></div>
        </div>
        <p class="tc-evidence-context">Estas oraciones ya se usaron para ajustar el glosario. Los resultados
        describen esos ejemplos y no estiman el rendimiento en textos nuevos.</p>
        <details class="tc-project-details"><summary>Referencia y límites de esta comparación</summary>
          <p>La reserva reúne {referencia['unidades']} unidades de término: {referencia['humanas']} decisiones
          humanas y {referencia['ia']} anotaciones complementarias de GPT-6.2 Astra.
          Se excluyeron {referencia['excluidas']} casos por alcance. La selección se hizo con el glosario 1.2;
          no mide la cobertura completa de la edición actual.</p>
          <p>El punto de partida usa el motor {e(actual['motor_antes'])} y el glosario 1.2; la comparación
          usa el motor {e(actual['motor_despues'])} y el glosario 1.4. Una comprobación posterior con
          {e(actual['version_comprobada'])} sobre los mismos textos conserva esos resultados.</p>
          <p>
          La mejora no es uniforme: en otra muestra pequeña revisada por IA, aceptar «equipo» como variante
          de <i lang="en">rig</i> permite el uso válido, pero también deja pasar un error de atribución contextual.
          No retiré la variante porque está aceptada para el encargo.</p>
        </details>
      </div>
      <div class="tc-evidence" aria-labelledby="tc-evaluacion-historica">
        <h3 id="tc-evaluacion-historica">Evaluación histórica · Motor 0.1 y glosario v1</h3>
        <p class="tc-evidence-context">Revisión humana de 20 oraciones · {tc['n']} casos de término en traducción.
        Estas cifras corresponden a esa edición, no a una evaluación independiente de la versión actual.</p>
        <div class="tc-metrics">
          <div><strong>{tc['tp']} de {errores}</strong><span>errores detectados</span>
            <p>De los errores identificados en la revisión humana, detectó el {round(100 * tc['tp'] / errores)} %.</p></div>
          <div><strong>{precision} %</strong><span>de los avisos eran errores reales</span>
            <p>{tc['tp']} de sus {avisos} avisos coincidieron con la revisión humana.</p></div>
          <div><strong>{tc['fp']} frente a {base['fp']}</strong><span>falsas alarmas</span>
            <p>Menos avisos innecesarios que buscar solo la traducción preferida como texto exacto.</p></div>
        </div>
        <div class="tc-evidence-table"><table>
          <caption>La evaluación comparó dos maneras de revisar los mismos {tc['n']} casos de término en traducción</caption>
          <thead><tr><th scope="col">Resultado</th><th scope="col">Búsqueda exacta</th><th scope="col">TermCheck</th></tr></thead>
          <tbody>
            <tr><th scope="row">Errores detectados, de {errores}</th><td>{base['tp']}</td><td>{tc['tp']}</td></tr>
            <tr><th scope="row">Falsas alarmas</th><td>{base['fp']}</td><td>{tc['fp']}</td></tr>
            <tr><th scope="row">Errores que quedaron sin marcar</th><td>{base['fn']}</td><td>{tc['fn']}</td></tr>
          </tbody>
        </table></div>
        <p>Al revisar las traducciones de DeepL, TermCheck encontró 21 de los 23 errores terminológicos
        anotados y generó 2 falsas alarmas. Esta cifra mide la revisión de los términos con el glosario;
        no compara la calidad global de las traducciones.</p>
        <div class="tc-evidence-table"><table>
          <caption>TermCheck revisando 40 casos traducidos con DeepL</caption>
          <thead><tr><th scope="col">Resultado</th><th scope="col">Casos</th></tr></thead>
          <tbody>
            <tr><th scope="row">Errores terminológicos detectados</th><td>{deepl['tp']} de {deepl['errores']}</td></tr>
            <tr><th scope="row">Falsas alarmas</th><td>{deepl['fp']}</td></tr>
            <tr><th scope="row">Errores que quedaron sin marcar</th><td>{deepl['fn']}</td></tr>
          </tbody>
        </table></div>
        <details class="tc-project-details"><summary>Cómo leer estos resultados</summary>
          <p>La muestra reúne {tc['n']} casos: 40 unidades de término y oración traducidas por tres sistemas,
          en 20 oraciones. No son {tc['n']} contextos distintos. Las traducciones se anotaron sin ver
          qué sistema las produjo ni qué decía el verificador, siguiendo el criterio de uso argentino aplicado al glosario.</p>
          <p>La comparación fue con una búsqueda exacta; no se evaluó TermCheck frente a un LLM usado como revisor.
          En la fila de DeepL, las cifras muestran cómo el verificador clasificó términos de esas traducciones;
          no enfrentan a TermCheck con DeepL como traductores ni miden la calidad general de DeepL.
          Estos números corresponden a la versión 0.1 y al glosario v1, no estiman el rendimiento
          de la edición actual. La muestra es pequeña y los resultados tienen incertidumbre.</p>
          <p>Para contrastar casos y apoyar las pruebas también usé Fable 5.2 Max y GPT 6.2 Astra Max.
          En esta evaluación histórica, los resultados numéricos publicados se calcularon contra la anotación de referencia
          descrita en esta sección.</p>
          <p>En la publicación, el intervalo de confianza del 95 % es 76–94 % para la precisión
          y 82–97 % para la detección de errores.</p>
        </details>
        <p class="tc-evidence-note"><a href="{e(FUENTE)}" target="_blank" rel="noopener">Consultar el método y los resultados completos</a>.</p>
      </div>
    </section>
    <section class="tc-project-section" aria-labelledby="tc-como-funciona">
      <div class="tc-project-heading">
        <h2 id="tc-como-funciona">Cómo funciona por dentro</h2>
        <p>El proceso tiene cuatro pasos: del texto de entrada a una marca que podés revisar.</p>
      </div>
      <ol class="tc-architecture">
        <li><h3>Recibe los textos y el glosario</h3><p>La interfaz, hecha con {e(interfaz)},
        recibe el original en inglés y su traducción. También lee CSV, TSV, XLIFF y TMX.
        El glosario aporta las equivalencias y las decisiones de uso.</p></li>
        <li><h3>Reconoce los términos</h3><p>Aplica NLP (procesamiento del lenguaje natural) y técnicas
        de lingüística computacional: Python y spaCy analizan formas y categorías para reconocer plurales
        y distinguir el sustantivo <i lang="en">well</i> de la expresión <i lang="en">as well as</i>.</p></li>
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
      No encontrar avisos no garantiza que toda la traducción esté bien. La interpretación del contexto
      y la decisión final quedan en manos de quien revisa.</p>
    </section>
    """


def mostrar():
    import streamlit as st
    st.html(contenido())
