// Compare the external editor's stat decoding/patches with captured ROM operands.
// All patches are evaluated in memory; the source ROM is never written.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {candidateSlideReactionRecord,nativeSlideReactionTable} from '../dist/native-slide-reaction-choice.mjs';

const [editorRoot,romPath,output]=process.argv.slice(2);
if(!editorRoot||!romPath||!output)throw new Error('Uso: node tools/audit_issd_editor_reaction_stats.mjs <editor> <rom> <saida>');
const sha=data=>createHash('sha256').update(data).digest('hex');
const image=await readFile(romPath);
if(createHash('md5').update(image).digest('hex')!=='345ddedcd63412b9373dabb67c11fc05')throw new Error('ROM USA sem cabeçalho esperada');
const editor=await import(pathToFileURL(path.resolve(editorRoot,'src/rom/deluxe.mjs')).href);
const players=await import(pathToFileURL(path.resolve(editorRoot,'src/rom/players.mjs')).href);
const catalog=JSON.parse(await readFile(new URL('../dist/data/issd-rom-catalog.json',import.meta.url),'utf8'));
const reaction=JSON.parse(await readFile(new URL('../docs/issd-slide-reaction-choice-observation.json',import.meta.url),'utf8'));
let checked=0;
for(const team of catalog.teams)for(const player of team.players){
 const offset=players.playerOffsets(image,team.id,player.slot).attributes;
 const bytes=image.subarray(offset,offset+7),raw=player.raw.attributes_hex;
 if(Buffer.from(bytes).toString('hex')!==raw)throw new Error('Registro do editor difere do catálogo');
 const stats=editor.deluxeAttributes(bytes);
 if(stats.balance!==(bytes[2]>>4)+1||stats.dribbling!==(bytes[3]>>4)+1)throw new Error('Decodificação inesperada');
 checked++;
}
if(checked!==720)throw new Error('Catálogo incompleto');
const team=2,slot=9,offset=players.playerOffsets(image,team,slot).attributes;
const before=Buffer.from(image.subarray(offset,offset+7));
const patches=players.playerPatches(Uint8Array.from(image),team,slot,{balance:1,dribbling:1});
const patch=patches.find(p=>p.offset===offset);
if(!patch||patches.length!==1||patch.bytes.length!==7)throw new Error('Patch inesperado do editor');
const after=Buffer.from(patch.bytes);
if(after[2]!==0x07||after[3]!==0x05||[0,1,4,5,6].some(i=>before[i]!==after[i]))throw new Error('Patch alterou bytes inesperados');
const lookup=bytes=>nativeSlideReactionTable({attacker30:reaction.entry.attacker30,...candidateSlideReactionRecord(bytes.toString('hex'),reaction.record.record_sixth_word),global78:reaction.entry.global78});
const original=lookup(before),counterfactual=lookup(after);
if(original.index!==43||original.tableByte!==1||counterfactual.index!==15||counterfactual.tableByte!==0)throw new Error('Índice de reação inesperado');
const commit=execFileSync('git',['-C',editorRoot,'rev-parse','HEAD'],{encoding:'utf8'}).trim();
const report={schema:'issd-editor-reaction-stats/v1',editor_repository:'https://github.com/EstebanFuentealba/web-snes-issd-studio',editor_commit:commit,rom_sha256:sha(image),records_checked:checked,example:{team:'England',slot,player:'T.Keegan',rom_offset:`0x${offset.toString(16).toUpperCase()}`,before_hex:before.toString('hex'),patched_hex:after.toString('hex'),editor_before:{balance:8,dribbling:8},editor_after:{balance:1,dribbling:1},original,counterfactual},limits:['Counterfactual uses captured runtime words and global value; it is not an emulator run.','The candidate record identity and runtime mapping are not fully proven.','The editor labels are evidence of its interpretation, not independent proof of the original game UI semantics.','Other game state, conditions, and direct-page behavior can affect the result.','The ROM was read only and is not distributed.']};
await writeFile(output,JSON.stringify(report,null,2)+'\n');
console.log(`OK: ${checked} registros; patch hipotético altera índice ${original.index} → ${counterfactual.index}`);
