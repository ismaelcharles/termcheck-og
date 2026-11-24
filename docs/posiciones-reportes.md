# Posiciones y marcas en reportes

24 de noviembre de 2026. Motor 0.2.6, glosario publicado 1.4.

La primera pasada añadió 19 controles sin detectar desfases en esos casos. La segunda amplió la prueba
a CRLF/CR y a Chromium: encontró una normalización del texto que el analizador inicial no contemplaba.
Los 23 controles actuales pasan, con una corrección del HTML descargado incluida en esta revisión.
El motor y el glosario no cambian. El resultado no constituye una garantía sobre todo texto posible.

## Qué se comprobó

`tests/test_posiciones_reportes.py` contiene 22 casos dirigidos con un glosario mínimo inventado y un
recorrido de la página real con el glosario publicado. No usan anotaciones humanas ni la reserva de
evaluación y no agregan métricas de calidad terminológica.

- Comillas, signos de puntuación, ampersand y caracteres de HTML escapados.
- Mayúsculas y ausencia de tilde; tilde compuesta y descompuesta en Unicode.
- Espacios al inicio y al final, tabulaciones, saltos LF/CRLF/CR y emojis antes del término.
  Los retornos de carro se prueban tanto antes como dentro de las formas inglesa y española.
- Los seis guiones reconocidos por el motor: `-‐‑‒–—`.
- Repeticiones con etiquetas distintas y repeticiones con una sola traducción disponible.
- Traducción vacía, formas no encontradas y dos formas coordinadas con un tramo compartido.

Las pruebas reconstruyen el texto desde el HTML con un analizador independiente que aplica la
normalización de saltos del parser HTML antes de resolver las entidades, y cotejan, carácter
por carácter, la cobertura de las marcas, sus etiquetas y sus títulos con las posiciones del motor.
También verifican la conservación íntegra del texto y la equivalencia del bloque de pantalla, con y sin
filtro de observaciones, con el HTML descargado. Las superposiciones conservan ambos títulos y la
etiqueta de mayor aviso.

La segunda pasada también fija los índices esperados mediante búsquedas literales independientes,
para no limitarse a comparar el motor con un renderizador que consume sus mismas posiciones. El CSV
entregado por la página se coteja por segmento, sistema, contextos, etiqueta y límites.

El CSV en memoria y el escrito a disco deben ser idénticos en UTF-8. Cada fila conserva los contextos
originales y el tramo español exacto. El recorrido con AppTest verifica dos segmentos en la página,
captura los datos entregados a los botones de descarga y los compara con los bloques mostrados. Esto
prueba la lógica de la página. La comprobación adicional de Chromium se describe a continuación;
no se ejecutó ese recorrido sobre producción.

## Hallazgo de la segunda pasada: retornos de carro

El parser HTML convierte CRLF y CR literales en LF. El primer analizador de pruebas de Python no
lo hacía, por lo que no bastaba para verificar conservación exacta del texto en un navegador.

`resaltar` ahora codifica cada CR como `&#13;`, manteniendo el escape de HTML del resto del texto.
Así, el DOM del HTML descargado conserva el texto original y sus posiciones, incluidos CRLF dentro
de un término. No se modifican los textos del CSV ni las decisiones del motor.

Streamlit sanitiza el HTML y lo vuelve a insertar. Ese segundo procesamiento normaliza CRLF/CR a LF
en pantalla incluso con la entidad. Los términos resaltados son los mismos, pero el texto del DOM no
es una copia exacta del contexto original en esos casos. Para cotejar sus índices hay que convertir
cada límite con la misma normalización de saltos y contar puntos de código, no unidades UTF-16.
Los índices del CSV continúan refiriéndose exclusivamente a su `target_es` original.

Chromium comprobó los 22 HTML completos, reconstruyó las marcas con índices de puntos de código y
cotejó su cobertura y etiquetas. También cargó un CSV real con CRLF dentro de una forma, emoji y
tilde descompuesta, descargó CSV/HTML y comprobó sus datos. El CSV descargado es idéntico byte por
byte al generado directamente por el motor. La pantalla se cotejó tras la normalización descrita,
a 1280 y 390 píxeles, sin desbordes horizontales ni errores JavaScript. Las capturas se inspeccionaron.

Entradas, scripts, resultados y capturas quedan en `salida/segunda-revision-20261124/`, fuera de Git.
`resultado-inicial.json` conserva la reproducción del fallo previo en dos casos; `navegador.json`
registra la comprobación final satisfactoria.

## Activación y publicación

