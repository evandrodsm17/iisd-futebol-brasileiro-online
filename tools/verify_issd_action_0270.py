"""Verify the 0270 dispatch row and action-to-ball call path."""
from pathlib import Path
from extract_issd_ball_attachment import ASM


def verify(source,rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    if rom[header+0xbfc8:header+0xbfd0]!=bytes.fromhex('9f979f979f972009'):
        raise ValueError('State 0270 ROM mismatch')
    checks=(('849755','849785',('LDA.w #$0270','JSR.w CODE_84854E',
             'LDA.w #DATA_82D01F','JMP.w CODE_84E60C')),
            ('84979F','8497B5',('JSR.w CODE_84E5D1','DEC.b $70',
             'JSL.l CODE_80DE3D','JSL.l CODE_85F3FE')),
            ('85F3FE','85F42A',('LDX.w #$001E','JSL.l CODE_80DE55',
             'LDX.w #$0017','JSL.l CODE_85F8B9','STX.w $00A4')))
    for start,end,fragments in checks:
        block=source.split('CODE_'+start+':',1)[1].split('CODE_'+end+':',1)[0];pos=0
        for fragment in fragments:
            pos=block.find(fragment,pos)
            if pos<0: raise ValueError(f'Missing or reordered {fragment} in {start}')
            pos+=len(fragment)
    return len(checks)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path);a=p.parse_args()
    print('OK: state 0270 ROM row and',verify(ASM.read_text(encoding='utf-8'),a.rom.read_bytes()),'assembly paths')
