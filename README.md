# TermCheck O&G

Verificador de terminología para traducción automática inglés → español en Oil & Gas upstream, con el español
técnico de Argentina como variante. Está pensado para quien post-edita o revisa traducciones técnicas y hoy
controla los términos a ojo, segmento por segmento.

Recibe el texto en inglés, su traducción y un glosario bilingüe. Marca los términos del glosario que quedaron mal
traducidos, sin traducir o con una forma que el glosario no conoce. No traduce ni corrige estilo.

## 1. El problema

La traducción automática produce frases fluidas y aun así falla en los términos del dominio. En un procedimiento
de perforación o de seguridad, un término mal traducido es un error caro, y cuesta verlo porque la frase suena
bien. Los glosarios generales tampoco alcanzan: muchas formas que se usan en España o en otros países no son las
que se usan en un yacimiento argentino.

<!-- autor:ejemplos:inicio -->
> **Pendiente, lo completa el autor.** Dos ejemplos reales del corpus: la oración en inglés, lo que tradujo el
> sistema y la forma que se usa en Argentina.
<!-- autor:ejemplos:fin -->

## 2. Demo

Se puede probar sin cuenta en **https://termcheck.aval.site/demo**

Se pega el texto en inglés y su traducción, o se sube un archivo de dos columnas, y devuelve el reporte. El botón
«Cargar un ejemplo» pone tres oraciones del corpus traducidas con Opus-MT. También acepta un glosario propio en
CSV. Corre en un servidor compartido, así que tiene límites: archivos de hasta 1 MB, 200 segmentos y 20.000
letras por lado. Los textos no se guardan.

![La demo con el ejemplo cargado: el texto en inglés, la traducción y el reporte con los términos resaltados](docs/img/demo.png)

## 3. Cómo funciona

```
 glosario.csv ─┐
               ├─► [1] Normalizar ─► [2] Detectar términos ─► [3] Buscar traducción ─► [4] Clasificar ─► [5] Reporte
 origen (EN) ──┤     (minúsculas,       en el inglés             en el español           (etiqueta por     (HTML y CSV)
 destino (ES) ─┘      tildes, guiones)  (lemas y categoría)      (lemas y raíces)         aparición)
```

1. **Normalizar.** Se comparan los textos en minúsculas, sin tildes y con los guiones unificados. El reporte
   muestra el texto original.
2. **Detectar los términos en inglés.** Cada término del glosario se busca en la oración de origen por lema y
   por forma, con spaCy. En los términos de una palabra se mira la categoría gramatical, para no confundir el
   sustantivo «well» con «as well as». Si dos términos se pisan, gana el más largo.
3. **Buscar la traducción.** Para cada término detectado se buscan en la traducción la forma preferida, las
   formas válidas y las prohibidas. El español cambia en género y número, así que se compara por lema y, como
   respaldo, por raíz (Snowball).
4. **Clasificar** cada aparición con una etiqueta.
5. **Reportar.** Un HTML con los términos resaltados por color y un CSV con una fila por aparición.

| Etiqueta | Qué significa | Se marca para revisar |
|---|---|---|
| `OK` | Aparece la traducción preferida | No |
| `VARIANTE` | Aparece una forma válida que no es la preferida | No, es informativa |
| `PROHIBIDO` | Aparece una forma que el glosario da por incorrecta | Sí |
| `SIN_TRADUCIR` | El término quedó en inglés y el glosario no lo acepta como préstamo | Sí |
| `NO_ENCONTRADO` | El término está en el inglés y ninguna forma conocida aparece en la traducción | Sí |
| `INCONSISTENTE` | En el mismo documento, el término se tradujo de más de una manera | Advertencia |

Los casos difíciles (plural y género, tildes, «as well as», términos que se pisan, préstamos aceptados, siglas,
variantes de escritura en inglés) están cubiertos con pruebas automáticas en `tests/test_hard_cases.py`.

## 4. Resultados

El verificador se mide contra una anotación humana hecha a ciegas: para cada término del glosario en cada
traducción, el autor anotó si estaba bien o mal sin ver qué sistema la produjo ni qué decía el verificador. Se
tradujeron 120 oraciones con tres sistemas (Opus-MT, Claude sin glosario y DeepL).

- **Recall:** de los errores que anotó el autor, qué parte marca el verificador. Es la medida que más importa.
- **Precisión:** de lo que marca el verificador, qué parte era un error.
- **Baseline:** el método ingenuo, que busca la forma preferida como texto exacto. La diferencia con el
  verificador es lo que aportan los lemas, las raíces y las formas válidas del glosario.

