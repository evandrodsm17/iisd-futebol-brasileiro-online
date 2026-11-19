import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {nativePenaltyRectanglesForSelector as select,nativePenaltyHitbox as hit,nativePenaltyContactDisposition as disposition} from './penalty-hitbox.mjs';

test('selection validates native offsets and returns independent records',()=>{
 const data={schema:'issd-penalty-hitbox-tables/v1',tables:[{selector:0,rectangles:[[1,2,3,4]]}]};
 const values=select(data,0);values[0][0]=99;assert.equal(data.tables[0].rectangles[0][0],1);
 for(const invalid of [-1,1,32])assert.throws(()=>select(data,invalid),RangeError);
 assert.throws(()=>select(data,2),RangeError);
 assert.throws(()=>select({...data,tables:[...data.tables,...data.tables]},0),RangeError);
});

test('native flags gate the geometry result before selecting contact',()=>{
 assert.equal(disposition({flags:0x20,shotIndex:2,hit:true}),'blocked');
 assert.equal(disposition({flags:0x40,shotIndex:2,hit:false}),'blocked');
 assert.equal(disposition({flags:0,shotIndex:0,hit:false}),'miss');
 for(const shotIndex of [1,2,3])assert.equal(disposition({flags:0x100,shotIndex,hit:true}),'selected');
 for(const shotIndex of [0,4,5,0xffff])assert.equal(disposition({flags:0x100,shotIndex,hit:true}),'excluded');
 assert.equal(disposition({flags:0,shotIndex:5,hit:true}),'selected');
 assert.throws(()=>disposition({flags:0,shotIndex:-1,hit:true}),RangeError);
});

const asset='dist/assets/issd/penalty-hitbox-tables-local.json';
test('local extraction reproduces sampled collision decisions and unaligned entry', {skip:!existsSync(asset)},()=>{
 const data=JSON.parse(readFileSync(asset,'utf8'));
 const observed=JSON.parse(readFileSync('docs/issd-penalty-selector.json','utf8'));
 assert.equal(data.tables.length,16);assert.deepEqual(select(data,30),[[4,222,4,248],[226,5,248,0]]);
 for(const e of observed.samples){
  const rectangles=select(data,e.selector);
  const result=hit({x:e.x,y:e.y,z:e.z,otherX:e.other_x,otherY:e.other_y,otherZ:e.other_z,objectFlags:e.object_flags,offset:e.offset,rectangles});
  assert.equal(result,e.site==='collision_hit',`frame ${e.frame}`);
 }
});
