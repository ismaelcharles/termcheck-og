# Auditoría de base antes de retomar un LLM

20 de noviembre de 2026. Motor 0.2.6; glosario 1.4, 104 conceptos. El LLM queda en pausa por decisión
del autor: no se elige modelo, no se hacen llamadas ni se integra el prototipo en la web.

## Estado y condiciones de cierre

| Frente | Comprobación realizada | Qué falta para cerrarlo |
|---|---|---|
| Validación de uso | Material y registro preparados para una sesión externa | Una sesión real con un traductor, registrar tareas, bloqueos y comprensión del alcance; resolver los bloqueos graves encontrados |
| Contexto | Corregida la contradicción entre una variante completa aceptada y una prohibida contenida | La atribución entre referentes y las repeticiones siguen limitadas; no se declara resuelto el caso de equipo |
| Cobertura | Auditados 104 conceptos y 266 formas; exposición medida en 306 segmentos | Obtener y revisar contextos para los 18 conceptos ausentes; la coherencia de formas no valida su uso en textos nuevos |
| Archivos CAT | Siete originales públicos ya comprobados para otros idiomas; material y cotejador EN–ES preparados | Una exportación original EN–ES desde Trados y otra desde memoQ, con pasos, versión y archivo conservados |

**No se dan por cerrados los cuatro frentes por haber preparado pruebas.** Los estados separan evidencia
obtenida de participación y archivos todavía necesarios. Una sesión de uso tampoco sustituye una evaluación
humana independiente de precisión y recall.

## Contexto: corrección concreta de una falsa alarma

El glosario acepta tubería de revestimiento corta para liner y desaconseja revestimiento aislado.
El motor anterior marcaba la expresión completa como PROHIBIDO por encontrar dentro la palabra corta.
La auditoría de las 266 formas declaradas detectó esa contradicción.

En 0.2.6 se descarta una coincidencia prohibida solo cuando sus tokens están estrictamente contenidos en
una forma completa admitida del mismo concepto, y esa forma sigue libre para ese término. No se retira
la prohibida del glosario ni se cambia globalmente la prioridad entre etiquetas.

Se comprueban singular, plural, mayúsculas, offsets, glosarios propios, una prohibida separada antes o
después de la variante, expresiones incompletas, una prohibida más larga que una variante corta y tokens
reservados para otro concepto. Una prohibida separada conserva el aviso. Esta regla no alinea referentes.

El cambio corrige una de las 266 comprobaciones de coherencia: antes 265 pasaban y una fallaba; ahora
pasan las 266. No son 266 traducciones evaluadas por una persona, sino formas declaradas por el glosario
en frases de control inventadas. Sobre los 378 pares de la comparación de cierre, las salidas de 0.2.5
y 0.2.6 permanecen idénticas. El caso de atribución de equipo continúa abierto, con las restricciones
léxicas descartadas registradas en el [informe anterior](prueba-nueva-2026-11.md).

Pasaron las 14 regresiones específicas de esta corrección y las siete pruebas de preparación/cotejo del
material. La suite completa da 412 pruebas aprobadas; 51 pertenecen al prototipo LLM local en pausa y
usan respuestas controladas, por lo que no cuentan como validación de un modelo. En previsualización,
Chromium comprobó ocho verificaciones por texto, la carga de los ocho segmentos del material, descarga
de HTML/CSV y tamaños de PC/teléfono. El CSV coincide con la CLI en todos los campos de resultados.
El mismo recorrido específico pasó en producción tras activar 0.2.6; ambos servicios están saludables.
El [registro agregado](auditoria-base-validacion.json) conserva la versión, commit, huellas y estados
pendientes. El glosario y los 51 archivos congelados permanecen intactos.

## Cobertura: alcance observado, separado del rendimiento

El script `scripts/auditar_cobertura.py` lee el glosario vigente, el corpus y, opcionalmente, las muestras
públicas. No altera los datos históricos. Cuenta contextos únicos tras normalizar mayúsculas, espacios
y guiones; esa deduplicación no implica independencia de documentos.

En el corpus de 120 oraciones más los 186 segmentos públicos hay 306 entradas y 302 contextos únicos.
El motor detecta al menos una aparición de 86 de los 104 conceptos. Otros 18 no tienen aparición en
ese material. La búsqueda literal independiente encuentra candidatos para los mismos 86 conceptos,
pero no constituye una referencia: no resuelve categorías gramaticales, anidamientos ni todos los plurales.

Los conceptos sin contexto detectado son:

