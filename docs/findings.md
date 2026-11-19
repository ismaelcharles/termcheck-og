# Hallazgos

> Redactado por Claude el 2026-11-14 a pedido del autor, con su anotación, sus comentarios y el glosario v1. Los
> números salen de `salida/eval_prueba.md` y los casos de `salida/eval_prueba_casos.csv`.

## Con qué se midió

- Conjunto de prueba: 20 oraciones y 120 términos anotados (53 errores según la anotación).
- Glosario: `data/glossary/glossary_v1.csv`, congelado el 2026-11-14 (99 términos, sha256 `5c7f9844eb4d7525`) antes de anotar la prueba.
- Un solo anotador humano. La guía está en `docs/annotation_guidelines.md`. Un modelo de lenguaje anotó lo mismo
  a ciegas para medir el acuerdo (punto 4).

## 1. Verificador frente al baseline

El baseline busca la traducción preferida como texto exacto en minúsculas.

| Método | Precisión | Recall | F1 |
|---|---|---|---|
| Baseline | 0,74 (0,63–0,83) | 0,98 (0,90–1,00) | 0,85 |
| TermCheck | 0,88 (0,76–0,94) | 0,92 (0,82–0,97) | 0,90 |

Entre paréntesis, el intervalo de confianza del 95 % (Wilson). El baseline da 18 falsos positivos y 1 falso
negativo; TermCheck, 7 y 4.

El baseline casi no deja pasar errores (recall 0,98) porque marca todo lo que no sea la forma preferida escrita
igual. Por eso da 18 falsas alarmas sobre 67 términos correctos: marca plurales, formas válidas del glosario y
variantes de escritura. TermCheck baja las falsas alarmas a 7, porque reconoce las formas válidas y los plurales,
y a cambio deja pasar 4 errores. La precisión sube de 0,74 a 0,88 y el recall baja de 0,98 a 0,92.

Los intervalos de los dos métodos se pisan. Con 120 términos la diferencia de F1 (0,90 contra 0,85) no alcanza
para decir que uno es mejor que el otro. Lo que sí se ve es de dónde sale cada error, y eso está en el punto 3.

En desarrollo la diferencia fue mayor (F1 0,95 contra 0,72). Ese número es optimista, porque el glosario se
ajustó con esas mismas oraciones.

## 2. Errores de terminología por sistema de traducción

| Sistema | Términos | Errores | Error de término | Omisión | Sin traducir |
|---|---|---|---|---|---|
| Opus-MT | 40 | 26 (65,0 %) | 25 | 1 | 0 |
| Claude | 40 | 4 (10,0 %) | 4 | 0 | 0 |
| DeepL | 40 | 23 (57,5 %) | 23 | 0 | 0 |

Claude es el que mejor maneja la terminología: 4 errores en 40 términos. DeepL y Opus-MT se equivocan en más
de la mitad. Ningún sistema recibió el glosario.

- **Opus-MT** traduce palabra por palabra y el resultado no es terminología de ningún país: «obras de dibujo»
  (*drawworks*), «ascensores» (*elevators*), «carcasa» (*casing*), «taladro» (*driller*), «bodega» (*cellar*),
  «varilla aspirante» (*sucker rod*). Tiene la única omisión: en S091 desaparece *workover*.
- **DeepL** escribe frases correctas con términos de español general o de otra variedad: «cabrestante»
  (*drawworks*), «mesa giratoria» (*rotary table*), «tenazas» (*tongs*), «plataformas» (*rig*), «tubería»
  (*tubing*), «accionamiento superior» (*top drive*), «operario de torre» (*derrickman*). Son los errores más
  difíciles de ver al revisar, porque la frase suena bien.
- **Claude** usa cañería, espacio anular, top drive y malacate. Sus 4 errores son formas más generales que la
  del glosario: «equipo» (*rig*), «cable» (*wireline*), «línea de suministro» (*flowline*) y
  «reacondicionamiento» (*workover*).

Los términos con más errores entre los tres sistemas son *wireline* y *workover* (5 cada uno), y *drawworks*,
*tongs* y *tubing* (4 cada uno). En *wireline*, *workover*, *tubing*, *top drive* y *kelly* la forma que se usa
en Argentina es la inglesa, y el error del sistema fue traducirla. Por eso no hubo ningún «Sin traducir» en la
prueba: en este dominio los sistemas traducen de más.

## 3. Análisis de errores del verificador

