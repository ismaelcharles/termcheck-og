# Reserva de 60 oraciones: revisión con referencia mixta

Fecha de cierre: 19 de noviembre de 2026.

Se revisaron 180 traducciones de 60 oraciones, con 447 unidades de término, oración y sistema de traducción.
Dos unidades se excluyeron por alcance y quedaron 445 evaluables, sin dudas de clasificación pendientes.
Los resultados son descriptivos: las oraciones ya se utilizaron para ajustar el glosario y la referencia
combina decisiones humanas con anotaciones de IA. No sustituyen la evaluación histórica de 0.1/v1.

## Cómo se construyó la referencia

1. Se congelaron el motor, los datos y el glosario 1.2. La selección de términos produjo 447 unidades;
   cada término cuenta una vez por oración y sistema, aunque tenga varias apariciones.
2. Una primera lectura de GPT-6.2 Astra, sin nombres de sistemas ni resultados del verificador,
   se contrastó con las marcas del motor congelado. Hubo 132 desacuerdos, 15 dudas de alcance y 300 acuerdos.
3. El autor revisó los 132 desacuerdos, las 15 dudas de alcance y una muestra aleatoria de 30 acuerdos:
   177 decisiones, con 91 notas. La muestra se seleccionó con semilla 684265. La revisión permitía consultar
   el glosario y, después de guardar cada decisión, las lecturas de las herramientas. Fue una selección
   dirigida para revisar fallos, no una anotación humana completa e independiente.
4. Los criterios del autor se incorporaron al glosario 1.3 y al reconocimiento del motor. Después,
   GPT-6.2 Astra anotó los otros 270 casos usando ese glosario y las aclaraciones humanas, sin consultar
   los dictámenes anteriores ni las marcas del verificador para esos casos.
5. La referencia final aplica cinco ajustes derivados de decisiones explícitas posteriores del autor:
   dos aceptaciones de «equipo» para rig y tres de «barras de sondeo» para drill pipe. Las respuestas
   originales se conservaron separadas de esos ajustes.
6. Astra dejó tres casos de «múltiple de estrangulación» en duda. El autor indicó aplicar el glosario
   vigente: se clasificaron ERROR_TERMINO para este encargo. La forma preferida es «manifold de surgencia»;
   las variantes aceptadas son «múltiple de surgencia», «múltiple de choke» y «choke manifold».

El complemento original de Astra contiene 216 CORRECTO, 49 ERROR_TERMINO, una OMISION, un NO_VA y tres DUDA.
Tras los ajustes y las resoluciones, la referencia mixta final contiene 291 unidades correctas, 154 con error
y dos NO_VA. Los dos descartes corresponden a fracturing dentro de fracturing fluid.
Las respuestas humanas sobre corrección son binarias: no distinguen entre error de término, omisión y
término sin traducir. Por eso no se presentan métricas por tipo de error.

## Comparación descriptiva

Para cada unidad, cualquier aparición marcada por el verificador cuenta como aviso. Una unidad sin detección
cuenta como ausencia de aviso, no como exclusión. Solo se excluyen los dos NO_VA de la referencia.
Se comparan ambas combinaciones con la misma referencia final, que incorpora el criterio terminológico
posterior del autor; la fila congelada no es una evaluación según las preferencias originales de 1.2.

| Combinación | Unidades | TP | FP | FN | TN | Precisión | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Motor y glosario 1.2 congelados | 445 | 137 | 42 | 17 | 249 | 0,765 | 0,890 | 0,823 |
| TermCheck 0.2.4 y glosario 1.3 | 445 | 139 | 13 | 15 | 278 | 0,914 | 0,903 | 0,908 |

En estos ejemplos, la combinación actual produce 29 falsas alarmas menos y detecta dos errores más.
Esto reúne cambios del glosario y del motor; no permite atribuir la diferencia a uno de ellos por separado.
Los [resultados agregados en JSON](resultados-reserva-60.json) conservan los conteos y las métricas sin redondear.

## Límites y trazabilidad

- La referencia tiene un solo autor humano y un complemento de IA. Los errores compartidos entre las
  herramientas pueden permanecer; las coincidencias no equivalen a una validación humana.
- Los textos y las decisiones ya intervinieron en las reformas. El cierre no aporta una medición
  independiente de la versión actual ni demuestra una mejora general en textos nuevos.
- Las unidades provienen de la selección de términos de 1.2; no miden toda la cobertura de 1.3.
- Las 180 traducciones comparten 60 contextos. Las 445 unidades no son observaciones independientes.
  No se añaden intervalos de confianza que oculten la incertidumbre de la referencia mixta.
- El archivo público contiene resultados agregados. Los dictámenes, las notas humanas, las resoluciones
  y el informe por caso permanecen en el archivo privado de evaluación. Este resumen por sí solo no
  permite reproducir toda la anotación.

El cierre verificó las 51 huellas de los archivos congelados y conservó intacta la base de respuestas humanas.
El motor actual corresponde al commit `05cbf049b00fb02998c4e72dcf8eacdf3288eafc`; el JSON agregado identifica
también el glosario y los dictámenes mediante SHA-256.

Para obtener una referencia íntegramente humana sobre esta reserva falta revisar las 270 anotaciones
complementarias. Para medir la edición actual de forma independiente hacen falta contextos nuevos y una
referencia humana fijada antes de consultar los resultados del verificador.
