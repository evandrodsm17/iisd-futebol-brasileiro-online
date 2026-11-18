import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildComparison,summarizeNativeFlight,simulateWebHighShot} from './audit_issd_type6_web_comparison.mjs';

test('summarizes captured native frame gaps without inventing missing updates',()=>{
 const native=JSON.parse(readFileSync('docs/issd-shot-type6-flight.json','utf8'));
 const result=summarizeNativeFlight(native.cases);
 assert.deepEqual(result.map(c=>c.updates),[66,66,66]);
 assert.deepEqual(result.map(c=>c.elapsedFramesToImpact),[75,76,75]);
 assert.deepEqual(result.map(c=>c.intervals),[{1:56,2:9},{1:55,2:10},{1:56,2:9}]);
 assert.equal(result[0].peakNativeHeight,77.859375);
 assert.throws(()=>summarizeNativeFlight([]),RangeError);
});

test('comparison follows current web shot and marks the projection conditional',()=>{
 const native=JSON.parse(readFileSync('docs/issd-shot-type6-flight.json','utf8'));
 const scale=JSON.parse(readFileSync('docs/issd-native-web-scale-diagnostic.json','utf8'));
 const result=buildComparison(native,scale),current=simulateWebHighShot();
 assert.equal(current.simulationTicksPerSecond,60);
 assert.ok(Math.abs(current.gravity-.14)<1e-12);
 assert.ok(Math.abs(current.peakHeight-26.6)<1e-10);
 assert.equal(result.browserHighShot.landingTick,39);
 assert.ok(result.conditionalProjection.assumptions.length>=3);
});
