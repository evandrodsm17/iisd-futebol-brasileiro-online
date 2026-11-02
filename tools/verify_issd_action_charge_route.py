"""Verify the $0430 routing and key action-charge calls against local evidence."""
from pathlib import Path
from extract_issd_ball_attachment import ASM, ROOT


def verify(source, rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    expected=bytes.fromhex('65ab59abb9c33004')
    offset=0xbd58+0x430
    if rom[header+offset:header+offset+8]!=expected:
        raise ValueError('State 0430 ROM mismatch')
    checks=[('84AB99','84ABB5',('BIT.w $0026,x','BNE.b CODE_84AC0C')),
            ('84AD5E','84AD8A',('BIT.w $0026,x','BNE.b CODE_84ADB9')),
            ('84AC0C','84AC54',('JSL.l CODE_80DA3C','LDY.w #$0020',
                               'JSR.w CODE_848548','LDA.w #DATA_82CFAF',
                               'LDY.w #DATA_82CF9F','JMP.w CODE_84E600')),
            ('84ADB9','84ADD1',('JSL.l CODE_80DA3C','LDY.w #$0024',
                               'JSL.l CODE_80E1DF','JMP.w CODE_84AC1E'))]
    for start,end,fragments in checks:
        block=source.split('CODE_'+start+':',1)[1].split('CODE_'+end+':',1)[0]
        pos=0
        for fragment in fragments:
            pos=block.find(fragment,pos)
            if pos<0: raise ValueError(f'Missing or reordered {fragment} in {start}')
            pos+=len(fragment)
    return len(checks)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('rom',type=Path)
    args=parser.parse_args()
    print(f'OK: state 0430 ROM bytes and {verify(ASM.read_text(encoding="utf-8"),args.rom.read_bytes())} assembly paths')
