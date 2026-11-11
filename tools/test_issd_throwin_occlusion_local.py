"""Local regression test for contested throw reception foreground evidence."""
import argparse
from pathlib import Path
import audit_issd_throwin_body as audit


def run(root,rom):
    ordinary=audit.audit(root,rom,0x1500,True,True,True,True,False)
    verified=audit.audit(root,rom,0x1500,True,True,True,True,True)
    assert len(ordinary['frames'])==15 and len(ordinary['screen_mismatches'])==29
    assert len(verified['frames'])==44 and sum(row['occluded_pixels']>0 for row in verified['frames'])==29
    original=audit.compose
    def without_foreground(oam,vram,cgram,obsel,indices):
        return {} if len(indices)>20 else original(oam,vram,cgram,obsel,indices)
    try:
        audit.compose=without_foreground
        rejected=audit.audit(root,rom,0x1500,True,True,True,True,True)
        assert len(rejected['frames'])==15 and len(rejected['screen_mismatches'])==29
    finally:
        audit.compose=original
    print('OK: 29 occluded frames verified; missing foreground evidence rejects them')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',required=True,type=Path);parser.add_argument('--rom',required=True,type=Path)
    args=parser.parse_args();run(args.capture,args.rom)
