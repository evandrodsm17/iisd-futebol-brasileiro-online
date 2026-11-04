import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createNativeSlideBody} from '../dist/native-slide-body.mjs';
import {composeOam} from '../dist/native-oam-compositor.mjs';
const read=p=>JSON.parse(fs.readFileSync(p));const root='./dist/';
const data=read(root+'assets/issd/slide-lab-local/preview.json'),left=read(root+'assets/issd/slide-lab-local/left.json'),dirs=read(root+'assets/issd/slide-lab-local/directions.json'),motion=read(root+'assets/issd/runtime-body-local.json'),preview=read(root+'assets/issd/editor-preview-local.json'),colors=read(root+'data/issd-team-detail-colors.json'),catalog=read(root+'data/issd-rom-catalog.json');
const canvas=(w,h)=>{let o={};o.getContext=()=>o;o.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});o.putImageData=im=>{o.pixels=im.data};return o};
const renderer=createNativeSlideBody(data,motion,canvas,preview,left,dirs,colors);
let checked=0;
for(const direction of [0,1,2,3,4,5,6,7]){
 const req={team:30,kit:'home',appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber:7,palette:catalog.teams[30].kit.home.sprite_palette};
 assert.ok(renderer.supports(req));let tick=0;
 for(const f of dirs.cycles[direction]){
  const vram=new Uint8Array(65536);for(const tile of f.tiles)vram.set(Buffer.from(tile.data,'base64'),tile.address);
  const expected=composeOam({vram,cgram:Buffer.from(f.cgram,'base64'),obsel:f.obsel,parts:f.parts,width:96,height:96}).rgba;
  assert.deepEqual(renderer.frame(tick,req).pixels,expected,`direction ${direction}, descriptor ${f.descriptor}`);tick+=f.ticks;checked++;
 }
}
for(const team of [2,18,22,35])for(const kit of ['home','away'])for(const direction of [3,4,5]){
 const req={team,kit,appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber:7,palette:catalog.teams[team].kit[kit].sprite_palette};
 assert.ok(renderer.supports(req),`transparent detail team ${team} ${kit} direction ${direction}`);
 for(let tick=0;tick<renderer.duration;tick++)assert.ok(renderer.frame(tick,req));
}
for(const kit of ['home','away'])for(const direction of [3,4,5]){
 const req={team:28,kit,appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber:7,palette:catalog.teams[28].kit[kit].sprite_palette};
 assert.ok(renderer.supports(req),'Cameroon index 10 palette');
 for(let tick=0;tick<renderer.duration;tick++)assert.ok(renderer.frame(tick,req));
}
let contexts=0;for(let team=0;team<36;team++)for(const kit of ['home','away'])for(let direction=0;direction<8;direction++)for(let shirtNumber=1;shirtNumber<=20;shirtNumber++){
 const req={team,kit,appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber,palette:catalog.teams[team].kit[kit].sprite_palette};
 assert.ok(renderer.supports(req),`team ${team}, kit ${kit}, direction ${direction}, shirt ${shirtNumber}`);contexts++;
}
console.log(`OK: ${contexts} combinations supported`);
console.log(`OK: ${checked} captured directional frames match byte-for-byte; transparent details available for four teams`);
