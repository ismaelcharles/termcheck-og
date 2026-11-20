"""Coteja una exportación TMX EN–ES con el material de control, sin editarla.

La cabecera declara el generador; no certifica por sí misma la procedencia.
Se necesita además registrar cómo se obtuvo el original desde la herramienta.
"""
from collections import Counter
from pathlib import Path
import argparse,csv,hashlib,json,re,sys
from xml.dom import minidom,Node

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from termcheck.formatos import leer


def norm(s):return re.sub(r'\s+',' ',s).strip()


def comprobar(archivo,referencia,herramienta,version):
    raw=archivo.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if archivo.suffix.lower()!='.tmx':raise ValueError('Para este control se necesita un TMX original exportado desde la herramienta')
    pairs,skip=leer(raw,archivo.name)  # valida XML y entidades antes de la lectura independiente
    doc=minidom.parseString(raw);headers=doc.getElementsByTagName('header')
    creator=headers[0].getAttribute('creationtool') if headers else ''
    if not creator or not re.search('memoq' if herramienta=='memoq' else 'trados|sdl',creator,re.I):
        raise ValueError('La cabecera no identifica la herramienta declarada; no se da por validada la procedencia')
    with referencia.open() as f:expected=Counter((norm(r['source_en']),norm(r['target_es'])) for r in csv.DictReader(f,delimiter='\t'))
    actual=Counter((norm(en),norm(es)) for _,en,es in pairs)
    # Segunda lectura, sin reutilizar la extracción del lector.
    def text(node):
        output=[]
        def walk(e):
            for c in e.childNodes:
                if c.nodeType in (Node.TEXT_NODE,Node.CDATA_SECTION_NODE):output.append(c.data)
                elif c.nodeType==Node.ELEMENT_NODE and c.tagName not in {'bpt','ept','ph','it','ut'}:walk(c)
        walk(node);return norm(''.join(output))
    independent=Counter()
    for tu in doc.getElementsByTagName('tu'):
        variants={}
        for v in [n for n in tu.childNodes if n.nodeType==Node.ELEMENT_NODE and n.tagName=='tuv']:
            lang=(v.getAttribute('xml:lang') or v.getAttribute('lang')).lower().replace('_','-').split('-')[0]
            segments=v.getElementsByTagName('seg')
            variants.setdefault(lang,text(segments[0]) if segments else '')
        if variants.get('en') and variants.get('es'):independent[(variants['en'],variants['es'])]+=1
    if actual!=independent:raise ValueError('La extracción difiere de la lectura XML independiente')
    assert hashlib.sha256(archivo.read_bytes()).hexdigest()==digest
    return dict(herramienta_declarada=herramienta,version_declarada=version,creationtool=creator,
                creationtoolversion=headers[0].getAttribute('creationtoolversion'),sha256=digest,
                pares=sum(actual.values()),pares_referencia=sum(expected.values()),omitidos_sin_es=skip,
                faltantes=sum((expected-actual).values()),adicionales=sum((actual-expected).values()),
                coincide_con_referencia=actual==expected and skip==0,coincide_con_lectura_independiente=True,
                original_intacto=True,procedencia='Cabecera y declaración; requiere registrar la exportación real',
                alcance='Control de importación TMX; no valida formato nativo, reexportación ni calidad de traducción')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archivo',type=Path,required=True);parser.add_argument('--referencia',type=Path,required=True)
    parser.add_argument('--herramienta',choices=['trados','memoq'],required=True);parser.add_argument('--version',required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    try:
        result=comprobar(args.archivo,args.referencia,args.herramienta,args.version)
        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False,indent=2));raise SystemExit(0 if result['coincide_con_referencia'] else 2)
    except ValueError as e:print(str(e),file=sys.stderr);raise SystemExit(2)
