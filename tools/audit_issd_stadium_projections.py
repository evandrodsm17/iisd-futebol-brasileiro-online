"""Measure supported stadium previews and record the unresolved layouts."""
import argparse, hashlib, json
from pathlib import Path
from audit_issd_stadium_projection import measure

def audit(root):
    results=[]
    for layout in range(8):
        path=root/f'layout-{layout}.png'
        try: results.append({'layout':layout,'status':'measured','observation':measure(path)})
        except ValueError as error: results.append({'layout':layout,'status':'unresolved','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reason':str(error)})
    return {'schema':'issd-stadium-projections-observation/v1','layouts':results}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=audit(args.directory);args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK:',sum(item['status']=='measured' for item in result['layouts']),'medidos;',sum(item['status']=='unresolved' for item in result['layouts']),'pendentes')
