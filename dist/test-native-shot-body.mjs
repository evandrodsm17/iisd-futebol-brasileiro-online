import assert from 'node:assert/strict';
import {createNativeShotBody} from './native-shot-body.mjs';

// One opaque 4bpp pixel with palette index 7 in each frame.
const tiles=new Uint8Array(0x600);tiles[0]=0x80;tiles[1]=0x80;tiles[16]=0x80;
const f={origin_x:48,origin_y:68,props:2,parts:[{dx:4,dy:4,tile:0,attr:0,large:false}],tiles:btoa(String.fromCharCode(...tiles))};
const data={schema:'issd-shot-body-local/v1',screen_direction:2,width:96,height:96,frames:Array(6).fill(f)};
const locomotion={schema:'issd-runtime-body-local/v1',cycles:{walking:[{height:48}]}};
const preview={schema:'issd-editor-preview-local/v1',teams:Array.from({length:36},()=>({palettes:[Array(16).fill(0),Array(16).fill(0)]}))};
const make=(w,h)=>({getContext:()=>({createImageData:()=>({data:new Uint8ClampedArray(w*h*4)}),putImageData(image){this.image=image;}})});
const renderer=createNativeShotBody(data,make,locomotion,preview);
const req={team:0,kit:'home',position:'MF',appearance:{skin_tone:0,hair_style:0},screenDirection:2,palette:Array(16).fill('#ff0000')};
for(let team=0;team<36;team++)for(const kit of ['home','away'])assert.equal(renderer.supports({...req,team,kit}),true);
assert.equal(renderer.supports({...req,screenDirection:1}),false);
assert.equal(renderer.supports({...req,position:'GK'}),false);
assert.ok(renderer.frame(0,req));
assert.equal(renderer.frame(renderer.duration,req),null);
assert.equal(renderer.referenceHeight(2),48);
console.log('OK: chute dinâmico limitado à direção capturada e uniformes válidos');
