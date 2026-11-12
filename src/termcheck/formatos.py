"""Leer archivos de las herramientas de traducción: XLIFF 1.2, XLIFF 2.0 y TMX (plan, parte 7).

    from termcheck.formatos import leer
    pares, sin_traduccion = leer(Path("proyecto.xliff").read_bytes(), "proyecto.xliff")
    for seg_id, en, es in pares:
        ...

Devuelve los segmentos que tienen inglés y traducción, y cuántos se saltearon por no tener traducción.
Solo usa la biblioteca estándar de Python.

Qué lee:
- XLIFF 1.2: cada <trans-unit> con su <source> y su <target>. Si la unidad está partida en segmentos
  (<seg-source> con <mrk mtype="seg">), sale un par por segmento.
- XLIFF 2.0: cada <segment> de cada <unit>. Los <ignorable> no cuentan.
- TMX: cada <tu> con una <tuv> en inglés y otra en español (xml:lang que empieza con «en» y con «es»).
  Si los idiomas no están marcados así, toma el idioma de origen del encabezado y la otra variante.

Las etiquetas internas (negritas, marcadores de formato) se sacan y queda el texto. Lo que va dentro de
<bpt>, <ept>, <ph>, <it> y <ut> es código de formato y no texto: se descarta.

Qué NO lee: los formatos propios de cada herramienta (.sdlxliff de Trados, .mqxliff de memoQ). Se probó con
archivos armados a mano según la norma, no con exportaciones reales de esas herramientas.

Seguridad: un XML puede traer definiciones (<!ENTITY>) que hacen crecer el archivo hasta agotar la memoria.
Por eso se rechaza cualquier archivo que defina entidades o que traiga un DOCTYPE con definiciones adentro.
El DOCTYPE simple que ponen muchos TMX (<!DOCTYPE tmx SYSTEM "tmx14.dtd">) se saca antes de leer y no se va a
buscar ningún archivo externo.
"""
import re
import xml.etree.ElementTree as ET

EXTENSIONES = (".xliff", ".xlf", ".tmx")
CODIGO = {"bpt", "ept", "ph", "it", "ut"}  # su contenido es código de formato, no texto
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


class ErrorDeFormato(ValueError):
    """El archivo no se pudo leer. El mensaje está pensado para mostrarlo tal cual."""


def es_de_traduccion(nombre):
    """True si por la extensión es un XLIFF o un TMX."""
    return str(nombre).lower().endswith(EXTENSIONES)


