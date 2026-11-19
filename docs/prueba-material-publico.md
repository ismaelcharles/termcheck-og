# Prueba de importación con material público

Fecha: 19 de noviembre de 2026. TermCheck 0.2.4, glosario 1.3.

Se probaron dos fuentes públicas: un texto petrolero bilingüe y una memoria de traducción original.
La lectura, la verificación, la revisión en pantalla y la descarga CSV funcionaron. La prueba encontró
avisos por coincidencias léxicas fuera del dominio y por una variante con palabras intercaladas.
No se anotó una referencia de corrección ni se calcularon precisión, recall o F1.

## Fuentes y preparación

- **Directiva 2013/30/UE, artículo 2.** Texto sobre seguridad de operaciones petroleras y gasíferas mar adentro,
  en [inglés](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013L0030) y
  [español](https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX:32013L0030).
  La descarga se realizó desde el [repositorio de publicaciones de la UE](https://publications.europa.eu/resource/celex/32013L0030),
  negociando `Accept: application/xhtml+xml` y `Accept-Language: en` o `es`, porque EUR-Lex devolvía
  respuestas vacías en la descarga directa. Se extrajeron los 48 párrafos de contenido del artículo 2,
  se normalizaron espacios y se excluyeron títulos y marcadores de numeración. Los pares se alinearon
  por su posición y se revisó la correspondencia de las definiciones. Se crearon TSV, XLIFF 1.2 y TMX
  localmente: el texto es público y real; los dos contenedores XML son derivados, no exportaciones de un CAT.
- **DGT-TM, publicación 2011, volumen `Vol_2006_5.zip`.** Descarga del
  [archivo oficial](https://wt-public.emm4u.eu/Resources/DGT-TM-2011/Vol_2006_5.zip), enlazado desde la
  [página de DGT-TM](https://joint-research-centre.ec.europa.eu/language-technology-resources/dgt-translation-memory_en).
  Se usó el miembro `E2006C0069.tmx` sin modificar, de 587.760 bytes, multilingüe, UTF-16LE con BOM
  y DOCTYPE externo. Se obtuvieron 73 pares inglés–español y se omitieron 11 unidades con inglés sin español.
  Se cotejaron los pares leídos contra las variantes del XML original. Es material administrativo de EFTA,
  utilizado para comprobar el formato y el comportamiento fuera del dominio; no es un encargo petrolero.

Fuente y titular de DGT-TM: Comisión Europea, que conserva la propiedad de los datos.
Consulta y descarga: 19 de noviembre de 2026; publicación del conjunto utilizada: 2011.
La extracción y el uso se identifican aquí conforme a las condiciones de reutilización de la página de DGT-TM.
No se atribuyen los contenedores derivados ni los avisos de TermCheck a las instituciones de origen.

## Resultados de funcionamiento

| Entrada | Pares leídos | Sin español omitidos | Apariciones reconocidas | Avisos |
|---|---:|---:|---:|---:|
| Artículo 2, XLIFF derivado | 48 | 0 | 3 | 3 |
| Artículo 2, TMX derivado | 48 | 0 | 3 | 3 |
| DGT-TM original | 73 | 11 | 8 | 8 |

Los CSV de la CLI para el XLIFF y el TMX derivados son idénticos byte por byte.
Chromium comprobó la carga del XLIFF de 48 pares y del TMX original de 73 pares en la demo local,
la advertencia de las 11 omisiones, los totales en pantalla y la descarga CSV con 3 y 8 filas de resultados,
respectivamente. No hubo excepciones JavaScript. Esta comprobación fue local; no se modificó producción.

## Hallazgos de la prueba inicial

1. **`case/cases` se detecta como `casing` (T031).** Ocurre dos veces en la directiva y ocho en el TMX
   administrativo. En esos contextos se trata de «caso/casos», no de cañería. Son coincidencias de detección
   fuera del sentido técnico, no errores demostrados de las traducciones. Conviene corregir esta confusión
   y comprobar que se sigan reconociendo `casing` y sus formas pertinentes.
2. **`well control` → «control de un pozo».** La traducción oficial del artículo 2 produce NO_ENCONTRADO
   porque el glosario espera «control de pozo». El aviso señala una forma no reconocida; por sí solo no
   demuestra un error. El reconocimiento de modificadores intercalados continúa limitado.

En esta prueba inicial no se cambió el motor ni el glosario. La versión 0.2.5 corrigió después ambos
hallazgos y amplió la comprobación; el [registro posterior](pruebas-traducciones-publicas.md) documenta
el antes y el después. El español europeo de las fuentes puede
diferir del encargo argentino; esas diferencias requieren juicio contextual y no equivalen automáticamente
a errores. La baja cobertura del glosario en esta muestra tampoco permite evaluar la traducción completa.

## Evidencias

Los archivos de entrada, los originales descargados, el script de preparación, las huellas SHA-256,
los reportes CSV/HTML y las capturas de Chromium se conservan localmente en `salida/prueba-publica/`.
El [resumen de comprobación](prueba-material-publico.json) versiona las procedencias, las huellas,
los conteos y el resultado del recorrido de navegador sin incorporar el volumen completo al repositorio.

Esta prueba aporta un TMX público original y texto externo al corpus. Sigue pendiente una exportación
real de Trados o memoQ y una prueba de uso con traductores.
