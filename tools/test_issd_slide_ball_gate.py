import json
import random
import subprocess
import unittest
from pathlib import Path
from issd_contact_volume import contact_volume
from extract_issd_slide_ball_gate import extract
from audit_issd_slide_ball_probe import audit

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'


class SlideBallGateTest(unittest.TestCase):
    def test_table_matches_local_rom(self):
        if not ROM.exists():self.skipTest('Requires local ROM')
        data=extract(ROM.read_bytes())
        self.assertEqual(list(data['geometry'].values()),[12,24,8,16,8,16])
        with self.assertRaises(ValueError):extract(bytes(0x8000))

    def test_javascript_matches_existing_word_model(self):
        rng=random.Random(216);cases=[];expected=[]
        for _ in range(500):
            actor={k:rng.randrange(65536) for k in ('x','y','z')}
            actor.update({k:rng.choice([0,1,0xffff,rng.randrange(65536)]) for k in ('offsetX','offsetY','offsetZ')})
            ball={k:(actor[k]+rng.randrange(-40,41))&65535 for k in ('x','y','z')}
            case={'timer':rng.randrange(1,9),'actorIsA6':False,'actorFlags':0,'phase':0,'globalFlags':0,'priorContactCarry':True,'actor':actor,'ball':ball}
            result=contact_volume([12,24,8,16,8,16],tuple(actor[k] for k in ('x','y','z')),
                                  tuple(actor[k] for k in ('offsetX','offsetY','offsetZ')),
                                  tuple(ball[k] for k in ('x','y','z')),phase=0,flag_11fa=0,actor_flags=0)
            cases.append(case);expected.append('outside' if result['carry'] else 'contact')
        js="import {nativeSlideBallGate} from './dist/native-slide-ball-gate.mjs';let s='';for await(const c of process.stdin)s+=c;process.stdout.write(JSON.stringify(JSON.parse(s).map(x=>nativeSlideBallGate(x).route)));"
        result=subprocess.run(['node','--input-type=module','-e',js],cwd=ROOT,input=json.dumps(cases),text=True,capture_output=True,check=True)
        self.assertEqual(json.loads(result.stdout),expected)

    def test_isolated_probe_when_available(self):
        root=ROOT/'analysis/slide-gate-probe'
        paths=[root/'A/slide-ball-gate.jsonl',root/'synthetic/slide-ball-gate.jsonl']
        if not all(p.exists() for p in paths):self.skipTest('Requires isolated replay captures')
        result=audit(paths)
        self.assertEqual(len(result['samples']),9)
        self.assertEqual(sum(s['synthetic'] and s['carry']==0 for s in result['samples']),1)
        self.assertTrue(all(s['script']=='$DF7F' for s in result['samples']))


if __name__=='__main__':unittest.main()
