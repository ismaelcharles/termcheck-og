"""Inventario de exposición del glosario y comprobación de sus formas declaradas.

No estima recall ni valida terminología por sí mismo. El control literal es una
lista de candidatos independiente del detector, no una referencia anotada.
"""
from collections import Counter
from pathlib import Path
import argparse
import csv
import hashlib
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from termcheck import VERSION
from termcheck.checker import detectar, verificar
from termcheck.matcher import analizar
from termcheck.glossary import cargar
from termcheck.formatos import leer


def normalizar(text):
    return re.sub(r'\s+',' ',re.sub(r'[-‐‑–—]',' ',text.casefold())).strip()


def literal(text,forms):
    text=normalizar(text)
    for form in forms:
        form=normalizar(form)
        # Solo singular y plural regular como candidatos de revisión.
        if re.search(r'(?<!\w)'+re.escape(form)+r'(?:s|es)?(?!\w)',text):return True
    return False


def auditar(out, public_samples=None):
    if public_samples:
        public_samples=public_samples.resolve()
    glossary=ROOT/'data/glossary/glossary_v1_4.csv'
    terms=cargar(glossary)
    rows=[];inputs=[glossary,ROOT/'data/corpus/segments.tsv',ROOT/'data/annotations/gold.csv']
    with inputs[1].open() as f:
        rows += [dict(grupo='corpus',id=r['seg_id'],en=r['source_en']) for r in csv.DictReader(f,delimiter='\t')]
    if public_samples:
        for group,name in [('directiva','directiva-art2.xlf'),('dgt','E2006C0069.tmx'),('dgt-control','E2006G0001.tmx')]:
            path=public_samples/name;inputs.append(path)
            pairs,_=leer(path.read_bytes(),name)
            rows += [dict(grupo=group,id=sid,en=en) for sid,en,_ in pairs]
        for group in ('ifc-offshore','ifc-onshore'):
            path=public_samples/'ampliacion'/(group+'-pares.json');inputs.append(path)
            rows += [dict(grupo=group,id=r['id'],en=r['en']) for r in json.loads(path.read_text())]
    counts={t.id:Counter() for t in terms};seen={t.id:set() for t in terms};candidates={t.id:set() for t in terms}
    contexts=[]
    for row in rows:
        key=hashlib.sha256(normalizar(row['en']).encode()).hexdigest()
        found={t.id for _,_,t in detectar(analizar(row['en'],'en'),terms)}
        cand={t.id for t in terms if literal(row['en'],t.en)}
        contexts.append(dict(grupo=row['grupo'],id=row['id'],sha256_normalizado=key,
                             detectados=sorted(found),candidatos_literales=sorted(cand)))
        for tid in found:
            counts[tid][row['grupo']]+=1;seen[tid].add(key)
        for tid in cand:candidates[tid].add(key)
    with inputs[2].open() as f:gold=[r for r in csv.DictReader(f) if r['label'] not in ('NO_VA','DUDA')]
    contract=[]
    for t in terms:
        en='Inspect the '+t.en[0]+'.'
        for kind,forms in [('preferida',[t.es_preferred]),('valida',t.es_allowed),('prohibida',t.es_forbidden)]:
            for form in forms:
                own=[o for o in verificar(en,'Inspeccione '+form+'.',terms) if o.term_id==t.id]
                ok=bool(own) and all((o.label=='PROHIBIDO') if kind=='prohibida' else not o.marcada for o in own)
                contract.append(dict(term_id=t.id,tipo=kind,forma=form,etiquetas=[o.label for o in own],ok=ok))
    inventory=[]
    for t in terms:
        human=[r for r in gold if r['term_id']==t.id]
        inventory.append(dict(term_id=t.id,en='|'.join(t.en),area=t.subdomain,
            contextos_detectados_unicos=len(seen[t.id]),contextos_candidatos_literales_unicos=len(candidates[t.id]),
            contextos_humanos_historicos=len({r['seg_id'] for r in human}),decisiones_humanas_historicas=len(human),
            formas_controladas=sum(r['term_id']==t.id for r in contract),
            fallos_formas=sum(r['term_id']==t.id and not r['ok'] for r in contract),por_grupo=dict(counts[t.id])))
    summary=dict(version=VERSION,glosario='1.4',conceptos=len(terms),
        segmentos_por_grupo=dict(Counter(r['grupo'] for r in rows)),
        segmentos_totales=len(rows),contextos_unicos=len({r['sha256_normalizado'] for r in contexts}),
        conceptos_con_deteccion=sum(bool(r['contextos_detectados_unicos']) for r in inventory),
        conceptos_sin_deteccion=[r['term_id'] for r in inventory if not r['contextos_detectados_unicos']],
        conceptos_con_candidato_literal=sum(bool(r['contextos_candidatos_literales_unicos']) for r in inventory),
        conceptos_sin_referencia_humana_historica=[r['term_id'] for r in inventory if not r['contextos_humanos_historicos']],
        formas_controladas=len(contract),fallos_formas=sum(not r['ok'] for r in contract),
        limites=['Exposición observada, no recall ni validación de calidad.',
                 'El candidato literal no distingue categoría, conceptos anidados ni todos los plurales.',
                 'El control de formas es coherencia declarativa del glosario, no evidencia de uso real.',
                 'La referencia humana histórica corresponde a su glosario y criterio históricos.'])
    out.mkdir(parents=True,exist_ok=True)
    for name,data in [('resumen.json',summary),('inventario.json',inventory),('formas.json',contract),('contextos.json',contexts)]:
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (out/'insumos-sha256.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2)+'\n')
    with (out/'inventario.csv').open('w',newline='') as f:
        fields=[k for k in inventory[0] if k!='por_grupo'];writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({k:r[k] for k in fields} for r in inventory)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--muestras-publicas',type=Path)
    args=parser.parse_args()
    auditar(args.out,args.muestras_publicas)
