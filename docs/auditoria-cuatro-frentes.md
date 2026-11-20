# Auditoría de base antes de retomar un LLM

20 de noviembre de 2026. Motor 0.2.6; glosario 1.4, 104 conceptos. El LLM queda en pausa por decisión
del autor: no se elige modelo, no se hacen llamadas ni se integra el prototipo en la web.

**Alcance actualizado por el autor:** no se incorporarán otros traductores ni se continuará buscando
exportaciones originales de Trados/memoQ como condición para avanzar. Se cierra la revisión que puede
realizarse con pruebas automatizadas y trabajo de IA, conservando las limitaciones como tales.

## Estado y condiciones de cierre

| Frente | Comprobación realizada | Estado dentro del alcance acordado |
|---|---|---|
| Flujo de uso | Recorridos automatizados en navegador, entrada, revisión, catálogo, descargas y PC/teléfono | Comprobación técnica realizada; no se presenta como estudio con usuarios |
| Contexto | Corregida la contradicción entre una variante completa aceptada y una prohibida contenida | La atribución entre referentes y las repeticiones siguen limitadas; no se declara resuelto el caso de equipo |
| Cobertura | Auditados 104 conceptos y 266 formas; 36 controles dirigidos para los 18 ausentes en las muestras naturales | Control técnico completado; exposición natural permanece en 86/104 y no equivale a recall |
| Archivos CAT | Pruebas de los formatos estándar y siete originales públicos de otros idiomas | Se conserva el alcance XLIFF 1.2/2.0 y TMX; dialectos nativos sin habilitar y búsqueda de exportaciones fuera de esta etapa |

El cierre es técnico y acotado: no afirma que todos los problemas de contexto estén resueltos ni que la
herramienta tenga validación humana independiente. El caso de equipo se conserva como limitación
reproducible para evaluar, más adelante, una intervención contextual.

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
material. Antes de añadir los controles dirigidos de los 18 conceptos, la suite daba 412 pruebas aprobadas;
51 pertenecen al prototipo LLM local en pausa y
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
en las muestras naturales; las frases de control no se presentan como contextos reales.

### Controles autónomos para los 18 conceptos

`data/checks/cobertura_18_v1_4.json` fija 18 contextos inventados por IA, con una traducción válida y otra
que omite el término o lo reemplaza por un concepto distinto. Son 36 pares y 18 conceptos, no traducciones
publicadas ni nuevas decisiones sobre el glosario. Las formas válidas proceden de la edición 1.4; no se
clasifica un sinónimo como error solamente por estar ausente del glosario.

Los 36 controles comprueban detección en el inglés, marcado de la omisión/confusión, conservación de
la forma admitida y posiciones del texto. Una prueba adicional comprueba que los conceptos correspondan
exactamente a los 18 huecos identificados. No se reemplazan el corpus ni las métricas históricas; el
inventario de exposición natural sigue siendo 86 de 104. Los 104 conceptos quedan cubiertos por controles
declarativos y los 18 huecos cuentan además con estos controles contextuales dirigidos.

Los 36 pares pasan: 18 traducciones válidas sin aviso y 18 omisiones/confusiones señaladas para el concepto
objetivo. El reporte completo tiene 38 apariciones porque dos pares también mencionan annulus; esas dos
apariciones acompañantes se reconocen correctamente. El resultado se informa como control dirigido,
sin convertirlo en una nueva estimación de precisión o recall. La suite local completa pasa 449 pruebas:
398 corresponden al proyecto publicado y 51 al prototipo local en pausa, con respuestas controladas.

## Material externo archivado, fuera del alcance actual

`scripts/preparar_prueba_uso.py` genera ocho pares inventados, un XLIFF 1.2, archivos de texto/TSV,
un registro vacío de observación y una planilla para la revisión previa. El ZIP no contiene respuestas
esperadas ni participantes ficticios. Se prueba con la demo pública, sin documentos de clientes.

El protocolo anterior queda archivado: por la decisión de alcance no se pedirán participantes ni sesiones.
El material se usó para comprobar técnicamente carga y descargas. No hay registros externos ni se
presenta una simulación automática como una prueba con personas.

```bash
.venv/bin/python scripts/preparar_prueba_uso.py --out salida/prueba-uso
```

El material preparado en esta sesión está en `salida/auditoria-base-20261120/material-externo/`.
No se envió a participantes desde el proyecto y no hay sesiones registradas.

## Archivos CAT: compatibilidad declarada, sin esperar nuevas exportaciones

El XLIFF del material es un control creado localmente, no una exportación del proveedor. La comprobación
positiva de XLIFF 1.2/2.0 y TMX usa los controles estándar y los originales públicos de DGT ya probados.
Los siete archivos de otros pares se conservaron sin alterar sus idiomas y no se presentan como pruebas EN–ES.

El cotejador preparado queda archivado como utilidad opcional. No se continuará buscando ni solicitando
exportaciones para esta etapa. `.sdlxliff`, `.mqxliff` y paquetes de proyecto permanecen fuera del soporte
anunciado. Los controles anteriores y sus límites se conservan en el [informe de muestras CAT](pruebas-archivos-cat.md).

## Separación de la línea base y del LLM

La aplicación sigue siendo un verificador por reglas y glosario. El prototipo LLM permanece local,
sin publicar ni ejecutar inferencia. Su muestra preparada para el motor anterior no debe reutilizarse
sin una nueva preparación cuando se retome el experimento: las huellas de código detectan el cambio.

La auditoría no sustituye la evaluación histórica ni recalcula su referencia. Los registros privados
de control, comparaciones, capturas y paquetes están en `salida/auditoria-base-20261120/`.