| ID | Denominación inglesa |
|---|---|
| T001 | scraper / pig |
| T005 | cased hole |
| T013 | hook |
| T023 | true vertical depth |
| T028 | gas migration |
| T029 | balanced plug |
| T033 | desilter |
| T046 | sliding sleeve |
| T048 | well kill |
| T050 | multiwell pad |
| T060 | rotary hose |
| T061 | standpipe |
| T067 | desander |
| T072 | mud pit |
| T075 | weight indicator |
| T084 | emulsion |
| T090 | electrical submersible pump |
| T092 | mud return line |

El [inventario agregado](cobertura-1-4.json) conserva los conteos por concepto y grupo. También distingue
la presencia en las anotaciones humanas históricas: ausencia en ese archivo no significa que el término
no haya sido revisado al construir el glosario. Esas anotaciones no se trasladan automáticamente a la
edición 1.4. No se interpreta 86/104 como recall ni como porcentaje de traducciones correctas.

Reproducción, con las muestras privadas de trabajo disponibles:

```bash
.venv/bin/python scripts/auditar_cobertura.py \
  --out salida/auditoria-base/cobertura --muestras-publicas salida/prueba-publica
```

Sin `--muestras-publicas`, el script informa solo la exposición en el corpus distribuido en el repositorio.
No se agregaron términos ni equivalencias para inflar la cobertura. Los 18 ausentes quedan identificados
para conseguir evidencia; las frases de control no se presentan como contextos reales.

## Validación de uso: material listo, cero sesiones registradas

`scripts/preparar_prueba_uso.py` genera ocho pares inventados, un XLIFF 1.2, archivos de texto/TSV,
un registro vacío de observación y una planilla para la revisión previa. El ZIP no contiene respuestas
esperadas ni participantes ficticios. Se prueba con la demo pública, sin documentos de clientes.

La sesión propuesta dura 15–20 minutos. La persona revisa los pares antes de ver resultados, pega texto,
sube el archivo, consulta una ficha, descarga el reporte y explica el alcance de un segmento sin avisos.
Quien observa registra si completa cada tarea sin ayuda, cuánto tarda y dónde se bloquea.

Para declarar realizada una primera prueba exploratoria se necesita una persona externa con perfil de
traducción y sus registros reales. Con una sesión no se generaliza a todos los traductores; una segunda
sesión independiente ayuda a contrastar los problemas. No se presenta este material como validación ya hecha.

```bash
.venv/bin/python scripts/preparar_prueba_uso.py --out salida/prueba-uso
```

El material preparado en esta sesión está en `salida/auditoria-base-20261120/material-externo/`.
No se envió a participantes desde el proyecto y no hay sesiones registradas.

## Archivos CAT: cómo obtener y verificar la evidencia que falta

El XLIFF del material es un control creado localmente, no una exportación del proveedor. Permite que
una persona con Trados o memoQ lo importe y exporte una memoria TMX EN–ES desde la herramienta,
conservando los ocho pares. Debe registrar herramienta, versión, fecha y pasos; el original no se edita.

El script `scripts/comprobar_exportacion_cat.py` exige un TMX, comprueba el generador declarado en la
cabecera, compara los pares con la referencia independientemente del orden y contrasta la extracción
con una lectura DOM separada. Registra huella, unidades perdidas/adicionales y destinos vacíos, sin
modificar el original. Una cabecera coincidente no certifica por sí sola la procedencia: hacen falta
los pasos de la exportación y el archivo obtenido. Sus pruebas automáticas usan TMX inventados y se
identifican como tales; no cierran la prueba real.

```bash
.venv/bin/python scripts/comprobar_exportacion_cat.py \
  --archivo EXPORTACION_ORIGINAL.tmx --referencia salida/prueba-uso/referencia.tsv \
  --herramienta memoq --version VERSION_REAL --out salida/prueba-uso/resultado-memoq.json
```

Para Trados se usa `--herramienta trados`. Los nombres en mayúsculas son marcadores a reemplazar.
Después de verificar el TMX, falta cargar ese mismo original en la demo y cotejar su reporte con la CLI.
No se habilitan `.sdlxliff`, `.mqxliff` ni paquetes de proyecto por este procedimiento. Los controles
anteriores y sus límites se conservan en el [informe de muestras CAT](pruebas-archivos-cat.md).

## Separación de la línea base y del LLM

La aplicación sigue siendo un verificador por reglas y glosario. El prototipo LLM permanece local,
sin publicar ni ejecutar inferencia. Su muestra preparada para el motor anterior no debe reutilizarse
sin una nueva preparación cuando se retome el experimento: las huellas de código detectan el cambio.

La auditoría no sustituye la evaluación histórica ni recalcula su referencia. Los registros privados
de control, comparaciones, capturas y paquetes están en `salida/auditoria-base-20261120/`.
