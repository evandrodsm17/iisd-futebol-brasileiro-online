"""Summarize isolated camera candidate and immediate injection observations."""
import argparse,collections,hashlib,json
from pathlib import Path

def audit(path):
 raw=path.read_bytes();rows=[json.loads(line) for line in raw.splitlines()]
 frames=[r for r in rows if r['type']=='frame'];inject=[r for r in rows if r['type']=='inject'];writes=[r for r in rows if r['type']=='write']
 if len(frames)!=180 or len(inject)!=3 or any(sum(r['phase']==p for r in frames)!=90 for p in (1,2)):raise ValueError('Incomplete probe')
 if any(((r['r98']+r['ball08']-(r['r9a']+r['ball0c']))&65535)!=r['targetX'] or ((r['r9a']+r['ball0c'])&65535)!=r['targetY'] for r in inject):raise ValueError('Injected coordinates do not match target')
 after=[r for r in frames if r['phase']==2 and r['step']<=3]
 if any(r['ball2a']==1676 for r in after):raise ValueError('Unexpected post-frame position: reevaluate probe')
 relations=collections.Counter(((r['r13a0']-r['r98'])&65535,(r['r13b0']-r['r9a'])&65535) for r in frames)
 sites=collections.Counter((r['phase'],r['watch'],r['pc']) for r in writes)
 return {'schema':'issd-camera-target-observation/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'frames':len(frames),'immediate_injections':inject,'first_three_post_frames':after,'candidate_differences':[{'r13a0_minus_r98':a,'r13b0_minus_r9a':b,'count':n} for (a,b),n in sorted(relations.items())],'write_sites':[{'phase':p,'watch':f'{a:06X}','pc_returned':f'{pc:06X}','count':n} for (p,a,pc),n in sorted(sites.items())],'limitations':['Synthetic RAM injection and one saved state; not ordinary gameplay.','Memory-write callbacks are limited to registered addresses and BizHawk timing; an unobserved writer is not excluded.','The relationships are observational, not proof that these words are camera targets.','Registers and position were sampled on different callbacks and must not be treated as simultaneous CPU states.']}

def main():
 p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('output',type=Path);a=p.parse_args();result=audit(a.trace);a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK:',result['frames'],'frames;',len(result['immediate_injections']),'verified injections; candidate differences',result['candidate_differences'])
if __name__=='__main__':main()
