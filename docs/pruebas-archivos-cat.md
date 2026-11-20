# Comprobaciones con muestras públicas de Trados y memoQ

20 de noviembre de 2026. TermCheck 0.2.5; glosario 1.4 sin cambios.

Actualización de alcance: el autor decidió no dedicar más trabajo a conseguir exportaciones originales.
La falta de una muestra EN–ES de Trados/memoQ se conserva como límite de la comprobación, pero deja de
ser una tarea o condición para avanzar. Se mantiene el soporte estándar anunciado; no se habilitan
dialectos nativos. El alcance vigente figura en la [auditoría de base](auditoria-cuatro-frentes.md).

## Resultado y alcance

Se conservaron y comprobaron siete originales públicos: tres SDLXLIFF del repositorio oficial de RWS,
dos MQXLIFF de proyectos públicos de terceros y dos TMX del repositorio de RWS. No se cambió el contenido,
la extensión ni el idioma declarado de ninguno. Las descargas se fijaron por commit y SHA-256.

**La prueba de importación de exportaciones originales inglés–español sigue pendiente.** Las muestras
encontradas usan alemán, italiano, japonés o galés. No se las reetiquetó como español ni se fabricó una
traducción para presentarla como exportación real. La búsqueda revisó repositorios públicos de RWS,
MateCat, OpenXLIFF y utilidades de XLIFF/memoQ; no encontrar esa muestra no demuestra que no exista.

Los siete archivos permitieron comprobar el tratamiento de idiomas y, en cinco de ellos, contrastar
auxiliares de extracción de texto y segmentación con una lectura XML independiente. No se detectó un fallo
en esos controles; no se modificó el lector ni se habilitaron formatos nuevos.

## Procedencia