<!-- resultados:inicio (lo escribe scripts/actualizar_readme.py; no editar a mano) -->
Evaluación final sobre el conjunto de prueba, con el glosario v1 congelado. Calculada el 2026-11-14.

120 términos anotados en 20 oraciones (52 errores según la anotación). El verificador no detectó 0 de ellos (cuentan como no marcados).

### Verificador frente al baseline

| Método | Términos | TP | FP | FN | TN | Precisión (IC 95 %) | Recall (IC 95 %) | F1 |
|---|---:|---:|---:|---:|---:|---|---|---:|
| Baseline (texto exacto) | 120 | 51 | 19 | 1 | 49 | 0,73 (0,61–0,82) | 0,98 (0,90–1,00) | 0,84 |
| TermCheck | 120 | 48 | 8 | 4 | 60 | 0,86 (0,74–0,93) | 0,92 (0,82–0,97) | 0,89 |

### Por sistema de traducción (TermCheck)

| Sistema | Términos | TP | FP | FN | TN | Precisión (IC 95 %) | Recall (IC 95 %) | F1 |
|---|---:|---:|---:|---:|---:|---|---|---:|
| claude | 40 | 3 | 2 | 1 | 34 | 0,60 (0,23–0,88) | 0,75 (0,30–0,95) | 0,67 |
| deepl | 40 | 21 | 2 | 2 | 15 | 0,91 (0,73–0,98) | 0,91 (0,73–0,98) | 0,91 |
| opusmt | 40 | 24 | 4 | 1 | 11 | 0,86 (0,69–0,94) | 0,96 (0,80–0,99) | 0,91 |

### Errores de terminología según la anotación, por sistema

| Sistema | Términos | Errores | % | Error de término | Omisión | Sin traducir |
|---|---:|---:|---:|---:|---:|---:|
| claude | 40 | 4 | 10,00 | 4 | 0 | 0 |
| deepl | 40 | 23 | 57,50 | 23 | 0 | 0 |
| opusmt | 40 | 25 | 62,50 | 24 | 1 | 0 |

### Recall por tipo de error (TermCheck)

| Etiqueta del dueño | Casos | Detectados |
|---|---:|---:|
| ERROR_TERMINO | 51 | 48 |
| OMISION | 1 | 0 |
| SIN_TRADUCIR | 0 | 0 |

### Qué etiqueta dio el verificador según la anotación

| Anotación \ Verificador | OK | VARIANTE | PROHIBIDO | SIN_TRADUCIR | NO_ENCONTRADO | (no detectado) |
|---|---:|---:|---:|---:|---:|---:|
| CORRECTO | 51 | 10 | 0 | 0 | 7 | 0 |
| ERROR_TERMINO | 1 | 2 | 7 | 0 | 41 | 0 |
| OMISION | 0 | 1 | 0 | 0 | 0 | 0 |
| SIN_TRADUCIR | 0 | 0 | 0 | 0 | 0 | 0 |

IC 95 %: intervalo de Wilson. Con pocos casos es ancho: los números son orientativos.
<!-- resultados:fin -->

### Hallazgos

<!-- autor:hallazgos:inicio -->
> **Pendiente, lo completa el autor** cuando esté la evaluación final: qué sistema maneja mejor la terminología,
> qué tipos de error aparecen más y por qué falla el verificador cuando falla.
<!-- autor:hallazgos:fin -->

## 5. Validación

No hubo entrevistas ni pruebas con traductores. El plan original preveía mostrarle la herramienta a entre 3 y 5
personas; eso no se hizo. Hasta ahora el verificador se midió solo contra la anotación del autor y nadie más lo
usó con textos propios.

## 6. Limitaciones

- **Pocos datos.** La prueba tiene 20 oraciones (el plan preveía 80) y el conjunto de desarrollo 15. Los
  intervalos de confianza son anchos y los números son orientativos.
- **Un solo anotador humano.** La anotación refleja el criterio de una persona. El segundo anotador fue un
  modelo de lenguaje (Claude Fable 5.2), que anotó a ciegas las mismas oraciones y solo se usó para medir el
  acuerdo. En la prueba coincidieron en 98 de 120 términos (acuerdo 0,82; kappa de Cohen 0,62 con las cuatro
  etiquetas y 0,61 con correcto o error). En desarrollo, sobre 111 términos, el kappa fue 0,55 y 0,54. En casi
  todos los desacuerdos el autor marcó error y el modelo, correcto.
- **«Correcto» por defecto.** La pantalla de anotación tiene un botón que pone «Correcto» en todo lo que falta
  de una oración. Ahorra tiempo y puede hacer que algún error pase como correcto.
