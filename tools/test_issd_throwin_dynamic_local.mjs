import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createNativeThrowBody} from '../dist/native-throwin-body.mjs';
import {composeOam} from '../dist/native-oam-compositor.mjs';
const read=p=>JSON.parse(fs.readFileSync(p));const root='./dist/';
const data=read(root+'assets/issd/slide-lab-local/throwin-dynamic.json'),motion=read(root+'assets/issd/runtime-body-local.json'),preview=read(root+'assets/issd/editor-preview-local.json'),colors=read(root+'data/issd-team-detail-colors.json'),catalog=read(root+'data/issd-rom-catalog.json');
const canvas=(w,h)=>{let c={};c.getContext=()=>c;c.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});c.putImageData=im=>{c.pixels=im.data};return c;};
const renderer=createNativeThrowBody(data,motion,canvas,preview,colors);
for(const direction of [0,4]){
 const request={team:26,kit:'home',appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber:2,palette:catalog.teams[26].kit.home.sprite_palette};
 assert.ok(renderer.supports(request));
 for(let tick=0;tick<20;tick++){
  const f=data.cycles[direction][tick],vram=new Uint8Array(65536);for(const tile of f.tiles)vram.set(Buffer.from(tile.data,'base64'),tile.address);
  const expected=composeOam({vram,cgram:Buffer.from(f.cgram,'base64'),obsel:f.obsel,parts:f.parts,width:96,height:96}).rgba;
  assert.deepEqual(renderer.frame(tick,request).pixels,expected,`captured direction ${direction} tick ${tick}`);
 }
}
let supported=0;
for(let team=0;team<36;team++)for(const kit of ['home','away'])for(const direction of [0,4])for(let shirtNumber=1;shirtNumber<=20;shirtNumber++){
 const request={team,kit,appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber,palette:catalog.teams[team].kit[kit].sprite_palette};
 if(renderer.supports(request)){assert.ok(renderer.frame(0,request));supported++;}
}
console.log(`OK: 40 captured frames match exactly; ${supported} team/kit/shirt contexts supported`);

const sample={team:26,kit:'home',appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:0,shirtNumber:2,palette:catalog.teams[26].kit.home.sprite_palette};
assert.equal(renderer.supports({...sample,screenDirection:2}),false,'uncaptured directions are rejected');
assert.equal(renderer.supports({...sample,position:'GK'}),false,'goalkeeper visual is not assumed');
const alternate={...sample,kit:'away',palette:catalog.teams[26].kit.away.sprite_palette};
assert.ok(renderer.supports(alternate));assert.notDeepEqual(renderer.frame(0,sample).pixels,renderer.frame(0,alternate).pixels,'uniform palette changes the composed pixels');
console.log('OK: unsupported contexts rejected and alternate kit changes pixels');
