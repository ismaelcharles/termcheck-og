"""Prepara material inventado para una prueba de uso y una exportación CAT real.

El ZIP no contiene respuestas esperadas. No registra participantes ni resultados
de sesiones que no se hayan realizado.
"""
from pathlib import Path
import argparse,csv,hashlib,json,zipfile
import xml.etree.ElementTree as ET

ROWS=[
 ('V01','Inspect the wellhead.','Inspeccione la boca de pozo.'),
 ('V02','Run the casing.','Baje la carcasa.'),
 ('V03','Move the rig.','Mueva el equipo.'),
 ('V04','Install the liner.','Instale la tubería de revestimiento corta.'),
 ('V05','The drilling rig and associated equipment are ready.','La torre de perforación y el equipo asociado están listos.'),
 ('V06','Check the choke manifold.','Revise el manifold de surgencia.'),
 ('V07','Inspect the casing and the casing.','Inspeccione el casing y la carcasa.'),
 ('V08','Confirm the date of the meeting.','Confirme la fecha de la reunión.'),
]

GUIDE='''PRUEBA BREVE DE TERMCHECK — MATERIAL INVENTADO

Duración orientativa: 15–20 minutos. Usar https://termcheck.aval.site/demo/
No se requieren datos de clientes ni cuenta de TermCheck.

1. Antes de abrir resultados, leer los ocho pares de referencia.tsv y anotar
   qué términos revisaría y por qué. Puede consultar el glosario 1.4.
2. Pegar los textos de V01 y V02, verificar y explicar las observaciones.
3. Cargar muestra.xlf, revisar los segmentos y consultar una ficha del glosario.
   Registrar cualquier diferencia entre su revisión inicial y lo que muestra la app.
4. Descargar los reportes HTML/CSV y comprobar que pueda identificar el segmento
   y las palabras que le interesan. En V08 explicar qué permite concluir la ausencia
   de observaciones y qué queda fuera del alcance de la herramienta.

La persona que observa registra tareas completadas, bloqueos y comentarios en
registro-uso.csv. No ayudar antes de registrar el bloqueo. Usar un identificador
anónimo; no hace falta guardar nombre, correo, empleador ni contenido de clientes.
Una sesión realizada es una prueba exploratoria de uso, no una estimación de precisión.

SI TIENE TRADOS O MEMOQ

Importar muestra.xlf como documento bilingüe EN–ES, conservando los ocho pares.
Exportar una memoria TMX desde la herramienta, sin editar sus idiomas ni el XML.
Anotar herramienta, versión, fecha y pasos usados. Conservar el archivo exportado.
El archivo muestra.xlf fue creado localmente: NO es una exportación Trados/memoQ.
Solo el TMX generado por la herramienta podrá usarse para esa comprobación.
No se solicitan paquetes de proyecto ni documentos de clientes.
'''


def preparar(out):
    if (out/'manifiesto.json').exists():
        raise ValueError('El material ya está preparado; no sobrescribir registros de participantes')
    out.mkdir(parents=True,exist_ok=True)
    with (out/'referencia.tsv').open('w',newline='') as f:
        w=csv.writer(f,delimiter='\t');w.writerow(['seg_id','source_en','target_es']);w.writerows(ROWS)
    for name,index in [('origen.txt',1),('traduccion.txt',2)]:
        (out/name).write_text('\n'.join(r[index] for r in ROWS)+'\n')
    root=ET.Element('xliff',{'version':'1.2','xmlns':'urn:oasis:names:tc:xliff:document:1.2'})
    file=ET.SubElement(root,'file',{'source-language':'en-US','target-language':'es-AR','original':'prueba-inventada','datatype':'plaintext'})
    header=ET.SubElement(file,'header');ET.SubElement(header,'tool',{'tool-id':'termcheck-control-local','tool-name':'TermCheck control local'})
    body=ET.SubElement(file,'body')
    for sid,en,es in ROWS:
        unit=ET.SubElement(body,'trans-unit',{'id':sid});ET.SubElement(unit,'source').text=en;ET.SubElement(unit,'target').text=es
    (out/'muestra.xlf').write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True))
    (out/'LEEME.txt').write_text(GUIDE)
    with (out/'registro-uso.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['participante_anonimo','fecha','perfil','tarea','completada_sin_ayuda','minutos','bloqueo','comentario'])
        for i in range(1,5):w.writerow(['','','',i,'','','',''])
    with (out/'revision-previa.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['participante_anonimo','seg_id','termino_ingles','fragmento_es','decision','motivo'])
        for sid,_,_ in ROWS:w.writerow(['',sid,'','','',''])
    files=['LEEME.txt','referencia.tsv','origen.txt','traduccion.txt','muestra.xlf','registro-uso.csv','revision-previa.csv']
    manifest=dict(segmentos=8,procedencia='Inventado y preparado localmente; no exportado por CAT',
                  participantes_reales=0,exportaciones_cat_reales=0,
                  sha256={name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in files})
    (out/'manifiesto.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(out/'material-prueba.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in files+['manifiesto.json']:z.write(out/name,name)
    print(out/'material-prueba.zip')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    preparar(parser.parse_args().out)
