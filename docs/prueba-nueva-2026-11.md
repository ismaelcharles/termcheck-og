# Preparación de una revisión humana en contextos nuevos

20 de noviembre de 2026. Estado: revisión IA y comparación inicial terminadas. La preparación inicial
no ejecutó el motor; posteriormente el autor delegó la revisión y se ejecutó después de fijar sus decisiones.

## Muestra y alcance

Se seleccionaron 12 segmentos del anexo A de la guía de IFC sobre petróleo y gas en tierra (2007),
de sus versiones [inglesa](https://www.ifc.org/content/dam/ifc/doc/2000/2007-onshore-oil-gas-development-ehs-guidelines-en.pdf)
y [española](https://www.ifc.org/content/dam/ifc/doc/2000/2007-onshore-oil-gas-development-ehs-guidelines-es.pdf).
Cubren perforación exploratoria, producción y abandono. Páginas impresas: inglés 26–27; español 32–34.

La selección es dirigida por el contenido inglés, no aleatoria ni basada en resultados del verificador.
Los segmentos se emparejaron por sus límites oracionales, conservando la traducción publicada y normalizando
los saltos de línea y espacios de la extracción PDF. No se corrigieron errores lingüísticos del documento.
Se verificó que ningún original elegido esté contenido literalmente, tras normalizar puntuación y espacios,
en el corpus ni en las cinco muestras públicas anteriores. Esto no descarta semejanzas de contenido.

**Son contextos nuevos de una fuente ya utilizada.** No constituyen una prueba independiente de documento
ni permiten estimar el rendimiento general del sistema. Se reutilizan los PDF descargados el 19 de noviembre;
los enlaces oficiales se consultaron nuevamente el 20. Las huellas identifican las copias locales.

El inventario inicial contiene 23 apariciones de 15 conceptos. Fue preparado con asistencia de IA,
sin importar ni ejecutar el detector, el buscador español ni el clasificador de TermCheck. Es una lista
provisional: la persona que anota debe comprobarla, agregar lo que falte y explicar las exclusiones.
Se conservan por separado las repeticiones de un mismo término. El inventario final determinará el
denominador de la comparación, no la lista que produzca el motor.

## Procedimiento antes de medir

1. Revisar los pares completos con el criterio del encargo argentino y el glosario 1.4.
2. Para cada aparición, registrar CORRECTO, ERROR_TERMINO, OMISION o SIN_TRADUCIR y el fragmento literal
   español correspondiente. NO_VA exige un motivo. DUDA queda pendiente y no permite cerrar la referencia.
3. Confirmar el inventario de cada segmento. El formulario no completa decisiones por defecto.
4. Descargar la referencia cerrada. Conservar una copia y registrar su SHA-256 **antes** de ejecutar TermCheck.
   Hasta ese momento puede corregirse el borrador; después, cualquier cambio de criterio debe quedar auditado.
5. Comparar el motor 0.2.5 y el glosario 1.4 identificados en el manifiesto con la referencia cerrada.
   No ajustar el motor o el glosario mirando esta muestra antes de registrar la comparación inicial.
6. Separar falsas alarmas, errores no marcados y apariciones que el detector inglés no encontró;
   informar denominadores y exclusiones. Una ausencia del detector no puede desaparecer de las cuentas.

El formulario comprueba que los fragmentos citados existan y que no queden decisiones pendientes;
esa validación no certifica el juicio humano. Las diferencias de variedad se juzgan para el encargo,
sin atribuir a la publicación un error general de traducción.

## Revisión delegada y comparación inicial

El autor pidió que el asistente hiciera la revisión para ahorrar tiempo. Por tanto, la referencia es de IA,
no humana. Codex revisó los 23 casos con el glosario 1.4 y la guía de anotación histórica, dando prioridad a
las decisiones terminológicas posteriores. No se presume que toda forma ausente del glosario sea incorrecta.
Como apoyo se consultaron las fichas de SLB para
[drill collar](https://glossary.slb.com/es/terms/d/drill_collar),
[workover](https://glossary.slb.com/es/terms/w/workover) y
[drillstring](https://glossary.slb.com/es/terms/d/drillstring).
Esas fuentes respaldan conceptos y equivalencias; no demuestran exclusividad de uso argentino.

Antes de ejecutar el motor se guardó `referencia-ia.json`, con 13 decisiones CORRECTO, 9 ERROR_TERMINO
y una DUDA. Su SHA-256 es `c855b640444cf0632fea5b67b092ddac98616e6795606ddeaf269f47f437a23e`.
La duda corresponde a la relación posesiva entre rig y derrick en N04: la guía previa no resuelve cómo
evaluar una elipsis. Se excluye explícitamente de las cuentas; no se la convierte en acierto ni en error.

La referencia fue comprobada por huella antes y después de la ejecución. También se verificaron las huellas
de código, glosario y muestra identificadas en el manifiesto. El motor 0.2.5 con glosario 1.4 detectó
las 23 apariciones iniciales, sin apariciones adicionales ni ausencias respecto de ese inventario.

| Comparación con la referencia IA | Casos |
|---|---:|
| Errores señalados (TP) | 8 |
| Errores sin señalar (FN) | 1 |
| Formas correctas señaladas (FP) | 0 |
| Formas correctas sin aviso (TN) | 13 |
| Duda excluida | 1 |

Estos conteos son descriptivos de una muestra dirigida y de los juicios de un asistente.
No actualizan ni reemplazan las cifras históricas de precisión y recall.

### Hallazgo concreto: atribución de una variante al referente equivocado

En N01 el motor acepta T011 como VARIANTE al encontrar «equipo». Sin embargo, esa palabra corresponde
al equipo asociado del original, mientras que drilling rig se tradujo como «torre de perforación».
La ficha de rig acepta equipo cuando refiere al conjunto de perforación; la ficha de derrick distingue
la torre. La búsqueda dentro del segmento no comprueba esa correspondencia y deja pasar este caso.
No conviene retirar equipo de las variantes válidas: corregiría este ejemplo a costa de usos legítimos.

Este caso documenta una limitación de alineación contextual para una corrección futura. No se ha
implementado una regla particular ni se ha añadido el LLM pendiente. Desde esta comparación, la muestra
es material conocido: cualquier ajuste posterior debe identificarse como desarrollo y requiere otros
contextos para una evaluación nueva.

### Sensibilidad al criterio terminológico

Cuatro decisiones de error contienen juicios IA de registro o especificidad que merecen cautela:
N05-1 (drill collar), N05-3 (drill string), N08-1 (liner) y N11-1 (workover).
No son nuevas prohibiciones del glosario ni decisiones atribuidas al autor.

- Si se apartan esos cuatro casos, quedan TP4/FP0/FN1/TN13, con la misma duda excluida.
- Si otra revisión aceptara las cuatro traducciones, quedarían TP4/FP4/FN1/TN13.

La precisión aparente sobre los casos evaluables sería respectivamente 1,00 y 0,50 en esos escenarios.
Esto muestra por qué esta revisión IA no equivale a una referencia humana independiente y por qué no
se presenta como prueba de una mejora general. El fallo de atribución de N01 permanece en ambos escenarios.

## Ensayo posterior: restricciones léxicas para «equipo»

El autor autorizó investigar una corrección acotada y conservarla solo si no perjudicaba los usos válidos.
Se prepararon 23 pares inventados y el caso N01 conocido, con una aparición de rig por par.
Los juicios IA se fijaron en `salida/atribucion-equipo-20261120/casos.json` antes de ejecutar el ensayo.
Son casos de desarrollo elegidos para contrastar referentes, modificadores, orden y variantes completas;
no representan frecuencias de errores ni una evaluación independiente.

Sobre las salidas del motor se simularon tres filtros que retirarían la aceptación por equipo aislado:

1. Cuando también aparece equipment en el inglés.
2. Cuando equipo lleva asociado, auxiliar o adicional como modificador siguiente.
3. Cuando se cumplen ambas condiciones.

La preferida equipo de perforación, el préstamo rig y las formas prohibidas conservaron sus etiquetas.
El ensayo se repitió con un glosario mínimo propio y un ID diferente: las decisiones de los filtros
coincidieron con las del glosario publicado, sin depender de T011. El código de los filtros está separado
del motor; sus conteos muestran cómo cambiarían las decisiones de aceptación, no una implementación
completa con resaltados, sugerencias y reserva de palabras modificados.

| Estrategia | Errores señalados | Errores omitidos | Falsas alarmas | Correctos sin aviso |
|---|---:|---:|---:|---:|
| Motor actual | 2 | 5 | 0 | 17 |
| Rechazar equipo si aparece equipment | 7 | 0 | 9 | 8 |
| Rechazar equipo con esos modificadores | 6 | 1 | 5 | 12 |
| Exigir equipment y modificador | 6 | 1 | 3 | 14 |

Las tres restricciones detectan N01, pero introducen falsas alarmas. Por ejemplo, en un original que
identifica un rig adicional junto con sus equipos, equipo adicional sigue siendo una traducción válida
del rig. Rechazarla por el modificador y la presencia de equipment atribuye el referente de forma errónea.
También hay traducciones correctas en las que rig corresponde a equipo y equipment a accesorios o
equipamiento, incluso cuando cambia el orden.

**Decisión: no incorporar ninguno de estos filtros.** Se conserva equipo como variante válida y no se
cambia el motor ni su versión. Este ensayo descarta las tres restricciones probadas; no demuestra que
toda regla posible vaya a fallar ni obliga a implementar un LLM. El caso queda registrado como criterio
de prueba para una solución de alineación contextual futura. No se recalcularon las evaluaciones previas.

Los casos, su SHA-256, el script reproducible `ensayar.py` y el resultado por caso `resultado.json`
quedan en `salida/atribucion-equipo-20261120/`, fuera del repositorio público. La referencia IA de los
12 segmentos permanece intacta; este experimento no altera sus decisiones ni su comparación inicial.

## Archivos privados de trabajo

Carpeta `salida/revision-nueva-20261120/`, excluida de Git:

- `revision.html`: formulario sin conexión, con fichas, guardado local, importación y descarga JSON.
- `muestra.tsv` y `muestra.json`: pares y páginas originales.
- `anotaciones.csv`: alternativa tabular, con decisiones en blanco.
- `datos-revision.json`: inventario inicial y fichas de consulta.
- `glosario-referencia.csv`: copia exacta de 1.4.
- `manifiesto.json`: fuentes, límites, huellas de datos y código, y commit inicial.
- `preparar.py` y `crear-formulario.py`: preparación reproducible; no deben ejecutarse para sobrescribir
  una referencia ya anotada. Las respuestas descargadas se conservan en archivos separados.
- `comprobacion-formulario.json`: comprobación de la interfaz con datos de prueba descartables.
- `referencia-ia.json`, `referencia-ia.sha256` y `anotaciones-ia.csv`: revisión IA fijada antes del motor.
- `anotar-ia.py`: materialización de los juicios de esta sesión; impide sobrescribir una referencia existente.
- `comparar.py`, `comparacion.json`, `motor.csv` y `motor.html`: ejecución posterior y comparación por
  segmento, término y posiciones exactas del original, con exclusiones y análisis de sensibilidad.

No se publican los extractos completos, respuestas humanas ni juicios individuales. Esta preparación
no modifica producción, evaluaciones previas ni el glosario. La incorporación de un LLM al verificador
continúa pendiente y no forma parte de este ensayo.
