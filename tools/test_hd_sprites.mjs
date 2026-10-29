import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HD_DIRECTIONS,validateHDManifest,resolveHDFrame,importHDManifest} from '../dist/hd-sprites.mjs';
const input=JSON.parse(readFileSync(new URL('../dist/data/hd-sprite-pack.example.json',import.meta.url),'utf8'));
const manifest=validateHDManifest(input);
assert.equal(HD_DIRECTIONS.length,8);
assert.equal(manifest.animations.walking.frames,10);
const pack={manifest,images:{'idle.png':{},'walking.png':{},'running.png':{}}};
for(let d=0;d<8;d++){const frame=resolveHDFrame(pack,'running',d,4);assert.equal(frame.sx,64);assert.equal(frame.sy,d*96);}
assert.equal(resolveHDFrame(pack,'running',0,26).frame,0);
assert.equal(resolveHDFrame(pack,'walking',0,29).frame,9);
assert.equal(resolveHDFrame(pack,'walking',0,30).frame,0);
assert.equal(resolveHDFrame(pack,'running',8,0),null);
assert.equal(resolveHDFrame(pack,'kick',0,0),null);
function rejects(change){const json=structuredClone(input);change(json);assert.throws(()=>validateHDManifest(json));}
rejects(j=>j.schema_version=2);
rejects(j=>j.animations.running.file='../bad.png');
rejects(j=>j.animations.running.direction_rows=[0,0,1,2,3,4,5,6]);
rejects(j=>j.animations.walking.ticks_per_frame=[2]);
const dimensions={'idle.png':[64,768],'walking.png':[640,768],'running.png':[512,768]};
const oldImage=globalThis.Image,create=URL.createObjectURL,revoke=URL.revokeObjectURL,revoked=[];
URL.createObjectURL=file=>'blob:'+file.name;
URL.revokeObjectURL=url=>revoked.push(url);
globalThis.Image=class{set src(url){[this.naturalWidth,this.naturalHeight]=dimensions[url.slice(5)]||[0,0];queueMicrotask(()=>this.onload());}};
try{
 const files=Object.keys(dimensions).map(name=>({name,size:1024}));
 const loaded=await importHDManifest(input,files);
 assert.equal(Object.keys(loaded.images).length,3);
 loaded.dispose();assert.equal(revoked.length,3);
 await assert.rejects(importHDManifest(input,files.slice(1)),/não encontrado/);
 await assert.rejects(importHDManifest(input,[...files,files[0]]),/duplicado/);
 dimensions['running.png']=[12,12];
 await assert.rejects(importHDManifest(input,files),/precisa ter/);
}finally{globalThis.Image=oldImage;URL.createObjectURL=create;URL.revokeObjectURL=revoke;}
console.log('HD sprites: manifest, 8 directions, timing, PNG import and cleanup OK');