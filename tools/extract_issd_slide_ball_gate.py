"""Extract the ROM table and static guards of the observed slide/ball route."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5


def extract(rom):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected USA ROM')
    rom=rom[header:];offset=0xcf6b
    values=[int.from_bytes(rom[offset+i*2:offset+i*2+2],'little') for i in range(12)]
    if values!=[12,24,8,16,8,16,24,48,16,32,8,16]:raise ValueError('Unexpected DATA_81CF6B table')
    return {'schema':'issd-slide-ball-gate/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'source':{'setup':'$84:A056','handler':'$84:A08D','hitbox_entry':'$85:F11A','shared_gate':'$85:FAEA','table':'$81:CF6B','file_offset':'0x00CF6B'},
            'setup':{'timer_70':12,'timer_72':8,'script':'$82:DB25','handler_record':'$02D0'},
            'geometry':{'x_center':values[0],'x_width':values[1],'y_center':values[2],'y_width':values[3],'z_center':values[4],'z_width':values[5]},
            'following_words':values[6:],
            'guards':['At CODE_84:A08D, when the actor differs from global $00A6, decremented $70 between 0 and 7 and actor+$6E bits $0420 clear allow CODE_85:F11A; the preceding CODE_84:E8B0 carry-clear branch additionally calls CODE_85:F125.',
                      'CODE_85:FAEA returns carry set if actor+$6E bit $0400 is set, global $00C0 is nonzero, or global $11FA is negative.',
                      'CODE_85:FAF1 tests actor+$08/$0C/$10 plus $38/$3A/$3C against ball $0408/$040C/$0410 using the six table words.',
                      'A successful geometric gate sets actor+$6E bit $0400; subsequent response uses additional routines and actor references.'],
            'limitations':['Static control flow and table values only; no native replay comparison in this artifact.',
                           'Neither entry button, complete collision policy, foul decision nor browser units are established.',
                           'The order and behavior of the earlier CODE_84:E8B0 gate remain separate from this model.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=extract(a.rom.read_bytes());a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('Extracted slide/ball gate')
