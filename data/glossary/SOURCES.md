# Fuentes y licencias

Qué se usó para armar el glosario, el corpus y las traducciones, y qué se puede reutilizar.

## Glosario (`glossary_en_es.csv`)

99 términos de perforación, terminación, producción y seguridad en locación. Cada fila dice en la columna
`source` de dónde sale la decisión. La forma preferida y las formas válidas las eligió el autor del proyecto;
las fuentes son el respaldo de esa elección.

| Fuente | Para qué se usó | Términos que la citan | Licencia y cuidado |
|---|---|---:|---|
| [SLB Energy Glossary](https://glossary.slb.com) (español) | Consultar el equivalente en español de cada término | 85 | Con copyright. Se cita la página de cada término. No se copió ninguna definición. Es español general, sin variedad regional. |
| [OSHA Oil and Gas Well Drilling and Servicing eTool](https://www.osha.gov/etools/oil-and-gas) | Confirmar que el término en inglés se usa así en textos reales | 32 | Obra del gobierno de EE. UU. El glosario del eTool y los recuadros marcados con † vienen del *Dictionary of Petroleum Terms* de Petex (© 2001): esas definiciones no son de dominio público y no se usaron. |
| Apuntes de un curso de operador de planta de petróleo y gas (Neuquén) | Ver cómo aparece el término en material de capacitación en español | 66 citas | Material privado, no se publica. Se cita por documento y página. Sirve para el concepto; como prueba de uso argentino es débil (parte del material mezcla variedades). |
| Criterio propio | Uso de campo del autor, cuando las fuentes escritas no alcanzaban o no coincidían con lo que se dice en Argentina | 21 | Decisión del autor. |
| Revisión previa de candidatos | Sugerencia revisada por el autor antes de entrar al glosario | 10 | Interna; el archivo no se publica. |
| escoarg.com.ar | Uso en el mercado argentino (texto comercial) | 1 | Se cita la página. |
| [IATE](https://iate.europa.eu) | Terminología de la Unión Europea | 1 | Reutilizable citando «IATE, European Union». Es español de España. |

Un término puede citar más de una fuente, por eso la columna no suma 99.

Una fuente argentina que confirma varias formas preferidas (trépano, zaranda, bomba de lodo) es la nota técnica
de *Petrotecnia* 4-2025, pp. 46-49, de la revista del Instituto Argentino del Petróleo y del Gas:
https://petrotecnia.com.ar/425/46-49.pdf

## Corpus (`data/corpus/segments.tsv`)

120 oraciones en inglés original. Todas son de textos del gobierno federal de EE. UU., que no tienen copyright.
Cada fila lleva la dirección de la página de origen.

| Fuente | Oraciones |
|---|---:|
| OSHA Oil and Gas Well Drilling and Servicing eTool | 102 |
| BSEE, 30 CFR 250 (subpartes D, E, G, H y Q) | 10 |
| BLM, 43 CFR 3160 y 3170, y Gold Book (capítulo 5) | 7 |
| EPA, 40 CFR 146 | 1 |

Los documentos del CFR están en `data/corpus/fuentes/`, con sus direcciones en el README de esa carpeta.
Se excluyeron las definiciones marcadas con † en el eTool (son de Petex, con copyright).

## Traducciones automáticas (`data/mt/translations.tsv`)

Generadas para este proyecto. El sistema, la fecha y la versión de cada una están en `data/mt/versiones.csv` y el
método en `data/mt/README.md`.

| Sistema | Fecha |
|---|---|
| Helsinki-NLP/opus-mt-en-es (licencia Apache-2.0) | 2026-11-08 |
| Claude Opus 5.5, sin glosario | 2026-11-08 |
| DeepL Translator, versión web gratuita | 2026-11-09 |

## Anotación (`data/annotations/gold.csv`)

Hecha por el autor del proyecto, a ciegas (sin ver el sistema ni el resultado del verificador).

## Licencias de este repositorio

- Código: MIT (archivo `LICENSE`).
- Glosario, anotación y traducciones: la licencia de los datos todavía no está definida.
