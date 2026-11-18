"""Lee tablas bilingües sin descartar filas defectuosas ni cambiar la pareja de textos."""
import csv
import io


def leer_tabla(datos):
    """CSV de dos columnas (coma, punto y coma o tabulación) → pares de textos."""
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError as e:
        raise ValueError("No pude leer el archivo. Tiene que ser texto en UTF-8.") from e
    if not texto.strip():
        raise ValueError("El archivo está vacío.")
    try:
        separador = csv.Sniffer().sniff(texto, delimiters=",;\t").delimiter
    except csv.Error:
        # Una fila rota puede impedir la detección; se lee con el encabezado para señalar la fila precisa.
        primera = texto.splitlines()[0]
        separador = "\t" if "\t" in primera else max(",;", key=primera.count)
    lector = csv.reader(io.StringIO(texto, newline=""), delimiter=separador, strict=True)
    pares = []
    try:
        for fila in lector:
            if not fila or not any(c.strip() for c in fila):
                continue
            if not pares and [c.strip().lower() for c in fila] == ["source_en", "target_es"]:
                continue
            if len(fila) != 2:
                cantidad = f"{len(fila)} {'columna' if len(fila) == 1 else 'columnas'}"
                raise ValueError(f"La fila {lector.line_num} tiene {cantidad}; se necesitan dos: "
                                 "inglés y español. No se verificó el archivo.")
            if not fila[0].strip():
                raise ValueError(f"Falta el original en inglés en la fila {lector.line_num}. "
                                 "No se verificó el archivo.")
            # Un destino vacío sí se verifica: puede ser una omisión.
            pares.append((fila[0], fila[1]))
    except csv.Error as e:
        raise ValueError(f"No pude leer el CSV cerca de la fila {lector.line_num}: revisá las comillas "
                         "y el separador. No se verificó el archivo.") from e
    if not pares:
        raise ValueError("No encontré filas con textos para verificar.")
    return pares