Cada falso positivo (FP) y falso negativo (FN) de `salida/eval_prueba_casos.csv` va en una causa. La columna
«causa_sugerida» es una pista automática; la que vale es la columna «causa», que llena el autor.

| Causa | FP | FN |
|---|---|---|
| Morfología | 0 | 0 |
| Sinónimo que falta en el glosario | 3 | 0 |
| Préstamo | 1 | 0 |
| Ambigüedad | 0 | 3 |
| Término dentro de otro o no detectado | 0 | 0 |
| Error de la anotación | 0 | 0 |
| Coordinación | 3 | 0 |
| Forma del glosario que el autor rechaza | 0 | 1 |
| Total | 7 | 4 |

Las dos últimas causas no estaban en la lista original y se agregaron porque los casos no entraban en las otras.

### Morfología
Ningún caso. Los plurales y los cambios de género se reconocieron bien en la prueba.

### Sinónimo que falta en el glosario
S007, DeepL y Opus-MT. *perforating* → «la perforación». El autor la anotó como correcta, con este comentario
en la misma oración: «perforación es un término aceptado, pero "punzado" es preferido». El glosario solo lista
«punzado» y el verificador marcó `NO_ENCONTRADO`. Se arregla agregando «perforación» como forma válida.

S048, Claude. *the kelly using the kelly spinner* → «el vástago (kelly) con el enroscador del vástago». *kelly*
aparece dos veces en inglés, la segunda dentro de *kelly spinner*, que no está en el glosario. La primera se
encontró. Para la segunda, el autor acepta «vástago» solo («es kelly o vástago») y el glosario lista «vástago de
perforación», así que el verificador marcó `NO_ENCONTRADO`.

### Préstamo
S016, Opus-MT. *gas-lift* → «gas-lift», con guion. El glosario lista «gas lift» y el verificador no iguala las
dos escrituras, así que marcó `NO_ENCONTRADO`.

### Ambigüedad
- S091, Claude y Opus-MT. *workover* → «reacondicionamiento» en Claude y nada en Opus-MT. La oración termina
  con *cannot be repaired*, que los sistemas tradujeron «repararse» y «reparada». El glosario acepta
  «reparación» para *workover*; el verificador igualó la raíz y dio el término por encontrado (`VARIANTE`). Son
  2 de los 4 errores que no marcó.
- S005, DeepL. *kelly* → «varilla Kelly». El verificador encontró «Kelly», que es la forma preferida, y dio
  `OK`. El autor rechaza la expresión entera. El verificador no mira las palabras que rodean al término.

### Término dentro de otro o no detectado
Ningún caso.

### Error de la anotación
Ningún caso en la evaluación final. Hubo uno antes: en S005 la errata «kely» (Opus-MT) se había anotado
«Correcto», y en S061 la misma errata, «Error de término». El 14/11, después de la primera evaluación, el autor
fijó el criterio (valen «kelly» o «vástago») y la etiqueta de S005 pasó a error. Es la única etiqueta de la
prueba que se cambió después de ver resultados. Antes del cambio los números eran: TermCheck, precisión 0,86,
recall 0,92 y F1 0,89; baseline, 0,73, 0,98 y 0,84.

### Coordinación
S101, los tres sistemas. *An oil or gas well* → «Un pozo de petróleo o gas». El verificador busca «pozo de gas»
con las palabras juntas y marcó `NO_ENCONTRADO` en las tres traducciones, que están bien. Ya había pasado en
desarrollo (S053). Es la causa que más falsas alarmas dio.

### Forma del glosario que el autor rechaza
S050, DeepL. *wellhead* → «boca del pozo». El glosario v1 la lista como válida (se agregó el 13/11) y el
verificador dio `VARIANTE`. En la prueba el autor la anotó como error, con el comentario «"boca del pozo" es un
término inadecuado, quitarlo de glosario». El v1 no se tocó, porque se congeló antes de anotar la prueba.

## 4. Acuerdo entre anotadores

El segundo anotador fue un modelo de lenguaje (Claude Fable 5.2). Anotó a ciegas las mismas oraciones, sin ver
qué sistema hizo cada traducción, ni la anotación del autor, ni el verificador. Su anotación está en
`data/annotations/segundo_fable.csv` y solo se usó para medir el acuerdo: la referencia es la anotación del
autor. Los números son de antes de revisar los desacuerdos (`scripts/kappa.py`).

