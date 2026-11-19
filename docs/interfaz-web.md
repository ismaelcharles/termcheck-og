# Interfaz pública paralela

Implementada en `web/` con FastAPI, plantillas Jinja y HTMX 2.0.8 servido localmente
(licencia incluida). Reutiliza el motor de `src/termcheck` sin modificar sus reglas.
La demo publicada y la aplicación privada siguen en Streamlit.

## Ejecutar

Instalar `requirements-web.txt` en el entorno del proyecto y ejecutar:

```bash
bash scripts/previsualizar-web.sh
```

Disponible en `http://127.0.0.1:8530/`. `TERMCHECK_PUERTO_WEB` cambia el puerto.
No modifica servicios ni configura alojamiento externo. Para cerrar, Ctrl+C.

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
TERMCHECK_URL=http://127.0.0.1:8530/ node scripts/revisar-web.cjs
```

El ensayo de navegador usa las herramientas ya instaladas en este servidor, comprueba
archivos, revisión, descargas completas, navegación, temas y tres visitantes independientes.
Guarda capturas PC/teléfono, HTML, CSV, PDF y `navegador.json` en `salida/web/`.
Las pruebas HTTP contrastan el CSV por aparición directamente con el motor, incluidas las
formas singular y plural de elevator. No recalculan la evaluación congelada del proyecto.

Esta entrega es una previsualización local. Antes de sustituir la demo hay que preparar la
ruta del proxy y el servicio, revisar el montaje bajo esa ruta, comparar latencia y memoria
en el mismo servidor, y comprobar recuperación a la demo existente. La prueba de tres
visitantes comprueba aislamiento; no demuestra capacidad para una carga pública grande.

Referencias: [formularios y archivos de FastAPI](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/),
[formularios multipart con HTMX](https://htmx.org/attributes/hx-encoding/).
