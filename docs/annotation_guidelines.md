# Guía de anotación

> Redactada por Claude el 2026-11-14 a pedido del autor. Los criterios y los ejemplos se sacaron de su anotación
> (`data/annotations/gold.csv`), de sus comentarios y del glosario v1. Donde dice **[A DECIDIR]** la anotación no
> alcanza para saber el criterio y falta que lo diga el autor.

## Para qué sirve

Esta guía dice cómo se etiqueta cada término del glosario en cada traducción automática. Con ella, la anotación
sale igual hoy que dentro de un mes, y otra persona podría repetirla. Es la vara contra la que se mide el verificador.

## Qué se anota

- Una fila por cada aparición de un término del glosario en la oración en inglés, y por cada sistema (Opus-MT,
  Claude, DeepL).
- Solo los términos del glosario. Otros errores de la traducción no se anotan, ni siquiera en `comment`.
  El comentario se usó solo para aclarar una decisión sobre el término.
- Se anota a ciegas, sin ver lo que diría el verificador.
- Primero el conjunto de desarrollo (15 oraciones). El de prueba (20) recién cuando el glosario esté congelado.

## Etiquetas

### CORRECTO
La traducción del término es correcta, aunque no esté en el glosario.

- S005, Claude: *drawworks* → «malacate».
- S012, Claude: *casing* → «cañería». No es la forma preferida («casing») y es válida.
- S007, DeepL: *perforating* → «perforación». El glosario no la lista. Comentario del autor: «perforación es un
  término aceptado, pero "punzado" es preferido».

### ERROR_TERMINO
El término está mal traducido. Incluye las formas que se entienden pero no se usan en un equipo argentino.

- S012, Opus-MT: *casing* → «carcasa». Traducción literal.
- S005, DeepL: *drawworks* → «cabrestante». Español general; en Argentina se dice «malacate».
- S050, DeepL: *tubing* → «tubería». Más general que el término.

### OMISION
El término desapareció de la traducción.

- S091, Opus-MT: *Sidetracking is the workover term for drilling…* → «Sidetracking es el término para
  perforar…». *workover* no está. Es el único caso en las 35 oraciones anotadas.

### SIN_TRADUCIR
El término quedó en inglés y no es un préstamo aceptado.

- S004, Opus-MT: *in the derrick* → «en el derrick». En Argentina se dice «torre de perforación» o «torre».
- S118, Opus-MT: el mismo término, igual.

Un préstamo está aceptado cuando el glosario lista la forma inglesa como preferida o como válida. En el glosario
v1 son 26: BOP, rig, tubing, shale, shale shaker, swivel, MD, gas migration, casing, choke manifold, gas lift,
kelly, kick, packer, top drive, liner, flowback, fracking, doghouse, standpipe, derrickman, cellar, coiled
tubing, ESP, wireline y workover.

## Columnas de `data/annotations/gold.csv`

| Columna | Qué va |
|---|---|
| `seg_id` | La oración (S001…) |
| `system` | `opusmt`, `claude` o `deepl` |
| `term_id` | El término del glosario (T001…) |
| `label` | Una de las cuatro etiquetas |
| `es_used` | La forma tal como aparece en la traducción. Es obligatoria en ERROR_TERMINO y SIN_TRADUCIR. Vacía en OMISION; en CORRECTO es opcional |
| `comment` | Opcional: el porqué en los casos dudosos |

## Casos dudosos

Cómo se resolvió cada caso en la anotación. Los que dicen **[A DECIDIR]** no aparecieron, o aparecieron con dos
criterios distintos.

1. **Otra variedad del español.** ERROR_TERMINO. La vara es el uso de campo en Argentina. Ejemplos: «cabrestante»
   por *drawworks* y «mesa giratoria» por *rotary table* (S005, DeepL), «tenazas» por *tongs* (S048, DeepL).
2. **Siglas.** Una sigla en inglés es correcta si el glosario la lista (BOP, MD, ESP). Si no, es SIN_TRADUCIR.
3. **Traducción a medias.** **[A DECIDIR]**. El caso más cercano es «varilla Kelly» por *kelly* (S005, DeepL),
   que se anotó ERROR_TERMINO: la forma válida está, con una palabra agregada que no se usa.
4. **Reemplazo por pronombre o elipsis.** **[A DECIDIR]**. No apareció.
5. **Concordancia.** **[A DECIDIR]**. No apareció ningún caso en que el único problema fuera el número o el
   género.
6. **Más general o más específico.** ERROR_TERMINO. Ejemplos: «equipo» por *rig* (S025, Claude), «cable» por
   *wireline* (S044, Claude), «tubería» por *tubing* (S050, DeepL).
7. **El mismo término dos veces en la oración.** Una sola etiqueta por oración, sistema y término. Si una de las
   apariciones está mal, la etiqueta es de error.
8. **Términos que se solapan.** Se anota el más largo. El de adentro se marca «No va» y no cuenta (por ejemplo,
   `casing` dentro de `casing shoe`).
9. **Variantes de escritura en inglés** (`flow line` / `flowline`). Van contra el mismo `term_id`; el glosario
   lista las dos escrituras.
10. **Errores de forma.** Una errata en el término es ERROR_TERMINO. «kely» por *kelly* (Opus-MT, S005 y S061)
    es error: valen «kelly» o «vástago».
11. **«de» y «del» dentro del término.** No son lo mismo. «cabeza del pozo» es ERROR_TERMINO aunque «cabeza de
    pozo» sea válida.

## Registro de decisiones

| Fecha | Caso | Decisión | Ejemplo (seg_id, sistema) |
|---|---|---|---|
| 2026-11-09 | Forma usada | Obligatoria solo en los errores, para que anotar lleve menos tiempo | — |
| 2026-11-11 | «de» y «del» | «cabeza del pozo» no es «cabeza de pozo» | S118 |
| 2026-11-13 | Revisión de desacuerdos en desarrollo | 3 etiquetas propias corregidas a CORRECTO (formas válidas del glosario marcadas como error) | S006 DeepL, S009 DeepL y Opus-MT |
| 2026-11-13 | *wellhead* | «boca del pozo» entra al glosario como válida | — |
| 2026-11-14 | *wellhead* | «boca del pozo» es inadecuada y hay que sacarla del glosario. El v1 ya estaba congelado y la conserva | S050, DeepL |
| 2026-11-14 | *kelly* | Valen «kelly» o «vástago». «kely» es error; la etiqueta de S005 se corrigió después de la primera evaluación | S005 y S061, Opus-MT |
| 2026-11-14 | *perforating* | «perforación» es aceptada; «punzado» es la preferida | S007 |

## Acuerdo entre anotadores

No hubo un segundo anotador humano. Un modelo de lenguaje (Claude Fable 5.2) anotó a ciegas las mismas 35
oraciones y con eso se calculó la kappa de Cohen: 0,55 en desarrollo y 0,62 en la prueba. El detalle está en
`docs/findings.md`, punto 4.
