"""Límites de la demo pública (el servidor es compartido). Los usa la página Verificar cuando corre como demo.

El tamaño máximo de archivo subido (1 MB) lo pone el servicio: `--server.maxUploadSize 1` en deploy/demo.sh.
"""
MAX_SEGMENTOS = 200      # segmentos por verificación
MAX_LETRAS = 20000       # letras en cada cuadro de texto, y en cada lado de un archivo
MAX_TERMINOS = 1000      # términos de un glosario subido


def aplicar(pares):
    """pares: [(seg_id, sistema, inglés, traducción)] → (pares que se verifican, aviso o "", se puede seguir)."""
    aviso = ""
    if len(pares) > MAX_SEGMENTOS:
        aviso = f"Son {len(pares)} segmentos. La demo verifica los primeros {MAX_SEGMENTOS}."
        pares = pares[:MAX_SEGMENTOS]
    if sum(len(p[2]) for p in pares) > MAX_LETRAS or sum(len(p[3]) for p in pares) > MAX_LETRAS:
        return [], (f"El texto es demasiado largo para la demo (máximo {MAX_LETRAS} letras de cada lado). "
                    "Probá con una parte."), False
    return pares, aviso, True
