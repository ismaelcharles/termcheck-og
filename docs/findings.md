# Hallazgos

> Redactado por Claude el 2026-11-14 a pedido del autor, con su anotación, sus comentarios y el glosario v1. Los
> números salen de `salida/eval_prueba.md` y los casos de `salida/eval_prueba_casos.csv`.

## Con qué se midió

- Conjunto de prueba: 20 oraciones y 120 términos anotados (52 errores según la anotación).
- Glosario: `data/glossary/glossary_v1.csv`, congelado el 2026-11-14 (99 términos, sha256 `5c7f9844eb4d7525`) antes de anotar la prueba.
- Un solo anotador humano. La guía está en `docs/annotation_guidelines.md`. Un modelo de lenguaje anotó lo mismo
  a ciegas para medir el acuerdo (punto 4).

## 1. Verificador frente al baseline

El baseline busca la traducción preferida como texto exacto en minúsculas.

| Método | Precisión | Recall | F1 |
|---|---|---|---|
| Baseline | 0,73 (0,61–0,82) | 0,98 (0,90–1,00) | 0,84 |
| TermCheck | 0,86 (0,74–0,93) | 0,92 (0,82–0,97) | 0,89 |

Entre paréntesis, el intervalo de confianza del 95 % (Wilson). El baseline da 19 falsos positivos y 1 falso
negativo; TermCheck, 8 y 4.

El baseline casi no deja pasar errores (recall 0,98) porque marca todo lo que no sea la forma preferida escrita
igual. Por eso da 19 falsas alarmas sobre 68 términos correctos: marca plurales, formas válidas del glosario y
variantes de escritura. TermCheck baja las falsas alarmas a 8, porque reconoce las formas válidas y los plurales,
y a cambio deja pasar 4 errores. La precisión sube de 0,73 a 0,86 y el recall baja de 0,98 a 0,92.

Los intervalos de los dos métodos se pisan. Con 120 términos la diferencia de F1 (0,89 contra 0,84) no alcanza
para decir que uno es mejor que el otro. Lo que sí se ve es de dónde sale cada error, y eso está en el punto 3.

En desarrollo la diferencia fue mayor (F1 0,95 contra 0,72). Ese número es optimista, porque el glosario se
ajustó con esas mismas oraciones.

## 2. Errores de terminología por sistema de traducción

| Sistema | Términos | Errores | Error de término | Omisión | Sin traducir |
|---|---|---|---|---|---|
| Opus-MT | 40 | 25 (62,5 %) | 24 | 1 | 0 |
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
| Sinónimo que falta en el glosario | 2 | 0 |
| Préstamo | 1 | 0 |
| Ambigüedad | 0 | 3 |
| Término dentro de otro o no detectado | 1 | 0 |
| Error de la anotación | 1 | 0 |
| Coordinación | 3 | 0 |
| Forma del glosario que el autor rechaza | 0 | 1 |
| Total | 8 | 4 |

Las dos últimas causas no estaban en la lista original y se agregaron porque los casos no entraban en las otras.

### Morfología
Ningún caso. Los plurales y los cambios de género se reconocieron bien en la prueba.

### Sinónimo que falta en el glosario
S007, DeepL y Opus-MT. *perforating* → «la perforación». El autor la anotó como correcta, con este comentario
en la misma oración: «perforación es un término aceptado, pero "punzado" es preferido». El glosario solo lista
«punzado» y el verificador marcó `NO_ENCONTRADO`. Se arregla agregando «perforación» como forma válida.

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
S048, Claude. *the kelly using the kelly spinner* → «el vástago (kelly) con el enroscador del vástago». *kelly*
aparece dos veces en inglés, la segunda dentro de *kelly spinner*, que no está en el glosario. La primera se
encontró. Para la segunda, «vástago» solo no es una forma válida (el glosario lista «vástago de perforación») y
el verificador marcó `NO_ENCONTRADO`.

### Error de la anotación
S005, Opus-MT. *kelly* → «kely». Se anotó «Correcto». La misma errata del mismo sistema se anotó «Error de
término» en S061. Una de las dos etiquetas es un descuido; falta que el autor diga cuál. Si la de S005 pasa a
error, el verificador gana un acierto y pierde una falsa alarma.

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
correcto. En desarrollo el autor revisó los desacuerdos y corrigió 3 etiquetas propias. En la prueba no se
corrigió ninguna.

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
- Agregar «perforación» como forma válida de *perforating*.
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
