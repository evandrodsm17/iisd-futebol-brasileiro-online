import assert from 'node:assert/strict';
import {previewPixels} from './rom-player-preview.mjs';
const blank=btoa(String.fromCharCode(...new Uint8Array(48*56)));
const hair=btoa(String.fromCharCode(...new Uint8Array(64).fill(3)));
const data={schema:'issd-editor-preview-local/v1',teams:[{body:Array(8).fill(blank),palettes:[[1],[2],[3],[4]]}],
 goalkeeper:Array(8).fill(blank),heads:Object.fromEntries(Array.from({length:8},(_,i)=>[i,{x:1,y:2,attr:0,selector:1}])),
 hair_tiles:Array.from({length:13},()=>[hair]),flips:{'0':[false,true,false,false,false,false,false,false],'1':Array(8).fill(false)}};
assert.equal(previewPixels(data,0,0,'FW',0,0).pixels[2*48+1],0);
assert.equal(previewPixels(data,0,0,'FW',0,1).pixels[2*48+1],3);
assert.equal(previewPixels(data,0,1,'FW',1,1).pixels[2*48+46],3);
assert.deepEqual(previewPixels(data,0,0,'FW',1,0).palette,[2]);
assert.equal(previewPixels(data,0,0,'GK',0,1).pixels[2*48+1],0);
assert.throws(()=>previewPixels(data,0,8,'FW',0,0));
console.log('OK: composição de prévia, cabelos, paletas e espelhamento');
