import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createNativeReceiptBody} from '../dist/native-throwin-body.mjs';
import {composeOam} from '../dist/native-oam-compositor.mjs';
const read=p=>JSON.parse(fs.readFileSync(p)),root='./dist/';
const data=read(root+'assets/issd/slide-lab-local/receipt-dynamic.json'),motion=read(root+'assets/issd/runtime-body-local.json'),preview=read(root+'assets/issd/editor-preview-local.json'),colors=read(root+'data/issd-team-detail-colors.json'),catalog=read(root+'data/issd-rom-catalog.json');
const make=(w,h)=>{const c={};c.getContext=()=>c;c.createImageData=()=>({data:new Uint8ClampedArray(w*h*4)});c.putImageData=im=>{c.pixels=im.data};return c;};
const renderer=createNativeReceiptBody(data,motion,make,preview,colors),request={team:26,kit:'home',appearance:{skin_tone:0,hair_style:0},position:'DF',screenDirection:3,shirtNumber:5,palette:catalog.teams[26].kit.home.sprite_palette};
assert.ok(renderer.supports(request));
for(let tick=0;tick<44;tick++){
 const f=data.cycles[3][tick],vram=new Uint8Array(65536);for(const tile of f.tiles)vram.set(Buffer.from(tile.data,'base64'),tile.address);
 const expected=composeOam({vram,cgram:Buffer.from(f.cgram,'base64'),obsel:f.obsel,parts:f.parts,width:96,height:96}).rgba;
 assert.deepEqual(renderer.frame(tick,request).pixels,expected,`captured receipt tick ${tick}`);
}
let supported=0;for(let team=0;team<36;team++)for(const kit of ['home','away'])for(let shirtNumber=1;shirtNumber<=20;shirtNumber++){
 const req={...request,team,kit,shirtNumber,palette:catalog.teams[team].kit[kit].sprite_palette};if(renderer.supports(req)){assert.ok(renderer.frame(0,req));supported++;}
}
assert.equal(renderer.supports({...request,screenDirection:2}),false);
console.log(`OK: 44 captured receipt frames match exactly; ${supported} team/kit/shirt contexts supported`);
