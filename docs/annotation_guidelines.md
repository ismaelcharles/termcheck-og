# Guía de anotación

> Estructura propuesta por Claude el 2026-11-09. Las definiciones y las decisiones las escribe el dueño.
> Donde dice **[A DECIDIR]** falta su criterio. Las etiquetas y el formato vienen del plan del proyecto (5.4).

## Para qué sirve

Esta guía dice cómo se etiqueta cada término del glosario en cada traducción automática. Con ella, la anotación
sale igual hoy que dentro de un mes, y otra persona podría repetirla. Es la vara contra la que se mide el verificador.

## Qué se anota

- Una fila por cada aparición de un término del glosario en la oración en inglés, y por cada sistema (Opus-MT,
  Claude, DeepL).
- Solo los términos del glosario. Otros errores de la traducción no se anotan. **[A DECIDIR]**: si se anota en
  `comment` un error grave que no es de terminología.
- Se anota a ciegas, sin ver lo que diría el verificador.
- Primero el conjunto de desarrollo (15 oraciones). El de prueba (20) recién cuando el glosario esté congelado.

## Etiquetas

### CORRECTO
La traducción del término es correcta, aunque no esté en el glosario.
**[A DECIDIR]**: ejemplos propios.

### ERROR_TERMINO
El término está mal traducido.
**[A DECIDIR]**: ejemplos propios.

### OMISION
El término desapareció de la traducción.
**[A DECIDIR]**: ejemplos propios.

### SIN_TRADUCIR
El término quedó en inglés y no es un préstamo aceptado.
**[A DECIDIR]**: ejemplos propios y lista de préstamos aceptados.

## Columnas de `data/annotations/gold.csv`

| Columna | Qué va |
|---|---|
| `seg_id` | La oración (S001…) |
| `system` | `opusmt`, `claude` o `deepl` |
| `term_id` | El término del glosario (T001…) |
| `label` | Una de las cuatro etiquetas |
| `es_used` | La forma en español tal como aparece en la traducción. **[A DECIDIR]**: qué va con OMISION (vacío) |
| `comment` | Opcional: el porqué en los casos dudosos |

## Casos dudosos

Preguntas que van a aparecer al anotar. Cada una se contesta con una regla y un ejemplo, y la respuesta queda
anotada acá con su fecha.

1. **Otra variedad del español.** Una traducción usada en otro país pero no en la Argentina (por ejemplo, de
   México o de Venezuela): ¿CORRECTO o ERROR_TERMINO?
2. **Siglas.** Una sigla en inglés que queda igual (BOP): ¿cuándo es préstamo aceptado y cuándo SIN_TRADUCIR?
3. **Traducción a medias.** Una parte del término traducida y otra no, o un término de varias palabras traducido
   solo en parte: ¿qué etiqueta lleva?
4. **Reemplazo por pronombre o elipsis.** El término no se repite porque la oración lo retoma con «este», «lo» o
   lo sobreentiende: ¿OMISION o CORRECTO?
5. **Concordancia.** El término está bien pero en el número o el género equivocado: ¿cuenta como error de
   terminología?
6. **Más general o más específico.** Una palabra correcta pero más amplia que el término («equipo» por un equipo
   concreto): ¿CORRECTO o ERROR_TERMINO?
7. **El mismo término dos veces en la oración.** ¿Una fila por aparición o una por oración?
8. **Términos que se solapan.** Un término del glosario dentro de otro más largo (como `casing` dentro de
   `casing shoe`): ¿se anotan los dos?
9. **Variantes de escritura en inglés** (`flow line` / `flowline`): se anota contra el mismo `term_id`.
   **[A CONFIRMAR]**
10. **Errores de forma.** Una tilde que falta o un error de tipeo en el término: ¿cuenta?

## Registro de decisiones

| Fecha | Caso | Decisión | Ejemplo (seg_id, sistema) |
|---|---|---|---|
| | | | |

## Acuerdo entre anotadores (opcional)

Si un compañero anota unas 30 oraciones con esta guía, se calcula la kappa de Cohen. **[A DECIDIR]**: si se hace.
