"""Lanzar: PYTHONPATH=src .venv/bin/uvicorn web.main:app --host 127.0.0.1 --port 8530."""
import random
import unicodedata
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.formparsers import MultiPartParser

from app.proyecto_publico import contenido
from termcheck import VERSION, report
from termcheck.ejemplos import PORTADA, ILUSTRATIVOS
from termcheck.glossary import ErrorDeGlosario, edicion_publicada, publicado
from termcheck.formatos import ErrorDeFormato
from web import servicio

CARPETA = Path(__file__).resolve().parent
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=CARPETA / "static"), name="static")
app.mount("/fonts", StaticFiles(directory=servicio.RAIZ / "app/static/fonts"), name="fonts")
# Las cargas de hasta 1 MB permanecen en memoria durante el análisis.
MultiPartParser.spool_max_size = 3 * servicio.MAX_ARCHIVO
templates = Jinja2Templates(directory=CARPETA / "templates")
templates.env.globals.update(bloque=report.bloque_segmento, version=VERSION,
                             edicion_glosario=lambda: edicion_publicada(servicio.RAIZ / "data/glossary"))


@app.middleware("http")
async def privacidad(request, call_next):
    # Límite también para cuerpos multipart; se rechaza antes de que el parser pueda crear temporales.
    if request.method == "POST":
        origen = request.headers.get("origin")
        from urllib.parse import urlsplit
        if origen and urlsplit(origen).netloc != request.headers.get("host"):
            return Response("Origen no permitido", status_code=403)
        cuerpo = bytearray()
        async for parte in request.stream():
            cuerpo.extend(parte)
            if len(cuerpo) > 2 * servicio.MAX_ARCHIVO + 256_000:
                return Response("La carga supera el tamaño permitido.", status_code=413)
        request._body = bytes(cuerpo)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    return response


def renderizar(request, nombre, **contexto):
    return templates.TemplateResponse(request=request, name=nombre, context=contexto)


def contexto_inicio():
    terminos, _ = servicio.glosario()
    return dict(terminos=terminos, destacados=random.sample(terminos, 3),
                  bienvenida=random.choice(PORTADA), ejemplo=servicio.ejemplo_desarrollo(),
                  proyecto=contenido("FastAPI y HTMX"), css_reporte=report.CSS)


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return renderizar(request, "index.html", **contexto_inicio())


def seccion(request, nombre, pestana, **contexto):
    if request.headers.get("HX-Request") == "true":
        return renderizar(request, nombre, **contexto)
    panel = templates.get_template(nombre).render(**contexto)
    return renderizar(request, "index.html", **contexto_inicio(), panel=panel, pestana=pestana)


async def carga(form, campo):
    archivo = form.get(campo)
    if not isinstance(archivo, UploadFile) or not archivo.filename:
        return None, ""
    datos = await archivo.read(servicio.MAX_ARCHIVO + 1)
    if len(datos) > servicio.MAX_ARCHIVO:
        raise ValueError("El archivo supera el máximo de 1 MB.")
    return datos, Path(archivo.filename).name


@app.post("/verificar", response_class=HTMLResponse)
async def verificar(request: Request):
    try:
        # spool_max_size supera el cuerpo permitido: las cargas viven únicamente en memoria.
        async with request.form(max_files=2, max_fields=8, max_part_size=servicio.MAX_ARCHIVO) as form:
            datos, nombre = await carga(form, "glosario")
            terminos, referencia = servicio.glosario(datos, nombre)
            aviso = ""
            if form.get("modo") == "archivo":
                datos, nombre = await carga(form, "archivo")
                if datos is None:
                    raise ValueError("Elegí un archivo bilingüe para verificar.")
                pares, aviso = servicio.pares_archivo(datos, nombre)
            else:
                pares = servicio.pares_texto(str(form.get("en", "")), str(form.get("es", "")))
            resultado = await run_in_threadpool(servicio.analizar, pares, terminos, referencia, aviso)
        return renderizar(request, "resultado.html", **resultado)
    except (ValueError, ErrorDeGlosario, ErrorDeFormato, HTTPException) as e:
        return renderizar(request, "error.html", mensaje=str(getattr(e, "detail", e)))


def plegar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if not unicodedata.combining(c))


@app.get("/glosario", response_class=HTMLResponse)
def catalogo(request: Request, q: str = "", area: str = "", pagina: int = 1):
    terminos, _ = servicio.glosario()
    consulta = plegar(q[:200].strip())
    filtrados = [t for t in terminos if (not area or t.subdomain == area) and
                 (not consulta or consulta in plegar(" ".join([*t.en, t.es_preferred, *t.es_allowed, *t.es_forbidden, t.note])))]
    paginas = max(1, (len(filtrados) + 11) // 12)
    pagina = min(max(pagina, 1), paginas)
    contexto = dict(terminos=filtrados[(pagina-1)*12:pagina*12], total=len(filtrados), q=q[:200], area=area,
                    areas=sorted({t.subdomain for t in terminos}), numero=pagina, paginas=paginas)
    return seccion(request, "catalogo.html", "glosario", **contexto)


@app.get("/glosario.csv")
def descargar_glosario():
    ruta = publicado(servicio.RAIZ / "data/glossary")
    return Response(ruta.read_bytes(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{ruta.name}"'})


@app.get("/ejemplos", response_class=HTMLResponse)
def ejemplos(request: Request):
    limpiar = lambda s: s.replace("[[", "").replace("]]", "").replace("((", "").replace("))", "")
    return seccion(request, "ejemplos.html", "ejemplos", ejemplos=[dict(e, original=limpiar(e["en"]), traduccion=limpiar(e["es"])) for e in ILUSTRATIVOS])


@app.post("/ejemplo", response_class=HTMLResponse)
async def probar_ejemplo(request: Request):
    async with request.form(max_files=0, max_fields=2, max_part_size=8000) as form:
        try:
            indice = int(str(form.get("indice", "0")))
            if not 0 <= indice < len(ILUSTRATIVOS):
                raise ValueError()
            texto = str(form.get("traduccion", ""))
            if len(texto) > 1500:
                raise ValueError()
        except ValueError:
            return renderizar(request, "error.html", mensaje="Ejemplo inválido.")
        original = ILUSTRATIVOS[indice]["en"].replace("[[", "").replace("]]", "").replace("((", "").replace("))", "")
        terminos, _ = servicio.glosario()
        from termcheck.checker import verificar as motor
        oc = await run_in_threadpool(motor, original, texto, terminos)
    return HTMLResponse(report.bloque_segmento(original, texto, oc))


@app.get("/salud")
def salud():
    return {"estado": "ok", "version": VERSION}


# Caddy conserva /demo/ al reenviar al puerto público. El área privada usa otro servicio.
publica = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
publica.mount("/demo", app)
