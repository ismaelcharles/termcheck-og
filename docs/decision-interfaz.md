# Evaluación de la interfaz pública de TermCheck

Fecha: 19 de noviembre de 2026. Propuesta de arquitectura; no se ha migrado la aplicación.

## Necesidad

La parte pública ya combina una presentación, ejemplos interactivos, un verificador bilingüe,
filtros de revisión, archivos de intercambio, descargas y consulta del glosario. El diseño propio,
la adaptación al teléfono y la navegación tienen cada vez más peso.

En el código actual, `app/static/termcheck.css` depende de selectores `data-testid` y de la
estructura de widgets de Streamlit. `app/demo.py` y las páginas coordinan la navegación y la
conservación del texto mediante `st.session_state`. La franja nativa al desplazar requirió CSS
específico. Son costes de adaptación observados; no demuestran un fallo del motor lingüístico.

## Opciones

| Opción | Ventaja para este proyecto | Coste o límite | Valoración |
| --- | --- | --- | --- |
| Continuar con Streamlit | Conserva la aplicación, formularios, autenticación privada y pruebas de páginas | Mantiene la dependencia del diseño de widgets y del ciclo de sesiones y reejecuciones | Adecuado para el área privada y como solución actual mientras preparo otra interfaz |
| FastAPI + plantillas HTML/CSS + HTMX | Permite definir el HTML, diseño y navegación; conserva el motor Python y actualiza regiones concretas con respuestas HTML | Hay que implementar formularios, estado, validación, descargas y pruebas web que hoy resuelve Streamlit | Opción recomendada para la parte pública actual |
| API Python + interfaz React | Permite una interfaz con mucho estado e interacciones complejas | Añade una aplicación JavaScript, compilación y un contrato entre cliente y servidor | Reservar para un editor avanzado, trabajo colaborativo u otras necesidades concretas |

La preferencia por FastAPI/HTMX es un juicio de adecuación al proyecto, no una medición de
rendimiento. No se ha demostrado una reducción de latencia, memoria o coste mediante un ensayo
comparativo. El análisis con spaCy y las reglas conserva su coste al cambiar la interfaz.

## Qué puedo conservar

`src/termcheck/` no importa Streamlit. Contiene el análisis, normalización, verificación,
consistencia, lectura de formatos y generación de reportes. Es posible reutilizar el motor,
el glosario, las fuentes tipográficas y parte del CSS y HTML sin reescribir las reglas lingüísticas.
Las pruebas del motor siguen siendo útiles; las pruebas de páginas de Streamlit requieren
sustitución o adaptación para la nueva interfaz.

La aplicación privada puede permanecer en Streamlit. La propuesta afecta a la página pública,
no obliga a migrar al mismo tiempo la anotación, la edición del glosario ni su autenticación.

## Prueba que resolvería la decisión

Preparar una versión paralela en una ruta de previsualización con el flujo completo de pegar,
verificar, consultar fichas, filtrar observaciones y descargar HTML/CSV. Conservar la página actual
hasta comprobar paridad. Después ampliar la prueba a carga de CSV/TSV/XLIFF/TMX, glosarios propios,
validaciones y límites, navegación con conservación del texto y temas claro/oscuro.

Comparar en el mismo servidor:

- Coincidencia exacta de etiquetas, posiciones y descargas con las entradas de regresión.
- Uso en 390 y 1280 px, navegación por teclado y conservación del texto al consultar el glosario.
- Tiempo hasta poder usar la página y tiempo de verificación, distinguiendo arranque y uso posterior.
- Memoria y comportamiento con varias personas verificando a la vez.

La migración conviene si mejora el control de la interfaz y la experiencia sin perder funciones ni
introducir un coste de mantenimiento desproporcionado. El cambio por sí solo no mejora la detección
terminológica ni actualiza las métricas de evaluación.

## Documentación consultada

- [Streamlit: ejecución y reejecuciones](https://docs.streamlit.io/get-started/fundamentals/main-concepts).
  La ejecución completa es el comportamiento predeterminado; formularios, fragmentos y opciones de widgets
  permiten limitarla. No toda interacción obliga a recalcular el motor.
- [FastAPI: plantillas y archivos estáticos](https://fastapi.tiangolo.com/advanced/templates/).
- [HTMX: peticiones y actualización de regiones HTML](https://htmx.org/docs/).