| Conjunto | Términos en común | Acuerdo observado | Kappa (cuatro etiquetas) | Kappa (correcto o error) | Desacuerdos |
|---|---:|---:|---:|---:|---:|
| Desarrollo | 111 | 0,77 | 0,55 | 0,54 | 25 |
| Prueba | 120 | 0,82 | 0,62 | 0,61 | 22 |

En 22 de los 25 desacuerdos de desarrollo y en 19 de los 22 de la prueba, el autor marcó error y el modelo,
correcto. En desarrollo el autor revisó los desacuerdos y corrigió 3 etiquetas propias. En la prueba corrigió 1
(«kely», S005); con ese cambio el kappa de la prueba queda en 0,64 y 0,63.

Un kappa de 0,62 es un acuerdo moderado. Los desacuerdos no son al azar: casi todos van para el mismo lado.

- En 19 casos de la prueba el autor marcó error y el modelo, correcto. Son formas que se entienden y que no se
  usan en un equipo argentino: «cable» por *wireline*, «tubería» por *tubing*, «equipo» por *rig*, «mesa
  giratoria» por *rotary table*, «reacondicionamiento» por *workover*, «operario de torre» por *derrickman*. En
  10 de esos 19 el modelo dejó anotado que dudaba («genérico», «hiperónimo», «no es el término de campo»).
- En 3 casos fue al revés: «perforación» por *perforating* (dos veces) y la errata «kely». Son los mismos
  casos del punto 3.

El modelo acepta la forma general cuando el sentido se conserva. El autor pide la forma de campo. Esa
diferencia es lo que el glosario quiere registrar, y un anotador sin experiencia de campo no la ve. Por eso el
kappa mide acá el acuerdo con un lector general y no la calidad de la anotación. Falta un segundo anotador
humano del rubro.

## Qué cambiaría en la versión 2

Propuestas que salen de los casos de arriba. El orden y la decisión son del autor.

En el glosario:
- Sacar «boca del pozo» de las formas válidas de *wellhead*.
- Agregar «perforación» como forma válida de *perforating* y «vástago» como forma válida de *kelly*.
- Revisar «reparación» como forma válida de *workover*, o pedir que coincida la palabra entera.

En el verificador:
- Reconocer un término partido por una coordinación («pozo de petróleo o gas»).
- Igualar las escrituras con guion y sin guion («gas-lift», «gas lift»).
- No dar por encontrada una forma válida cuando la palabra de la traducción es de otra clase («repararse» no es
  «reparación»).
- Alinear cada término con las palabras que lo traducen. Hoy busca en la oración entera, y por eso se
  confundió en S091.

En la medición:
- Más oraciones. Con 20 los intervalos son anchos.
- Un segundo anotador humano que trabaje en el rubro.
- Textos operativos de empresas argentinas, además de normas de EE. UU.

## Versión 0.2

> Agregado por Claude el 2026-11-15, a pedido del autor. Los números salen de una sola corrida de
> `scripts/evaluate.py --conjunto prueba` con el código de la versión 0.2 ya cerrado.

De las propuestas de arriba para el verificador se hicieron tres. El glosario v1 y la anotación no se tocaron.

| Propuesta | Qué se hizo | Casos de la prueba |
|---|---|---|
| Guion | Una palabra con guion cuenta como sus partes: «gas-lift» es «gas lift» | S016, Opus-MT (1 FP) |
| Coordinación | Una forma de varias palabras vale cuando va coordinada con otra y comparten el principio: «pozo de petróleo o gas» por «pozo de gas» | S101, los tres sistemas (3 FP) |
| Clase de palabra | El respaldo ya no compara por raíz. Solo iguala el plural y el género, así que «repararse» y «reparada» no pasan por «reparación» | S091, Claude y Opus-MT (2 FN) |

### El resultado y cuánto vale

| Versión | TP | FP | FN | TN | Precisión | Recall | F1 |
|---|---:|---:|---:|---:|---|---|---:|
| 0.1 | 49 | 7 | 4 | 60 | 0,88 (0,76–0,94) | 0,92 (0,82–0,97) | 0,90 |
| 0.2 | 51 | 3 | 2 | 64 | 0,94 (0,85–0,98) | 0,96 (0,87–0,99) | 0,95 |

Cambiaron los seis casos de la tabla de arriba y ningún otro. El baseline no cambia (0,74, 0,98 y 0,85).

