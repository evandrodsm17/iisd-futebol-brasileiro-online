import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createKeeperDive} from './native-keeper-dive.mjs';
const paths=['./assets/issd/native-keeper-dive-local.json','./assets/issd/editor-preview-local.json'].map(path=>new URL(path,import.meta.url));
if(paths.every(existsSync)){
 const [data,preview]=paths.map(path=>JSON.parse(readFileSync(path,'utf8')));
 const make=(w,h)=>({getContext:()=>({createImageData:()=>({data:new Uint8ClampedArray(w*h*4)}),putImageData(){}})});
 const renderer=createKeeperDive(data,preview,make),req={team:30,skin:0,screenDirection:6};
 assert.equal(renderer.duration,36);assert.equal(renderer.supports(req),true);
 assert.equal(renderer.supports({...req,screenDirection:2}),true);
 assert.equal(renderer.supports({...req,screenDirection:1}),true);
 assert.equal(renderer.supports({...req,screenDirection:3}),true);
 assert.equal(renderer.supports({...req,screenDirection:0}),false);
 for(let t=0;t<renderer.duration;t++)assert.ok(renderer.frame(t,req));
 assert.equal(renderer.frame(36,req),null);
 for(let team=0;team<36;team++)for(const skin of [0,1])for(const screenDirection of [1,2,3,5,6,7])assert.ok(renderer.frame(0,{...req,team,skin,screenDirection}));
 console.log('OK: três poses de goleiro capturadas e paletas disponíveis');
}else console.log('OK: dados locais de goleiro ausentes; teste de renderização ignorado');
