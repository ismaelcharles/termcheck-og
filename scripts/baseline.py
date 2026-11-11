"""El método ingenuo contra el que se compara el verificador (plan 6.2).

Busca la traducción preferida como texto exacto en minúsculas dentro de la traducción. Si no está, «marca».
No sabe de plurales, tildes, variantes aceptadas ni préstamos: justamente eso es lo que el verificador agrega.

    marca("Saque las tuberías de producción.", "tubería de producción")   # True: no la encontró (falso error)
"""


def marca(target_es, es_preferred):
    """True si el baseline marca el término para revisar."""
    return es_preferred.strip().lower() not in (target_es or "").lower()


if __name__ == "__main__":
    print(marca("Saque las tuberías de producción.", "tubería de producción"))
