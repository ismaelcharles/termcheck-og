# Hallazgos

> Estructura propuesta por Claude el 2026-11-12, según el plan del proyecto (6.3). El contenido lo escribe el autor.
> Donde dice **[A COMPLETAR]** falta su texto. Los números salen de `salida/eval_prueba.md` y los casos de
> `salida/eval_prueba_casos.csv`, que se generan con «Calcular la evaluación final».

## Con qué se midió

- Conjunto de prueba: **[A COMPLETAR]** oraciones y **[A COMPLETAR]** términos anotados.
- Glosario: `data/glossary/glossary_v1.csv`, congelado el **[A COMPLETAR]** antes de anotar la prueba.
- Un solo anotador. La guía está en `docs/annotation_guidelines.md`.

## 1. Verificador frente al baseline

El baseline busca la traducción preferida como texto exacto en minúsculas.

| Método | Precisión | Recall | F1 |
|---|---|---|---|
| Baseline | **[A COMPLETAR]** | | |
| TermCheck | **[A COMPLETAR]** | | |

Qué muestra la diferencia: **[A COMPLETAR]**

## 2. Errores de terminología por sistema de traducción

| Sistema | Términos | Errores | Error de término | Omisión | Sin traducir |
|---|---|---|---|---|---|
| Opus-MT | **[A COMPLETAR]** | | | | |
| Claude | **[A COMPLETAR]** | | | | |
| DeepL | **[A COMPLETAR]** | | | | |

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

No se hizo. **[A COMPLETAR]** si hay un segundo anotador: cantidad de términos en común y los dos valores de
kappa que da `scripts/kappa.py`.

## Qué cambiaría en la versión 2

**[A COMPLETAR]**
