import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createNativeThrowBody} from '../dist/native-throwin-body.mjs';
import {composeOam} from '../dist/native-oam-compositor.mjs';
const read=p=>JSON.parse(fs.readFileSync(p));const root='./dist/';
const data=read(root+'assets/issd/slide-lab-local/throwin-dynamic.json'),motion=read(root+'assets/issd/runtime-body-local.json'),preview=read(root+'assets/issd/editor-preview-local.json'),colors=read(root+'data/issd-team-detail-colors.json'),catalog=read(root+'data/issd-rom-catalog.json');
const canvas=(w,h)=>{let c={};c.getContext=()=>c;c.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});c.putImageData=im=>{c.pixels=im.data};return c;};
const renderer=createNativeThrowBody(data,motion,canvas,preview,colors);
for(const direction of [0,1,3,4,5,7]){
 const request={team:26,kit:'home',appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber:2,palette:catalog.teams[26].kit.home.sprite_palette};
 assert.ok(renderer.supports(request));
 for(let tick=0;tick<20;tick++){
  const f=data.cycles[direction][tick],vram=new Uint8Array(65536);for(const tile of f.tiles)vram.set(Buffer.from(tile.data,'base64'),tile.address);
  const expected=composeOam({vram,cgram:Buffer.from(f.cgram,'base64'),obsel:f.obsel,parts:f.parts,width:96,height:96}).rgba;
  assert.deepEqual(renderer.frame(tick,request).pixels,expected,`captured direction ${direction} tick ${tick}`);
 }
}
let supported=0;
for(let team=0;team<36;team++)for(const kit of ['home','away'])for(const direction of [0,1,3,4,5,7])for(let shirtNumber=1;shirtNumber<=20;shirtNumber++){
 const request={team,kit,appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber,palette:catalog.teams[team].kit[kit].sprite_palette};
 if(renderer.supports(request)){assert.ok(renderer.frame(0,request));supported++;}
}
console.log(`OK: 120 captured frames match exactly; ${supported} team/kit/shirt contexts supported`);

const sample={team:26,kit:'home',appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:0,shirtNumber:2,palette:catalog.teams[26].kit.home.sprite_palette};
assert.equal(renderer.supports({...sample,screenDirection:2}),false,'uncaptured directions are rejected');
assert.equal(renderer.supports({...sample,position:'GK'}),false,'goalkeeper visual is not assumed');
const alternate={...sample,kit:'away',palette:catalog.teams[26].kit.away.sprite_palette};
assert.ok(renderer.supports(alternate));assert.notDeepEqual(renderer.frame(0,sample).pixels,renderer.frame(0,alternate).pixels,'uniform palette changes the composed pixels');
console.log('OK: unsupported contexts rejected and alternate kit changes pixels');

const anchors={0:[-3,-38,true],1:[-11,-36,true],3:[-3,-44,false],4:[-3,-44,false],5:[-3,-44,false],7:[5,-36,true]};
for(const direction of [0,1,3,4,5,7]){
 const request={team:26,kit:'home',appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:direction,shirtNumber:2,palette:catalog.teams[26].kit.home.sprite_palette};
 for(let tick=0;tick<4;tick++){
  const expected=data.cycles[direction][tick].held_ball,held=renderer.heldBall(tick,request);
  assert.ok(held);assert.deepEqual(held.canvas.pixels,Uint8ClampedArray.from(Buffer.from(expected.rgba,'base64')));
  assert.deepEqual([held.x,held.y,held.width,held.height,held.front],[expected.x,expected.y,expected.width,expected.height,expected.front]);
 }
 const initial=renderer.heldBall(0,request);assert.deepEqual([initial.x,initial.y,initial.front],anchors[direction]);
 assert.equal(renderer.heldBall(4,request),null);
}
console.log('OK: 24 held-ball frames match captured pixels, positions and draw order');