- **Fuentes del glosario.** El respaldo escrito es sobre todo un glosario general de español sin variedad
  regional. Parte de los apuntes de curso que se consultaron se generaron con herramientas de IA y no sirven
  como prueba de uso argentino. Donde las fuentes no alcanzaban, la forma preferida es criterio de campo del
  autor. El detalle está en `data/glossary/SOURCES.md`.
- **Glosario chico y solo de sustantivos.** Son 99 términos. 20 de ellos no aparecen en ninguna oración del
  corpus, así que no se evaluaron.
- **El corpus son textos del gobierno de EE. UU.** (OSHA y reglamentos federales). Es inglés de normas y de
  seguridad, no documentación operativa de una empresa.
- **`NO_ENCONTRADO` no distingue causas.** Puede ser un error, una omisión o un sinónimo correcto que el
  glosario no lista. Lo decide quien revisa.
- **No hay alineación de palabras.** El verificador busca las formas dentro del segmento entero. Si un término
  aparece dos veces y una sola está bien traducida, puede no verlo.
- **Términos dentro de otros.** Si un término del glosario queda dentro de otro más largo, solo se evalúa el
  largo.
- **Una sola variante y un solo par de lenguas.** Inglés → español técnico de Argentina.
- **Las traducciones no se pueden repetir igual.** Claude y DeepL pueden contestar distinto otro día. La fecha
  y la versión de cada sistema están en `data/mt/versiones.csv`.

## 7. Cómo usarlo

Probado en Linux con Python 3.12.

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm
.venv/bin/python -m spacy download es_core_news_sm
```

`requirements.txt` incluye `torch` y `transformers`, que solo hacen falta para volver a traducir con Opus-MT
(`scripts/translate_opusmt.py`). Para verificar no se usan.

Verificar un par de archivos de texto, con una oración por línea y en el mismo orden:

```
.venv/bin/python scripts/run_check.py --src origen.txt --tgt traduccion.txt --out salida/mio
```

Verificar un archivo XLIFF 1.2, XLIFF 2.0 o TMX. La página Verificar también los acepta en «Subir archivo»:

```
.venv/bin/python scripts/run_check.py --file proyecto.xliff --out salida/proyecto
```

Escribe `salida/mio.csv` y `salida/mio.html`. Con `--glossary` se usa otro glosario, con las mismas columnas que
`data/glossary/glossary_en_es.csv`.

La demo en la propia máquina (solo la página de verificación):

```
.venv/bin/streamlit run app/demo.py
```

La app completa, con el glosario, la anotación y los resultados, sin inicio de sesión:

```
TERMCHECK_SIN_LOGIN=1 .venv/bin/streamlit run app/streamlit_app.py
```

Las dos quedan en http://127.0.0.1:8501.

Las pruebas automáticas y la evaluación:

```
.venv/bin/python -m pytest -q
.venv/bin/python scripts/evaluate.py
```

Qué hay en cada carpeta:

| Carpeta | Contenido |
|---|---|
| `src/termcheck/` | El verificador: glosario, normalización, detección, clasificación, consistencia y reporte |
| `scripts/` | Armado del corpus, traducción, división en conjuntos, verificación, baseline y evaluación |
| `app/` | La app web (Streamlit): glosario, traducciones, anotación, verificación y resultados; `demo.py` es la demo pública |
| `data/` | Glosario, corpus, traducciones, división en conjuntos y anotación |
| `tests/` | Pruebas automáticas, con un proyecto inventado que no toca los datos reales |
| `docs/` | La guía de anotación y los hallazgos |

## 8. Datos y licencias

- **Código:** MIT (archivo `LICENSE`).
- **Corpus:** 120 oraciones en inglés de textos del gobierno federal de EE. UU., sin copyright. Cada una lleva
  la dirección de su página de origen.
- **Glosario, anotación y traducciones:** hechos para este proyecto. Su licencia todavía no está definida.

Las fuentes de cada término, lo que se excluyó por copyright y el método de cada sistema de traducción están en
[`data/glossary/SOURCES.md`](data/glossary/SOURCES.md) y en [`data/mt/README.md`](data/mt/README.md).

## 9. Próximos pasos

- Un segundo anotador humano sobre una parte de la prueba, para medir el acuerdo entre personas.
- Más formas prohibidas en el glosario, cada una con un error real que la respalde.
- Probar la lectura de XLIFF y TMX con exportaciones reales de Trados y memoQ. Hoy lee XLIFF 1.2, XLIFF 2.0 y TMX
  según la norma, probados con archivos armados a mano. No lee `.sdlxliff` ni `.mqxliff`.
- Probar la herramienta con traductores que hagan post-edición técnica.
