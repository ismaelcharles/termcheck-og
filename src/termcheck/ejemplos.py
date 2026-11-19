PORTADA = (
    {"id": "T011", "en": "drilling rig",
     "original": "The drilling rig was moved to the new location.",
     "inicial": "La plataforma de perforación se trasladó a la nueva locación.",
     "corregida": "El equipo de perforación se trasladó a la nueva locación.",
     "contexto": "El parte describe una perforación en tierra. Una sola palabra cambia dónde imaginamos el equipo."},
    {"id": "T038", "en": "kick",
     "original": "The crew detected a kick during drilling.",
     "inicial": "La cuadrilla detectó una patada durante la perforación.",
     "corregida": "La cuadrilla detectó una surgencia durante la perforación.",
     "contexto": "El parte describe una entrada de fluido de la formación al pozo. La traducción literal pierde el sentido técnico."},
    {"id": "T019", "en": "wellhead",
     "original": "Inspect the wellhead before starting production.",
     "inicial": "Inspeccioná la cabeza del pozo antes de iniciar la producción.",
     "corregida": "Inspeccioná la boca de pozo antes de iniciar la producción.",
     "contexto": "La instrucción se refiere al equipo en superficie. El glosario fija la denominación elegida para este encargo."},
    {"id": "T035", "en": "drill pipe",
     "original": "Inspect the drill pipe before drilling.",
     "inicial": "Inspeccioná el tubo de perforación antes de perforar.",
     "corregida": "Inspeccioná la barra de sondeo antes de perforar.",
     "contexto": "La instrucción pide revisar una pieza de la sarta. La elección del término responde al registro petrolero argentino."},
)


ILUSTRATIVOS = [
    {"titulo": "Traducción prohibida", "etiqueta": "PROHIBIDO",
     "en": "The [[shale]] formation lies 3,000 m below the surface.",
     "es": "La formación de [[esquisto]] está a 3.000 m de profundidad.",
     "porque": "«Esquisto» es *schist*, otra roca. El glosario lo marca como error frecuente de la traducción "
               "automática: en Vaca Muerta se dice «shale» o «lutita»."},
    {"titulo": "Error que suena bien", "etiqueta": "PROHIBIDO",
     "en": "The [[drilling rig]] was moved to the new location.",
     "es": "La [[plataforma de perforación]] se trasladó a la nueva locación.",
     "porque": "Para este contexto de perforación en tierra, el glosario prefiere «equipo de perforación» "
               "y señala «plataforma de perforación». Una frase fluida también puede apartarse de la "
               "terminología elegida para el encargo."},
    {"titulo": "Plural que coincide", "etiqueta": "OK",
     "en": "Check the [[drilling fluids]] every shift.",
     "es": "Controlá los [[lodos de perforación]] en cada turno.",
     "porque": "El glosario dice «lodo de perforación», en singular. El verificador compara lemas "
               "(«lodos» → «lodo»), así que el plural no es error."},
    {"titulo": "Préstamo aceptado", "etiqueta": "OK",
     "en": "Run the [[casing]] to 2,000 m.",
     "es": "Bajar el [[casing]] hasta 2.000 m.",
     "porque": "Quedó en inglés, pero en el campo argentino se dice «casing». Como el glosario lo acepta, no se marca."},
    {"titulo": "Quedó en inglés", "etiqueta": "SIN_TRADUCIR",
     "en": "The [[pumpjack]] stopped at noon.",
     "es": "El [[pumpjack]] se detuvo al mediodía.",
     "porque": "El glosario prefiere «AIB» y no acepta «pumpjack» como préstamo. Por eso lo señala para revisar."},
    {"titulo": "No aparece", "etiqueta": "NO_ENCONTRADO",
     "en": "The [[blowout preventer]] was tested before drilling.",
     "es": "El [[equipo de seguridad]] se probó antes de perforar.",
     "porque": "Ninguna traducción conocida («BOP», «preventor de reventones») está en la traducción. Puede ser "
               "una omisión o un sinónimo que falta en el glosario: lo decide quien revisa."},
    {"titulo": "«well» que no es pozo", "etiqueta": "OK",
     "en": "Check the [[BOP]] as ((well)) as the choke manifold.",
     "es": "Revisá el [[BOP]] y también el choke manifold.",
     "porque": "Acá «well» es adverbio (*as well as* = «además de»), no el sustantivo «pozo». El verificador mira "
               "la categoría gramatical y no lo cuenta como término.", "apagado": "ADV: no es el término «pozo»"},
]


