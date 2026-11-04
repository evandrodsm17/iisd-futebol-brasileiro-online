import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createNativeFallBody} from '../dist/native-fall-body.mjs';
import {createFallCapture,createFallRecoveryCapture} from '../dist/editor/fall-lab.mjs';
const read=p=>JSON.parse(readFileSync(p,'utf8')),root='dist/';
const data=read(root+'assets/issd/slide-lab-local/fall-dynamic.json'),preview=read(root+'assets/issd/editor-preview-local.json'),detail=read(root+'data/issd-team-detail-colors.json'),catalog=read(root+'data/issd-rom-catalog.json');
const make=(w,h)=>{const c={};c.getContext=()=>c;c.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});c.putImageData=im=>{c.pixels=im.data};return c;};
const renderer=createNativeFallBody(data,preview,detail,make);
const reference={team:2,kit:'home',skin:0,shirtNumber:10,screenDirection:5,palette:catalog.teams[2].kit.home.sprite_palette};
for(const [direction,fall,recovery] of [[5,'fall.json','fall-recovery.json'],[2,'fall-right.json','fall-recovery-right.json'],[7,'fall-upleft.json','fall-recovery-upleft.json']]){
 const original=createFallCapture(read(root+'assets/issd/slide-lab-local/'+fall),make),after=createFallRecoveryCapture(read(root+'assets/issd/slide-lab-local/'+recovery),make),req={...reference,screenDirection:direction};
 assert.ok(renderer.supports(req));for(let tick=0;tick<35;tick++)assert.deepEqual(renderer.frame(tick,req).pixels,original.frame(tick).pixels,`direction ${direction} tick ${tick}`);
 for(let tick=0;tick<5;tick++)assert.deepEqual(renderer.frame(35+tick,req).pixels,after.frame(tick).pixels,`direction ${direction} continuation ${tick}`);
}
let count=0;for(let team=0;team<36;team++)for(const kit of ['home','away'])for(let skin=0;skin<2;skin++)for(let shirtNumber=1;shirtNumber<=20;shirtNumber++)for(const screenDirection of [2,5,7]){
 const req={team,kit,skin,shirtNumber,screenDirection,palette:catalog.teams[team].kit[kit].sprite_palette};assert.ok(renderer.supports(req),JSON.stringify({team,kit,skin,shirtNumber,screenDirection}));count++;
}
assert.equal(renderer.supports({...reference,screenDirection:1}),false);
console.log(`OK: 120 reference frames exact; ${count} team, kit, skin, shirt and direction contexts supported`);