El autor autorizó publicar el conjunto. Se activó la corrección y se reiniciaron ambos servicios
Streamlit, que respondieron saludables. En producción se repitió la carga CSV con CRLF, emoji y tilde
descompuesta: CSV descargado idéntico al del motor, HTML descargado con CRLF conservado y pantalla
correcta tras la normalización descrita, a 1280/390 píxeles y sin errores JavaScript. El registro privado
de ese recorrido es `salida/segunda-revision-20261124/produccion-navegador.json`.

La entrega incluye solo código de reportes, sus 23 controles y los tres documentos públicos
relacionados. La clasificación sigue en motor 0.2.6 y el glosario en 1.4; no se altera la evaluación
histórica ni se incorpora el experimento LLM.

## Convención de posiciones

`start` es el índice del primer carácter de la forma encontrada en `target_es`; `end` es el índice
inmediatamente posterior al último. Se cuentan desde cero los puntos de código Unicode del texto
original. En Python, `target_es[start:end] == es_found` para una forma encontrada.

No se cuentan bytes, caracteres visuales agrupados ni unidades UTF-16. Una letra y su tilde combinante
ocupan dos posiciones; un emoji fuera del plano básico ocupa una. En JavaScript, para reproducir esos
índices se puede usar `Array.from(target_es).slice(start, end).join('')`.

En `NO_ENCONTRADO`, ambos índices valen `-1` y `es_found` está vacío. No se debe aplicar ese par como
un tramo; la sugerencia por parecido no se resalta como traducción encontrada. El inglés conserva su
marca. Las posiciones son relativas al segmento, no al archivo completo ni al documento CAT original.

## Límite contextual que sigue pendiente

La igualdad de posiciones no demuestra que una forma española traduzca la mención inglesa particular
a la que se asignó. Con tres menciones de `rig` y las formas españolas `equipo`, `plataforma de
perforación` y `rig`, el motor toma primero la prohibida por su prioridad de clasificación. La primera
fila puede apuntar a la segunda forma española. El CSV y el resaltado representan esa misma decisión,
pero no acreditan una alineación semántica por aparición.

Asimismo, `pozo de petróleo o gas` es un tramo continuo para la forma coordinada de `pozo de gas`:
incluye palabras compartidas y la alternativa intermedia. No se presenta como una cita discontinua.

La corrección de esas correspondencias pertenece al trabajo de alineación contextual. El prototipo
con LLM sigue en pausa; esta revisión no lo ejecuta ni lo integra.

## Reproducción

```bash
.venv/bin/python -m pytest tests/test_posiciones_reportes.py -q
```

Resultado: **23 passed**. Suite local completa: **473 passed**, incluidas 51 pruebas del prototipo LLM
que sigue sin publicar. La suite del proyecto público tiene **422 pruebas**. Se conserva el aviso previo
de deprecación Starlette/httpx. Las dos pasadas de revisión se hicieron antes de activar la corrección.

## Estado del proyecto y cabos sueltos

- Al iniciar la revisión, `main` y la rama remota coincidían en `247d654`. Esta entrega reúne la
  corrección de reportes, sus pruebas, el informe y las referencias de README/cierre.
- El botón de publicación de datos solo detectaba `README.md` entre estos cambios: su lista permite
  anotaciones, glosarios y documentos históricos, pero no este código ni los informes nuevos. Usarlo
  para esta revisión habría dejado una publicación incompleta y enlaces a un documento ausente.
  La entrega usa una selección explícita de esos cinco archivos, sin usar ese botón.
- Motor 0.2.6 y glosario 1.4, 104 conceptos: huellas idénticas a la auditoría de base y sin errores de
  validación del glosario. `pip check` no detectó conflictos. Los enlaces locales de la documentación
  pública examinada tienen destino en el árbol actual.
- Ambos servicios Streamlit están activos; sus endpoints de salud responden `ok`, el endpoint público
  de la demo responde `ok` y `/revision` devuelve HTTP 200. FastAPI permanece como prototipo.
  Estos controles de salud no sustituyen un recorrido funcional de producción.
- El prototipo LLM y su documentación/pruebas siguen locales y en pausa. No se ejecutó inferencia ni
  se incluyeron en los cambios de esta revisión. Los worktrees de interfaces anteriores se conservaron.
- Continúan abiertos la alineación contextual y la licencia de los datos. Las pruebas externas con
  traductores y nuevas exportaciones de Trados/memoQ siguen fuera de esta etapa por decisión previa;
  no se reactivan como tareas bloqueantes. Las cifras históricas de pruebas se conservan con su fecha.
- Avisos técnicos sin fallo de flujo: deprecación Starlette/httpx en la suite y un aviso de Streamlit
  por asignar a `vf_modo` tanto un valor predeterminado como estado de sesión al cambiar de entrada.
  No hubo excepciones en la página ni errores JavaScript. No se actualizaron dependencias ni se
  cambió la navegación para resolver estos avisos en esta revisión.
