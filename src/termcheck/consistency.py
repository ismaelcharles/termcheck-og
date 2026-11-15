"""Consistencia en el documento (plan 3.2, etiqueta INCONSISTENTE).

Un «documento» es el conjunto de segmentos de un mismo sistema. Si un término se tradujo con formas distintas
(entre la preferida y las válidas) en distintos segmentos, se da una advertencia. Se compara qué forma del
glosario coincidió, así «tubería de producción» y «tuberías de producción» son la misma.

    advertencias = inconsistencias(ocurrencias)
    # [Inconsistencia(system="deepl", term_id="T030", formas={"lodo de perforación": ["S003"],
    #                                                         "fluido de perforación": ["S007"]})]
"""
from dataclasses import dataclass, field


@dataclass
class Inconsistencia:
    system: str
    term_id: str
    formas: dict = field(default_factory=dict)  # forma tal como apareció la primera vez → [seg_id]
    term_en: str = ""                           # el término en inglés, como apareció la primera vez

    def __str__(self):
        partes = "; ".join(f"«{f}» en {', '.join(s)}" for f, s in self.formas.items())
        return f"INCONSISTENTE {self.system} {self.term_id}: {partes}"


def inconsistencias(ocurrencias):
    """[Ocurrencia] → [Inconsistencia], una por (sistema, término) con más de una forma aceptada."""
    grupos, en_ingles = {}, {}
    for o in ocurrencias:
        if o.label not in ("OK", "VARIANTE"):
            continue
        formas = grupos.setdefault((o.system, o.term_id), {})
        en_ingles.setdefault((o.system, o.term_id), o.term_en)
        clave = o.es_form or o.es_found
        nombre, segs = formas.get(clave, (o.es_found, []))
        if o.seg_id not in segs:
            segs.append(o.seg_id)
        formas[clave] = (nombre, segs)
    salida = []
    for (system, term_id), formas in sorted(grupos.items()):
        if len(formas) > 1:
            salida.append(Inconsistencia(system, term_id, {n: s for n, s in formas.values()},
                                         en_ingles[(system, term_id)]))
    return salida
