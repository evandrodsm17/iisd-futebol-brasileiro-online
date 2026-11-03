import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync,readFileSync} from 'node:fs';
import {idleDescriptor,renderIdleFrame} from './native-idle.mjs';
const path=new URL('./assets/issd/idle-runtime-local.json',import.meta.url),ref=new URL('../analysis/idle-reference-hashes.json',import.meta.url);
if(existsSync(path)&&existsSync(ref)){
 const data=JSON.parse(readFileSync(path,'utf8')),refs=JSON.parse(readFileSync(ref,'utf8'));
 assert.equal(refs.frames.length,34);
 for(const item of refs.frames){
  const cycle=data.cycles[item.name][item.direction],frame=cycle.frames.find(f=>f.descriptor===item.descriptor),cgram=Buffer.from(frame.cgram,'base64');
  const palettes=Array.from({length:8},(_,bank)=>Array.from({length:16},(_,i)=>{
   const n=cgram.readUInt16LE((bank*16+i)*2);return '#'+[0,5,10].map(shift=>Math.floor(((n>>shift)&31)*255/31).toString(16).padStart(2,'0')).join('');
  }));
  assert.equal(createHash('sha256').update(renderIdleFrame(cycle,item.descriptor,palettes).rgba).digest('hex'),item.sha256,`${item.name}/${item.direction}/${item.descriptor}`);
 }
 for(const cycle of data.cycles.idle){
  assert.equal(idleDescriptor(cycle,0,data.idle_durations,false),cycle.sequence[0]);
  assert.equal(idleDescriptor(cycle,24,data.idle_durations,false),cycle.sequence[1]);
  assert.equal(idleDescriptor(cycle,30,data.idle_durations,false),cycle.sequence[2]);
  assert.equal(idleDescriptor(cycle,54,data.idle_durations,false),cycle.sequence[3]);
 }
 for(const cycle of data.cycles.idle_with_ball)assert.ok(cycle.frames.some(f=>f.descriptor===idleDescriptor(cycle,0,data.idle_durations,true)));
 console.log(`OK: ${refs.frames.length} poses capturadas e sequência de espera sem bola`);
}else console.log('OK: captura local não disponível');