Este número de la 0.2 es optimista. Las tres reglas salieron de leer los errores de esta prueba, y medirlas
sobre la misma prueba solo muestra que arreglan lo que se quería arreglar y que no rompen otra cosa en esas 20
oraciones. No dice cuánto acierta la 0.2 con oraciones nuevas. La medida del proyecto es la de la 0.1.

Lo que se cuidó para no ajustar de más:

- Cada regla se escribió como regla general y se probó con oraciones inventadas y un glosario mínimo propio
  (`tests/test_version_02.py`). Ninguna prueba automática lee la prueba real.
- Los cambios se miraron solo en desarrollo. Ahí desaparecieron las 3 falsas alarmas de S053 («pozo de petróleo
  o gas», la misma causa) y no cambió ninguna otra etiqueta: 3 FP y 1 FN pasaron a 0 FP y 1 FN, y el F1 de 0,96
  a 0,99.
- La detección de términos en inglés se comparó antes y después en las 120 oraciones y salió idéntica.
- El código se cerró en un commit antes de correr la prueba, y la prueba se corrió una vez.

Con los errores sintéticos de `scripts/inject_errors.py` (desarrollo) no empeoró nada. Los términos en inglés
puestos a propósito se marcan 40 de 40, todos con la etiqueta esperada. Antes eran 37 de 37 y 2 salían como
`NO_ENCONTRADO` en vez de `SIN_TRADUCIR`: era «bridge plugs», un plural inglés que la raíz no igualaba con
«bridge plug» y que la regla del plural sí reconoce.

### Por causa, con la versión 0.2

| Causa | FP | FN |
|---|---|---|
| Sinónimo que falta en el glosario | 3 | 0 |
| Préstamo | 0 | 0 |
| Ambigüedad | 0 | 1 |
| Coordinación | 0 | 0 |
| Forma del glosario que el autor rechaza | 0 | 1 |
| Total | 3 | 2 |

Lo que queda es del glosario o pide mirar las palabras que rodean al término: «perforación» por *perforating*
(S007, 2 FP), «vástago» por *kelly* (S048, 1 FP), «varilla Kelly» (S005, 1 FN) y «boca del pozo» (S050, 1 FN).

### Límites de las reglas nuevas

- La coordinación se reconoce cuando las formas comparten el principio. No se reconoce del otro lado: «lodo o
  fluido de perforación» no vale por «lodo de perforación».
- En una forma coordinada, el principio («pozo de») queda libre para otro término. Si en la oración hay otro
  término que se traduce con esa misma palabra y falta, el verificador puede darlo por encontrado.
- La regla acepta hasta tres palabras entre el principio y la conjunción. Con más, no la reconoce.
- El respaldo iguala el género, así que «zapato» se lee como «zapata». Para *casing shoe* el glosario lista las
  dos, una como preferida y otra como válida, y el verificador responde con la preferida.
- Las formas verbales dependen del lema de spaCy. Si spaCy no reconoce un verbo conjugado, ya no hay raíz que lo
  rescate. El glosario v1 solo tiene sustantivos, así que esto no se midió.
- Sigue sin haber alineación de palabras. El caso S091 se arregló porque «repararse» ya no coincide con
  «reparación», no porque el verificador sepa qué palabra traduce a *workover*.

Al cerrar la versión 0.2 quedaban 60 oraciones reservadas. El 19 de noviembre de 2026 se completó su revisión
con referencia mixta humana/IA, después de utilizarlas para ajustar el glosario. Ya no son una prueba
independiente de la edición actual.

## Revisión posterior de la reserva de 60 oraciones

La revisión reúne 177 decisiones humanas y 270 anotaciones complementarias de GPT-6.2 Astra. De las 447
unidades, dos se excluyen por alcance y 445 son evaluables. Con TermCheck 0.2.4 y glosario 1.3 se obtuvieron
139 TP, 13 FP, 15 FN y 278 TN: precisión 0,914, recall 0,903 y F1 0,908.

La referencia incorpora aclaraciones posteriores del autor y tres resoluciones según el glosario vigente.
La selección humana fue dirigida y las anotaciones de Astra usaron los criterios ya revisados. Estos números
describen ejemplos conocidos; no sustituyen las métricas históricas de este documento ni miden rendimiento
en contextos nuevos. El [informe de la reserva](evaluacion-reserva-60.md) detalla el método y la comparación
con la combinación congelada de motor y glosario 1.2.
