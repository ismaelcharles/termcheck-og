# Correcciones y pruebas con traducciones públicas

19 de noviembre de 2026. Comparación de TermCheck 0.2.4 y 0.2.5, con el mismo glosario 1.3.

Se probaron cinco muestras, con 186 segmentos inglés–español. Los cambios eliminaron 11 detecciones de
`case/cases` como `casing` y reconocieron «control de un pozo» sin aviso. Las demás apariciones conservaron
sus etiquetas. No se cambió el glosario ni se recalcularon las evaluaciones anteriores.

## Correcciones

- **Formas inglesas en -ing.** El lema que spaCy asigna a `casing` puede ser `case`. Ahora, cuando una de
  las formas comparadas termina en -ing o -ings, se exige coincidencia de la forma o de su plural simple.
  Se conservan `casing/casings` y las variantes explícitas del glosario, sin equipararlas a `case/cases`.
- **Artículo indefinido en español.** Una forma puede incluir `un/una/unos/unas` después de «de» y ante un
  sustantivo: «control de un pozo» conserva «control de pozo». El tramo completo se resalta y se reserva
  para ese término. La regla también se aplica a formas prohibidas y no omite palabras como «otro»,
  «ningún» ni adjetivos intercalados. «De» y «del» continúan siendo distintos.
- **Versión visible.** La leyenda de la demo toma la versión del motor, para que la pantalla y el reporte
  descargado identifiquen la misma edición.

Las regresiones automáticas usan frases inventadas, incluidos controles negativos y formas técnicas válidas.
La muestra histórica de evaluación y sus archivos congelados no se usaron para ajustar estas reglas.

## Material y procedencia

1. **EUR-Lex, Directiva 2013/30/UE, artículo 2:** los mismos 48 pares de la
   [prueba inicial](prueba-material-publico.md).
2. **DGT-TM 2011, `E2006C0069.tmx`:** 73 pares de un TMX original, con 11 unidades sin español omitidas.
3. **DGT-TM 2011, `E2006G0001.tmx`:** 47 pares de otro TMX original del mismo volumen, con tres unidades
   sin español omitidas. Es un control fuera del dominio petrolero.
