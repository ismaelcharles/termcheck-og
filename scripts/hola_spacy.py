"""Fase 0: comprobar que spaCy anda en inglés y en español.

Para cada palabra muestra: la palabra tal como está, su lema (la forma de diccionario)
y su categoría gramatical (NOUN = sustantivo, VERB = verbo, ADJ = adjetivo, etc.).
"""
import spacy

# Cargar los dos modelos chicos (corren en CPU).
nlp_en = spacy.load("en_core_web_sm")
nlp_es = spacy.load("es_core_news_sm")

oracion_en = "The drilling rigs were checked as well as the wellheads."
oracion_es = "Se revisaron las tuberías de producción y el lodo de perforación."


def mostrar(nlp, oracion):
    print(oracion)
    print(f"{'palabra':<14}{'lema':<14}categoría")
    for palabra in nlp(oracion):
        print(f"{palabra.text:<14}{palabra.lemma_:<14}{palabra.pos_}")
    print()


mostrar(nlp_en, oracion_en)
mostrar(nlp_es, oracion_es)
