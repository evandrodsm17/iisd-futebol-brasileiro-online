// Optional local comparison against an independently checked-out reference editor.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import {previewPixels} from '../dist/editor/rom-player-preview.mjs';
const [romPath,dataPath,referencePath]=process.argv.slice(2);
if(!romPath||!dataPath||!referencePath)throw Error('Usage: node verify_issd_editor_preview.mjs <ROM> <preview.json> <reference checkout>');
const {playerPreviewFrames}=await import(pathToFileURL(path.resolve(referencePath,'src/rom/player-preview.mjs')));
const rom=new Uint8Array(await readFile(romPath));const header=rom.length%0x8000===512?512:0;
const data=JSON.parse(await readFile(dataPath,'utf8'));let frames=0;
for(const team of [0,2,8,27,30,35])for(const goalie of [false,true])for(const skin of [0,1])for(let hair=0;hair<=13;hair++){
 const reference=playerPreviewFrames(rom.subarray(header),team,{position:goalie?1:2,skin,hair});
 for(let direction=0;direction<8;direction++){
  const ours=previewPixels(data,team,direction,goalie?'GK':'FW',skin,hair);
  assert.deepEqual(Array.from(ours.pixels),reference[direction].matrix.flat(),`team=${team} goalie=${goalie} skin=${skin} hair=${hair} direction=${direction}`);
  for(const index of new Set(ours.pixels)){
   if(!index)continue;
   const value=ours.palette[index],hex='#'+[0,5,10].map(shift=>Math.round(((value>>shift)&31)*255/31).toString(16).padStart(2,'0')).join('');
   assert.equal(hex,reference[direction].colors[index],`palette team=${team} index=${index}`);
  }
  frames++;
 }
}
console.log(`OK: ${frames} prévias e paletas coincidem com o editor de referência`);
