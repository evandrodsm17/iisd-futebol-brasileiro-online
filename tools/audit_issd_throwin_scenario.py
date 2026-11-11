#!/usr/bin/env python3
"""Verify the stock USA ROM's fifth scenario without modifying the ROM."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED='d2fe66c1ce66c65ce14e478c94be2e616f9e2cad374b5783a6a64d3c1a99cfa9'
OFFSET=0x5FD34
SUMMARY=0x3EE3B + 4*56

def audit(path):
    rom=path.read_bytes()
    digest=hashlib.sha256(rom).hexdigest()
    if len(rom)!=0x200000 or digest!=EXPECTED:
        raise ValueError('A auditoria exige a ROM USA sem cabeçalho com o hash conhecido.')
    record=rom[OFFSET:OFFSET+15]
    if len(record)!=15: raise ValueError('Registro incompleto')
    decode=lambda data: ''.join(' ' if b==0 else chr(65+b-0x68) if 0x68<=b<=0x81 else str(b-0x5e) if 0x5e<=b<=0x67 else {0x54:'.',0x57:'-',0x5a:"'",0x5c:':'}.get(b,'?') for b in data).rstrip()
    text=[decode(rom[SUMMARY+row*28:SUMMARY+(row+1)*28]) for row in range(2)]
    x=int.from_bytes(record[11:13],'little',signed=True)
    y=int.from_bytes(record[13:15],'little',signed=True)
    if record[10]!=16 or record[9]!=2 or (x,y)!=(1280,-1) or "TURKEY'S THROW IN" not in text[1]:
        raise ValueError('Registro ou legenda divergem do cenário esperado.')
    return {'rom_sha256':digest,'scenario_number':5,'record_offset':OFFSET,'record_hex':record.hex(' '),'summary_offset':SUMMARY,'summary':text,'start_byte':record[10],'stadium_id':record[9],'ball_native_x':x,'ball_native_y':y,'source':'Original USA ROM, scenario table and built-in description','scope':'Scenario initialization only; no throw animation or input timing established.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(audit(args.rom),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
