"""Una variante completa admitida no se convierte en prohibida por una parte suya."""
import pytest

from termcheck.checker import verificar
from termcheck.glossary import Termino


LINER=Termino('CLIENTE-LINER',['liner'],'NOUN','liner',
              ['tubería de revestimiento corta','tubería corta'],['revestimiento'])


@pytest.mark.parametrize('texto,forma',[
    ('Instale la tubería de revestimiento corta.','tubería de revestimiento corta'),
    ('Instale las tuberías de revestimiento cortas.','tuberías de revestimiento cortas'),
    ('Instale la TUBERÍA DE REVESTIMIENTO CORTA.','TUBERÍA DE REVESTIMIENTO CORTA'),
])
def test_variante_completa_admitida(texto,forma):
    [o]=verificar('Install the liner.',texto,[LINER])
    assert (o.label,o.es_found)==('VARIANTE',forma)
    assert texto[o.start:o.end]==forma


@pytest.mark.parametrize('texto',[
    'Instale el revestimiento.',
    'Instale la tubería de revestimiento.',
    'Instale la tubería de revestimiento larga.',
    'Instale la tubería de revestimiento corta y revise el revestimiento.',
    'Revise el revestimiento e instale la tubería de revestimiento corta.',
    'Instale la tubería corta y revise el revestimiento.',
    'Instale el liner y revise el revestimiento.',
])
def test_prohibida_fuera_de_la_variante_sigue_marcada(texto):
    [o]=verificar('Install the liner.',texto,[LINER])
    assert o.label=='PROHIBIDO'
    assert o.es_found=='revestimiento'
    assert texto[o.start:o.end]=='revestimiento'
    if 'corta' in texto and 'revestimiento corta' in texto:
        assert not texto.index('tubería de revestimiento corta')<=o.start<texto.index('tubería de revestimiento corta')+len('tubería de revestimiento corta')


def test_no_descarta_una_prohibida_mayor_por_variante_corta():
    term=Termino('CLIENTE-COLGADOR',['liner hanger'],'NOUN','colgador de liner',
                 ['colgador'],['colgador de revestimiento'])
    [o]=verificar('Inspect the liner hanger.','Inspeccione el colgador de revestimiento.',[term])
    assert (o.label,o.es_found)==('PROHIBIDO','colgador de revestimiento')


def test_preferida_completa_tambien_desambigua_su_parte():
    term=Termino('CLIENTE',['liner'],'NOUN','tubería de revestimiento corta',[],['revestimiento'])
    [o]=verificar('Install the liner.','Instale la tubería de revestimiento corta.',[term])
    assert o.label=='OK'


def test_apariciones_separadas_no_se_ocultan():
    text='Instale una tubería de revestimiento corta y luego un revestimiento.'
    oc=verificar('Install a liner and then another liner.',text,[LINER])
    assert len(oc)==2
    assert any(o.label=='PROHIBIDO' for o in oc)
    assert any(o.label=='VARIANTE' for o in oc)


def test_forma_reservada_para_otro_termino_no_silencia_prohibida():
    pipe=Termino('CLIENTE-PIPE',['pipe assembly'],'NOUN','tubería')
    oc=verificar('Install the liner near the pipe assembly.','Instale la tubería de revestimiento corta.',[LINER,pipe])
    assert next(o for o in oc if o.term_id==pipe.id).label=='OK'
    assert next(o for o in oc if o.term_id==LINER.id).label=='PROHIBIDO'
