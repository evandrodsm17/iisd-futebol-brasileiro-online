"""Audit selected post-contact instruction sequences in the disassembly."""
from extract_issd_ball_attachment import ASM


CHECKS = (
    ('85F45F','85F48B',('JSL.l CODE_80D5BC','JSL.l CODE_80E3CE',
                         'LDA.w #$00FF','STA.b $3E','BIT.w #$1000',
                         'BIT.w #$0800','STZ.w $00AE','JMP.w CODE_85F871')),
    ('85F66B','85F694',('STZ.w $17CA','LDA.w #$00FF','STA.b $3E',
                         'LDX.w $00B4','CMP.b $9A','JMP.w CODE_85F767',
                         'STZ.w $00B4')),
    ('80E3CE','80E3F5',('LDY.b $9A','CMP.w $00EC,y','STA.w $00EE,y',
                         'CMP.w $00C0,y','STA.w $00C2,y',
                         'CMP.w $00D8,y','STA.w $00DA,y')),
    ('85F767','85F7A1',('LDA.w $002C,x','STY.w $00AC','STY.w $00D8',
                         'STY.w $00DE','JSL.l CODE_80D5DF',
                         'JSL.l CODE_80E63B','STZ.w $00B4')),
    ('85F871','85F89B',('STZ.w $00B4','STZ.w $19D8','STZ.w $12DC',
                         'STZ.w $12DA','STZ.w $00AE','STX.w $12F4',
                         'LDX.w $00D0','BNE.b CODE_85F86D',
                         'STA.w $0002','STA.w $00EC','BRA.b CODE_85F8D6')),
    ('85F89B','85F8B9',('STZ.w $00B4','STZ.w $19D8','STX.w $12F4',
                         'LDX.w $00D0','BNE.b CODE_85F86D',
                         'STA.w $19B8','STA.w $00EC','BRA.b CODE_85F8D6')),
)


def verify(source):
    for start,end,fragments in CHECKS:
        block=source.split('CODE_'+start+':',1)[1].split('CODE_'+end+':',1)[0]
        position=0
        for fragment in fragments:
            position=block.find(fragment,position)
            if position<0: raise ValueError(f'Missing or reordered {fragment} in {start}')
            position+=len(fragment)
    return len(CHECKS)


if __name__=='__main__':
    print(f'OK: {verify(ASM.read_text(encoding="utf-8"))} post-contact assembly sequences')