4. **IFC, Offshore Oil and Gas Development (2015):** 16 párrafos numerados, 49–58 y 114–119, de las versiones
   [inglesa](https://www.ifc.org/content/dam/ifc/doc/2010/2015-offshore-oil-gas-development-ehs-guidelines-en.pdf)
   y [española](https://www.ifc.org/content/dam/ifc/doc/2010/2015-offshore-oil-gas-development-ehs-guidelines-es.pdf).
   Cubren fluidos de perforación y control de pozos.
5. **IFC, Onshore Oil and Gas Development (2007):** dos párrafos equivalentes de la sección Well Blowouts /
   Reventones en los pozos, en las versiones
   [inglesa](https://www.ifc.org/content/dam/ifc/doc/2000/2007-onshore-oil-gas-development-ehs-guidelines-en.pdf)
   y [española](https://www.ifc.org/content/dam/ifc/doc/2000/2007-onshore-oil-gas-development-ehs-guidelines-es.pdf).

Los enlaces de IFC se obtuvieron de su [catálogo oficial](https://www.ifc.org/en/insights-reports/general-environmental-health-and-safety-guidelines/ehs-guidelines-oil-gas-mining).
Se conservaron los PDF y sus SHA-256. Se extrajo texto con `pdftotext`, excluyendo cabeceras, pies y notas;
los párrafos se alinearon por numeración o sección. Se repararon dos viñetas desplazadas por la extracción
y espacios sobrantes ante signos de puntuación. La repetición del párrafo 116 está en ambos originales y
se conservó. GPT-6.2 Astra revisó la alineación de los 18 pares de IFC, cotejó los textos y registró juicios
terminológicos cualitativos según el encargo argentino. Esa revisión es de IA, no una referencia humana.

Los XLIFF 1.2 y TMX de los pares de IFC se construyeron localmente; se verificó que devolvieran los mismos
pares al leerlos. Son traducciones técnicas publicadas, no encargos privados ni exportaciones de Trados o memoQ.
Los dos TMX de DGT se usaron sin modificar. La Comisión Europea conserva la propiedad de DGT-TM;
fuente, publicación 2011, descarga del 19 de noviembre de 2026 y condiciones de uso se registran en la
[prueba inicial](prueba-material-publico.md).

## Resultados de funcionamiento

| Muestra | Segmentos | Apariciones 0.2.4 → 0.2.5 | Avisos 0.2.4 → 0.2.5 |
|---|---:|---:|---:|
| Directiva, artículo 2 | 48 | 3 → 1 | 3 → 0 |
| DGT, primera memoria | 73 | 8 → 0 | 8 → 0 |
| DGT, memoria de control | 47 | 0 → 0 | 0 → 0 |
| IFC, costa afuera | 16 | 69 → 68 | 7 → 6 |
| IFC, operaciones terrestres | 2 | 13 → 13 | 0 → 0 |
| Total | 186 | 93 → 82 | 18 → 6 |

La comparación usa exactamente los mismos pares y la misma edición del glosario. El motor anterior se
copió del commit `05cbf049b00fb02998c4e72dcf8eacdf3288eafc`, sin cambiar el checkout ni el estado congelado.
Las apariciones son las del reporte del motor; no son unidades de referencia humana.

Chromium comprobó los cinco archivos en la demo local: carga, unidades omitidas, cobertura, revisión,
descargas CSV y HTML, y versión del reporte. Los CSV del navegador coinciden con la CLI en sus campos
de resultados; el identificador del sistema de entrada puede diferir. Se probaron además tres regresiones
desde los cuadros de texto. Las memorias sin términos muestran explícitamente ausencia de cobertura.

## Avisos y límites que siguen abiertos

Quedan seis apariciones para revisar en IFC costa afuera. La revisión cualitativa de Astra distinguió:

- **Dos `pipe ram` y un `kick`:** juzgó incorrectas las traducciones como componentes de corte y como
  «golpe de presión», respectivamente. Los avisos se conservan según el glosario.
- **`rig` → «torre de perforación»:** estrecha el referente en el párrafo 53; «equipo de perforación»
  expresa mejor el conjunto al que regresa el fluido. Se conserva el aviso.
- **`cement bond log` → «registro de adherencia del cemento»:** Astra lo consideró una variante técnica
  válida, ausente del glosario. Se mantiene NO_ENCONTRADO hasta una decisión terminológica del autor.
- **`disposal well`:** el párrafo traduce «pozo de evacuación», distinto de «pozo sumidero». El motor
  marca «eliminación», que aparece en la gestión de fluidos y cortes. La ficha prohíbe esa palabra
  aislada; la búsqueda por segmento la atribuye al término aunque tenga otro referente. Se consultó
  al autor si corresponde retirar la prohibición aislada, conservando «pozo de eliminación».

En la muestra terrestre, Astra también observó *well control drills* traducido como «perforaciones
regulares de control del pozo». El término *well control* está reconocido, pero el sentido de *drills*
en capacitación queda fuera de los conceptos actuales del glosario. Cero avisos no valida esa oración.

Estas pruebas verifican funcionamiento y documentan ejemplos. No estiman precisión o recall, no comparan
la calidad general de las traducciones y no validan el contenido como instrucciones operativas.
Continúan pendientes las exportaciones reales de Trados/memoQ y la prueba de uso con traductores.

## Evidencia

El [resumen agregado](pruebas-traducciones-publicas.json) contiene conteos, huellas y procedencias.
Los PDF, pares alineados, revisión de Astra, scripts de preparación/comparación, reportes y capturas se
conservan en `salida/prueba-publica/ampliacion/`. El archivo de muestras se mantiene separado de la
evaluación histórica y de la referencia mixta de las 60 oraciones.
