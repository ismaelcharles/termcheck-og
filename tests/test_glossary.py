"""Pruebas de la carga y validación del glosario (src/termcheck/glossary.py) y de la normalización.

Correr:  .venv/bin/python -m pytest -v

Usan un glosario mínimo propio, escrito en cada prueba (las filas de ejemplo del plan): no dependen del glosario real.
"""
import pytest

from termcheck.glossary import ErrorDeGlosario, cargar, separar, validar
from termcheck.normalize import normalizar

ENCABEZADO = "id,en,pos,es_preferred,es_allowed,es_forbidden,subdomain,note,source\n"


def escribir(tmp_path, filas, encabezado=ENCABEZADO, bom=False):
    """Escribe un CSV de prueba y devuelve su ruta."""
    ruta = tmp_path / "glosario.csv"
    ruta.write_text(("﻿" if bom else "") + encabezado + "".join(f + "\n" for f in filas), encoding="utf-8")
    return ruta


def errores(problemas):
    return [p for p in problemas if p.tipo == "error"]


# ───────── normalizar ─────────

def test_normalizar_tildes_y_mayusculas():
    assert normalizar("Lodo de Perforacion") == normalizar("lodo de perforación")


def test_normalizar_guiones_y_espacios():
    assert normalizar("Well-Head ") == "well head"
    assert normalizar("lodo  de\tperforación") == "lodo de perforacion"


# ───────── separar ─────────

def test_separar_variantes():
    assert separar("wellhead | well-head |") == ["wellhead", "well-head"]
    assert separar("") == []


# ───────── cargar ─────────

def test_cargar_separa_variantes(tmp_path):
    ruta = escribir(tmp_path, [
        'T007,blowout preventer|BOP,NOUN,BOP,preventor de reventones,,control de pozo,,VERIFICAR',
    ])
    [t] = cargar(ruta)
    assert t.id == "T007"
    assert t.en == ["blowout preventer", "BOP"]
    assert t.es_preferred == "BOP"
    assert t.es_allowed == ["preventor de reventones"]
    assert t.es_forbidden == []


def test_cargar_campo_con_comas_entre_comillas(tmp_path):
    ruta = escribir(tmp_path, [
        'T001,drilling rig|rig,NOUN,equipo de perforación,,plataforma de perforación,perforación,'
        '"\'plataforma\' implica offshore, en tierra es \'equipo\'",VERIFICAR',
    ])
    [t] = cargar(ruta)
    assert t.note == "'plataforma' implica offshore, en tierra es 'equipo'"


def test_cargar_acepta_bom_de_excel(tmp_path):
    ruta = escribir(tmp_path, ['T005,well,NOUN,pozo,,,general,,VERIFICAR'], bom=True)
    [t] = cargar(ruta)
    assert t.id == "T005"


def test_cargar_saltea_filas_vacias(tmp_path):
    ruta = escribir(tmp_path, ['T005,well,NOUN,pozo,,,general,,VERIFICAR', ',,,,,,,,'])
    assert len(cargar(ruta)) == 1


def test_cargar_falta_columna(tmp_path):
    ruta = escribir(tmp_path, ['T005,well,NOUN,pozo'], encabezado="id,en,pos,es_preferred\n")
    with pytest.raises(ErrorDeGlosario, match="es_allowed"):
        cargar(ruta)


def test_cargar_archivo_que_no_existe(tmp_path):
    with pytest.raises(ErrorDeGlosario):
        cargar(tmp_path / "no_esta.csv")


# ───────── validar ─────────

def test_glosario_correcto_no_tiene_problemas(tmp_path):
    ruta = escribir(tmp_path, [
        'T003,shale,NOUN,shale,lutita,esquisto,geología,,VERIFICAR',
        'T004,casing,NOUN,casing,cañería de entubación|tubería de revestimiento,,perforación,,VERIFICAR',
    ])
    assert validar(cargar(ruta)) == []


def test_id_repetido(tmp_path):
    ruta = escribir(tmp_path, [
        'T003,shale,NOUN,shale,,,geología,,VERIFICAR',
        'T003,casing,NOUN,casing,,,perforación,,VERIFICAR',
    ])
    assert any("repetido" in p.mensaje for p in errores(validar(cargar(ruta))))


def test_falta_preferida_e_ingles(tmp_path):
    ruta = escribir(tmp_path, ['T009,,NOUN,,,,perforación,,VERIFICAR'])
    mensajes = [p.mensaje for p in errores(validar(cargar(ruta)))]
    assert "falta el término en inglés" in mensajes
    assert "falta la traducción preferida" in mensajes


def test_categoria_que_no_existe(tmp_path):
    ruta = escribir(tmp_path, ['T005,well,SUSTANTIVO,pozo,,,general,,VERIFICAR'])
    assert any("categoría" in p.mensaje for p in errores(validar(cargar(ruta))))


def test_forma_valida_y_prohibida_a_la_vez(tmp_path):
    # Con tildes y mayúsculas distintas sigue siendo la misma forma
    ruta = escribir(tmp_path, [
        'T001,drilling rig,NOUN,equipo de perforación,Plataforma de Perforacion,plataforma de perforación,,,VERIFICAR',
    ])
    [p] = errores(validar(cargar(ruta)))
    assert "válida" in p.mensaje and "prohibida" in p.mensaje


def test_preferida_repetida_como_valida(tmp_path):
    ruta = escribir(tmp_path, ['T005,well,NOUN,pozo,pozo,,general,,VERIFICAR'])
    assert len(errores(validar(cargar(ruta)))) == 1


def test_misma_forma_en_ingles_en_dos_terminos(tmp_path):
    ruta = escribir(tmp_path, [
        'T001,drilling rig|rig,NOUN,equipo de perforación,,,perforación,,VERIFICAR',
        'T008,Rig,NOUN,equipo,,,perforación,,VERIFICAR',
    ])
    [p] = errores(validar(cargar(ruta)))
    assert p.id == "T008" and "T001" in p.mensaje


def test_variantes_de_escritura_con_guion_chocan(tmp_path):
    # «well-head» y «well head» se normalizan igual: listarlas en dos términos distintos es un error
    ruta = escribir(tmp_path, [
        'T010,well-head,NOUN,cabeza de pozo,,,producción,,VERIFICAR',
        'T011,well head,NOUN,cabeza de pozo,,,producción,,VERIFICAR',
    ])
    assert len(errores(validar(cargar(ruta)))) == 1


def test_sin_fuente_es_aviso_no_error(tmp_path):
    ruta = escribir(tmp_path, ['T005,well,NOUN,pozo,,,general,,'])
    [p] = validar(cargar(ruta))
    assert p.tipo == "aviso"


def test_misma_forma_espanola_en_dos_terminos_vale(tmp_path):
    # «anular» puede valer para annulus y para annular preventer: la búsqueda en español es por término
    ruta = escribir(tmp_path, [
        'T004,annulus,NOUN,espacio anular,anular,,perforación,,VERIFICAR',
        'T020,annular preventer,NOUN,preventor anular,anular,,control de pozo,,VERIFICAR',
    ])
    assert validar(cargar(ruta)) == []


def test_forma_repetida_dentro_del_mismo_termino_es_aviso(tmp_path):
    ruta = escribir(tmp_path, ['T012,screen-out|screen out,NOUN,arenamiento,,,terminación,,VERIFICAR'])
    [p] = validar(cargar(ruta))
    assert p.tipo == "aviso"
