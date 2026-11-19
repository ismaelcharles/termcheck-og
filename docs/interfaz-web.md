# Prototipo de interfaz pública con FastAPI y HTMX

Implementada en `web/` con FastAPI, plantillas Jinja y HTMX 2.0.8 servido localmente
(licencia incluida). Reutiliza el motor de `src/termcheck` sin modificar sus reglas.
La demo pública volvió a Streamlit tras el rechazo visual del autor. FastAPI queda
conservado como prototipo, sin activación pública. `app/demo.py` sirve la demo actual.

## Ejecutar

Instalar `requirements-web.txt` en el entorno del proyecto y ejecutar:

```bash
bash scripts/previsualizar-web.sh
```

Disponible en `http://127.0.0.1:8530/demo/`. `TERMCHECK_PUERTO_WEB` cambia el puerto.
El lanzador local no modifica servicios ni configura alojamiento externo. Para cerrar, Ctrl+C.

## Funciones

- Pegar textos, ejemplo de desarrollo y carga CSV/TSV/XLIFF 1.2/2.0/TMX.
- Edición pública del glosario o CSV propio, con validación y límites de la demo.
- Revisión por segmento, filtro de observaciones, fichas relacionadas e inconsistencias.
- Exportación HTML/CSV del documento completo, con huella del glosario.
- Catálogo de consulta con búsqueda bilingüe sin tildes, áreas, paginación y descarga exacta.
- Siete ejemplos editables, cuatro casos rotativos de bienvenida y tres fichas aleatorias.
- Temas claro, oscuro y sistema; vista adaptable al teléfono.
- Presentación, métricas históricas y explicación del método compartidas con Streamlit.

Los textos, cargas y resultados viven en el documento de la pestaña mientras está abierta.
La navegación conserva el formulario y los archivos sin reenviarlos. Cambiar de segmento,
filtro o tema no ejecuta el motor. Editar la entrada invalida el resultado anterior.
Vaciar borra los textos, la carga bilingüe y la revisión; conserva la elección del glosario.
Recargar o cerrar la pestaña elimina su contenido. Solo la preferencia de apariencia se
guarda en el navegador. No se usan cookies ni sesiones de texto en el servidor.

El servidor procesa cada carga en memoria con un máximo de 1 MB por archivo y un límite
total de solicitud. Los reportes se descargan desde el navegador, sin un almacén de resultados.
Los cuerpos no se registran; el lanzador desactiva el registro de accesos de Uvicorn.

## Comprobar

```bash
.venv/bin/pytest -q
TERMCHECK_URL=http://127.0.0.1:8530/demo/ node scripts/revisar-web.cjs
```

El ensayo de navegador usa las herramientas ya instaladas en este servidor, comprueba
archivos, revisión, descargas completas, navegación, temas y tres visitantes independientes.
Guarda capturas PC/teléfono, HTML, CSV, PDF y `navegador.json` en `salida/web/`.
Las pruebas HTTP contrastan el CSV por aparición directamente con el motor, incluidas las
formas singular y plural de elevator. No recalculan la evaluación congelada del proyecto.

La aplicación ASGI `web.main:publica` monta las rutas bajo `/demo/`, incluidos recursos y
enlaces directos al catálogo y los ejemplos. El servicio público conserva su puerto y sus
límites de recursos. La recuperación consiste en retirar el cambio de ejecutable y reiniciar
la implementación Streamlit conservada.

El script `scripts/medir-interfaz.cjs` registra cuatro visitas con contextos nuevos y una
verificación breve antes y después del cambio. Es una medición descriptiva del servidor,
no una prueba de carga ni una estimación de rendimiento general. La prueba de tres
visitantes comprueba aislamiento; no demuestra capacidad para una carga pública grande.

Referencias: [formularios y archivos de FastAPI](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/),
[formularios multipart con HTMX](https://htmx.org/attributes/hx-encoding/).

## Activación del 19 de noviembre de 2026

La demo pública quedó migrada en [termcheck.aval.site/demo/](https://termcheck.aval.site/demo/).
La ruta y el proxy se conservaron; cambió el ejecutable del servicio público a Uvicorn.
El servicio privado continúa activo con Streamlit. Se conserva una rama de recuperación
anterior a la migración y la configuración previa del servicio.

Validación: 310 pruebas aprobadas y recorrido Chromium completo en prepublicación y
producción, incluyendo recursos bajo `/demo/`, enlaces directos, CSV exacto del glosario,
archivos, reportes completos, temas y tres visitantes independientes. No hubo errores
JavaScript ni desbordes en 1280 y 390 px. El motor y los datos lingüísticos no cambiaron.

Medición descriptiva con Chromium en el mismo servidor y URL local, conservando una cuota
de CPU de 50 % para el servicio. Cada ronda abrió un contexto nuevo y verificó
«Inspect the elevator.» / «Inspeccioná el elevador.». Se separó la primera visita de las
siguientes tres; no se midió el arranque del proceso:

| Interfaz | Primera visita: formulario / verificación | Mediana de las tres siguientes: formulario / verificación |
| --- | --- | --- |
| Streamlit | 2.592 / 1.497 ms | 2.107 / 1.473 ms |
| FastAPI + HTMX | 191 / 357 ms | 164 / 325 ms |

La memoria del grupo del servicio al terminar fue 330 MiB para Streamlit y 285 MiB para
FastAPI. Incluye cachés; los procesos tenían distinta antigüedad. Estos resultados describen
una muestra breve y un único texto, con variación de carga del servidor entre corridas.
No demuestran mejoras generales de rendimiento ni capacidad sostenida. Evidencias locales:
`salida/web/mediciones/streamlit.json`, `fastapi.json` y `salida/web/produccion/navegador.json`.


## Retirada de la migración pública

El autor consideró la presentación inferior a la interfaz Streamlit anterior. Se retiró
el cambio del ejecutable y se restauró Streamlit en la misma URL pública. El código
FastAPI se conserva para revisión; la validación funcional no implica aprobación visual.
README y capturas recuperan la presentación de Streamlit. La medición anterior describe
el experimento retirado y no justifica su publicación.
