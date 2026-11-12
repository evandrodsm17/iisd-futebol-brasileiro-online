// Audit attribute layouts against the external editor and the local cartridge, read-only.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import path from 'node:path';

const [root,romPath,output]=process.argv.slice(2);
if(!root||!romPath||!output)throw Error('Uso: node tools/audit_issd_editor_attributes.mjs <editor> <rom> <saida>');
const rom=await readFile(romPath);
if(createHash('md5').update(rom).digest('hex')!=='345ddedcd63412b9373dabb67c11fc05')throw Error('ROM USA sem cabeçalho esperada');
const {deluxeAttributes}=await import(pathToFileURL(path.resolve(root,'src/rom/deluxe.mjs')).href);
const {playerOffsets,playerPatches}=await import(pathToFileURL(path.resolve(root,'src/rom/players.mjs')).href);
const catalog=JSON.parse(await readFile(new URL('../dist/data/issd-rom-catalog.json',import.meta.url),'utf8'));
const fields=[['acceleration','acceleration',0,4],['speed','speed',0,0],['shotPower','shooting',1,4],['curl','technique',1,0],['balance','balance',2,4],['intelligence','intelligence',2,0],['dribbling','dribbling',3,4],['jump','jumping',3,0],['energy','stamina',4,0]];
const counts=Object.fromEntries(fields.map(([name])=>[name,Array(16).fill(0)]));
let checked=0;
for(const team of catalog.teams)for(const player of team.players){
 const offset=playerOffsets(rom,team.id,player.slot).attributes,bytes=rom.subarray(offset,offset+7);
 if(bytes.toString('hex')!==player.raw.attributes_hex)throw Error('Bytes divergentes');
 const decoded=deluxeAttributes(bytes);
 for(const [external,local,byte,shift] of fields){
  const nibble=(bytes[byte]>>shift)&15;counts[external][nibble]++;
  if(decoded[external]!==nibble+1)throw Error('Leitura externa divergente');
  const clamped=Math.max(2,Math.min(9,nibble));
  const band=Array.from({length:100},(_,i)=>i).filter(i=>2+Math.floor((i*7+49)/99)===clamped);
  if(player.attributes[local]!==Math.floor((band[0]+band.at(-1))/2))throw Error('Leitura do catálogo divergente');
 }
 checked++;
}
if(checked!==720)throw Error('Catálogo incompleto');
let patchesChecked=0;
for(const [name,,byte,shift] of fields)for(const value of [1,10]){
 const offset=playerOffsets(rom,2,9).attributes,before=rom.subarray(offset,offset+7);
 const patches=playerPatches(Uint8Array.from(rom),2,9,{[name]:value});
 const patch=patches.find(p=>p.offset===offset);
 if(patches.length!==1||!patch||patch.bytes.length!==7)throw Error('Patch inesperado');
 for(let i=0;i<7;i++){
  const mask=i===byte?15<<shift:0;
  if((patch.bytes[i]&~mask)!==(before[i]&~mask)||i===byte&&((patch.bytes[i]>>shift)&15)!==value-1)throw Error('Patch alterou campo incorreto');
 }
 patchesChecked++;
}
const report={schema:'issd-editor-attributes/v1',editor_repository:'https://github.com/EstebanFuentealba/web-snes-issd-studio',editor_commit:execFileSync('git',['-C',root,'rev-parse','HEAD'],{encoding:'utf8'}).trim(),rom_sha256:createHash('sha256').update(rom).digest('hex'),records_checked:checked,patches_checked:patchesChecked,fields:fields.map(([editor,catalog,byte,shift])=>({editor,catalog,byte,nibble:shift?'high':'low',counts:counts[editor]})),limits:['Editor labels and byte positions are not proof of gameplay effects.','Catalog projection clamps native nibbles to 2..9 and loses distinctions.','Patches were evaluated in memory only; the ROM was not modified.']};
await writeFile(output,JSON.stringify(report,null,2)+'\n');
console.log(`OK: ${checked} registros, ${fields.length} atributos e ${patchesChecked} patches em memória`);
