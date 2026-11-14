# Hallazgos

> Estructura propuesta por Claude el 2026-11-12, según el plan del proyecto (6.3). El contenido lo escribe el autor.
> Donde dice **[A COMPLETAR]** falta su texto. Los números salen de `salida/eval_prueba.md` y los casos de
> `salida/eval_prueba_casos.csv`, que se generan con «Calcular la evaluación final».

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

Qué muestra la diferencia: **[A COMPLETAR]**

## 2. Errores de terminología por sistema de traducción

| Sistema | Términos | Errores | Error de término | Omisión | Sin traducir |
|---|---|---|---|---|---|
| Opus-MT | 40 | 25 (62,5 %) | 24 | 1 | 0 |
| Claude | 40 | 4 (10,0 %) | 4 | 0 | 0 |
| DeepL | 40 | 23 (57,5 %) | 23 | 0 | 0 |

Qué sistema maneja mejor la terminología y en qué términos falla cada uno: **[A COMPLETAR]**

## 3. Análisis de errores del verificador

Cada falso positivo (FP) y falso negativo (FN) de `salida/eval_prueba_casos.csv` va en una causa. La columna
«causa_sugerida» es una pista automática; la que vale es la columna «causa», que llena el autor.

| Causa | FP | FN |
|---|---|---|
| Morfología | **[A COMPLETAR]** | |
| Sinónimo que falta en el glosario | | |
| Préstamo | | |
| Ambigüedad | | |
| Término dentro de otro o no detectado | | |
| Error de la anotación | | |

### Morfología
**[A COMPLETAR]**: 2 o 3 ejemplos, con el inglés, la traducción y lo que dijo el verificador.

### Sinónimo que falta en el glosario
**[A COMPLETAR]**

### Préstamo
**[A COMPLETAR]**

### Ambigüedad
**[A COMPLETAR]**

### Término dentro de otro o no detectado
**[A COMPLETAR]**

### Error de la anotación
**[A COMPLETAR]**

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

Qué muestran los desacuerdos: **[A COMPLETAR]**

## Qué cambiaría en la versión 2

**[A COMPLETAR]**