def _a_texto(datos):
    """Los bytes del archivo como texto. Mira la marca de orden de bytes y la codificación declarada."""
    if isinstance(datos, str):
        return datos
    if datos[:3] == b"\xef\xbb\xbf":
        return datos[3:].decode("utf-8")
    if datos[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return datos.decode("utf-16")
    declarada = re.match(rb"\s*<\?xml[^>]*encoding=[\"']([A-Za-z0-9._-]+)[\"']", datos[:200])
    codificacion = declarada.group(1).decode("ascii") if declarada else "utf-8"
    try:
        return datos.decode(codificacion)
    except (LookupError, UnicodeDecodeError):
        raise ErrorDeFormato("No pude leer el archivo: la codificación no es la que declara. Guardalo en UTF-8.")


def _raiz(datos):
    """El XML ya leído. Rechaza los archivos con definiciones de entidades."""
    texto = _a_texto(datos)
    if "<!ENTITY" in texto:
        raise ErrorDeFormato("El archivo define entidades XML (<!ENTITY>). Por seguridad no se lee.")
    doctype = re.search(r"<!DOCTYPE[^>\[]*(\[)?", texto)
    if doctype and doctype.group(1):
        raise ErrorDeFormato("El archivo trae un DOCTYPE con definiciones adentro. Por seguridad no se lee.")
    if doctype:
        texto = texto[:doctype.start()] + re.sub(r"<!DOCTYPE[^>]*>", "", texto[doctype.start():], count=1)
    texto = re.sub(r"^\s*<\?xml[^>]*\?>", "", texto, count=1)  # ya está decodificado: la declaración sobra
    try:
        return ET.fromstring(texto)
    except ET.ParseError as e:
        raise ErrorDeFormato(f"El archivo no es un XML válido ({e}).")


def _nombre(elemento):
    """El nombre de la etiqueta sin el espacio de nombres: «{urn:…}source» → «source»."""
    return elemento.tag.rsplit("}", 1)[-1] if isinstance(elemento.tag, str) else ""


def _hijos(elemento, nombre):
    return [h for h in elemento if _nombre(h) == nombre]


def _todos(elemento, nombre):
    return [h for h in elemento.iter() if _nombre(h) == nombre]


def _texto(elemento):
    """El texto de un elemento sin las etiquetas internas y con los espacios acomodados."""
    if elemento is None:
        return ""

    def partes(e):
        yield e.text or ""
        for hijo in e:
            if _nombre(hijo) not in CODIGO:
                yield from partes(hijo)
            yield hijo.tail or ""

    return re.sub(r"\s+", " ", "".join(partes(elemento))).strip()


def _segmentos_mrk(elemento):
    """{mid: elemento} de los <mrk mtype="seg"> de un <seg-source> o un <target> (XLIFF 1.2)."""
    if elemento is None:
        return {}
    return {m.get("mid", str(n)): m for n, m in enumerate(_todos(elemento, "mrk")) if m.get("mtype") == "seg"}


def _xliff_1(raiz):
    for n, unidad in enumerate(_todos(raiz, "trans-unit"), start=1):
        uid = unidad.get("id") or str(n)
        origen = (_hijos(unidad, "source") or [None])[0]
        destino = (_hijos(unidad, "target") or [None])[0]
        partido = _segmentos_mrk((_hijos(unidad, "seg-source") or [None])[0])
        if partido:
            traducido = _segmentos_mrk(destino)
            for mid, m in partido.items():
                yield f"{uid}#{mid}", _texto(m), _texto(traducido.get(mid))
        else:
            yield uid, _texto(origen), _texto(destino)


def _xliff_2(raiz):
    for n, unidad in enumerate(_todos(raiz, "unit"), start=1):
        uid = unidad.get("id") or str(n)
        segmentos = _hijos(unidad, "segment")
        for m, seg in enumerate(segmentos, start=1):
            sid = uid if len(segmentos) == 1 else f"{uid}#{seg.get('id') or m}"
            yield sid, _texto((_hijos(seg, "source") or [None])[0]), _texto((_hijos(seg, "target") or [None])[0])


def _tmx(raiz):
    encabezado = (_todos(raiz, "header") or [None])[0]
    origen_general = (encabezado.get("srclang") or "").lower() if encabezado is not None else ""
    for n, tu in enumerate(_todos(raiz, "tu"), start=1):
        variantes = []
        for tuv in _hijos(tu, "tuv"):
            idioma = (tuv.get(XML_LANG) or tuv.get("lang") or "").lower()
            variantes.append((idioma, _texto((_hijos(tuv, "seg") or [None])[0])))
        en = next((t for i, t in variantes if i.startswith("en")), None)
        es = next((t for i, t in variantes if i.startswith("es")), None)
        if en is None and es is None:
            # Ninguna variante dice «en» ni «es»: el idioma de origen del archivo y la otra variante
            origen = (tu.get("srclang") or origen_general).lower()
            en = next((t for i, t in variantes if origen and i == origen), None)
            es = next((t for i, t in variantes if i != origen), None) if en is not None else None
        if en is None:
            continue
        yield tu.get("tuid") or str(n), en, es or ""


def leer(datos, nombre=""):
    """Bytes de un XLIFF o un TMX → ([(seg_id, inglés, traducción)], cuántos se saltearon sin traducción).

    Los identificadores no se repiten: si el archivo repite uno, al segundo se le agrega «-2», y así.
    Levanta ErrorDeFormato si el archivo no es XML, trae entidades o no es ninguno de los tres formatos.
    """
    raiz = _raiz(datos)
    tipo = _nombre(raiz)
    if tipo == "xliff":
        version = (raiz.get("version") or "").strip()
        if version.startswith("1"):
            filas = _xliff_1(raiz)
        elif version.startswith("2"):
            filas = _xliff_2(raiz)
        else:
            raise ErrorDeFormato(f"No conozco esa versión de XLIFF («{version or 'sin versión'}»). Leo 1.2 y 2.0.")
    elif tipo == "tmx":
        filas = _tmx(raiz)
    else:
        raise ErrorDeFormato(f"El archivo no es XLIFF ni TMX (empieza con <{tipo}>).")
    pares, sin_traduccion, vistos = [], 0, {}
    for seg_id, en, es in filas:
        if not en:
            continue
        if not es:
            sin_traduccion += 1
            continue
        vistos[seg_id] = vistos.get(seg_id, 0) + 1
        if vistos[seg_id] > 1:
            seg_id = f"{seg_id}-{vistos[seg_id]}"
        pares.append((seg_id, en, es))
    if not pares and not sin_traduccion:
        raise ErrorDeFormato("No encontré segmentos en el archivo.")
    return pares, sin_traduccion
