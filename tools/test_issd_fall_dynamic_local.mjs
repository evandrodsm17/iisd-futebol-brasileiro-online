import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createNativeFallBody} from '../dist/native-fall-body.mjs';
import {createFallCapture,createFallRecoveryCapture} from '../dist/editor/fall-lab.mjs';
const read=p=>JSON.parse(readFileSync(p,'utf8')),root='dist/';
const data=read(root+'assets/issd/slide-lab-local/fall-dynamic.json'),preview=read(root+'assets/issd/editor-preview-local.json'),detail=read(root+'data/issd-team-detail-colors.json'),catalog=read(root+'data/issd-rom-catalog.json');
const make=(w,h)=>{const c={};c.getContext=()=>c;c.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});c.putImageData=im=>{c.pixels=im.data};return c;};
const renderer=createNativeFallBody(data,preview,detail,make),original=createFallCapture(read(root+'assets/issd/slide-lab-local/fall.json'),make);
const recovery=createFallRecoveryCapture(read(root+'assets/issd/slide-lab-local/fall-recovery.json'),make);
const reference={team:2,kit:'home',skin:0,shirtNumber:10,screenDirection:5,palette:catalog.teams[2].kit.home.sprite_palette};
assert.ok(renderer.supports(reference));for(let tick=0;tick<35;tick++)assert.deepEqual(renderer.frame(tick,reference).pixels,original.frame(tick).pixels,`tick ${tick}`);
for(let tick=0;tick<5;tick++)assert.deepEqual(renderer.frame(35+tick,reference).pixels,recovery.frame(tick).pixels,`recovery tick ${tick}`);
let count=0;for(let team=0;team<36;team++)for(const kit of ['home','away'])for(let skin=0;skin<2;skin++)for(let shirtNumber=1;shirtNumber<=20;shirtNumber++){
 const req={team,kit,skin,shirtNumber,screenDirection:5,palette:catalog.teams[team].kit[kit].sprite_palette};assert.ok(renderer.supports(req),JSON.stringify({team,kit,skin,shirtNumber}));count++;
}
assert.equal(renderer.supports({...reference,screenDirection:1}),false);
console.log(`OK: 40 reference frames exact; ${count} team, kit, skin and shirt contexts supported`);
