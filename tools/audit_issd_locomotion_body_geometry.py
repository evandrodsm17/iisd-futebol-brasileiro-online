"""Compare extracted ROM body geometry to WRAM and observed motion traces."""
import argparse
import hashlib
import json
from pathlib import Path
from export_issd_team_motion import SCRIPTS,descriptors,trace
from extract_issd_catalog import EXPECTED_MD5


def audit(rom,geometry,trace_path,capture,bridge):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];rows=trace(trace_path);actors={}
    for row in rows:
        for actor in row.get('actors',[]):
            if actor['address']==0x0d00:actors.setdefault((actor['direction'],actor['descriptor']),actor)
    signed=lambda n:n if n<32768 else n-65536
    checked=[]
    for motion,script in SCRIPTS.items():
        for direction in range(8):
            for desc in descriptors(rom,script,direction):
                actor=actors[(direction,desc)];parts=geometry['poses'][str(desc)]['parts'];observed=actor['parts']
                if len(parts)!=len(observed):raise ValueError('Piece count mismatch')
                for p,o in zip(parts,observed):
                    dx=signed(p['dx']);dy=signed(p['dy']);large=p['large']
                    if actor['object_flags']&64:dx=-dx
                    expected=(dx-(8 if large else 4),dy-(8 if large else 4),p['tile'],16 if large else 8)
                    if expected!=(o['x'],o['y'],o.get('geometry_tile',o['tile']),o['size']):raise ValueError(f'Geometry mismatch {motion}/{direction}/{desc:04X}')
                checked.append({'motion':motion,'direction':direction,'descriptor':desc})
    raw=(capture/'hair-runtime.jsonl').read_bytes();entries={r['step']:r for r in map(json.loads,raw.splitlines()) if r.get('type')=='body_geometry'}
    for f in bridge['frames']:
        if geometry['poses'][str(f['descriptor'])]['parts']!=entries[f['step']]['parts']:raise ValueError(f"WRAM geometry mismatch {f['step']}")
    return {'schema':'issd-locomotion-body-geometry-audit/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'trace_sha256':hashlib.sha256(trace_path.read_bytes()).hexdigest(),'capture_sha256':hashlib.sha256(raw).hexdigest(),
            'trace_cycles':checked,'wram_samples':len(bridge['frames']),
            'limitations':['Trace checks relative positions, sizes and tile indices; not final palette or full screenshots.',
                           'Same-frame raw WRAM comparison covers one actor and one direction only.',
                           'Running/walking timing and selection remain governed by existing extracted script tables.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('geometry',type=Path);p.add_argument('trace',type=Path);p.add_argument('capture',type=Path);p.add_argument('bridge',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.rom.read_bytes(),json.loads(a.geometry.read_text(encoding='utf8')),a.trace,a.capture,json.loads(a.bridge.read_text(encoding='utf8')))
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(f"Verified {len(r['trace_cycles'])} direction frames and {r['wram_samples']} WRAM samples")