| Muestra | Fuente fijada | Par declarado | Uso en esta prueba |
|---|---|---|---|
| QuickPlace | [RWS, prueba SDLTM Import Plus](https://github.com/RWS/Sdl-Community/blob/eb7e401f3dddf605e1357d3a718d04f487fd7ad2/SDLTM%20Import%20Plus/SDLTMImportUnitTests/TestingFiles/%231%20-%20quickplace.docx.sdlxliff) | EN–DE | Segmentos múltiples, grupos de formato y placeholders |
| TTSExample | [RWS, prueba SDLTM Import Plus](https://github.com/RWS/Sdl-Community/blob/eb7e401f3dddf605e1357d3a718d04f487fd7ad2/SDLTM%20Import%20Plus/SDLTMImportUnitTests/TestingFiles/TTSExample.docx.sdlxliff) | EN–DE | Destinos vacíos |
| QuotesSample | [RWS, XLIFF Manager](https://github.com/RWS/Sdl-Community/blob/eb7e401f3dddf605e1357d3a718d04f487fd7ad2/XLIFF%20Manager%20for%20Trados%20Studio/XLIFF.Manager.UnitTests/TestFiles/Sdlxliff/QuotesSample.docx.sdlxliff) | EN–IT | Segmentos dentro de grupos y marcas de comentario |
| Muestra del visor MQXLIFF | [IkueHirata, muestra](https://github.com/IkueHirata/mqxliff-viewer/blob/616d3afce618d1a75457497bee1e8ae902e93421/sample/translation_status_sample.xlsx_jpn.mqxliff) | EN–JA | Texto y destinos vacíos |
| Muestra de QA memoQ | [ShunSakurai, prueba](https://github.com/ShunSakurai/check_forbidden/blob/0d5615bd824fe2d81a8be34fbbea18072c243b02/Test/document.mqxliff) | EN–JA | Códigos bpt/ept/ph y destino vacío |
| Exportación SDL TM8 | [RWS, export.tmx](https://github.com/RWS/Sdl-Community/blob/eb7e401f3dddf605e1357d3a718d04f487fd7ad2/SDLTM%20Import%20Plus/SDLTMImportUnitTests/TestingFiles/export.tmx) | CY–EN | Unidades sin variante española |
| Memoria Workbench | [RWS, Master English–German](https://github.com/RWS/Sdl-Community/blob/eb7e401f3dddf605e1357d3a718d04f487fd7ad2/File%20type%20definition%20for%20TMX/Sample%20Files/Master%20English%20-%20German.tmx) | EN–DE | Unidades sin variante española y códigos de formato |

Los SDLXLIFF contienen metadatos SDL y proceden de pruebas del proveedor. Los MQXLIFF contienen metadatos
memoQ, pero son muestras de terceros: no se atribuyen a memoQ ni a un encargo real. Los encabezados de
los TMX identifican SDL Language Platform 8.1 y TRADOS Translator’s Workbench Edition 8 Build 863.
Esto documenta su procedencia disponible; no equivale a reproducir la exportación en esas aplicaciones.

La [documentación de memoQ sobre SDLXLIFF](https://docs.memoq.com/current/en/Workspace/sdlxliff-files.html)
describe extensiones y cambios controlados que requieren tratamiento propio. Su
[guía de exportación bilingüe](https://docs-memoq-com.azurewebsites.net/current/en/Workspace/bilingual-export-wizard.html)
distingue XLIFF sin las partes propias de memoQ, XLIFF con información adicional y paquetes comprimidos.
Por eso comprobar algunos elementos XLIFF no alcanza para anunciar soporte completo de un dialecto.

## Controles realizados

- Se llamó al lector completo con los originales. Los cinco XLIFF se rechazaron por el par de idiomas,
  como corresponde. Las extensiones `.sdlxliff` y `.mqxliff` continúan sin habilitarse en la entrada de archivos.
- Los dos TMX no producen pares EN–ES: el lector omite respectivamente 118 y 111 unidades inglesas
  sin variante española. No toma el alemán o el galés como español.
- Para el control estructural, se leyeron los originales con `xml.dom.minidom`, por separado del lector
  basado en ElementTree. Se comparó el texto de source/target y los marcadores mid con los auxiliares
  `_texto` y `_segmentos_mrk`, sin desactivar la validación de idiomas ni llamar a una importación adaptada.
- En total, ese control abarcó 48 segmentos: 41 con destino y siete destinos vacíos. Coincidieron texto,
  orden y separación de segmentos en los auxiliares examinados. Incluye mrk dentro de g y marcas de
  comentario; los códigos bpt/ept/ph se omiten del texto, conservando sus colas. No se trasladan notas
  de revisión al contenido del segmento.
- Las huellas de los siete originales permanecieron idénticas después de las comprobaciones.
- Pasaron las pruebas automáticas existentes del lector y su integración en la página Verificar.

El control estructural no ejecutó la verificación terminológica de traducciones a otros idiomas.
Tampoco comprueba que todos los dialectos sean compatibles, ni preservación de formato al reexportar,
proyectos, skeletons, versiones históricas, estados o cambios controlados. TermCheck extrae texto para
revisión; los originales permanecen sin cambios.

## Evidencias y pendiente exacto

En `salida/prueba-cat-20261120/`, excluida de Git, quedan los originales, los árboles de repositorios
consultados, las direcciones de descarga y `validar.py` / `validacion.json`, con los controles por archivo,
conteos y SHA-256. La comparación de texto usa una referencia DOM separada; no se instaló ni ejecutó
código de esos repositorios. El informe público no reproduce documentos ni metadatos personales de las muestras.

Para cerrar el pendiente hace falta un XLIFF estándar o TMX original EN–ES exportado desde cada herramienta,
con procedencia verificable y pares que se puedan cotejar. Para habilitar los dialectos nativos haría falta
además delimitar y probar las extensiones que afectan el texto actual. Hasta entonces se mantienen el
alcance declarado y las extensiones admitidas; no hay cambio de versión ni despliegue asociado a este ensayo.
