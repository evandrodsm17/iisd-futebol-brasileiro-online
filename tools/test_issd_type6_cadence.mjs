import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {summarizeNativeFlight} from './audit_issd_type6_web_comparison.mjs';

test('observed gaps agree with the independently audited emulator lag frames',()=>{
  const flight=JSON.parse(readFileSync('docs/issd-shot-type6-flight.json','utf8'));
  const cadence=JSON.parse(readFileSync('docs/issd-shot-type6-cadence.json','utf8'));
  const summaries=summarizeNativeFlight(flight.cases);
  assert.equal(cadence.cases.length,3);
  for(let i=0;i<3;i++){
    const c=cadence.cases[i];
    assert.equal(c.direction,summaries[i].direction);
    assert.equal(c.updates,summaries[i].updates);
    assert.equal(c.lagged_without_update.length,summaries[i].intervals[2]);
    assert.ok(c.lagged_without_update.every(frame=>frame.lagged===true));
  }
});
