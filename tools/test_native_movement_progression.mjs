import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {advanceNativeMovementProgression as step,candidateMovementAttributeFields as fields} from './native_movement_progression.mjs';

assert.deepEqual(fields(0x67,2),{limitLow:7,delayLow:3});
assert.deepEqual(fields(0x67,0),{limitLow:3,delayLow:7});
assert.deepEqual(fields(0x21,0),{limitLow:0,delayLow:9});
assert.throws(()=>fields(0xa0,2),RangeError);
assert.deepEqual(fields(0x93,3),{limitLow:3,delayLow:0});
assert.deepEqual(fields(0x67,4),{limitLow:7,delayLow:3});
assert.throws(()=>fields(0x67,5),RangeError);
const fromRaw=fields(0x67,2);
assert.deepEqual(step({timer:0,level:6,limit:fromRaw.limitLow,delay:fromRaw.delayLow}),{timer:3,level:7,carry:false});

assert.deepEqual(step({timer:2,level:3,limit:5,delay:4}),{timer:1,level:3,carry:true});
assert.deepEqual(step({timer:1,level:3,limit:5,delay:4}),{timer:0,level:3,carry:true});
assert.deepEqual(step({timer:0,level:3,limit:5,delay:0xab04}),{timer:4,level:4,carry:false});
assert.deepEqual(step({timer:0,level:5,limit:5,delay:4}),{timer:0xffff,level:5,carry:true});
assert.deepEqual(step({timer:0x8000,level:1,limit:5,delay:1}),{timer:0x7fff,level:1,carry:true});
assert.deepEqual(step({timer:0,level:0xfffe,limit:0xffff,delay:0}),{timer:0,level:0xffff,carry:false});
assert.throws(()=>step({timer:-1,level:0,limit:0,delay:0}),RangeError);
for(const delay of [0,1,4,9]){
 let state={timer:delay,level:0,limit:3,delay};
 const increases=[];
 for(let i=1;i<=4*(delay+1);i++){
  const result=step(state);
  if(!result.carry) increases.push(i);
  state={...state,...result};
 }
 assert.deepEqual(increases,[delay+1,2*(delay+1),3*(delay+1)]);
}
const romPath='International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc';
if(existsSync(romPath)){
 const rom=readFileSync(romPath);
 assert.deepEqual(rom.subarray(0x5d9f,0x5db6),Buffer.from('c67210faa564c562b0f4a56629ff008572e664a564186b','hex'));
}else console.log('ROM local ausente: comparação de opcodes ignorada');
const tracePath='analysis/movement-progression-probe/trace-211.jsonl';
if(existsSync(tracePath)){
 const events=readFileSync(tracePath,'utf8').trim().split(/\r?\n/).map(JSON.parse);
 const pending=new Map();let compared=0;
 for(const event of events){
  if(event.site==='entry'){
   assert.ok(!pending.has(event.actor));pending.set(event.actor,event);
  }else if(event.site==='carry'||event.site==='increment'){
   const before=pending.get(event.actor);assert.ok(before);assert.equal(event.step,before.step);
   const result=step(before);
   assert.equal(result.timer,event.timer);assert.equal(result.level,event.level);
   assert.equal(result.carry,event.site==='carry');pending.delete(event.actor);compared++;
  }
 }
 assert.equal(pending.size,0);assert.equal(compared,510);
 console.log('OK: 510 pares observados no replay local');
}else console.log('Trace local ausente: comparação dinâmica ignorada');
for(const name of ['baseline','patched']){
 const path=`analysis/movement-progression-probe/init-fast-${name}.jsonl`;
 if(existsSync(path)){
  const events=readFileSync(path,'utf8').trim().split(/\r?\n/).map(JSON.parse);
  assert.equal(events.length,44);
  for(let i=0;i<events.length;i+=2){
   const a=events[i],b=events[i+1];
   assert.equal(a.site,'before');assert.equal(b.site,'after');assert.equal(a.actor,b.actor);
   assert.deepEqual(fields(a.raw,a.extra),{limitLow:b.limit_low,delayLow:b.delay_low});
  }
  console.log(`OK: 22 inicializações observadas (${name})`);
 }
}
console.log('OK: progressão nativa, limites, sinais e temporização em chamadas');
