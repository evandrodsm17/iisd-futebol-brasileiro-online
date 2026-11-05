import assert from 'node:assert/strict';
import {nativeSlideReactionChoice as choose} from './native-slide-reaction-choice.mjs';
const base={attackerAddress:0x0d00,attacker60:0x4000,targetAddress:0x1900,target30:2,target60:0,target68:1,target6c:0,target6e:0,foulSetting:1,global11f9:0,tableByte:1};
assert.deepEqual(choose(base),{route:'selected',carry:0,target6e:0x200,reaction:4,source:0x0d00,globalC6:0x1900});
assert.equal(choose({...base,target30:1}).reaction,0);
for(const change of [{global11f9:0x8000},{tableByte:0},{tableByte:2},{target60:0x800}]){
 const result=choose({...base,...change});assert.equal(result.route,'fallback');assert.equal(result.reaction,0x2002);assert.equal(result.carry,1);
}
assert.deepEqual(choose({...base,target68:0,target6c:0,global11f9:0x8000}),{route:'early_return',carry:0,target6e:0});
assert.equal(choose({...base,target68:0,target6c:0x100,global11f9:0x8000}).route,'fallback');
assert.equal(choose({...base,target68:0,foulSetting:0,global11f9:0x8000}).route,'fallback');
assert.equal(choose({...base,attacker60:0}).route,'early_return');
assert.equal(choose({...base,target6e:0x400}).target6e,0x600);
assert.throws(()=>choose({...base,tableByte:256}),RangeError);
console.log('OK: seleção parcial de reação após contato, baseada no disassembly');
