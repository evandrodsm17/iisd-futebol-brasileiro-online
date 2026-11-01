"""Verify the assembly evidence rejecting $1B90 as a carrier pointer."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm'


def verify(text):
    checks = [
        ('CODE_839BBE', 'CODE_839BDF', 'LDA.w #$5588\nSTA.w $1B90'),
        ('CODE_83B6CF', 'CODE_83B6EE', 'LDA.w DATA_81ABAD,y\nSTA.w $1B90'),
        ('DATA_81ABAD', 'DATA_81ABB1', 'dw $56F8,$5704'),
        ('CODE_80D953', 'CODE_80D978', 'LDY.w #$1B90'),
        ('CODE_80D953', 'CODE_80D978', 'SBC.w $002A,y'),
        ('CODE_80D953', 'CODE_80D978', 'SBC.w $002C,y'),
        ('CODE_80E1EA', 'CODE_80E1F4', 'LDA.w $1B98\nSTA.b $40\nLDA.w $1B9C\nSTA.b $42'),
    ]
    for start, end, expected in checks:
        block = text.split(start + ':', 1)[1].split(end + ':', 1)[0]
        normalized = '\n'.join(line.strip() for line in block.splitlines())
        if expected not in normalized:
            raise ValueError(f'Assembly evidence changed: {start}: {expected}')
    return len(checks)


if __name__ == '__main__':
    print(f'OK: {verify(SOURCE.read_text(encoding="utf-8"))} object $1B90 evidence checks')
