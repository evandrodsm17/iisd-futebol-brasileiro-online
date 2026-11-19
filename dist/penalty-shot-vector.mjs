import {nativePenaltyShotDirection} from './penalty-direction.mjs';
const OFFSETS=[0x28,0,0x50];
// The caller loads a manifest generated locally from the USA ROM. No keyboard
// mapping, team selection, collision or visual direction is implied.
export function nativePenaltyVectorFromTables(tables,variant,inputWord,flags){
 if(tables?.schema!=='issd-penalty-vectors/v1'||tables.rom_revision!=='USA'||!Array.isArray(tables.variants)||tables.variants.length!==3||!Number.isInteger(variant)||variant<0||variant>=3)throw new RangeError('Invalid penalty vector tables');
 const {code,base,index}=nativePenaltyShotDirection(inputWord,flags);
 const rows=tables.variants[variant];
 if(!Array.isArray(rows)||rows.length!==5)throw new RangeError('Invalid penalty vector variant');
 const row=rows[base];
 if(!row||['dx','dy','dz_clear','dz_set'].some(k=>!Number.isInteger(row[k])||row[k]<-32768||row[k]>32767))throw new RangeError('Invalid penalty vector');
 return {code,base,index,tableOffset:OFFSETS[variant]+2*base,dx:row.dx,dy:row.dy,dz:(flags&0x10)?row.dz_set:row.dz_clear};
}
